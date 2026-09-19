"""
CivicMind AI — MuRIL Multi-Task Neural Classifier (v1.1 Hardened Architecture)
Builds a unified multi-task architecture on top of google/muril-base-cased.

Tasks:
1. Grievance Detection (Binary: True/False)
2. Primary Category Classification (10 classes)
3. Subcategory Classification (45 classes, hierarchically constrained)
4. Severity Classification (4 classes: low, medium, high, critical)
5. Priority Classification (4 classes: low, medium, high, critical)
6. Additive Multi-Issue Detection (10 classes multi-label sigmoid)
"""
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import logging

from app.ml.taxonomy import (
    CATEGORIES,
    ALL_SUBCATEGORIES,
    PRIORITIES,
    SEVERITIES,
    DEFAULT_TASK_WEIGHTS,
    CATEGORY_TO_IDX,
    IDX_TO_CATEGORY,
    SUBCATEGORY_TO_IDX,
    IDX_TO_SUBCATEGORY,
    PRIORITY_TO_IDX,
    IDX_TO_PRIORITY,
    SEVERITY_TO_IDX,
    IDX_TO_SEVERITY,
    GRIEVANCE_TO_IDX,
    IDX_TO_GRIEVANCE,
    get_scoped_subcategory,
    TAXONOMY,
)

logger = logging.getLogger(__name__)


