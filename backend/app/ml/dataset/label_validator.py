"""
CivicMind AI — Label & Data Quality Validator
Audits dataset records for taxonomy adherence, schema completeness, and linguistic integrity.
"""
from typing import Dict, List, Tuple, Any
from app.ml.taxonomy import CATEGORIES, TAXONOMY, PRIORITIES, SEVERITIES


class LabelValidator:
    """Validates records and outputs quality statistics."""

    def __init__(self):
        self.valid_categories = set(CATEGORIES)
        self.valid_priorities = set(PRIORITIES)
        self.valid_severities = set(SEVERITIES)

    def validate_record(self, item: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates a single record against schema and taxonomy rules."""
        text = item.get("text", "")
        if not text or len(text.strip()) < 3:
            return False, "empty_or_too_short"

        cat = item.get("category")
        if cat not in self.valid_categories:
            return False, f"invalid_category_{cat}"

        sub = item.get("subcategory")
        allowed_subs = TAXONOMY.get(cat, [])
        if sub not in allowed_subs:
            return False, f"invalid_subcategory_{sub}_for_{cat}"

        prio = item.get("priority")
        if prio not in self.valid_priorities:
            return False, f"invalid_priority_{prio}"

        sev = item.get("severity")
        if sev not in self.valid_severities:
            return False, f"invalid_severity_{sev}"

        is_g = item.get("is_grievance")
        if not isinstance(is_g, bool):
            return False, "invalid_grievance_flag"

        # Non-grievance consistency check
        if not is_g and prio in ["critical", "high"]:
            return False, "non_grievance_with_high_priority"

        # Script vs text consistency check
        script = item.get("script")
        tamil_chars = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
        devanagari_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")

        if script == "native" and item.get("primary_language") == "ta" and tamil_chars == 0:
            return False, "native_tamil_lacks_tamil_script"

        if script == "native" and item.get("primary_language") == "hi" and devanagari_chars == 0:
            return False, "native_hindi_lacks_devanagari_script"

        return True, "valid"

    def audit_dataset(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Audits list of records, filters out invalid rows, and returns clean rows + report."""
        clean_records = []
        issues_tally: Dict[str, int] = {}
        seen_texts = set()
        exact_duplicates = 0

        for r in records:
            norm_text = r.get("text", "").strip().lower()
            if norm_text in seen_texts:
                exact_duplicates += 1
                continue
            seen_texts.add(norm_text)

            is_valid, reason = self.validate_record(r)
            if is_valid:
                clean_records.append(r)
            else:
                issues_tally[reason] = issues_tally.get(reason, 0) + 1

        report = {
            "total_submitted": len(records),
            "valid_records": len(clean_records),
            "exact_duplicates_removed": exact_duplicates,
            "invalid_records_removed": sum(issues_tally.values()),
            "issues_breakdown": issues_tally,
            "validation_pass_rate": round(len(clean_records) / max(1, len(records)) * 100, 2),
        }

        return clean_records, report
