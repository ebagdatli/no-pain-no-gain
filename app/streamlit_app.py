"""
Streamlit app for exercise pose prediction.
Upload a CSV with pose landmark columns (same format as train.csv) to get predictions.
"""
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
from joblib import load

# Run from repo root: streamlit run ExercisePrediction/app/streamlit_app.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODELS_DIR = ROOT / "models"


def load_model_and_artifacts():
    """Load model and artifacts from models/."""
    meta_path = MODELS_DIR / "meta.pkl"
    if not meta_path.exists():
        st.error(
            "Models not found. Train first: python run_competition.py ExercisePrediction"
        )
        return None, None, None, None, None

    meta = load(meta_path)
    encoder = load(MODELS_DIR / "encoder.pkl")
    scaler = load(MODELS_DIR / "scaler.pkl")
    categories = meta.get("categories", load(MODELS_DIR / "categories.pkl"))
    model_type = meta.get("model_type", "xgboost")

    model_path = meta.get("model_path")
    if model_path and not Path(model_path).is_absolute():
        model_path = MODELS_DIR / Path(model_path).name

    if model_type == "xgboost":
        model = load(model_path)
    else:
        import torch
        from src.train import build_pytorch_model
        input_size = meta.get("input_size", 99)
        num_classes = meta.get("num_classes", len(categories))
        model = build_pytorch_model(input_size, num_classes)
        model.load_state_dict(torch.load(model_path))
        model.eval()

    return model, encoder, scaler, categories, model_type


def predict(model, encoder, scaler, categories, model_type, X: np.ndarray):
    """Run prediction on feature matrix X."""
    X_scaled = scaler.transform(X)
    if model_type == "xgboost":
        pred_indices = model.predict(X_scaled)
    else:
        import torch
        with torch.no_grad():
            X_t = torch.from_numpy(X_scaled.astype(np.float32))
            outputs = model(X_t)
            _, pred_indices = torch.max(outputs, 1)
            pred_indices = pred_indices.numpy()
    return [encoder.inverse_transform([i])[0] for i in pred_indices]


def main():
    st.title("Exercise Pose Prediction")
    st.write(
        "Upload a CSV with pose landmark columns (pose_id, pose optional; "
        "required: 33 MediaPipe landmarks as x/y/z columns)."
    )

    model, encoder, scaler, categories, model_type = load_model_and_artifacts()
    if model is None:
        return

    st.subheader("Upload CSV")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to load CSV: {e}")
        return

    # Drop pose_id, pose if present; keep feature columns
    feature_cols = [c for c in df.columns if c not in ("pose_id", "pose")]
    if len(feature_cols) == 0:
        st.error("No feature columns found. Expected landmark columns (x_nose, y_nose, ...).")
        return

    X = df[feature_cols].values
    if X.shape[1] != scaler.n_features_in_:
        st.error(
            f"Expected {scaler.n_features_in_} features, got {X.shape[1]}. "
            "Ensure CSV has same columns as train.csv (33 landmarks × 3)."
        )
        return

    if st.button("Predict"):
        preds = predict(model, encoder, scaler, categories, model_type, X)
        df_result = df.copy()
        df_result["predicted_pose"] = preds
        st.subheader("Predictions")
        st.dataframe(df_result)
        st.write("Classes:", ", ".join(categories))


if __name__ == "__main__":
    main()