class MuRILMultiTaskForCivic(nn.Module):
    """
    Multi-task classification model with a shared MuRIL encoder and 6 task heads:
    - grievance_head (CrossEntropy)
    - category_head (CrossEntropy)
    - subcategory_head (CrossEntropy with hierarchical masking)
    - severity_head (CrossEntropy)
    - priority_head (CrossEntropy)
    - issue_head (BCEWithLogitsLoss for multi-label compound complaints)
    """

    def __init__(
        self,
        model_name_or_path: str = "google/muril-base-cased",
        task_weights: Optional[Dict[str, float]] = None,
        dropout_prob: float = 0.2,
        temperatures: Optional[Dict[str, float]] = None,
    ):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name_or_path)
        hidden_size = self.encoder.config.hidden_size  # 768 for MuRIL base

        self.dropout = nn.Dropout(dropout_prob)

        # 6 Task Classification Heads
        self.grievance_head = nn.Linear(hidden_size, 2)
        self.category_head = nn.Linear(hidden_size, len(CATEGORIES))
        self.subcategory_head = nn.Linear(hidden_size, len(ALL_SUBCATEGORIES))
        self.severity_head = nn.Linear(hidden_size, len(SEVERITIES))
        self.priority_head = nn.Linear(hidden_size, len(PRIORITIES))
        self.issue_head = nn.Linear(hidden_size, len(CATEGORIES))  # Multi-label issue detection

        # Loss weights
        self.task_weights = task_weights or DEFAULT_TASK_WEIGHTS.copy()
        if "issue" not in self.task_weights:
            self.task_weights["issue"] = 0.5

        # Temperature calibration dictionary (defaults to 1.0)
        self.temperatures = temperatures or {
            "grievance": 1.0,
            "category": 1.0,
            "subcategory": 1.0,
            "severity": 1.0,
            "priority": 1.0,
        }

        # Loss functions
        self.loss_fn = nn.CrossEntropyLoss()
        self.bce_loss_fn = nn.BCEWithLogitsLoss()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
        grievance_labels: Optional[torch.Tensor] = None,
        category_labels: Optional[torch.Tensor] = None,
        subcategory_labels: Optional[torch.Tensor] = None,
        severity_labels: Optional[torch.Tensor] = None,
        priority_labels: Optional[torch.Tensor] = None,
        issue_labels: Optional[torch.Tensor] = None,
    ) -> Dict[str, Any]:
        """
        Forward pass through shared encoder and classification heads.
        If labels are provided, computes weighted multi-task loss.
        """
        encoder_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        if token_type_ids is not None:
            encoder_kwargs["token_type_ids"] = token_type_ids

        outputs = self.encoder(**encoder_kwargs)
        # Use [CLS] representation (first token)
        cls_rep = outputs.last_hidden_state[:, 0, :]
        cls_rep = self.dropout(cls_rep)

        # Compute logits for all heads
        logits = {
            "grievance": self.grievance_head(cls_rep),
            "category": self.category_head(cls_rep),
            "subcategory": self.subcategory_head(cls_rep),
            "severity": self.severity_head(cls_rep),
            "priority": self.priority_head(cls_rep),
            "issue": self.issue_head(cls_rep),
        }

        result = {
            "logits": logits,
            "cls_embedding": cls_rep,
        }

        # Calculate loss if any label is provided
        if any(lbl is not None for lbl in [grievance_labels, category_labels, subcategory_labels, severity_labels, priority_labels, issue_labels]):
            total_loss = torch.tensor(0.0, device=input_ids.device)
            task_losses = {}

            if grievance_labels is not None:
                l_g = self.loss_fn(logits["grievance"], grievance_labels)
                task_losses["grievance"] = l_g.item()
                total_loss += self.task_weights.get("grievance", 1.0) * l_g

            if category_labels is not None:
                l_c = self.loss_fn(logits["category"], category_labels)
                task_losses["category"] = l_c.item()
                total_loss += self.task_weights.get("category", 1.0) * l_c

            if subcategory_labels is not None:
                l_sub = self.loss_fn(logits["subcategory"], subcategory_labels)
                task_losses["subcategory"] = l_sub.item()
                total_loss += self.task_weights.get("subcategory", 0.8) * l_sub

            if severity_labels is not None:
                l_s = self.loss_fn(logits["severity"], severity_labels)
                task_losses["severity"] = l_s.item()
                total_loss += self.task_weights.get("severity", 0.8) * l_s

            if priority_labels is not None:
                l_p = self.loss_fn(logits["priority"], priority_labels)
                task_losses["priority"] = l_p.item()
                total_loss += self.task_weights.get("priority", 1.0) * l_p

            if issue_labels is not None:
                l_iss = self.bce_loss_fn(logits["issue"], issue_labels.float())
                task_losses["issue"] = l_iss.item()
                total_loss += self.task_weights.get("issue", 0.5) * l_iss

            result["loss"] = total_loss
            result["task_losses"] = task_losses

        return result

    def predict(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
        top_k: int = 4,
        multi_issue_threshold: float = 0.40,
    ) -> List[Dict[str, Any]]:
        """
        Batch inference producing calibrated probabilities, hierarchically-consistent subcategories,
        and secondary issue detection.
        """
        self.eval()
        with torch.no_grad():
            out = self.forward(input_ids, attention_mask, token_type_ids)
            logits = out["logits"]

            # Apply learned temperature scaling per task
            tg = self.temperatures.get("grievance", 1.0)
            tc = self.temperatures.get("category", 1.0)
            tsub = self.temperatures.get("subcategory", 1.0)
            tsev = self.temperatures.get("severity", 1.0)
            tp = self.temperatures.get("priority", 1.0)

            probs_g = torch.softmax(logits["grievance"] / tg, dim=-1)
            probs_c = torch.softmax(logits["category"] / tc, dim=-1)
            probs_sub_raw = torch.softmax(logits["subcategory"] / tsub, dim=-1)
            probs_sev = torch.softmax(logits["severity"] / tsev, dim=-1)
            probs_p = torch.softmax(logits["priority"] / tp, dim=-1)
            probs_issues = torch.sigmoid(logits["issue"])

            batch_size = input_ids.size(0)
            predictions = []

            for i in range(batch_size):
                # 1. Grievance
                g_idx = torch.argmax(probs_g[i]).item()
                is_grievance = IDX_TO_GRIEVANCE[g_idx]
                g_conf = probs_g[i][g_idx].item()

                # 2. Primary Category
                c_idx = torch.argmax(probs_c[i]).item()
                category = IDX_TO_CATEGORY[c_idx]
                c_conf = probs_c[i][c_idx].item()

                # Top-k categories
                topk_vals, topk_indices = torch.topk(probs_c[i], min(top_k, len(CATEGORIES)))
                category_probs = {
                    IDX_TO_CATEGORY[idx.item()]: round(val.item(), 4)
                    for val, idx in zip(topk_vals, topk_indices)
                }

                # 3. Hierarchical Subcategory: Mask to only subcategories valid under predicted category
                valid_subcats = TAXONOMY.get(category, [])
                valid_scoped_indices = [
                    SUBCATEGORY_TO_IDX[f"{category}:{sub}"]
                    for sub in valid_subcats
                    if f"{category}:{sub}" in SUBCATEGORY_TO_IDX
                ]

                if valid_scoped_indices:
                    sub_logits_scoped = logits["subcategory"][i][valid_scoped_indices]
                    best_scoped_rel_idx = torch.argmax(sub_logits_scoped).item()
                    best_sub_idx = valid_scoped_indices[best_scoped_rel_idx]
                    scoped_sub = IDX_TO_SUBCATEGORY[best_sub_idx]
                    _, subcategory = scoped_sub.split(":", 1)
                    # Compute scoped probability over valid subcategories
                    scoped_probs = torch.softmax(sub_logits_scoped / tsub, dim=-1)
                    sub_conf = scoped_probs[best_scoped_rel_idx].item()
                else:
                    # Fallback to unconstrained
                    sub_idx = torch.argmax(probs_sub_raw[i]).item()
                    scoped_sub = IDX_TO_SUBCATEGORY[sub_idx]
                    _, subcategory = scoped_sub.split(":", 1)
                    sub_conf = probs_sub_raw[i][sub_idx].item()

                # 4. Multi-issue / Secondary Categories
                secondary_categories = []
                for cat_idx, cat_name in enumerate(CATEGORIES):
                    if cat_name != category:
                        cat_prob = probs_issues[i][cat_idx].item()
                        if cat_prob >= multi_issue_threshold:
                            secondary_categories.append({
                                "category": cat_name,
                                "probability": round(cat_prob, 4)
                            })

                # 5. Severity
                s_idx = torch.argmax(probs_sev[i]).item()
                severity = IDX_TO_SEVERITY[s_idx]
                sev_conf = probs_sev[i][s_idx].item()

                # 6. Priority
                p_idx = torch.argmax(probs_p[i]).item()
                priority = IDX_TO_PRIORITY[p_idx]
                p_conf = probs_p[i][p_idx].item()

                # Calibrated overall confidence score
                calibrated_conf = round(float(c_conf * 0.45 + p_conf * 0.35 + g_conf * 0.20), 4)

                predictions.append({
                    "is_grievance": is_grievance,
                    "grievance_confidence": round(g_conf, 4),
                    "category": category,
                    "category_confidence": round(c_conf, 4),
                    "category_probabilities": category_probs,
                    "secondary_categories": secondary_categories,
                    "subcategory": subcategory,
                    "subcategory_confidence": round(sub_conf, 4),
                    "severity": severity,
                    "severity_confidence": round(sev_conf, 4),
                    "priority": priority,
                    "priority_confidence": round(p_conf, 4),
                    "confidence": calibrated_conf,
                    "calibrated_confidence": calibrated_conf,
                })

            return predictions

    def save_pretrained(self, output_dir: str | Path, version: str = "v1.1", calibration_meta: Optional[Dict] = None):
        """Save entire model checkpoint, calibration parameters, and configuration."""
        save_path = Path(output_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save encoder
        self.encoder.save_pretrained(save_path / "encoder")

        # Save classification heads
        heads_state = {
            "grievance_head": self.grievance_head.state_dict(),
            "category_head": self.category_head.state_dict(),
            "subcategory_head": self.subcategory_head.state_dict(),
            "severity_head": self.severity_head.state_dict(),
            "priority_head": self.priority_head.state_dict(),
            "issue_head": self.issue_head.state_dict(),
            "task_weights": self.task_weights,
            "temperatures": self.temperatures,
        }
        torch.save(heads_state, save_path / "heads.pt")

        # Save metadata config
        config = {
            "model_type": "muril-multitask-civic",
            "version": version,
            "categories": CATEGORIES,
            "subcategories": ALL_SUBCATEGORIES,
            "priorities": PRIORITIES,
            "severities": SEVERITIES,
            "task_weights": self.task_weights,
            "temperatures": self.temperatures,
            "calibration": calibration_meta or {},
        }
        with open(save_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Also write calibration.json
        if calibration_meta:
            with open(save_path / "calibration.json", "w", encoding="utf-8") as f:
                json.dump(calibration_meta, f, indent=2)

    @classmethod
    def from_pretrained(cls, model_dir: str | Path) -> "MuRILMultiTaskForCivic":
        """Load trained model from versioned directory (supports v1.0 and v1.1)."""
        load_path = Path(model_dir)
        config_file = load_path / "config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Model config not found at {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        temperatures = config.get("temperatures")
        calib_file = load_path / "calibration.json"
        if calib_file.exists():
            try:
                with open(calib_file, "r", encoding="utf-8") as cf:
                    cdata = json.load(cf)
                    if "temperatures" in cdata:
                        temperatures = cdata["temperatures"]
            except Exception as e:
                logger.warning(f"Could not load calibration.json: {e}")

        model = cls(
            model_name_or_path=str(load_path / "encoder"),
            task_weights=config.get("task_weights"),
            temperatures=temperatures,
        )
        heads_state = torch.load(load_path / "heads.pt", map_location="cpu", weights_only=True)
        model.grievance_head.load_state_dict(heads_state["grievance_head"])
        model.category_head.load_state_dict(heads_state["category_head"])
        model.subcategory_head.load_state_dict(heads_state["subcategory_head"])
        model.severity_head.load_state_dict(heads_state["severity_head"])
        model.priority_head.load_state_dict(heads_state["priority_head"])

        if "issue_head" in heads_state:
            model.issue_head.load_state_dict(heads_state["issue_head"])

        if "temperatures" in heads_state and heads_state["temperatures"]:
            model.temperatures = heads_state["temperatures"]

        return model
