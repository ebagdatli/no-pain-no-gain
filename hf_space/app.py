"""
BecomeAPro - AI-Powered Exercise Tracker (Hugging Face Space)
Streamlit + WebRTC for in-browser real-time pose detection.
"""
import json
import logging
import urllib.request
from collections import Counter, deque
from pathlib import Path
from threading import Lock

import av
import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
from joblib import load
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from streamlit_webrtc import WebRtcMode, webrtc_streamer

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"
if not (MODELS_DIR / "meta.pkl").exists():
    MODELS_DIR = ROOT
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker_lite.task"
POSE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

BUFFER_SIZE = 12
CONFIDENCE_THRESHOLD = 0.65
SCALE_XY = 100.0
SCALE_Z = 200.0
FRAME_SKIP = 2
REP_DEBOUNCE = 3

BODY_LANDMARK_INDICES = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
BODY_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
]

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

NAME_ALIASES = {
    "right_index_1": "right_index", "left_index_1": "left_index",
    "left_pinky_1": "left_pinky", "right_pinky_1": "right_pinky",
}

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

EXERCISES = [
    {"name": "Sinav", "en": "Push-ups", "icon": "\U0001f4aa",
     "desc": "Gogus, omuz ve triceps kaslari icin temel egzersiz.", "color": "#00d4aa"},
    {"name": "Mekik", "en": "Sit-ups", "icon": "\U0001f504",
     "desc": "Karin kaslari icin etkili bir core egzersizi.", "color": "#7c3aed"},
    {"name": "Squat", "en": "Squats", "icon": "\U0001f9b5",
     "desc": "Bacak ve kalca kaslari icin en etkili hareket.", "color": "#f59e0b"},
    {"name": "Barfiks", "en": "Pull-ups", "icon": "\U0001f9d7",
     "desc": "Sirt ve biceps kaslarini guclendiren egzersiz.", "color": "#ef4444"},
    {"name": "Ziplama", "en": "Jumping Jacks", "icon": "\U0001f938",
     "desc": "Tam vucut kardiyo ve koordinasyon egzersizi.", "color": "#3b82f6"},
]

