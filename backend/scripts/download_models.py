#!/usr/bin/env python3
"""
CivicMind AI — Model Download Script
Pre-downloads MuRIL and verifies IndicLID installation.
Run once before first startup.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

import logging
logger = logging.getLogger(__name__)


def download_muril():
    print("\n📦 Downloading google/muril-base-cased (~900MB)...")
    try:
        from transformers import AutoTokenizer, AutoModel
        model_path = settings.muril_path
        model_path.mkdir(parents=True, exist_ok=True)

        if (model_path / "config.json").exists():
            print(f"✅ MuRIL already exists at {model_path}")
            return True

        print(f"   Saving to: {model_path}")
        t0 = time.time()

        print("   Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(settings.MURIL_MODEL_NAME)
        tokenizer.save_pretrained(str(model_path))
        print("   ✅ Tokenizer downloaded")

        print("   Downloading model weights (this may take several minutes)...")
        model = AutoModel.from_pretrained(settings.MURIL_MODEL_NAME)
        model.save_pretrained(str(model_path))

        elapsed = time.time() - t0
        print(f"   ✅ MuRIL downloaded in {elapsed:.1f}s")

        # Calculate size
        total_bytes = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())
        size_mb = total_bytes / (1024 * 1024)
        print(f"   📁 Size: {size_mb:.0f} MB")
        return True

    except ImportError:
        print("❌ transformers not installed. Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def check_indiclid():
    print("\n🔧 Checking IndicLID...")
    try:
        from IndicLID import IndicLID
        print("✅ ai4bharat-indiclid is installed")
        return True
    except ImportError:
        print("⚠️  ai4bharat-indiclid not installed.")
        print("   Install with: pip install ai4bharat-indiclid")
        print("   Fallback heuristic detection will be used.")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  CivicMind AI — Model Download Utility")
    print("=" * 60)

    muril_ok = download_muril()
    indiclid_ok = check_indiclid()

    print("\n" + "=" * 60)
    print(f"  MuRIL:    {'✅ READY' if muril_ok else '❌ FAILED'}")
    print(f"  IndicLID: {'✅ READY' if indiclid_ok else '⚠️  USING FALLBACK'}")
    print("=" * 60 + "\n")

    sys.exit(0 if muril_ok else 1)
