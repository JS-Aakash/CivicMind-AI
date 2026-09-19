#!/usr/bin/env python3
"""
CivicMind AI — Multi-Task Fine-Tuning Script (v1.1 Hardened)
Fine-tunes MuRIL across:
1. Grievance Detection
2. Primary Category Classification
3. Subcategory Classification
4. Severity Classification
5. Priority Classification
6. Additive Multi-Issue Detection (BCE Loss)

Learns temperature scaling calibration parameters post-training on validation split.
"""
import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from app.core.config import settings
from app.ml.taxonomy import (
    CATEGORIES,
    ALL_SUBCATEGORIES,
    PRIORITIES,
    SEVERITIES,
    CATEGORY_TO_IDX,
    SUBCATEGORY_TO_IDX,
    PRIORITY_TO_IDX,
    SEVERITY_TO_IDX,
    GRIEVANCE_TO_IDX,
    get_scoped_subcategory,
)
from app.ml.model import MuRILMultiTaskForCivic
from app.ml.calibration.temperature_scaling import fit_multi_task_temperatures

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class CivicGrievanceDataset(Dataset):
    """PyTorch Dataset for multi-task civic grievance training with multi-issue label encoding."""

    def __init__(self, data: List[Dict[str, Any]], tokenizer, max_length: int = 128):
        self.data = data
        texts = [str(item.get("text", "")) for item in data]
        logger.info(f"Pre-tokenizing {len(texts)} samples (max_length={max_length})...")
        enc = tokenizer(
            texts,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        self.input_ids = enc["input_ids"]
        self.attention_mask = enc["attention_mask"]

        self.grievance_labels = torch.tensor(
            [GRIEVANCE_TO_IDX.get(item.get("is_grievance", True), 1) for item in data], dtype=torch.long
        )
        self.category_labels = torch.tensor(
            [CATEGORY_TO_IDX.get(item.get("category", "other"), CATEGORY_TO_IDX["other"]) for item in data], dtype=torch.long
        )
        self.subcategory_labels = torch.tensor(
            [SUBCATEGORY_TO_IDX.get(get_scoped_subcategory(item.get("category", "other"), item.get("subcategory", "other")), 0) for item in data],
            dtype=torch.long,
        )
        self.severity_labels = torch.tensor(
            [SEVERITY_TO_IDX.get(item.get("severity", "medium"), SEVERITY_TO_IDX["medium"]) for item in data], dtype=torch.long
        )
        self.priority_labels = torch.tensor(
            [PRIORITY_TO_IDX.get(item.get("priority", "medium"), PRIORITY_TO_IDX["medium"]) for item in data], dtype=torch.long
        )

        # Multi-issue binary target vector (10-dim)
        issue_mat = torch.zeros((len(data), len(CATEGORIES)), dtype=torch.float32)
        for i, item in enumerate(data):
            primary_cat = item.get("category", "other")
            if primary_cat in CATEGORY_TO_IDX:
                issue_mat[i, CATEGORY_TO_IDX[primary_cat]] = 1.0
            # Include secondary categories if present
            for sec_cat in item.get("secondary_categories", []):
                if sec_cat in CATEGORY_TO_IDX:
                    issue_mat[i, CATEGORY_TO_IDX[sec_cat]] = 1.0
        self.issue_labels = issue_mat

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return {
            "input_ids": self.input_ids[idx],
            "attention_mask": self.attention_mask[idx],
            "grievance_label": self.grievance_labels[idx],
            "category_label": self.category_labels[idx],
            "subcategory_label": self.subcategory_labels[idx],
            "severity_label": self.severity_labels[idx],
            "priority_label": self.priority_labels[idx],
            "issue_label": self.issue_labels[idx],
        }


def update_progress_file(status_dict: Dict[str, Any], progress_file: Path):
    """Writes atomic status updates for API monitoring."""
    try:
        progress_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = progress_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(status_dict, f, indent=2)
        os.replace(temp_file, progress_file)
    except Exception as e:
        logger.warning(f"Could not update progress file: {e}")


def train_model(
    train_path: str = "data/train.json",
    val_path: str = "data/val.json",
    output_dir: str = "models/grievance/v1.1",
    epochs: int = 2,
    batch_size: int = 32,
    lr: float = 3.5e-5,
    max_length: int = 128,
    seed: int = 42,
    progress_file_path: str = "data/training_progress.json",
):
    torch.manual_seed(seed)
    progress_file = Path(progress_file_path)

    logger.info("=" * 65)
    logger.info(f"  CivicMind AI — MuRIL v1.1 Multi-Task Training -> {output_dir}")
    logger.info("=" * 65)

    # 1. Device Selection
    if torch.cuda.is_available():
        device = torch.device("cuda")
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        device_name = f"{torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)"
        use_amp = True
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        device_name = "Apple Silicon (MPS)"
        use_amp = False
    else:
        device = torch.device("cpu")
        device_name = "CPU"
        use_amp = False

    logger.info(f"Using device: {device_name} | Mixed precision: {use_amp}")

    # 2. Load Data
    logger.info(f"Loading training data from {train_path}...")
    with open(train_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(val_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    logger.info(f"Train samples: {len(train_data)} | Val samples: {len(val_data)}")

    # 3. Load Tokenizer
    local_muril_path = settings.MURIL_LOCAL_PATH
    if Path(local_muril_path).exists():
        tokenizer_src = local_muril_path
    else:
        tokenizer_src = settings.MURIL_MODEL_NAME

    logger.info(f"Loading tokenizer from {tokenizer_src}...")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_src)

    train_dataset = CivicGrievanceDataset(train_data, tokenizer, max_length=max_length)
    val_dataset = CivicGrievanceDataset(val_data, tokenizer, max_length=max_length)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, pin_memory=torch.cuda.is_available())
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # 4. Initialize Multi-Task Model
    logger.info(f"Initializing MuRIL Multi-Task model from {local_muril_path}...")
    model = MuRILMultiTaskForCivic(model_name_or_path=local_muril_path)
    model.to(device)

    # 5. Optimizer & LR Scheduler
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
            "weight_decay": 0.01,
        },
        {
            "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
            "weight_decay": 0.0,
        },
    ]
    optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=lr)

    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    # Initial Progress State
    start_time = time.time()
    update_progress_file({
        "status": "training",
        "current_epoch": 0,
        "total_epochs": epochs,
        "progress_percent": 0.0,
        "current_loss": 0.0,
        "validation_f1": 0.0,
        "device": device_name,
        "model_version": "v1.1",
        "stage": "Training MuRIL v1.1 started",
        "elapsed_seconds": 0,
    }, progress_file)

    for epoch in range(1, epochs + 1):
        model.train()
        total_epoch_loss = 0.0
        step_count = 0
        t0_epoch = time.time()

        for batch_idx, batch in enumerate(train_loader):
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            g_lbl = batch["grievance_label"].to(device)
            c_lbl = batch["category_label"].to(device)
            sub_lbl = batch["subcategory_label"].to(device)
            s_lbl = batch["severity_label"].to(device)
            p_lbl = batch["priority_label"].to(device)
            iss_lbl = batch["issue_label"].to(device)

            with torch.amp.autocast("cuda", enabled=use_amp):
                out = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    grievance_labels=g_lbl,
                    category_labels=c_lbl,
                    subcategory_labels=sub_lbl,
                    severity_labels=s_lbl,
                    priority_labels=p_lbl,
                    issue_labels=iss_lbl,
                )
                loss = out["loss"]

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            total_epoch_loss += loss.item()
            step_count += 1

            if (batch_idx + 1) % 50 == 0 or (batch_idx + 1) == len(train_loader):
                avg_loss = total_epoch_loss / step_count
                progress_pct = round(((epoch - 1) * len(train_loader) + (batch_idx + 1)) / total_steps * 100, 1)
                logger.info(f"Epoch {epoch}/{epochs} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {avg_loss:.4f} ({progress_pct}%)")

                update_progress_file({
                    "status": "training",
                    "current_epoch": epoch,
                    "total_epochs": epochs,
                    "progress_percent": progress_pct,
                    "current_loss": round(avg_loss, 4),
                    "device": device_name,
                    "model_version": "v1.1",
                    "stage": f"Epoch {epoch}/{epochs} in progress",
                    "elapsed_seconds": int(time.time() - start_time),
                }, progress_file)

        logger.info(f"Epoch {epoch} finished in {time.time() - t0_epoch:.1f}s. Running validation...")

    # 6. Post-training: Collect Validation Logits and Targets for Temperature Scaling Calibration
    logger.info("Computing validation logits for Temperature Scaling Calibration...")
    model.eval()
    val_logits_dict = {
        "grievance": [],
        "category": [],
        "subcategory": [],
        "severity": [],
        "priority": [],
    }
    val_labels_dict = {
        "grievance": [],
        "category": [],
        "subcategory": [],
        "severity": [],
        "priority": [],
    }

    correct_g = 0
    correct_c = 0
    correct_p = 0
    total_val = 0

    with torch.no_grad():
        for val_batch in val_loader:
            v_ids = val_batch["input_ids"].to(device)
            v_mask = val_batch["attention_mask"].to(device)
            v_g = val_batch["grievance_label"].to(device)
            v_c = val_batch["category_label"].to(device)
            v_sub = val_batch["subcategory_label"].to(device)
            v_s = val_batch["severity_label"].to(device)
            v_p = val_batch["priority_label"].to(device)

            with torch.amp.autocast("cuda", enabled=use_amp):
                v_out = model(v_ids, v_mask)
                logits = v_out["logits"]

            val_logits_dict["grievance"].append(logits["grievance"].cpu().float())
            val_logits_dict["category"].append(logits["category"].cpu().float())
            val_logits_dict["subcategory"].append(logits["subcategory"].cpu().float())
            val_logits_dict["severity"].append(logits["severity"].cpu().float())
            val_logits_dict["priority"].append(logits["priority"].cpu().float())

            val_labels_dict["grievance"].append(v_g.cpu())
            val_labels_dict["category"].append(v_c.cpu())
            val_labels_dict["subcategory"].append(v_sub.cpu())
            val_labels_dict["severity"].append(v_s.cpu())
            val_labels_dict["priority"].append(v_p.cpu())

            pred_g = torch.argmax(logits["grievance"], dim=-1)
            pred_c = torch.argmax(logits["category"], dim=-1)
            pred_p = torch.argmax(logits["priority"], dim=-1)

            correct_g += (pred_g == v_g).sum().item()
            correct_c += (pred_c == v_c).sum().item()
            correct_p += (pred_p == v_p).sum().item()
            total_val += len(v_ids)

    acc_g = correct_g / total_val
    acc_c = correct_c / total_val
    acc_p = correct_p / total_val
    logger.info(f"Raw Val Accuracies — Grievance: {acc_g*100:.2f}%, Category: {acc_c*100:.2f}%, Priority: {acc_p*100:.2f}%")

    val_logits_cat = {k: torch.cat(v, dim=0) for k, v in val_logits_dict.items()}
    val_labels_cat = {k: torch.cat(v, dim=0) for k, v in val_labels_dict.items()}

    logger.info("Optimizing Learned Temperature Scaling Parameters...")
    calib_results = fit_multi_task_temperatures(val_logits_cat, val_labels_cat)
    model.temperatures = calib_results["temperatures"]

    # 7. Save v1.1 Model & Config
    out_path = Path(output_dir)
    logger.info(f"Saving MuRIL v1.1 model to {out_path.resolve()}...")
    model.save_pretrained(out_path, version="v1.1", calibration_meta=calib_results)
    tokenizer.save_pretrained(out_path / "encoder")

    # Final Progress Update
    total_time = int(time.time() - start_time)
    update_progress_file({
        "status": "completed",
        "current_epoch": epochs,
        "total_epochs": epochs,
        "progress_percent": 100.0,
        "current_loss": round(total_epoch_loss / step_count, 4),
        "validation_accuracy": {
            "grievance": round(acc_g, 4),
            "category": round(acc_c, 4),
            "priority": round(acc_p, 4),
        },
        "temperatures": calib_results["temperatures"],
        "device": device_name,
        "model_version": "v1.1",
        "stage": "Training and Calibration Complete",
        "elapsed_seconds": total_time,
    }, progress_file)

    logger.info(f"✅ MuRIL v1.1 Training & Calibration Completed successfully in {total_time}s!")
    return calib_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MuRIL v1.1 Multi-Task Grievance Model")
    parser.add_argument("--train-path", type=str, default="data/train.json")
    parser.add_argument("--val-path", type=str, default="data/val.json")
    parser.add_argument("--output-dir", type=str, default="models/grievance/v1.1")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3.5e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    train_model(
        train_path=args.train_path,
        val_path=args.val_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        max_length=args.max_length,
        seed=args.seed,
    )