# ---------------------------------------------------------------------------
# Page config (must be first st call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="BecomeAPro | AI Exercise Tracker",
    page_icon="\U0001f3cb\ufe0f",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """\
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
#MainMenu, footer, header {visibility: hidden;}
.block-container {
    padding-top: 0 !important;
    max-width: 1100px;
    margin: 0 auto;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

.stApp {
    background: linear-gradient(180deg, #080810 0%, #0d0d1a 40%, #080810 100%);
    color: #e0e0e8;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Streamlit column gap normalization */
[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
    align-items: stretch !important;
}
[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stColumn"] > div {
    flex: 1;
}

/* Hero */
.hero {
    text-align: center;
    padding: 4rem 1rem 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60%; left: -30%; width: 160%; height: 220%;
    background:
        radial-gradient(ellipse at 30% 50%, rgba(0,212,170,0.07) 0%, transparent 50%),
        radial-gradient(ellipse at 70% 50%, rgba(124,58,237,0.07) 0%, transparent 50%);
    animation: drift 10s ease-in-out infinite alternate;
    pointer-events: none;
}
@keyframes drift {
    from { transform: translate(0,0) rotate(0deg); }
    to   { transform: translate(-3%,2%) rotate(1deg); }
}
.hero-badge {
    display: inline-block;
    background: rgba(0,212,170,0.08);
    border: 1px solid rgba(0,212,170,0.25);
    border-radius: 50px;
    padding: 6px 20px;
    font-size: 0.82rem;
    color: #00d4aa;
    font-weight: 600;
    margin-bottom: 1.6rem;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}
.hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.8rem);
    font-weight: 800;
    line-height: 1.08;
    margin: 0 0 1.1rem;
    color: #ffffff;
    position: relative;
}
.hero h1 .grad {
    background: linear-gradient(135deg, #00d4aa 0%, #7c3aed 55%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 1.08rem;
    color: #7a7a95;
    max-width: 540px;
    margin: 0 auto;
    line-height: 1.7;
    position: relative;
}

/* Section Titles */
.sec-title {
    font-size: 1.75rem;
    font-weight: 700;
    text-align: center;
    margin: 2.5rem 0 0.4rem;
    color: #fff;
}
.sec-sub {
    text-align: center;
    color: #7a7a95;
    font-size: 0.92rem;
    margin-bottom: 1.8rem;
}

/* Glass Card */
.g-card {
    background: rgba(18,18,30,0.65);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.055);
    border-radius: 16px;
    padding: 1.6rem 1.3rem;
    transition: all 0.35s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
    height: 100%;
    box-sizing: border-box;
}
.g-card:hover {
    border-color: rgba(0,212,170,0.18);
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.25);
}

/* Step Cards */
.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px; height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    color: #fff;
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.8rem;
}
.step-t { font-size: 1.05rem; font-weight: 600; color: #fff; margin-bottom: 0.4rem; }
.step-d { font-size: 0.85rem; color: #7a7a95; line-height: 1.6; }

/* Exercise Cards */
.accent-top {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
    opacity: 0.7;
    transition: opacity 0.3s;
}
.g-card:hover .accent-top { opacity: 1; }
.ex-icon  { font-size: 2.2rem; margin-bottom: 0.6rem; display: block; }
.ex-name  { font-size: 1rem; font-weight: 600; color: #fff; margin-bottom: 0.1rem; }
.ex-en    { font-size: 0.75rem; color: #5a5a7a; margin-bottom: 0.4rem; }
.ex-desc  { font-size: 0.8rem; color: #7a7a95; line-height: 1.5; }

/* CTA Section */
.cta-box {
    text-align: center;
    padding: 2.5rem 2rem 1.2rem;
    background: linear-gradient(135deg, rgba(0,212,170,0.04), rgba(124,58,237,0.04));
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 20px;
    margin: 2rem 0 0;
    position: relative;
    overflow: hidden;
}
.cta-box::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(0,212,170,0.12), transparent 40%, rgba(124,58,237,0.12));
    z-index: 0;
    pointer-events: none;
}
.cta-t { font-size: 1.6rem; font-weight: 700; color: #fff; margin-bottom: 0.4rem; position: relative; }
.cta-d { color: #7a7a95; margin-bottom: 0.2rem; font-size: 0.9rem; position: relative; }

/* Metric Card */
.m-val {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.m-lbl { font-size: 0.82rem; color: #7a7a95; font-weight: 500; margin-top: 4px; }

/* Primary Button */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 2.8rem !important;
    font-size: 1.08rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    color: #080810 !important;
    box-shadow: 0 4px 24px rgba(0,212,170,0.22) !important;
    transition: all 0.3s cubic-bezier(.4,0,.2,1) !important;
    letter-spacing: 0.3px !important;
    min-height: 56px !important;
}
div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 8px 36px rgba(0,212,170,0.38) !important;
    transform: translateY(-2px) !important;
}

/* Tip Box */
.tip-box {
    background: rgba(59,130,246,0.06);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 14px;
    padding: 1rem 1.4rem;
    color: #8ab4f8;
    font-size: 0.86rem;
    line-height: 1.6;
    margin: 0.8rem 0;
}
.tip-box strong { color: #a8ccff; }

/* Helpers */
.sep {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    margin: 2rem 0;
}

/* Footer */
.foot {
    text-align: center;
    padding: 2rem 0 1.5rem;
    color: #444460;
    font-size: 0.82rem;
    margin-top: 2.5rem;
    border-top: 1px solid rgba(255,255,255,0.04);
}
.foot a { color: #00d4aa; text-decoration: none; }

/* Scrollbar */
::-webkit-scrollbar       { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a52; }

/* WebRTC component wrapper */
iframe[title*="webrtc"] {
    border: 1px solid rgba(255,255,255,0.055) !important;
    border-radius: 16px !important;
    background: rgba(18,18,30,0.65) !important;
}

/* Onboarding Card */
.onboard-card {
    background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(0,212,170,0.08));
    border: 1px solid rgba(124,58,237,0.15);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
}
.onboard-card h3 { color: #fff; font-size: 1.3rem; margin-bottom: 0.6rem; }
.onboard-card p { color: #7a7a95; font-size: 0.92rem; line-height: 1.6; }
</style>
"""


# ---------------------------------------------------------------------------
# Pose detection helpers (from camera_demo.py, adapted for WebRTC)
# ---------------------------------------------------------------------------


def label_to_turkish(label: str) -> str:
    return POSE_TO_TURKISH.get(label, label)


