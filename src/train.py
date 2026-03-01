"""
Model definitions for exercise pose classification.
Supports PyTorch MLP and XGBoost.
"""
from typing import Optional, Tuple, Any
import numpy as np


def build_pytorch_model(
    input_size: int,
    num_classes: int,
    hidden_size: int = 200,
):
    """Build a simple PyTorch MLP for pose classification."""
    import torch
    import torch.nn as nn

    class NeuralNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.l1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.l2 = nn.Linear(hidden_size, num_classes)

        def forward(self, x):
            out = self.l1(x)
            out = self.relu(out)
            out = self.l2(out)
            return out

    return NeuralNet()


def train_pytorch(
    model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    class_weights: Optional[np.ndarray] = None,
    epochs: int = 40,
    lr: float = 0.01,
    batch_size: int = 50,
) -> Any:
    """Train PyTorch model. Returns trained model."""
    import torch
    from torch.utils.data import TensorDataset, DataLoader

    model.train()
    X_t = torch.from_numpy(X_train.astype(np.float32))
    y_t = torch.from_numpy(y_train.astype(np.int64))
    dataset = TensorDataset(X_t, y_t)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    criterion = torch.nn.CrossEntropyLoss(
        weight=torch.from_numpy(class_weights).float() if class_weights is not None else None
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        for features, labels in loader:
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

    return model


def build_and_train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    num_classes: int,
) -> Tuple[Any, float]:
    """Build and train XGBoost classifier. Returns (model, val_accuracy)."""
    from xgboost import XGBClassifier
    from sklearn.metrics import accuracy_score

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    return model, acc


def build_and_train_pytorch(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    input_size: int,
    num_classes: int,
    class_weights: Optional[np.ndarray] = None,
    epochs: int = 40,
) -> Tuple[Any, float]:
    """Build and train PyTorch MLP. Returns (model, val_accuracy)."""
    import torch

    model = build_pytorch_model(input_size, num_classes)
    if class_weights is None:
        class_weights = np.ones(num_classes, dtype=np.float32)
    train_pytorch(model, X_train, y_train, class_weights, epochs=epochs)

    model.eval()
    with torch.no_grad():
        X_t = torch.from_numpy(X_val.astype(np.float32))
        outputs = model(X_t)
        _, preds = torch.max(outputs, 1)
        acc = (preds.numpy() == y_val).mean()

    return model, acc
