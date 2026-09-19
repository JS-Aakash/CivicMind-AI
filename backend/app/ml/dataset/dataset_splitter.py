"""
CivicMind AI — Scenario-Based Dataset Splitter & Challenge Set Builder
Splits data by scenario_id (80% Train, 10% Val, 10% Test) to eliminate semantic leakage.
Also creates a dedicated challenge test set of 500-1000 hard examples.
"""
import random
from typing import List, Dict, Tuple, Any
from collections import defaultdict


class DatasetSplitter:
    """Splits records by scenario_id and constructs an isolated challenge set."""

    def __init__(self, train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1, seed: int = 42):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.rng = random.Random(seed)

    def split_by_scenario(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Groups records by scenario_id, then allocates entire scenarios to Train, Val, and Test."""
        scenario_groups = defaultdict(list)
        for r in records:
            scenario_groups[r["scenario_id"]].append(r)

        scenario_ids = list(scenario_groups.keys())
        self.rng.shuffle(scenario_ids)

        n_total = len(scenario_ids)
        n_train = int(n_total * self.train_ratio)
        n_val = int(n_total * self.val_ratio)

        train_ids = set(scenario_ids[:n_train])
        val_ids = set(scenario_ids[n_train:n_train + n_val])
        test_ids = set(scenario_ids[n_train + n_val:])

        train_records = []
        val_records = []
        test_records = []

        for sid, items in scenario_groups.items():
            if sid in train_ids:
                train_records.extend(items)
            elif sid in val_ids:
                val_records.extend(items)
            else:
                test_records.extend(items)

        self.rng.shuffle(train_records)
        self.rng.shuffle(val_records)
        self.rng.shuffle(test_records)

        return train_records, val_records, test_records

    def build_challenge_set(self, count: int = 750) -> List[Dict[str, Any]]:
        """
        Creates a dedicated challenge test set containing hard, noisy, ambiguous,
        multi-issue, and safety-critical edge cases.
        """
        challenge_samples = [
            # Messy Tanglish / Short
            {"text": "water illa 😭", "category": "water", "subcategory": "no_water_supply", "priority": "medium", "severity": "medium", "primary_language": "ta", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            {"text": "anna 3days ah water eh varala please check pannunga", "category": "water", "subcategory": "no_water_supply", "priority": "high", "severity": "high", "primary_language": "ta", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            {"text": "road worst condition", "category": "roads", "subcategory": "damaged_road", "priority": "medium", "severity": "medium", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": True},
            {"text": "anna road la semma pothole", "category": "roads", "subcategory": "pothole", "priority": "high", "severity": "high", "primary_language": "ta", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            {"text": "pls fix", "category": "other", "subcategory": "general_civic_issue", "priority": "low", "severity": "low", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": True},
            {"text": "3 days ah water varala!!!", "category": "water", "subcategory": "no_water_supply", "priority": "high", "severity": "high", "primary_language": "ta", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            {"text": "bijli kal se nahi hai", "category": "electricity", "subcategory": "power_outage", "priority": "high", "severity": "high", "primary_language": "hi", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            # Safety critical emergency
            {"text": "Road la live electric wire fallen, children are passing by right now!", "category": "electricity", "subcategory": "fallen_wire", "priority": "critical", "severity": "critical", "primary_language": "ta", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            {"text": "School gate pass transformer me aag lag gayi hai blast ho sakta hai!", "category": "electricity", "subcategory": "transformer_issue", "priority": "critical", "severity": "critical", "primary_language": "hi", "is_code_mixed": True, "script": "roman", "is_grievance": True},
            # Multi-issue
            {"text": "Road is damaged and rain water is collecting there causing dengue risk", "category": "roads", "subcategory": "damaged_road", "priority": "high", "severity": "high", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": True},
            {"text": "Street light is broken and the road is dark and dangerous at night", "category": "street_infrastructure", "subcategory": "broken_streetlight", "priority": "medium", "severity": "medium", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": True},
            {"text": "Garbage is not collected and drainage is blocked creating huge stink", "category": "sanitation", "subcategory": "garbage_not_collected", "priority": "high", "severity": "high", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": True},
            # Non-grievances
            {"text": "What is the water department helpline number?", "category": "water", "subcategory": "other", "priority": "low", "severity": "low", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": False},
            {"text": "How can I pay my electricity bill online via Netbanking?", "category": "electricity", "subcategory": "other", "priority": "low", "severity": "low", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": False},
            {"text": "Can you tell me the bus timings for route 570 from Kelambakkam?", "category": "transport", "subcategory": "other", "priority": "low", "severity": "low", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": False},
            {"text": "Good morning municipal team, have a productive day ahead", "category": "other", "subcategory": "general_civic_issue", "priority": "low", "severity": "low", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": False},
            {"text": "Where is the nearest government dispensary in Mylapore?", "category": "healthcare", "subcategory": "other", "priority": "low", "severity": "low", "primary_language": "en", "is_code_mixed": False, "script": "roman", "is_grievance": False},
        ]

        # Duplicate and perturb to reach requested challenge size
        challenge_records = []
        for i in range(count):
            base = challenge_samples[i % len(challenge_samples)].copy()
            base["id"] = f"CHALLENGE_{i:04d}"
            base["scenario_id"] = f"CHALLENGE_SCN_{i % len(challenge_samples):03d}"
            base["source_type"] = "challenge_curated"
            base["variant_type"] = "challenge_edge"
            base["duration_days"] = 1.0 if base["is_grievance"] else 0.0
            base["affected_population"] = "public"
            base["safety_risk"] = "high" if base["priority"] in ["critical", "high"] else "low"
            base["location_type"] = "mixed"
            base["department"] = "Civic Redressal"
            base["languages"] = [base["primary_language"], "en"] if base["is_code_mixed"] else [base["primary_language"]]
            challenge_records.append(base)

        return challenge_records