def ensure_pose_model() -> str:
    if POSE_MODEL_PATH.exists():
        return str(POSE_MODEL_PATH)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading pose_landmarker model...")
    urllib.request.urlretrieve(POSE_MODEL_URL, POSE_MODEL_PATH)
    logger.info("Download complete.")
    return str(POSE_MODEL_PATH)


def landmarks_to_vector(landmark_list, feature_columns):
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


def predict_single(ml_model, encoder, scaler, model_type, X, buffer):
    """Run prediction with smoothing over the last N frames."""
    X_scaled = scaler.transform(X)
    if model_type == "xgboost":
        pred_idx = ml_model.predict(X_scaled)[0]
        probs = ml_model.predict_proba(X_scaled)[0]
    else:
        import torch
        with torch.no_grad():
            X_t = torch.from_numpy(X_scaled.astype(np.float32))
            logits = ml_model(X_t)
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


def draw_overlay_panel(frame, label, conf, reps=None):
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

    cv2.putText(frame, f"Hareket: {turkce}", (x1 + 12, y1 + 38),
                font, 0.9, color, 2)
    cv2.putText(frame, f"Guven: %{conf * 100:.0f}", (x1 + 12, y1 + 72),
                font, 0.7, (200, 200, 200), 2)

    if has_reps:
        cv2.putText(frame, f"Tekrar: {reps}", (x1 + 12, y1 + 106),
                    font, 0.8, (0, 212, 170), 2)


# ---------------------------------------------------------------------------
# Thread-safe model & pose landmarker loader
# ---------------------------------------------------------------------------


@st.cache_resource
def load_all_artifacts():
    """Load ML model, scaler, encoder, feature columns, and MediaPipe pose landmarker.
    Returns None tuple if model files are missing."""
    meta_path = MODELS_DIR / "meta.pkl"
    metadata_path = MODELS_DIR / "metadata.json"
    if not meta_path.exists() or not metadata_path.exists():
        return None, None, None, None, None, None, None

    meta = load(meta_path)
    encoder = load(MODELS_DIR / "encoder.pkl")
    scaler = load(MODELS_DIR / "scaler.pkl")
    model_type = meta.get("model_type", "xgboost")

    model_path = meta.get("model_path")
    if model_path:
        filename = model_path.replace("\\", "/").split("/")[-1]
        model_path = MODELS_DIR / filename

    if model_type == "xgboost":
        ml_model = load(model_path)
    else:
        import torch
        input_size = meta.get("input_size", 99)
        num_classes = meta.get("num_classes", 10)
        from torch import nn
        ml_model = nn.Sequential(
            nn.Linear(input_size, 200),
            nn.ReLU(),
            nn.Linear(200, num_classes),
        )
        ml_model.load_state_dict(torch.load(model_path, map_location="cpu"))
        ml_model.eval()

    with open(metadata_path, encoding="utf-8") as f:
        feature_columns = json.load(f).get("feature_columns", [])

    pose_model_path = ensure_pose_model()
    base_options = mp_python.BaseOptions(model_asset_path=pose_model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
    )
    pose_landmarker = vision.PoseLandmarker.create_from_options(options)

    return ml_model, encoder, scaler, model_type, feature_columns, pose_landmarker, meta


# ---------------------------------------------------------------------------
# WebRTC video callback
# ---------------------------------------------------------------------------

_buffer_lock = Lock()
_prediction_buffer: deque = deque(maxlen=BUFFER_SIZE)


def _draw_body_skeleton(img, pose_landmarks):
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


