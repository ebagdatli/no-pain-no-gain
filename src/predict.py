"""
Save model and artifacts for deployment.
"""
import json
from pathlib import Path
from typing import List, Any

from joblib import dump, load


def save_model_and_artifacts(
    model: Any,
    encoder: Any,
    scaler: Any,
    class_names: List[str],
    val_accuracy: float,
    models_dir: str = "models",
    model_type: str = "xgboost",
    input_size: int = 99,
    feature_columns: List[str] = None,
) -> str:
    """
    Save model, encoder, scaler, and metadata.
    model_type: 'xgboost' or 'pytorch'
    feature_columns: order of features expected by model (for camera_demo alignment).
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    if model_type == "xgboost":
        model_path = models_dir / "final_model.pkl"
        dump(model, model_path)
    else:
        import torch
        model_path = models_dir / "final_model.pt"
        torch.save(model.state_dict(), model_path)

    dump(encoder, models_dir / "encoder.pkl")
    dump(encoder, models_dir / "label_encoder.pkl")
    dump(scaler, models_dir / "scaler.pkl")
    dump(class_names, models_dir / "categories.pkl")

    meta = {
        "model_path": str(model_path),
        "model_type": model_type,
        "categories": class_names,
        "val_accuracy": val_accuracy,
        "input_size": input_size,
        "num_classes": len(class_names),
    }
    meta_path = models_dir / "meta.pkl"
    dump(meta, meta_path)

    if feature_columns is not None:
        metadata_json = {"feature_columns": feature_columns}
        with open(models_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata_json, f, indent=2)

    return str(meta_path)


def load_model_and_artifacts(models_dir: str = "models"):
    """Load model, encoder, scaler, categories from models/."""
    models_dir = Path(models_dir)
    meta = load(models_dir / "meta.pkl")
    encoder = load(models_dir / "encoder.pkl")
    scaler = load(models_dir / "scaler.pkl")
    categories = load(models_dir / "categories.pkl")

    model_type = meta.get("model_type", "xgboost")
    model_path = meta.get("model_path")
    if model_path and not Path(model_path).is_absolute():
        model_path = models_dir / Path(model_path).name

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
