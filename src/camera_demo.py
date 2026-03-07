"""
Real-time exercise pose detection via webcam.
Uses MediaPipe Tasks for pose estimation, trained model for classification.
Includes smoothing and skeleton overlay.
"""
import json
import sys
import time
import urllib.request
from collections import Counter, deque
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from joblib import load
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Run from ExercisePrediction folder: python -m src.camera_demo
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODELS_DIR = ROOT / "models"
ASSETS_DIR = ROOT / "assets"
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker_lite.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

# Overlay settings
OVERLAY_PATH = ASSETS_DIR / "icons8-plank-100.png"
OVERLAY_SCALE = 0.55          # Overlay boyutu frame genisliginin %55'i
OVERLAY_OPACITY = 0.50         # Overlay seffafligi (0=gorunmez, 1=opak)
OVERLAY_Y_OFFSET = 0.9        # Dikey konum carpani (<1 = yukari kaydir)

# Pozisyon durumuna gore renkler (BGR)
COLOR_RED = (0, 0, 255)        # Hazirlik / yanlis pozisyon
COLOR_ORANGE = (0, 165, 255)   # Pozisyon yaklasimi
COLOR_GREEN = (0, 255, 0)      # Dogru pozisyon

# Hizalama esikleri
ALIGNMENT_GOOD_THRESHOLD = 0.70   # Bu ustunde = yesil
ALIGNMENT_CLOSE_THRESHOLD = 0.40  # Bu ustunde = turuncu, altinda = kirmizi

BUFFER_SIZE = 12
CONFIDENCE_THRESHOLD = 0.65
SCALE_XY = 100.0
SCALE_Z = 200.0
REP_DEBOUNCE = 3
REP_DISPLAY_FRAMES = 20

KCAL_PER_REP = {
    "pushups": 0.4,
    "situp": 0.3,
    "squats": 0.35,
    "pullups": 0.5,
    "jumping_jacks": 0.2,
}

EXERCISE_NAMES = {
    "pushups": "Sinav",
    "situp": "Mekik",
    "squats": "Squat",
    "pullups": "Barfiks",
    "jumping_jacks": "Ziplama",
}

BODY_LANDMARK_INDICES = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
BODY_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
]

# MediaPipe landmark index to column name (for metadata alignment)
# Order matches MediaPipe PoseLandmark 0-32
MP_INDEX_TO_NAME = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]
# Alias for dataset column names that may differ from MediaPipe
NAME_ALIASES = {
    "right_index_1": "right_index", "left_index_1": "left_index",
    "left_pinky_1": "left_pinky", "right_pinky_1": "right_pinky",
}

# Turkce hareket karsiliklari (pose label -> Turkce gosterim)
POSE_TO_TURKISH = {
    "situp_up": "Mekik (Yukari)",
    "situp_down": "Mekik (Asagi)",
    "pushups_up": "Sinav (Yukari)",
    "pushups_down": "Sinav (Asagi)",
    "pullups_up": "Barfiks (Yukari)",
    "pullups_down": "Barfiks (Asagi)",
    "squats_up": "Squat (Yukari)",
    "squats_down": "Squat (Asagi)",
    "jumping_jacks_up": "Ziplama (Yukari)",
    "jumping_jacks_down": "Ziplama (Asagi)",
    "Belirsiz": "Belirsiz",
}


def label_to_turkish(label):
    """Pose etiketini Turkce karsiligina cevir."""
    return POSE_TO_TURKISH.get(label, label)


def load_overlay(path, frame_w, frame_h):
    """PNG overlay'i yukle, alpha kanaliyla birlikte. Frame boyutuna gore olcekle."""
    overlay = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if overlay is None:
        print(f"Overlay yuklenemedi: {path}")
        return None
    # Alpha kanali yoksa ekle (tam opak)
    if overlay.shape[2] == 3:
        alpha_ch = np.full((*overlay.shape[:2], 1), 255, dtype=overlay.dtype)
        overlay = np.concatenate([overlay, alpha_ch], axis=2)

    # Frame genisliginin %55'i, yuksekligin %35-40'i hedeflenir
    target_w = int(frame_w * OVERLAY_SCALE)
    target_h = int(frame_h * 0.38)
    overlay = cv2.resize(overlay, (target_w, target_h), interpolation=cv2.INTER_AREA)
    return overlay