def make_video_frame_callback(ml_model, encoder, scaler, model_type,
                               feature_columns, pose_landmarker):
    """Create a closure that captures loaded artifacts for the WebRTC callback."""
    frame_counter = [0]
    cached_label = ["Belirsiz"]
    cached_conf = [0.0]

    rep_state = {
        "phase": "idle",
        "reps": 0,
        "debounce_count": 0,
        "pending_phase": None,
    }

    def _update_rep_counter(label):
        """State machine: idle -> down -> up (rep++) -> down -> up (rep++) ..."""
        phase = rep_state["phase"]

        if label == "pushups_down":
            target = "down"
        elif label == "pushups_up":
            target = "up"
        else:
            rep_state["debounce_count"] = 0
            rep_state["pending_phase"] = None
            return

        if phase == "idle" and target == "down":
            _try_transition("down")
        elif phase == "down" and target == "up":
            if _try_transition("up"):
                rep_state["reps"] += 1
        elif phase == "up" and target == "down":
            _try_transition("down")

    def _try_transition(target):
        if rep_state["pending_phase"] == target:
            rep_state["debounce_count"] += 1
        else:
            rep_state["pending_phase"] = target
            rep_state["debounce_count"] = 1

        if rep_state["debounce_count"] >= REP_DEBOUNCE:
            rep_state["phase"] = target
            rep_state["pending_phase"] = None
            rep_state["debounce_count"] = 0
            return True
        return False

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        frame_counter[0] += 1
        should_process = (frame_counter[0] % FRAME_SKIP == 0)

        if not should_process:
            draw_overlay_panel(img, cached_label[0], cached_conf[0],
                               reps=rep_state["reps"])
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        try:
            detection_result = pose_landmarker.detect(mp_image)
        except Exception:
            draw_overlay_panel(img, "Belirsiz", 0.0, reps=rep_state["reps"])
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        if detection_result.pose_landmarks:
            pose_landmarks = detection_result.pose_landmarks[0]
            _draw_body_skeleton(img, pose_landmarks)

            try:
                X = landmarks_to_vector(pose_landmarks, feature_columns)
                if X.shape[1] == scaler.n_features_in_:
                    with _buffer_lock:
                        label, conf = predict_single(
                            ml_model, encoder, scaler, model_type,
                            X, _prediction_buffer,
                        )
                    cached_label[0] = label
                    cached_conf[0] = conf
                    _update_rep_counter(label)
                    draw_overlay_panel(img, label, conf,
                                       reps=rep_state["reps"])
            except Exception as e:
                cv2.putText(img, f"Error: {e}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        else:
            cached_label[0] = "Belirsiz"
            cached_conf[0] = 0.0
            draw_overlay_panel(img, "Belirsiz", 0.0, reps=rep_state["reps"])
            h, w = img.shape[:2]
            cv2.putText(img, "Tam vucut gorunumunde durun",
                        (10, h - 25), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (0, 165, 255), 1)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    return video_frame_callback


# ---------------------------------------------------------------------------
# UI Sections
# ---------------------------------------------------------------------------


def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">AI-Powered Fitness</div>
            <h1>
                Egzersizlerini<br>
                <span class="grad">Yapay Zeka ile Takip Et</span>
            </h1>
            <p class="hero-sub">
                Kamerani ac, egzersizini yap. Yapay zeka hareketlerini anlik olarak tanir,
                tekrarlarini sayar ve performansini takip eder.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats():
    cols = st.columns(3)
    stats = [
        ("5", "Desteklenen Egzersiz"),
        ("10", "Hareket Pozisyonu"),
        ("33", "Vucut Noktasi Takibi"),
    ]
    for col, (val, label) in zip(cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="g-card" style="text-align:center; padding:1.4rem 1rem;">
                    <div class="m-val">{val}</div>
                    <div class="m-lbl">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_how_it_works():
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Nasil Calisir?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-sub">Uc basit adimda antrenmanina basla</div>',
        unsafe_allow_html=True,
    )
    steps = [
        ("1", "Kamerayi Baslat",
         "Asagidaki START butonuna tiklayarak tarayici kameranizi acin. "
         "Kameranin tam vucudunuzu gorecegi bir konumda durun."),
        ("2", "Egzersizini Yap",
         "Sinav, mekik, squat veya baska bir egzersiz yapmaya baslayin. "
         "AI modeli hareketlerinizi anlik olarak tanir."),
        ("3", "Sonuclarini Gor",
         "Hareket tipi ve guven orani video uzerinde "
         "canli olarak gosterilir."),
    ]
    cols = st.columns(3)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="g-card" style="text-align:center;">
                    <div class="step-num">{num}</div>
                    <div class="step-t">{title}</div>
                    <div class="step-d">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_exercises():
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-title">Desteklenen Egzersizler</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sec-sub">AI modelimiz asagidaki hareketleri taniyor</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(5)
    for col, ex in zip(cols, EXERCISES):
        with col:
            st.markdown(
                f"""
                <div class="g-card" style="text-align:center; padding:1.6rem 0.8rem;">
                    <div class="accent-top" style="background:{ex['color']};"></div>
                    <div class="ex-icon">{ex['icon']}</div>
                    <div class="ex-name">{ex['name']}</div>
                    <div class="ex-en">{ex['en']}</div>
                    <div class="ex-desc">{ex['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_camera_section(ml_model, encoder, scaler, model_type,
                           feature_columns, pose_landmarker):
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="cta-box">
            <div class="cta-t">Antrenmanina Basla</div>
            <div class="cta-d">
                Kameranizi acarak yapay zeka destekli egzersiz takibine baslayin
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tip-box" style="margin-top:1rem; text-align:center;">
            <strong>Ipucu:</strong> Iyi aydinlatilmis bir ortamda
            tam vucut gorunumunde durmaniz en iyi sonuclari verir.
            Tarayiciniz kamera izni isteyecektir.
        </div>
        """,
        unsafe_allow_html=True,
    )

    callback = make_video_frame_callback(
        ml_model, encoder, scaler, model_type, feature_columns, pose_landmarker,
    )

    webrtc_ctx = webrtc_streamer(
        key="exercise-detection",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=callback,
        media_stream_constraints={
            "video": {"width": {"ideal": 640}, "height": {"ideal": 480}},
            "audio": False,
        },
        async_processing=True,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        translations={
            "start": "Kamerayi Baslat",
            "stop": "Kamerayi Durdur",
            "select_device": "Cihaz Sec",
        },
    )

    st.markdown(
        """
        <script>
        const observer = new MutationObserver(() => {
            const iframes = document.querySelectorAll('iframe');
            iframes.forEach(iframe => {
                try {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (!doc || doc.getElementById('custom-webrtc-style')) return;
                    const style = doc.createElement('style');
                    style.id = 'custom-webrtc-style';
                    style.textContent = `
                        button {
                            background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%) !important;
                            border: none !important;
                            border-radius: 12px !important;
                            padding: 12px 32px !important;
                            font-size: 1rem !important;
                            font-weight: 600 !important;
                            color: #080810 !important;
                            cursor: pointer !important;
                            letter-spacing: 0.5px !important;
                            min-height: 48px !important;
                            transition: all 0.3s ease !important;
                        }
                        button:hover {
                            box-shadow: 0 6px 24px rgba(0,212,170,0.35) !important;
                            transform: translateY(-1px) !important;
                        }
                        select {
                            background: rgba(18,18,30,0.9) !important;
                            border: 1px solid rgba(255,255,255,0.12) !important;
                            border-radius: 10px !important;
                            color: #e0e0e8 !important;
                            padding: 8px 16px !important;
                            font-size: 0.85rem !important;
                        }
                        video {
                            border-radius: 12px !important;
                        }
                    `;
                    doc.head.appendChild(style);
                } catch(e) {}
            });
        });
        observer.observe(document.body, {childList: true, subtree: true});
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="foot">
            <strong>BecomeAPro</strong> &mdash; AI-Powered Exercise Tracker<br>
            <span style="font-size:0.78rem; margin-top:4px; display:inline-block;">
                MediaPipe &bull; XGBoost / PyTorch &bull; Streamlit &bull; WebRTC
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_missing():
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    _p1, col_c, _p2 = st.columns([1, 3, 1])
    with col_c:
        st.markdown(
            """
            <div class="onboard-card">
                <h3>Model Dosyalari Bulunamadi</h3>
                <p>
                    Uygulamanin calisabilmesi icin egitilmis model dosyalarinin
                    <code>models/</code> klasorune eklenmesi gerekiyor.
                </p>
                <p style="margin-top:1rem; font-size:0.85rem; color:#5a5a7a;">
                    Gerekli dosyalar: meta.pkl, encoder.pkl, scaler.pkl,
                    final_model.pkl, metadata.json
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    result = load_all_artifacts()
    ml_model = result[0]

    render_hero()

    if ml_model is None:
        render_model_missing()
        render_footer()
        return

    ml_model, encoder, scaler, model_type, feature_columns, pose_landmarker, _ = result

    render_stats()
    render_how_it_works()
    render_exercises()
    render_camera_section(
        ml_model, encoder, scaler, model_type, feature_columns, pose_landmarker,
    )
    render_footer()


if __name__ == "__main__":
    main()
