"""
CivicMind AI — Learned Temperature Scaling & Calibration Module
Optimizes post-hoc temperature scaling parameters per classification head using validation logits.
Computes Expected Calibration Error (ECE), Negative Log-Likelihood (NLL), and Brier Score.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE).
    probs: (N, C) predicted probabilities
    labels: (N,) true class indices
    """
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == labels).astype(float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return float(ece)


def compute_brier_score(probs: np.ndarray, labels: np.ndarray, num_classes: int) -> float:
    """
    Computes multi-class Brier score: Mean squared error between predicted probabilities and one-hot labels.
    """
    n_samples = len(labels)
    one_hot = np.zeros((n_samples, num_classes))
    for i, lbl in enumerate(labels):
        if 0 <= lbl < num_classes:
            one_hot[i, lbl] = 1.0
    return float(np.mean(np.sum((probs - one_hot) ** 2, axis=1)))


def compute_nll(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Computes Negative Log Likelihood (Cross Entropy)."""
    loss_fn = nn.CrossEntropyLoss()
    with torch.no_grad():
        return float(loss_fn(logits, labels).item())


class TemperatureScaler(nn.Module):
    """
    Optimizes a single temperature parameter T for a classification head
    using L-BFGS optimizer on validation logits.
    """
    def __init__(self, initial_temp: float = 1.0):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * initial_temp)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        # Scale logits by temperature
        return logits / self.temperature

    def fit(self, logits: torch.Tensor, labels: torch.Tensor, lr: float = 0.01, max_iter: int = 50) -> float:
        """Optimizes temperature to minimize NLL on validation set."""
        device = logits.device
        self.to(device)
        nll_criterion = nn.CrossEntropyLoss()

        # Initialize parameter
        self.temperature.data.fill_(1.0)
        optimizer = optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        def eval_loss():
            optimizer.zero_grad()
            # Constrain T > 0.01 to prevent division by zero or negative scaling
            self.temperature.data.clamp_(min=0.01, max=10.0)
            scaled_logits = self.forward(logits)
            loss = nll_criterion(scaled_logits, labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        self.temperature.data.clamp_(min=0.01, max=10.0)
        return float(self.temperature.item())


def fit_multi_task_temperatures(
    val_logits_dict: Dict[str, torch.Tensor],
    val_labels_dict: Dict[str, torch.Tensor],
) -> Dict[str, Any]:
    """
    Optimizes temperature scaling parameters for all heads and computes before/after calibration metrics.
    Returns:
        {
            "temperatures": {"grievance": T_g, "category": T_c, ...},
            "metrics_before": {"category": {"ece": ..., "nll": ..., "brier": ...}, ...},
            "metrics_after": {"category": {"ece": ..., "nll": ..., "brier": ...}, ...}
        }
    """
    results = {
        "temperatures": {},
        "metrics_before": {},
        "metrics_after": {},
    }

    for task_name, logits in val_logits_dict.items():
        if task_name not in val_labels_dict:
            continue
        labels = val_labels_dict[task_name]
        num_classes = logits.shape[-1]

        # 1. Metrics Before Calibration
        probs_before = torch.softmax(logits, dim=-1).cpu().numpy()
        labels_np = labels.cpu().numpy()
        ece_before = compute_ece(probs_before, labels_np)
        nll_before = compute_nll(logits, labels)
        brier_before = compute_brier_score(probs_before, labels_np, num_classes)

        # 2. Fit Temperature
        scaler = TemperatureScaler()
        best_t = scaler.fit(logits, labels)
        results["temperatures"][task_name] = round(best_t, 4)

        # 3. Metrics After Calibration
        scaled_logits = logits / best_t
        probs_after = torch.softmax(scaled_logits, dim=-1).cpu().numpy()
        ece_after = compute_ece(probs_after, labels_np)
        nll_after = compute_nll(scaled_logits, labels)
        brier_after = compute_brier_score(probs_after, labels_np, num_classes)

        results["metrics_before"][task_name] = {
            "ece": round(ece_before, 4),
            "nll": round(nll_before, 4),
            "brier": round(brier_before, 4),
        }
        results["metrics_after"][task_name] = {
            "ece": round(ece_after, 4),
            "nll": round(nll_after, 4),
            "brier": round(brier_after, 4),
        }

        logger.info(
            f"Task '{task_name}': Learned T = {best_t:.4f} | ECE: {ece_before:.4f} -> {ece_after:.4f} | NLL: {nll_before:.4f} -> {nll_after:.4f}"
        )

    return results
