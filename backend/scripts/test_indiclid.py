#!/usr/bin/env python3
"""
CivicMind AI — IndicLID Language Detection Test Script
Run from backend/ directory: python scripts/test_indiclid.py
"""
import asyncio
import sys
from pathlib import Path

# Enable UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import setup_logging
setup_logging()

SAMPLE_TEXTS = [
    ("English", "There has been no water supply for three days."),
    ("Tamil (native)", "மூன்று நாட்களாக குடிநீர் வரவில்லை."),
    ("Tanglish", "Moonu naala thanni varala."),
    ("Hindi (native)", "तीन दिन से पानी नहीं आ रहा है।"),
    ("Hinglish", "Teen din se water supply nahi aa rahi."),
    ("Mixed", "Anna 3 days ah water supply varala."),
]


async def test_indiclid():
    from app.services.language_service import language_detection_service

    print("\n" + "=" * 65)
    print("  CivicMind AI — IndicLID Language Detection Test")
    print("=" * 65 + "\n")

    print("🔧 Initializing IndicLID...")
    await language_detection_service.initialize()
    status = language_detection_service.get_status()
    backend = status["backend"]
    print(f"✅ Language detection ready | Backend: {backend}\n")

    print("Running language detection on multilingual samples:\n")
    all_passed = True

    for lang_name, text in SAMPLE_TEXTS:
        print(f"  [{lang_name}]")
        print(f"  Input: \"{text}\"")
        try:
            result = await language_detection_service.detect(text)
            print(f"  ✅ Primary: {result.primary_language} ({result.language_name})")
            print(f"     Languages: {result.languages}")
            print(f"     Script: {result.script}")
            print(f"     Code-mixed: {result.is_code_mixed}")
            print(f"     Confidence: {result.confidence:.2f}")
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            all_passed = False
        print()

    print("=" * 65)
    if all_passed:
        print(f"✅ ALL TESTS PASSED — Language detection working ({backend})")
        if backend == "heuristic_fallback":
            print("   ⚠️  Using heuristic fallback. Install ai4bharat-indiclid for real IndicLID.")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 65 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_indiclid())
    sys.exit(0 if success else 1)
