#!/usr/bin/env python3
"""
CivicMind AI — Master Dataset Generator
Generates ~15,000 multilingual civic grievance training examples across:
- English, Tamil native, Tanglish, Hindi native, Hinglish, Mixed dialect
- 10 official categories, official subcategories, priorities, severities
- 10-15% non-grievance inquiries
- Scenario-based 80/10/10 train/val/test splits + 750 challenge examples
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from collections import Counter

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# UTF-8 encoding support on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.ml.dataset.scenario_generator import ScenarioGenerator
from app.ml.dataset.language_variants import LanguageVariantGenerator
from app.ml.dataset.noise_generator import NoiseGenerator
from app.ml.dataset.label_validator import LabelValidator
from app.ml.dataset.deduplicator import Deduplicator
from app.ml.dataset.dataset_splitter import DatasetSplitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Target language distribution
LANGUAGE_DISTRIBUTION = [
    ("ta", 0.15),         # Tamil native script: ~15%
    ("ta_roman", 0.20),   # Tanglish: ~20%
    ("hi", 0.15),         # Hindi native script: ~15%
    ("hi_roman", 0.20),   # Hinglish: ~20%
    ("en", 0.15),         # English: ~15%
    ("mixed", 0.15),      # Mixed / code-mixed / noisy: ~15%
]

VARIANT_STYLES = [
    "neutral", "informal", "short", "formal", "urgent",
    "spelling_noise", "emoji_noise", "angry", "voice_transcription", "minimal"
]


def generate_civic_dataset(target_size: int = 15000, seed: int = 42, output_dir: str = "data"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 65)
    logger.info(f"CivicMind AI — Dataset Generation Pipeline (Target: {target_size}, Seed: {seed})")
    logger.info("=" * 65)

    # 1. Generate base scenarios (~6 variants per scenario)
    num_scenarios = int(target_size / 5.5) + 200
    logger.info(f"Step 1: Generating {num_scenarios} base scenario instances...")
    sc_gen = ScenarioGenerator(seed=seed)
    scenarios = sc_gen.generate_scenarios(num_scenarios)

    # 2. Expand into language variants and inject citizen noise
    logger.info("Step 2: Generating language variants & injecting citizen noise...")
    lang_gen = LanguageVariantGenerator(seed=seed)
    noise_gen = NoiseGenerator(seed=seed)

    raw_records = []
    rec_id = 1

    # Flatten distribution into weighted choices
    lang_choices = []
    for lang, weight in LANGUAGE_DISTRIBUTION:
        lang_choices.extend([lang] * int(weight * 100))

    import random
    rng = random.Random(seed)

    for scn in scenarios:
        # Generate 5-7 variants per scenario across diverse languages
        k_variants = rng.randint(5, 7)
        sampled_langs = rng.sample(lang_choices, k_variants)

        for lang in sampled_langs:
            vtype = rng.choice(VARIANT_STYLES)
            variant = lang_gen.generate_variant(scn, target_language=lang, variant_type=vtype)

            # Apply noise
            variant["text"] = noise_gen.apply_noise(variant["text"], variant["category"], vtype)
            variant["id"] = f"CIVIC_{rec_id:06d}"
            raw_records.append(variant)
            rec_id += 1

    logger.info(f"Generated {len(raw_records)} raw records.")

    # 3. Label validation and quality auditing
    logger.info("Step 3: Auditing label quality and taxonomy adherence...")
    validator = LabelValidator()
    valid_records, quality_report = validator.audit_dataset(raw_records)
    logger.info(f"Valid records after schema audit: {len(valid_records)} (Pass rate: {quality_report['validation_pass_rate']}%)")

    # 4. Deduplication
    logger.info("Step 4: Performing exact & semantic near-duplicate suppression...")
    deduper = Deduplicator(similarity_threshold=0.92)
    clean_records, dedup_report = deduper.deduplicate(valid_records)
    logger.info(f"Records after deduplication: {len(clean_records)} (Removed: {dedup_report['total_removed']})")

    # Trim or select up to target_size if needed, keeping deterministic order
    if len(clean_records) > target_size:
        clean_records = clean_records[:target_size]

    # 5. Scenario-based train/val/test splitting
    logger.info("Step 5: Performing scenario-based 80/10/10 split...")
    splitter = DatasetSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=seed)
    train_set, val_set, test_set = splitter.split_by_scenario(clean_records)

    # 6. Build isolated challenge set
    logger.info("Step 6: Constructing isolated challenge test set (750 edge cases)...")
    challenge_set = splitter.build_challenge_set(count=750)

    # 7. Compute statistics
    def _stats(dataset):
        return {
            "total": len(dataset),
            "languages": dict(Counter(r["primary_language"] for r in dataset)),
            "scripts": dict(Counter(r["script"] for r in dataset)),
            "code_mixed": dict(Counter(r["is_code_mixed"] for r in dataset)),
            "categories": dict(Counter(r["category"] for r in dataset)),
            "priorities": dict(Counter(r["priority"] for r in dataset)),
            "severities": dict(Counter(r["severity"] for r in dataset)),
            "grievance_distribution": dict(Counter(r["is_grievance"] for r in dataset)),
        }

    dataset_stats = {
        "dataset_version": "v1.0",
        "total_records": len(clean_records),
        "splits": {
            "train": len(train_set),
            "validation": len(val_set),
            "test": len(test_set),
            "challenge": len(challenge_set),
        },
        "overall_distribution": _stats(clean_records),
        "quality_audit": quality_report,
        "deduplication_audit": dedup_report,
    }

    # 8. Save all files
    logger.info("Step 7: Saving dataset files...")
    with open(out_path / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_set, f, ensure_ascii=False, indent=2)

    with open(out_path / "val.json", "w", encoding="utf-8") as f:
        json.dump(val_set, f, ensure_ascii=False, indent=2)

    with open(out_path / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)

    with open(out_path / "challenge.json", "w", encoding="utf-8") as f:
        json.dump(challenge_set, f, ensure_ascii=False, indent=2)

    with open(out_path / "dataset_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality_report, f, ensure_ascii=False, indent=2)

    with open(out_path / "dataset_statistics.json", "w", encoding="utf-8") as f:
        json.dump(dataset_stats, f, ensure_ascii=False, indent=2)

    logger.info("=" * 65)
    logger.info("✅ DATASET GENERATION COMPLETE")
    logger.info(f"   Train:      {len(train_set)} examples ({out_path / 'train.json'})")
    logger.info(f"   Validation: {len(val_set)} examples ({out_path / 'val.json'})")
    logger.info(f"   Test:       {len(test_set)} examples ({out_path / 'test.json'})")
    logger.info(f"   Challenge:  {len(challenge_set)} examples ({out_path / 'challenge.json'})")
    logger.info(f"   Stats:      {out_path / 'dataset_statistics.json'}")
    logger.info("=" * 65)

    return dataset_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CivicMind AI Dataset Generator")
    parser.add_argument("--size", type=int, default=15000, help="Target total records (default: 15000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory (default: data)")

    args = parser.parse_args()
    generate_civic_dataset(target_size=args.size, seed=args.seed, output_dir=args.output_dir)
