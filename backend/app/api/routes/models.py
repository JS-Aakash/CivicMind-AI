"""
CivicMind AI — Model & Training API Endpoints
Endpoints:
- GET  /api/model/status           - Model registry and download/readiness status
- POST /api/model/train            - Trigger background fine-tuning job
- GET  /api/model/training-status   - Live training progress (epoch, loss, F1, device)
- GET  /api/model/metrics          - Measured evaluation metrics (overall & per-language)
- GET  /api/model/comparison       - Measured v1.0 vs v1.1 comparative performance
- GET  /api/model/benchmark        - Measured inference latency & throughput benchmark
- GET  /api/dataset/stats          - Dataset statistics and taxonomy distributions
"""
import json
import asyncio
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.schemas import ModelStatusResponse, ModelInfo
from app.services.muril_service import muril_service
from app.services.language_service import language_detection_service
from app.core.config import settings

router = APIRouter()


@router.get("/model/status", response_model=ModelStatusResponse)
async def model_status():
    muril_status = muril_service.get_status()
    lang_status = language_detection_service.get_status()

    v1_dir = Path("models/grievance/v1")
    v1_1_dir = Path("models/grievance/v1.1")
    has_trained_v1 = (v1_dir / "config.json").exists() and (v1_dir / "heads.pt").exists()
    has_trained_v1_1 = (v1_1_dir / "config.json").exists() and (v1_1_dir / "heads.pt").exists()

    trained_model_v1_1_info = ModelInfo(
        name="civicmind/muril-multitask-v1.1",
        display_name="MuRIL Multi-Task Grievance Model (v1.1 Hardened)",
        type="Multi-Task Neural Classifier (6 Heads + Calibrated)",
        status="ready" if has_trained_v1_1 else "training",
        local_path=str(v1_1_dir) if has_trained_v1_1 else None,
        size_mb=round(sum(f.stat().st_size for f in v1_1_dir.rglob("*") if f.is_file()) / (1024 * 1024), 1) if has_trained_v1_1 else None,
        description="Hardened MuRIL multi-task model with learned temperature scaling, hierarchical subcategory decoding, and multi-issue detection.",
        module="Module 2.5 (Production Ready)",
    )

    trained_model_info = ModelInfo(
        name="civicmind/muril-multitask-v1",
        display_name="MuRIL Multi-Task Grievance Model (v1.0 Baseline)",
        type="Multi-Task Neural Classifier (5 Heads)",
        status="ready" if has_trained_v1 else "not_downloaded",
        local_path=str(v1_dir) if has_trained_v1 else None,
        size_mb=round(sum(f.stat().st_size for f in v1_dir.rglob("*") if f.is_file()) / (1024 * 1024), 1) if has_trained_v1 else None,
        description="Baseline fine-tuned MuRIL for 5 civic tasks: Grievance detection, Category, Subcategory, Severity, Priority.",
        module="Module 2 (Baseline Checkpoint)",
    )

    muril_base_info = ModelInfo(
        name="google/muril-base-cased",
        display_name="MuRIL Base (Encoder)",
        type="Multilingual Transformer (BERT-based)",
        status="ready" if muril_status["loaded"] else (
            "downloaded" if muril_status["downloaded"] else "not_downloaded"
        ),
        local_path=muril_status["local_path"],
        size_mb=muril_status["size_mb"],
        description="Base Multilingual Representations for Indian Languages. Provides 768-dim embeddings.",
        module="Module 1 (Foundation)",
    )

    indiclid_info = ModelInfo(
        name="ai4bharat/IndicLID",
        display_name="IndicLID",
        type="Language Identification Model",
        status="ready" if lang_status["initialized"] else "loading",
        local_path=None,
        size_mb=None,
        description="AI4Bharat language identification for 47 Indian languages. Identifies native vs Romanized script.",
        module="Module 1",
    )

    future_models = [
        ModelInfo(
            name="openai/whisper-medium",
            display_name="Whisper (Speech)",
            type="Speech-to-Text Transformer",
            status="not_downloaded",
            local_path=None,
            size_mb=None,
            description="Multilingual speech recognition for voice complaint submission.",
            module="Module 3 (planned)",
        ),
        ModelInfo(
            name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            display_name="Embedding Model",
            type="Sentence Embedding",
            status="not_downloaded",
            local_path=None,
            size_mb=None,
            description="High-quality semantic embeddings for duplicate detection.",
            module="Module 4 (planned)",
        ),
    ]

    all_models = [trained_model_v1_1_info, trained_model_info, muril_base_info, indiclid_info] + future_models
    all_ready = (has_trained_v1_1 or has_trained_v1) and indiclid_info.status == "ready"

    return ModelStatusResponse(models=all_models, all_ready=all_ready)


