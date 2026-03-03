"""
Real-time exercise pose detection via webcam.
Uses MediaPipe Tasks for pose estimation, trained model for classification.
Includes smoothing and skeleton overlay.
"""
import json
import sys
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
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker_lite.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

BUFFER_SIZE = 12
CONFIDENCE_THRESHOLD = 0.65
SCALE_XY = 100.0
SCALE_Z = 200.0
REP_DEBOUNCE = 3

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

    def update(self, label):
        if label == "pushups_down":
            target = "down"
        elif label == "pushups_up":
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

    print("Camera started. Press 'q' to quit.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            detection_result = pose_landmarker.detect(mp_image)

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
                draw_overlay_panel(frame, "Belirsiz", 0.0,
                                   reps=rep_counter.reps)
                h, w = frame.shape[:2]
                cv2.putText(
                    frame, "Tam profilde durun, iyi aydinlatilmis ortam",
                    (10, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 1
                )

            cv2.imshow("Exercise Pose Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        pose_landmarker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
