"""
Real-time exercise pose detection via webcam.
Uses MediaPipe Tasks for pose estimation, trained model for classification.
Includes smoothing, rep counter, and skeleton overlay.
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
# MediaPipe returns 0-1; training data uses ~-50 to 50. Scale to match.
SCALE_XY = 100.0  # (x - 0.5) * SCALE_XY
SCALE_Z = 200.0   # z * SCALE_Z (depth)

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


def rep_counter_logic(buffer, last_down_exercise, reps):
    """
    Count reps when transitioning down -> up for same exercise.
    e.g. situp_down -> situp_up = 1 rep. Avoid double-counting.
    """
    if len(buffer) < 2:
        return last_down_exercise, reps
    recent = list(buffer)[-8:]
    down_states = [s for s in recent if s.endswith("_down") and s != "Belirsiz"]
    up_states = [s for s in recent if s.endswith("_up") and s != "Belirsiz"]

    if down_states:
        down_ex = down_states[-1].replace("_down", "")
        last_down_exercise = down_ex
    if up_states:
        up_ex = up_states[-1].replace("_up", "")
        if last_down_exercise == up_ex:
            reps += 1
            last_down_exercise = None

    return last_down_exercise, reps


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
    last_down_exercise = None
    reps = 0

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
                # Draw skeleton (drawing_utils expects RGB)
                from mediapipe.tasks.python.vision import drawing_utils, drawing_styles
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                drawing_utils.draw_landmarks(
                    image=frame_rgb,
                    landmark_list=pose_landmarks,
                    connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
                    landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style(),
                    connection_drawing_spec=drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2),
                )
                frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                try:
                    X = landmarks_to_vector(pose_landmarks, feature_columns)
                    if X.shape[1] == scaler.n_features_in_:
                        label, conf = predict_with_smoothing(
                            model, encoder, scaler, categories, model_type, X, buffer
                        )
                        last_down_exercise, reps = rep_counter_logic(buffer, last_down_exercise, reps)

                        cv2.putText(
                            frame, f"Pose: {label} ({conf:.0%})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                        )
                        cv2.putText(
                            frame, f"Reps: {reps}",
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                        )
                except Exception as e:
                    cv2.putText(
                        frame, f"Error: {e}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
                    )
            else:
                cv2.putText(
                    frame, "Kullanici bekleniyor - Tam profilde durun",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2
                )
                cv2.putText(
                    frame, "Iyi aydinlatilmis ortamda calisir",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1
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
