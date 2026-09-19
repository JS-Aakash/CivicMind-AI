"""
CivicMind AI — Deduplicator
Handles exact-string and near-duplicate semantic suppression.
"""
from typing import List, Dict, Tuple, Any
import re


def _tokenize(text: str) -> set:
    """Normalize and tokenize text for fast n-gram / Jaccard overlap."""
    clean = re.sub(r"[^\w\s]", "", text.lower())
    words = clean.split()
    return set(words)


def jaccard_similarity(s1: set, s2: set) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not s1 or not s2:
        return 0.0
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    return intersection / union if union > 0 else 0.0


class Deduplicator:
    """Detects and removes exact and near-duplicates."""

    def __init__(self, similarity_threshold: float = 0.92):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filters exact and near-duplicate records while preserving legitimate scenario variations.
        Returns deduplicated records and a summary report.
        """
        exact_seen = set()
        token_sets: List[set] = []
        unique_records: List[Dict[str, Any]] = []

        exact_dupes = 0
        near_dupes = 0

        for r in records:
            raw_text = r.get("text", "").strip()
            norm = raw_text.lower()

            # 1. Exact duplicate check
            if norm in exact_seen:
                exact_dupes += 1
                continue

            # 2. Near-duplicate check against recent window (to keep execution fast for 15k items)
            t_set = _tokenize(raw_text)
            is_near_duplicate = False

            # Check against the last 150 items to catch high-density template clustering
            window = token_sets[-150:] if len(token_sets) > 150 else token_sets
            for prev_set in window:
                if jaccard_similarity(t_set, prev_set) >= self.similarity_threshold:
                    is_near_duplicate = True
                    break

            if is_near_duplicate:
                near_dupes += 1
                continue

            exact_seen.add(norm)
            token_sets.append(t_set)
            unique_records.append(r)

        report = {
            "total_input": len(records),
            "exact_duplicates": exact_dupes,
            "near_duplicates": near_dupes,
            "total_removed": exact_dupes + near_dupes,
            "final_count": len(unique_records),
        }

        return unique_records, report