@router.get("/model/training-status")
async def get_training_status():
    """Returns live training progress from the active or latest training run."""
    progress_file = Path("data/training_progress.json")
    if not progress_file.exists():
        return {
            "status": "idle",
            "current_epoch": 0,
            "total_epochs": 2,
            "progress_percent": 0.0,
            "current_loss": 0.0,
            "validation_f1": 0.0,
            "device": "NVIDIA GeForce RTX 3050 6GB Laptop GPU",
            "model_version": "v1.1",
            "stage": "Ready for training",
            "elapsed_seconds": 0,
        }

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/model/train")
async def trigger_training(background_tasks: BackgroundTasks, epochs: int = 2, batch_size: int = 32):
    """Triggers fine-tuning as an asynchronous background job."""
    progress_file = Path("data/training_progress.json")
    if progress_file.exists():
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            if state.get("status") == "training":
                return {"status": "already_training", "message": "Training is already in progress.", "progress": state}
        except Exception:
            pass

    def _run():
        subprocess.run(
            [sys.executable, "ml/train_multitask.py", "--epochs", str(epochs), "--batch-size", str(batch_size), "--output-dir", "models/grievance/v1.1"],
            cwd=str(Path(__file__).parent.parent.parent.parent),
        )

    background_tasks.add_task(_run)
    return {"status": "started", "message": f"MuRIL v1.1 training started for {epochs} epochs."}


@router.get("/model/metrics")
async def get_model_metrics():
    """Returns measured overall and per-language evaluation metrics."""
    comp_path = Path("artifacts/evaluation/v1_vs_v1_1.json")
    if comp_path.exists():
        with open(comp_path, "r", encoding="utf-8") as f:
            comp_data = json.load(f)
            return {
                "model_version": "v1.1",
                "comparison": comp_data,
                "overall": comp_data.get("v1_1_full_task_metrics", {}),
                "by_language": comp_data.get("language_breakdown_category_f1", {}),
                "evaluation_available": True,
            }

    overall_path = Path("data/metrics_overall.json")
    lang_path = Path("data/metrics_by_language.json")

    overall = {}
    by_language = {}
    if overall_path.exists():
        with open(overall_path, "r", encoding="utf-8") as f:
            overall = json.load(f)
    if lang_path.exists():
        with open(lang_path, "r", encoding="utf-8") as f:
            by_language = json.load(f)

    return {
        "model_version": "v1.0",
        "overall": overall,
        "by_language": by_language,
        "evaluation_available": bool(overall),
    }


@router.get("/model/comparison")
async def get_model_comparison():
    """Returns measured v1.0 vs v1.1 comparative performance across test & challenge sets."""
    comp_path = Path("artifacts/evaluation/v1_vs_v1_1.json")
    if not comp_path.exists():
        raise HTTPException(status_code=404, detail="Comparative evaluation not yet generated. Please run ml/evaluate.py first.")
    with open(comp_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/model/benchmark")
async def get_inference_benchmark():
    """Returns measured latency & throughput benchmarks."""
    bench_path = Path("artifacts/evaluation/inference_benchmark.json")
    if not bench_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not yet generated. Please run scripts/benchmark_inference.py first.")
    with open(bench_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/dataset/stats")
async def get_dataset_stats():
    """Returns dataset distributions and audit reports."""
    stats_path = Path("data/dataset_statistics.json")
    if not stats_path.exists():
        raise HTTPException(status_code=404, detail="Dataset statistics not found. Please run dataset generator first.")

    with open(stats_path, "r", encoding="utf-8") as f:
        return json.load(f)
