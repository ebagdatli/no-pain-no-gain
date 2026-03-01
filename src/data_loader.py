"""
Load exercise pose CSV from data/raw.
Expects train.csv with pose_id, pose, and 33 MediaPipe landmark columns (x,y,z).
"""
from pathlib import Path
from typing import Tuple

import pandas as pd


def get_data_dir(base_dir: str = ".") -> Path:
    """Return the directory containing train.csv."""
    base = Path(base_dir)
    data_dir = base / "data" / "raw"
    if not (data_dir / "train.csv").exists():
        raise FileNotFoundError(
            "Could not find 'train.csv' in data/raw/. "
            "Download from Kaggle: Multi-Class Exercise Poses for Human Skeleton "
            "(https://www.kaggle.com/datasets/dp5995/gym-exercise-mediapipe-33-landmarks) "
            "and place train.csv in ExercisePrediction/data/raw/"
        )
    return data_dir


def load_raw_data(base_dir: str = ".") -> Tuple[pd.DataFrame, Path]:
    """
    Load train.csv.
    Returns (df, data_dir).
    """
    data_dir = get_data_dir(base_dir)
    train_path = data_dir / "train.csv"
    df = pd.read_csv(train_path)
    return df, data_dir


def ensure_directories(base_dir: str = ".") -> None:
    """Ensure data/raw, data/processed, models exist."""
    base = Path(base_dir)
    for sub in ("data/raw", "data/processed", "models"):
        (base / sub).mkdir(parents=True, exist_ok=True)
