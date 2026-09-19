#!/usr/bin/env python3
"""
CivicMind AI — MuRIL Inference Test Script
Confirms google/muril-base-cased can be loaded and run locally.
Run from backend/ directory: python scripts/test_muril.py
"""
import asyncio
import sys
import time
from pathlib import Path

# Enable UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

SAMPLE_TEXTS = [
    ("English", "There has been no water supply for three days."),
    ("Tamil", "மூன்று நாட்களாக குடிநீர் வரவில்லை."),
    ("Tanglish", "Moonu naala thanni varala."),
    ("Hindi", "तीन दिन से पानी नहीं आ रहा है।"),
    ("Hinglish", "Teen din se water supply nahi aa rahi."),
    ("Mixed", "Anna 3 days ah water supply varala."),
]


async def test_muril():
    from app.services.muril_service import muril_service

    print("\n" + "=" * 65)
    print("  CivicMind AI — MuRIL Local Inference Test")
    print("=" * 65)
    print(f"  Model: {settings.MURIL_MODEL_NAME}")
    print(f"  Local path: {settings.MURIL_LOCAL_PATH}")
    print("=" * 65 + "\n")

    print("📦 Initializing MuRIL (will download if not cached)...")
    t0 = time.time()
    await muril_service.initialize()
    elapsed = time.time() - t0
    print(f"✅ MuRIL ready in {elapsed:.1f}s | Device: {muril_service._device}\n")

    print("Running inference on multilingual samples:\n")
    all_passed = True

    for lang_name, text in SAMPLE_TEXTS:
        print(f"  [{lang_name}]")
        print(f"  Input: \"{text}\"")
        t0 = time.time()
        try:
            result = await muril_service.embed(text)
            elapsed = time.time() - t0
            emb = result.embedding
            print(f"  ✅ Embedding: [{emb[0]:.4f}, {emb[1]:.4f}, ... {emb[-1]:.4f}]")
            print(f"     Dimensions: {result.dimensions} | Time: {elapsed*1000:.1f}ms")
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            all_passed = False
        print()

    print("=" * 65)
    if all_passed:
        print("✅ ALL TESTS PASSED — MuRIL is working locally")
    else:
        print("❌ SOME TESTS FAILED — Check errors above")
    print("=" * 65 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_muril())
    sys.exit(0 if success else 1)
