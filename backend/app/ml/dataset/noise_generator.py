"""
CivicMind AI — Noise & Citizen Realism Generator
Injects realistic citizen irregularities:
- Abbreviations (pls, bcoz, asap, info, rly, bro)
- Spelling noise (tanni/thanni, paani/pani, ppl, veh)
- Punctuation irregularities (multiple exclamation marks, missing periods)
- Emojis (🚨, 😡, 💧, ⚡, 🙏, 😭, ⚠️)
- Conversational colloquial markers
"""
import random
from typing import Dict, List, Any

COMMON_ABBREVIATIONS = {
    "please": "pls",
    "Please": "Pls",
    "because": "bcoz",
    "immediately": "immd",
    "urgent": "urgnt",
    "brother": "bro",
    "road": "rd",
    "street": "st",
    "water": "watr",
    "problem": "prob",
    "information": "info",
    "number": "no",
    "department": "dept",
}

COMMON_SPELLING_VARIATIONS = {
    "thanni": ["tanni", "thani", "thanniya"],
    "varala": ["varla", "varave illa", "varala pa"],
    "paani": ["pani", "panni"],
    "nahi": ["ni", "nhi"],
    "hai": ["h", "hain"],
    "bahut": ["bohot", "bht"],
    "romba": ["rmba", "rombha"],
    "kashtam": ["kastam", "kashtama"],
}

CATEGORY_EMOJIS = {
    "water": ["💧", "🚰", "🚱", "😭"],
    "roads": ["🚗", "⚠️", "🛑", "🛵"],
    "sanitation": ["🗑️", "😷", "🪰", "🤢"],
    "electricity": ["⚡", "💡", "🔌", "💥"],
    "drainage": ["🌊", "🌧️", "🕳️", "😷"],
    "transport": ["🚌", "🚏", "⏱️", "🚶"],
    "healthcare": ["🏥", "💉", "💊", "🚨"],
    "street_infrastructure": ["🔦", "🪚", "🚸"],
    "public_safety": ["🚨", "⚠️", "🆘", "🔥"],
    "other": ["ℹ️", "❓", "🙏"],
}


class NoiseGenerator:
    """Injects realistic noise and colloquial styling into text."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def apply_noise(self, text: str, category: str, variant_type: str = "neutral") -> str:
        """Applies probabilistic transformations according to the variant type."""
        words = text.split()
        if not words:
            return text

        # 1. Spelling variations & abbreviations (applied to ~30% of examples)
        if variant_type in ["spelling_noise", "informal", "short", "voice_transcription"] or self.rng.random() < 0.25:
            new_words = []
            for w in words:
                clean_w = w.lower().strip(".,!?:")
                if clean_w in COMMON_ABBREVIATIONS and self.rng.random() < 0.7:
                    new_words.append(COMMON_ABBREVIATIONS[clean_w])
                elif clean_w in COMMON_SPELLING_VARIATIONS and self.rng.random() < 0.6:
                    new_words.append(self.rng.choice(COMMON_SPELLING_VARIATIONS[clean_w]))
                else:
                    new_words.append(w)
            words = new_words

        # 2. Punctuation noise
        if variant_type in ["urgent", "angry"] or self.rng.random() < 0.2:
            if words and words[-1].endswith("."):
                words[-1] = words[-1][:-1] + (self.rng.choice(["!!!", "??", "!!", "!"]))

        # 3. Emoji injection
        if variant_type in ["emoji_noise", "angry", "urgent"] or self.rng.random() < 0.2:
            emojis = CATEGORY_EMOJIS.get(category, ["⚠️", "🚨"])
            emoji_str = " " + "".join(self.rng.sample(emojis, min(2, len(emojis))))
            words.append(emoji_str)

        # 4. Minimal / Short variant (truncate to core issue)
        if variant_type == "minimal" and len(words) > 6:
            words = words[:6]

        return " ".join(words).strip()
