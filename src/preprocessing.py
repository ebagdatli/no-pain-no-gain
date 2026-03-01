"""
Preprocessing for exercise pose classification.
Scale features, encode labels, train/val split.
"""
from typing import Tuple, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split


def prepare_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, LabelEncoder, MinMaxScaler, List[str], List[str]]:
    """
    Prepare X, y and split. Returns (X_train, X_val, y_train, y_val, encoder, scaler, class_names, feature_cols).
    """
    # Drop pose_id, pose
    feature_cols = [c for c in df.columns if c not in ("pose_id", "pose")]
    X = df[feature_cols].values
    y_raw = df["pose"].values

    encoder = LabelEncoder()
    y = encoder.fit_transform(y_raw)
    class_names = list(encoder.classes_)

    if stratify:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, stratify=y, shuffle=True, random_state=random_state
        )
    else:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, shuffle=True, random_state=random_state
        )

    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    return X_train, X_val, y_train, y_val, encoder, scaler, class_names, feature_cols


def compute_class_weights(y: np.ndarray) -> np.ndarray:
    """Compute balanced class weights for imbalanced data."""
    from sklearn.utils.class_weight import compute_class_weight
    classes = np.unique(y)
    return compute_class_weight(
        class_weight="balanced", classes=classes, y=y
    ).astype(np.float32)