def recolor_overlay(overlay, color_bgr):
    """
    Overlay'in alpha > 0 olan piksellerini verilen BGR renkle degistirir.
    Alpha kanali korunur.
    """
    if overlay is None:
        return None
    colored = overlay.copy()
    alpha_mask = colored[:, :, 3] > 0
    colored[alpha_mask, 0] = color_bgr[0]  # B
    colored[alpha_mask, 1] = color_bgr[1]  # G
    colored[alpha_mask, 2] = color_bgr[2]  # R
    return colored


def check_pose_alignment(pose_landmarks, overlay_shape, frame_shape):
    """
    MediaPipe landmark'lari ile overlay silüeti arasindaki hizalamayi kontrol eder.
    Donen deger: (match_pct, status)
        match_pct: 0.0-1.0 arasi hizalama yuzdesi
        status: 'aligned', 'close', 'no_pose'
    
    Kontrol edilen parametreler:
    1. Temel eklemlerin gorunurlugu (omuz + kalca)
    2. Vucut olcegi (overlay ile uyum)
    3. Vucut merkez konumu (overlay merkezine yakinlik)
    """
    fh, fw = frame_shape[:2]
    oh, ow = overlay_shape[:2]

    # Overlay merkez koordinatlari
    overlay_cx = fw / 2
    overlay_cy = (fh / 2) * OVERLAY_Y_OFFSET

    # Temel eklem indeksleri
    L_SHOULDER, R_SHOULDER = 11, 12
    L_HIP, R_HIP = 23, 24
    L_WRIST, R_WRIST = 15, 16
    L_ANKLE, R_ANKLE = 27, 28

    key_indices = [L_SHOULDER, R_SHOULDER, L_HIP, R_HIP]
    extra_indices = [L_WRIST, R_WRIST, L_ANKLE, R_ANKLE]

    # 1. Gorunurluk kontrolu
    visibility_score = 0.0
    for idx in key_indices:
        vis = pose_landmarks[idx].visibility
        if vis is not None and vis > 0.5:
            visibility_score += 0.25

    if visibility_score < 0.5:
        return 0.0, "no_pose"

    # Ekstra eklem gorunurlugu (bonus)
    extra_vis = 0.0
    for idx in extra_indices:
        vis = pose_landmarks[idx].visibility
        if vis is not None and vis > 0.5:
            extra_vis += 0.125

    # 2. Vucut olcegi kontrolu (omuz genisligi vs overlay genisligi)
    ls = pose_landmarks[L_SHOULDER]
    rs = pose_landmarks[R_SHOULDER]
    shoulder_dist_px = abs(ls.x - rs.x) * fw
    expected_width = ow * 0.35  # Overlay genisliginin %35'i omuz genisligi olmali
    scale_ratio = shoulder_dist_px / max(expected_width, 1)
    # 1.0'a ne kadar yakinsa o kadar iyi (±%30 tolerans)
    scale_score = max(0.0, 1.0 - abs(1.0 - scale_ratio) / 0.30)

    # 3. Merkez konum kontrolu
    body_cx = ((ls.x + rs.x) / 2) * fw
    lh = pose_landmarks[L_HIP]
    rh = pose_landmarks[R_HIP]
    body_cy = ((ls.y + rs.y + lh.y + rh.y) / 4) * fh

    dx = abs(body_cx - overlay_cx) / fw
    dy = abs(body_cy - overlay_cy) / fh
    position_score = max(0.0, 1.0 - (dx + dy) * 2)

    # Toplam skor
    match_pct = (
        visibility_score * 0.30
        + extra_vis * 0.10
        + scale_score * 0.30
        + position_score * 0.30
    )
    match_pct = min(1.0, match_pct)

    if match_pct >= ALIGNMENT_GOOD_THRESHOLD:
        status = "aligned"
    elif match_pct >= ALIGNMENT_CLOSE_THRESHOLD:
        status = "close"
    else:
        status = "no_pose"

    return match_pct, status


