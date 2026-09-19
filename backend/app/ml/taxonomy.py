"""
CivicMind AI — Central Taxonomy & Label Configuration
Defines the official categories, subcategories, priorities, severities, and mapping dictionaries.
"""
from typing import Dict, List, Tuple

# 10 Top-Level Categories
CATEGORIES: List[str] = [
    "water",
    "roads",
    "sanitation",
    "electricity",
    "transport",
    "healthcare",
    "drainage",
    "street_infrastructure",
    "public_safety",
    "other",
]

# Official Subcategories per Category
TAXONOMY: Dict[str, List[str]] = {
    "water": [
        "no_water_supply",
        "low_water_pressure",
        "water_leakage",
        "contaminated_water",
        "pipeline_damage",
        "irregular_supply",
        "water_tanker_issue",
        "other",
    ],
    "roads": [
        "pothole",
        "damaged_road",
        "road_blockage",
        "broken_footpath",
        "missing_road_sign",
        "traffic_signal_issue",
        "road_flooding",
        "other",
    ],
    "sanitation": [
        "garbage_not_collected",
        "overflowing_bin",
        "illegal_dumping",
        "public_toilet_issue",
        "waste_disposal",
        "other",
    ],
    "electricity": [
        "power_outage",
        "voltage_issue",
        "fallen_wire",
        "transformer_issue",
        "street_light_failure",
        "electrical_hazard",
        "other",
    ],
    "transport": [
        "bus_delay",
        "bus_unavailable",
        "bus_condition",
        "overcrowding",
        "fare_issue",
        "driver_conduct",
        "traffic_issue",
        "other",
    ],
    "healthcare": [
        "hospital_service",
        "medicine_unavailable",
        "doctor_unavailable",
        "ambulance_issue",
        "sanitation_healthcare",
        "other",
    ],
    "drainage": [
        "blocked_drain",
        "sewage_overflow",
        "waterlogging",
        "storm_drain_issue",
        "flooding",
        "other",
    ],
    "street_infrastructure": [
        "broken_streetlight",
        "damaged_public_property",
        "park_issue",
        "footpath_issue",
        "public_facility",
        "other",
    ],
    "public_safety": [
        "unsafe_area",
        "fallen_structure",
        "fire_hazard",
        "dangerous_wire",
        "accident_hazard",
        "other",
    ],
    "other": [
        "unknown_service",
        "general_civic_issue",
        "unclear",
        "other",
    ],
}

# Distinct subcategories across all categories (with category prefix for unique global indexing)
ALL_SUBCATEGORIES: List[str] = []
for cat, subs in TAXONOMY.items():
    for sub in subs:
        scoped_name = f"{cat}:{sub}"
        if scoped_name not in ALL_SUBCATEGORIES:
            ALL_SUBCATEGORIES.append(scoped_name)

# Priority Levels (Urgency of Response)
PRIORITIES: List[str] = ["low", "medium", "high", "critical"]

# Severity Levels (Seriousness of Underlying Problem)
SEVERITIES: List[str] = ["low", "medium", "high", "critical"]

# Grievance Binary Classes
GRIEVANCE_CLASSES: List[str] = ["non_grievance", "grievance"]

# Languages & Dialects
LANGUAGES: List[str] = [
    "en",        # English
    "ta",        # Tamil (Native script)
    "ta_roman",  # Tanglish / Romanized Tamil
    "hi",        # Hindi (Native script)
    "hi_roman",  # Hinglish / Romanized Hindi
    "mixed",     # Mixed / Code-mixed / Noisy
]

# Task Weights for Multi-Task Loss
DEFAULT_TASK_WEIGHTS: Dict[str, float] = {
    "grievance": 1.0,
    "category": 1.0,
    "subcategory": 0.8,
    "severity": 0.8,
    "priority": 1.0,
}

# Label Encoders / Decoders
CATEGORY_TO_IDX: Dict[str, int] = {cat: idx for idx, cat in enumerate(CATEGORIES)}
IDX_TO_CATEGORY: Dict[int, str] = {idx: cat for cat, idx in CATEGORY_TO_IDX.items()}

SUBCATEGORY_TO_IDX: Dict[str, int] = {sub: idx for idx, sub in enumerate(ALL_SUBCATEGORIES)}
IDX_TO_SUBCATEGORY: Dict[int, str] = {idx: sub for sub, idx in SUBCATEGORY_TO_IDX.items()}

PRIORITY_TO_IDX: Dict[str, int] = {p: idx for idx, p in enumerate(PRIORITIES)}
IDX_TO_PRIORITY: Dict[int, str] = {idx: p for p, idx in PRIORITY_TO_IDX.items()}

SEVERITY_TO_IDX: Dict[str, int] = {s: idx for idx, s in enumerate(SEVERITIES)}
IDX_TO_SEVERITY: Dict[int, str] = {idx: s for s, idx in SEVERITY_TO_IDX.items()}

GRIEVANCE_TO_IDX: Dict[bool, int] = {False: 0, True: 1}
IDX_TO_GRIEVANCE: Dict[int, bool] = {0: False, 1: True}


def get_scoped_subcategory(category: str, subcategory: str) -> str:
    """Ensure subcategory is in 'category:subcategory' format."""
    if ":" in subcategory:
        return subcategory
    return f"{category}:{subcategory}"


def parse_scoped_subcategory(scoped_name: str) -> Tuple[str, str]:
    """Parse 'category:subcategory' into (category, subcategory)."""
    if ":" in scoped_name:
        parts = scoped_name.split(":", 1)
        return parts[0], parts[1]
    return "other", scoped_name