def get_alignment_color(status):
    """Hizalama durumuna gore overlay rengini dondur (BGR)."""
    if status == "aligned":
        return COLOR_GREEN
    elif status == "close":
        return COLOR_ORANGE
    else:
        return COLOR_RED


def draw_alignment_bar(frame, match_pct, status):
    """Ekranin alt kisminda hizalama yuzdesi cubugu cizer."""
    h, w = frame.shape[:2]
    bar_h = 20
    bar_y = h - 50
    bar_x = 60
    bar_w = w - 120

    # Arka plan
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h),
                  (40, 40, 40), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h),
                  (80, 80, 80), 1)

    # Doluluk
    fill_w = int(bar_w * match_pct)
    color = get_alignment_color(status)
    if fill_w > 0:
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + fill_w, bar_y + bar_h), color, -1)

    # Yuzde metni
    pct_text = f"Hizalama: %{match_pct * 100:.0f}"
    cv2.putText(frame, pct_text,
                (bar_x + bar_w // 2 - 60, bar_y - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)


def draw_alignment_status(frame, status):
    """Ekranin ust ortasinda hizalama durumu yazisi gosterir."""
    h, w = frame.shape[:2]
    messages = {
        "aligned": "Harika! Dogru pozisyondasiniz.",
        "close": "Neredeyse! Biraz daha ayarlayin.",
        "no_pose": "Siluete hizalanin...",
    }
    msg = messages.get(status, "")
    color = get_alignment_color(status)

    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(msg, font, 0.7, 2)
    tx = (w - tw) // 2
    ty = h - 80

    # Arka plan kutusu
    cv2.rectangle(frame, (tx - 10, ty - th - 8), (tx + tw + 10, ty + 8),
                  (20, 20, 20), -1)
    cv2.putText(frame, msg, (tx, ty), font, 0.7, color, 2)


def apply_overlay(frame, overlay, opacity=None):
    """
    Overlay PNG'yi frame'in ortasina (hafif yukari) alpha blending ile uygula.
    opacity: 0.0-1.0 arasi seffaflik carpani (None ise OVERLAY_OPACITY kullanilir)
    """
    if overlay is None:
        return frame

    if opacity is None:
        opacity = OVERLAY_OPACITY

    fh, fw = frame.shape[:2]
    oh, ow = overlay.shape[:2]

    # Ortala, hafif yukari kaydir (OVERLAY_Y_OFFSET)
    x = max(0, fw // 2 - ow // 2)
    y = max(0, int((fh // 2 - oh // 2) * OVERLAY_Y_OFFSET))

    # Frame sinirlari icinde kal
    x_end = min(x + ow, fw)
    y_end = min(y + oh, fh)
    ow_actual = x_end - x
    oh_actual = y_end - y

    if ow_actual <= 0 or oh_actual <= 0:
        return frame

    overlay_crop = overlay[:oh_actual, :ow_actual]
    alpha = (overlay_crop[:, :, 3] / 255.0) * opacity

    roi = frame[y:y_end, x:x_end]
    for c in range(3):
        roi[:, :, c] = (
            alpha * overlay_crop[:, :, c]
            + (1 - alpha) * roi[:, :, c]
        ).astype(np.uint8)
    frame[y:y_end, x:x_end] = roi
    return frame


def draw_body_skeleton(img, pose_landmarks):
    """Draw only the 14 essential body landmarks and connections (skip face/hands/feet)."""
    h, w = img.shape[:2]
    points = {}
    for idx in BODY_LANDMARK_INDICES:
        lm = pose_landmarks[idx]
        px, py = int(lm.x * w), int(lm.y * h)
        points[idx] = (px, py)
        cv2.circle(img, (px, py), 5, (0, 212, 170), -1)
        cv2.circle(img, (px, py), 7, (0, 212, 170), 1)

    for a, b in BODY_CONNECTIONS:
        if a in points and b in points:
            cv2.line(img, points[a], points[b], (0, 255, 0), 2)


def draw_overlay_panel(frame, label, conf, reps=None):
    """Ekranda okunakli bir bilgi paneli cizer."""
    h, w = frame.shape[:2]
    has_reps = reps is not None and reps > 0
    panel_h = 120 if has_reps else 90
    panel_w = min(400, w - 20)
    x1, y1 = 10, 10
    x2, y2 = x1 + panel_w, y1 + panel_h

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 100), 2)

    turkce = label_to_turkish(label)
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0, 255, 150) if label != "Belirsiz" else (100, 100, 100)

    cv2.putText(frame, f"Hareket: {turkce}", (x1 + 12, y1 + 38), font, 0.9, color, 2)
    cv2.putText(frame, f"Guven: %{conf * 100:.0f}", (x1 + 12, y1 + 72), font, 0.7, (200, 200, 200), 2)

    if has_reps:
        cv2.putText(frame, f"Tekrar: {reps}", (x1 + 12, y1 + 106), font, 0.8, (0, 212, 170), 2)


def draw_center_counter(frame, reps, frames_since_rep):
    """Draw a large fading rep number in the center of the frame."""
    if frames_since_rep >= REP_DISPLAY_FRAMES:
        return
    alpha = 1.0 - (frames_since_rep / REP_DISPLAY_FRAMES)
    h, w = frame.shape[:2]
    text = str(reps)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 4.0
    thickness = 8
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    tx = (w - tw) // 2
    ty = (h + th) // 2

    overlay = frame.copy()
    cv2.putText(overlay, text, (tx, ty), font, scale, (200, 200, 200), thickness)
    cv2.addWeighted(overlay, alpha * 0.6, frame, 1.0 - alpha * 0.6, 0, frame)


def ensure_pose_model():
    """Download pose_landmarker model if not present."""
    if POSE_MODEL_PATH.exists():
        return str(POSE_MODEL_PATH)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("Downloading pose_landmarker model...")
    urllib.request.urlretrieve(POSE_MODEL_URL, POSE_MODEL_PATH)
    print("Download complete.")
    return str(POSE_MODEL_PATH)


def load_metadata():
    """Load metadata.json (feature_columns) and model artifacts."""
    meta_path = MODELS_DIR / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(
            "metadata.json not found. Train the model first: python run_competition.py ExercisePrediction"
        )
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    feature_columns = meta.get("feature_columns", [])
    if not feature_columns:
        raise ValueError("metadata.json must contain 'feature_columns'")

    encoder = load(MODELS_DIR / "encoder.pkl")
    scaler = load(MODELS_DIR / "scaler.pkl")
    categories = load(MODELS_DIR / "categories.pkl")

    meta_pkl = load(MODELS_DIR / "meta.pkl")
    model_type = meta_pkl.get("model_type", "xgboost")
    model_path = meta_pkl.get("model_path")
    if model_path and not Path(model_path).is_absolute():
        model_path = MODELS_DIR / Path(model_path).name

    if model_type == "xgboost":
        model = load(model_path)
    else:
        import torch
        from src.train import build_pytorch_model
        input_size = meta_pkl.get("input_size", 99)
        num_classes = meta_pkl.get("num_classes", len(categories))
        model = build_pytorch_model(input_size, num_classes)
        model.load_state_dict(torch.load(model_path))
        model.eval()

    return model, encoder, scaler, categories, model_type, feature_columns


def landmarks_to_vector(landmark_list, feature_columns):
    """
    Convert MediaPipe landmarks (list of NormalizedLandmark) to feature vector.
    landmark_list: list of 33 landmarks from result.pose_landmarks[0]
    """
    name_to_idx = {name: i for i, name in enumerate(MP_INDEX_TO_NAME)}
    for alias, canonical in NAME_ALIASES.items():
        name_to_idx[alias] = name_to_idx.get(canonical, 0)

    values = []
    for col in feature_columns:
        if not col.startswith(("x_", "y_", "z_")):
            continue
        axis = col[0]
        name = col[2:].strip()
        name = NAME_ALIASES.get(name, name)
        idx = name_to_idx.get(name, -1)
        if idx < 0:
            values.append(0.0)
            continue
        lm = landmark_list[idx]
        x_val = lm.x if lm.x is not None else 0.0
        y_val = lm.y if lm.y is not None else 0.0
        z_val = lm.z if lm.z is not None else 0.0
        if axis == "x":
            values.append((x_val - 0.5) * SCALE_XY)
        elif axis == "y":
            values.append((y_val - 0.5) * SCALE_XY)
        else:
            values.append(z_val * SCALE_Z)
    return np.array(values, dtype=np.float32).reshape(1, -1)


def predict_with_smoothing(model, encoder, scaler, categories, model_type, X, buffer):
    """Predict with smoothing: use mode of last N predictions if confidence >= threshold."""
    X_scaled = scaler.transform(X)
    if model_type == "xgboost":
        pred_idx = model.predict(X_scaled)[0]
        probs = model.predict_proba(X_scaled)[0]
    else:
        import torch
        with torch.no_grad():
            X_t = torch.from_numpy(X_scaled.astype(np.float32))
            logits = model(X_t)
            probs = torch.softmax(logits, dim=1).numpy()[0]
            pred_idx = int(np.argmax(probs))

    conf = float(probs[pred_idx])
    if conf < CONFIDENCE_THRESHOLD:
        buffer.append("Belirsiz")
    else:
        label = encoder.inverse_transform([pred_idx])[0]
        buffer.append(label)

    counted = Counter(buffer)
    mode_label = counted.most_common(1)[0][0]
    return mode_label, conf



class RepCounter:
    """State machine for counting exercise repetitions (down -> up = 1 rep)."""

    def __init__(self):
        self.phase = "idle"
        self.reps = 0
        self.debounce_count = 0
        self.pending_phase = None
        self.frames_since_rep = REP_DISPLAY_FRAMES
        self.exercise_reps = {}
        self.start_time = None

    def update(self, label):
        self.frames_since_rep += 1

        if self.start_time is None and label != "Belirsiz":
            self.start_time = time.time()

        exercise = label.rsplit("_", 1)[0] if "_" in label else None

        if label.endswith("_down"):
            target = "down"
        elif label.endswith("_up"):
            target = "up"
        else:
            self.debounce_count = 0
            self.pending_phase = None
            return

        if self.phase == "idle" and target == "down":
            self._try_transition("down")
        elif self.phase == "down" and target == "up":
            if self._try_transition("up"):
                self.reps += 1
                self.frames_since_rep = 0
                if exercise:
                    self.exercise_reps[exercise] = (
                        self.exercise_reps.get(exercise, 0) + 1
                    )
        elif self.phase == "up" and target == "down":
            self._try_transition("down")

    def _try_transition(self, target):
        if self.pending_phase == target:
            self.debounce_count += 1
        else:
            self.pending_phase = target
            self.debounce_count = 1

        if self.debounce_count >= REP_DEBOUNCE:
            self.phase = target
            self.pending_phase = None
            self.debounce_count = 0
            return True
        return False

    def summary(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        mins, secs = int(elapsed) // 60, int(elapsed) % 60
        total_kcal = sum(
            count * KCAL_PER_REP.get(ex, 0.3)
            for ex, count in self.exercise_reps.items()
        )
        return {
            "elapsed": elapsed,
            "mins": mins,
            "secs": secs,
            "exercise_reps": self.exercise_reps,
            "total_kcal": total_kcal,
        }


def main():
    print("Loading model and metadata...")
    model, encoder, scaler, categories, model_type, feature_columns = load_metadata()
    print("Model loaded. Preparing pose detector...")

    model_path = ensure_pose_model()
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
    )
    pose_landmarker = vision.PoseLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        sys.exit(1)

    buffer = deque(maxlen=BUFFER_SIZE)
    rep_counter = RepCounter()

    # Overlay'i ilk frame boyutuna gore yukle (bir kere)
    overlay_img = None
    overlay_base = None  # Orijinal (renksiz) overlay
    overlay_loaded = False
    current_overlay_color = None

    print("Camera started. Press 'q' to quit.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            # Overlay'i ilk frame geldiginde yukle (boyut bilgisi icin)
            if not overlay_loaded:
                fh, fw = frame.shape[:2]
                if OVERLAY_PATH.exists():
                    overlay_base = load_overlay(OVERLAY_PATH, fw, fh)
                    if overlay_base is not None:
                        print(f"Overlay yuklendi: {OVERLAY_PATH.name} "
                              f"({overlay_base.shape[1]}x{overlay_base.shape[0]})")
                        # Baslangicta kirmizi (hazirlik)
                        overlay_img = recolor_overlay(overlay_base, COLOR_RED)
                        current_overlay_color = COLOR_RED
                    else:
                        print("Overlay yuklenemedi, overlay'siz devam ediliyor.")
                else:
                    print(f"Overlay dosyasi bulunamadi: {OVERLAY_PATH}")
                overlay_loaded = True

            # Pose algilama (overlay rengi icin once yapilmali)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            detection_result = pose_landmarker.detect(mp_image)

            # Hizalama kontrolu ve overlay renk guncelleme
            alignment_pct = 0.0
            alignment_status = "no_pose"

            if detection_result.pose_landmarks and overlay_base is not None:
                pose_landmarks = detection_result.pose_landmarks[0]
                alignment_pct, alignment_status = check_pose_alignment(
                    pose_landmarks, overlay_base.shape, frame.shape
                )
                # Renk degistir (sadece durum degistiginde, performans icin)
                new_color = get_alignment_color(alignment_status)
                if new_color != current_overlay_color:
                    overlay_img = recolor_overlay(overlay_base, new_color)
                    current_overlay_color = new_color

            # Siluet overlay'i uygula (her zaman, arka planda)
            frame = apply_overlay(frame, overlay_img)

            if detection_result.pose_landmarks:
                pose_landmarks = detection_result.pose_landmarks[0]
                draw_body_skeleton(frame, pose_landmarks)
                try:
                    X = landmarks_to_vector(pose_landmarks, feature_columns)
                    if X.shape[1] == scaler.n_features_in_:
                        label, conf = predict_with_smoothing(
                            model, encoder, scaler, categories, model_type, X, buffer
                        )
                        rep_counter.update(label)
                        draw_overlay_panel(frame, label, conf,
                                           reps=rep_counter.reps)
                except Exception as e:
                    cv2.putText(
                        frame, f"Error: {e}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
                    )
            else:
                rep_counter.frames_since_rep += 1
                draw_overlay_panel(frame, "Belirsiz", 0.0,
                                   reps=rep_counter.reps)

            # Hizalama cubugu ve durum mesaji
            if overlay_base is not None:
                draw_alignment_bar(frame, alignment_pct, alignment_status)
                draw_alignment_status(frame, alignment_status)

            draw_center_counter(frame, rep_counter.reps,
                                rep_counter.frames_since_rep)

            cv2.imshow("Exercise Pose Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        pose_landmarker.close()
        cap.release()
        cv2.destroyAllWindows()

        if rep_counter.reps > 0:
            s = rep_counter.summary()
            print("\n" + "=" * 40)
            print("  ANTRENMAN OZETI")
            print("=" * 40)
            print(f"  Sure: {s['mins']} dk {s['secs']} sn")
            for ex, count in s["exercise_reps"].items():
                name = EXERCISE_NAMES.get(ex, ex)
                print(f"  {name}: {count} tekrar")
            print(f"  Tahmini Kalori: {s['total_kcal']:.1f} kcal")
            print("=" * 40)


if __name__ == "__main__":
    main()
