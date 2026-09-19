"""
CivicMind AI — Scenario Generator
Generates structured civic grievance and non-grievance scenarios.
"""
import random
from typing import Dict, List, Any
from app.ml.taxonomy import TAXONOMY, CATEGORIES

# Realistic location contexts (Chennai & metro focused)
LOCATIONS = [
    {"name": "T. Nagar", "type": "commercial_area", "ward": "Ward 117"},
    {"name": "Velachery", "type": "residential_lowland", "ward": "Ward 178"},
    {"name": "Anna Nagar", "type": "residential_colony", "ward": "Ward 102"},
    {"name": "Mylapore", "type": "dense_old_town", "ward": "Ward 124"},
    {"name": "Tambaram", "type": "outer_suburb", "ward": "Ward 190"},
    {"name": "Guindy", "type": "industrial_junction", "ward": "Ward 160"},
    {"name": "Perambur", "type": "railway_hub", "ward": "Ward 70"},
    {"name": "Adyar", "type": "riverfront_colony", "ward": "Ward 173"},
    {"name": "Chromepet", "type": "arterial_highway", "ward": "Ward 185"},
    {"name": "Royapuram", "type": "coastal_dense", "ward": "Ward 49"},
    {"name": "Near Government School", "type": "school_zone", "ward": "Ward 85"},
    {"name": "Main Bus Terminus", "type": "transit_hub", "ward": "Ward 130"},
    {"name": "Opposite Primary Health Center", "type": "hospital_zone", "ward": "Ward 94"},
    {"name": "Near Weekly Vegetable Market", "type": "market_area", "ward": "Ward 112"},
    {"name": "Children's Park Road", "type": "park_zone", "ward": "Ward 141"},
]

# Durations and their typical impact on urgency
DURATION_OPTIONS = [
    {"text": "since 2 hours", "days": 0.1, "urgency_boost": 0},
    {"text": "since morning", "days": 0.5, "urgency_boost": 0},
    {"text": "for 2 days", "days": 2.0, "urgency_boost": 1},
    {"text": "for 3 days", "days": 3.0, "urgency_boost": 1},
    {"text": "for 5 days", "days": 5.0, "urgency_boost": 2},
    {"text": "for more than a week", "days": 7.0, "urgency_boost": 2},
    {"text": "for 2 weeks", "days": 14.0, "urgency_boost": 2},
    {"text": "just now happened", "days": 0.05, "urgency_boost": 1},
]

# Department mapping
DEPARTMENT_MAP = {
    "water": "Chennai Metro Water (CMWSSB)",
    "roads": "Greater Chennai Corporation (Works Dept)",
    "sanitation": "Solid Waste Management Dept",
    "electricity": "TANGEDCO (Electricity Board)",
    "transport": "Metropolitan Transport Corporation (MTC)",
    "healthcare": "Public Health & Welfare Dept",
    "drainage": "Storm Water Drainage & Sewage Dept",
    "street_infrastructure": "Electrical & Street Lighting Dept",
    "public_safety": "Disaster Management & Civic Safety",
    "other": "General Grievance Redressal Cell",
}

# Rich scenario templates covering each subcategory
SCENARIO_TEMPLATES: List[Dict[str, Any]] = [
    # WATER
    {
        "template_id": "WAT_01",
        "category": "water",
        "subcategory": "no_water_supply",
        "problem": "drinking water pipeline is dry and no municipal water has arrived",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "low",
        "is_grievance": True,
    },
    {
        "template_id": "WAT_02",
        "category": "water",
        "subcategory": "contaminated_water",
        "problem": "tap water is yellow, muddy and smelling like sewage",
        "base_severity": "critical",
        "base_priority": "critical",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "WAT_03",
        "category": "water",
        "subcategory": "water_leakage",
        "problem": "underground water supply main pipe burst and fresh water is flooding the street",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "low",
        "is_grievance": True,
    },
    {
        "template_id": "WAT_04",
        "category": "water",
        "subcategory": "low_water_pressure",
        "problem": "water pressure in public supply line is too low to fill buckets",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": True,
    },
    {
        "template_id": "WAT_05",
        "category": "water",
        "subcategory": "water_tanker_issue",
        "problem": "booked government water tanker did not arrive and driver phone is switched off",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "low",
        "is_grievance": True,
    },
    {
        "template_id": "WAT_06",
        "category": "water",
        "subcategory": "pipeline_damage",
        "problem": "road construction workers broke drinking water pipe and water is gushing out",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "WAT_07",
        "category": "water",
        "subcategory": "irregular_supply",
        "problem": "water supply timing is irregular and coming at midnight without prior notice",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": True,
    },

    # ROADS
    {
        "template_id": "ROD_01",
        "category": "roads",
        "subcategory": "pothole",
        "problem": "deep dangerous pothole on the road causing two-wheeler riders to skid and fall",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "ROD_02",
        "category": "roads",
        "subcategory": "damaged_road",
        "problem": "entire road surface has peeled off leaving sharp gravel and uneven mud tracks",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "ROD_03",
        "category": "roads",
        "subcategory": "road_blockage",
        "problem": "fallen tree trunk and debris completely blocking both lanes of road",
        "base_severity": "high",
        "base_priority": "critical",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "ROD_04",
        "category": "roads",
        "subcategory": "broken_footpath",
        "problem": "concrete pedestrian footpath broken with exposed iron rebar making walking risky",
        "base_severity": "medium",
        "base_priority": "low",
        "safety_risk": "low",
        "is_grievance": True,
    },
    {
        "template_id": "ROD_05",
        "category": "roads",
        "subcategory": "traffic_signal_issue",
        "problem": "busy four-way intersection traffic lights are dead causing vehicle gridlock and close accidents",
        "base_severity": "high",
        "base_priority": "critical",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "ROD_06",
        "category": "roads",
        "subcategory": "missing_road_sign",
        "problem": "speed breaker sign and divider warning board missing leading to night accidents",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "medium",
        "is_grievance": True,
    },

    # SANITATION
    {
        "template_id": "SAN_01",
        "category": "sanitation",
        "subcategory": "garbage_not_collected",
        "problem": "door-to-door municipal waste collection van has not visited our street for days",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "low",
        "is_grievance": True,
    },
    {
        "template_id": "SAN_02",
        "category": "sanitation",
        "subcategory": "overflowing_bin",
        "problem": "community dustbin overflowing with rotting trash spilling onto the street and spreading foul stench",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "SAN_03",
        "category": "sanitation",
        "subcategory": "illegal_dumping",
        "problem": "commercial trucks dumping poultry and construction debris in vacant residential plot",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "SAN_04",
        "category": "sanitation",
        "subcategory": "public_toilet_issue",
        "problem": "public toilet near bus stop has no water, doors are jammed, and sewage leaking inside",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "low",
        "is_grievance": True,
    },

    # ELECTRICITY
    {
        "template_id": "ELE_01",
        "category": "electricity",
        "subcategory": "fallen_wire",
        "problem": "live 440V electrical wire snapped and hanging dangerously close to pavement",
        "base_severity": "critical",
        "base_priority": "critical",
        "safety_risk": "emergency",
        "is_grievance": True,
    },
    {
        "template_id": "ELE_02",
        "category": "electricity",
        "subcategory": "transformer_issue",
        "problem": "roadside electrical transformer sparking loudly with black smoke and burning smell",
        "base_severity": "critical",
        "base_priority": "critical",
        "safety_risk": "emergency",
        "is_grievance": True,
    },
    {
        "template_id": "ELE_03",
        "category": "electricity",
        "subcategory": "power_outage",
        "problem": "complete electricity blackout across entire neighborhood during extreme summer heat",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "ELE_04",
        "category": "electricity",
        "subcategory": "voltage_issue",
        "problem": "severe low voltage causing fans to stall and risking damage to home appliances",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": True,
    },
    {
        "template_id": "ELE_05",
        "category": "electricity",
        "subcategory": "street_light_failure",
        "problem": "series of 8 consecutive streetlights completely unlit making road pitch dark",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "medium",
        "is_grievance": True,
    },

    # DRAINAGE
    {
        "template_id": "DRA_01",
        "category": "drainage",
        "subcategory": "sewage_overflow",
        "problem": "underground sewer manhole overflowing with black foul-smelling sewage into residential front yards",
        "base_severity": "critical",
        "base_priority": "critical",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "DRA_02",
        "category": "drainage",
        "subcategory": "waterlogging",
        "problem": "knee-deep stagnant rainwater logged on street preventing residents and school children from exiting",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "DRA_03",
        "category": "drainage",
        "subcategory": "blocked_drain",
        "problem": "stormwater drain choked with plastic bags and solid debris causing rainwater backflow",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "low",
        "is_grievance": True,
    },

    # TRANSPORT
    {
        "template_id": "TRA_01",
        "category": "transport",
        "subcategory": "bus_unavailable",
        "problem": "government bus on route 21G not operating for 3 consecutive trips leaving workers stranded",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "none",
        "is_grievance": True,
    },
    {
        "template_id": "TRA_02",
        "category": "transport",
        "subcategory": "overcrowding",
        "problem": "public buses skipping designated bus shelter stop due to severe footboard overcrowding",
        "base_severity": "medium",
        "base_priority": "low",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "TRA_03",
        "category": "transport",
        "subcategory": "bus_condition",
        "problem": "bus floor corroded with gaping holes and broken windows causing rain to soak passengers",
        "base_severity": "medium",
        "base_priority": "low",
        "safety_risk": "low",
        "is_grievance": True,
    },

    # HEALTHCARE
    {
        "template_id": "HEA_01",
        "category": "healthcare",
        "subcategory": "medicine_unavailable",
        "problem": "government primary health center dispensary has no insulin or fever medicines in stock",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "HEA_02",
        "category": "healthcare",
        "subcategory": "doctor_unavailable",
        "problem": "duty doctor absent during emergency casualty hours with long queue of sick patients waiting",
        "base_severity": "critical",
        "base_priority": "critical",
        "safety_risk": "high",
        "is_grievance": True,
    },
    {
        "template_id": "HEA_03",
        "category": "healthcare",
        "subcategory": "sanitation_healthcare",
        "problem": "hospital ward bathrooms clogged with bio-waste and no disinfectant cleaned for 24 hours",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "high",
        "is_grievance": True,
    },

    # STREET INFRASTRUCTURE
    {
        "template_id": "STR_01",
        "category": "street_infrastructure",
        "subcategory": "broken_streetlight",
        "problem": "streetlight pole broken and bent into pedestrian path after minor collision",
        "base_severity": "medium",
        "base_priority": "medium",
        "safety_risk": "medium",
        "is_grievance": True,
    },
    {
        "template_id": "STR_02",
        "category": "street_infrastructure",
        "subcategory": "park_issue",
        "problem": "public corporation park swing chains snapped and children playing equipment is rusted sharp",
        "base_severity": "medium",
        "base_priority": "low",
        "safety_risk": "medium",
        "is_grievance": True,
    },

    # PUBLIC SAFETY
    {
        "template_id": "SAF_01",
        "category": "public_safety",
        "subcategory": "dangerous_wire",
        "problem": "heavy commercial cables pulled down by tempo hanging across entrance gate",
        "base_severity": "high",
        "base_priority": "critical",
        "safety_risk": "emergency",
        "is_grievance": True,
    },
    {
        "template_id": "SAF_02",
        "category": "public_safety",
        "subcategory": "unsafe_area",
        "problem": "abandoned compound wall cracking and leaning outward towards narrow school pedestrian path",
        "base_severity": "high",
        "base_priority": "high",
        "safety_risk": "high",
        "is_grievance": True,
    },

    # NON-GRIEVANCE INQUIRIES & QUESTIONS (10-15% of dataset)
    {
        "template_id": "NONG_01",
        "category": "water",
        "subcategory": "other",
        "problem": "How can I apply for a new municipal drinking water pipeline connection online?",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
    {
        "template_id": "NONG_02",
        "category": "electricity",
        "subcategory": "other",
        "problem": "What is the procedure and payment link to pay my monthly electricity bill via UPI?",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
    {
        "template_id": "NONG_03",
        "category": "transport",
        "subcategory": "other",
        "problem": "Can you please share the daily timetable for morning buses from Central to Guindy?",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
    {
        "template_id": "NONG_04",
        "category": "healthcare",
        "subcategory": "other",
        "problem": "What are the visiting hours and child vaccination timings at the Government General Hospital?",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
    {
        "template_id": "NONG_05",
        "category": "other",
        "subcategory": "general_civic_issue",
        "problem": "Hello, good morning to the municipal administration team. Have a great day.",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
    {
        "template_id": "NONG_06",
        "category": "sanitation",
        "subcategory": "other",
        "problem": "What is the toll-free customer care number for corporation sanitation ward office?",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
    {
        "template_id": "NONG_07",
        "category": "roads",
        "subcategory": "other",
        "problem": "Where can I read the corporation guidelines for applying for road cutting permission?",
        "base_severity": "low",
        "base_priority": "low",
        "safety_risk": "none",
        "is_grievance": False,
    },
]


class ScenarioGenerator:
    """Generates parameterized scenario instances."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate_scenarios(self, count: int) -> List[Dict[str, Any]]:
        """Generate `count` scenario instances by expanding templates with location, duration, and urgency variables."""
        scenarios = []
        templates = SCENARIO_TEMPLATES

        for i in range(count):
            tmpl = templates[i % len(templates)]
            loc = self.rng.choice(LOCATIONS)
            dur = self.rng.choice(DURATION_OPTIONS)

            # Determine dynamic priority based on duration and safety risk
            priority = tmpl["base_priority"]
            severity = tmpl["base_severity"]

            if tmpl["is_grievance"]:
                if tmpl["safety_risk"] == "emergency":
                    priority = "critical"
                    severity = "critical"
                elif dur["urgency_boost"] >= 2 and priority in ["low", "medium"]:
                    priority = "high"
                elif dur["urgency_boost"] >= 1 and priority == "low":
                    priority = "medium"

            scenario_id = f"SCN_{tmpl['template_id']}_{i:05d}"

            scenarios.append({
                "scenario_id": scenario_id,
                "template_id": tmpl["template_id"],
                "category": tmpl["category"],
                "subcategory": tmpl["subcategory"],
                "problem": tmpl["problem"],
                "severity": severity,
                "priority": priority,
                "is_grievance": tmpl["is_grievance"],
                "safety_risk": tmpl["safety_risk"],
                "duration_text": dur["text"] if tmpl["is_grievance"] else "N/A",
                "duration_days": dur["days"] if tmpl["is_grievance"] else 0.0,
                "location_name": loc["name"],
                "location_type": loc["type"],
                "ward": loc["ward"],
                "department": DEPARTMENT_MAP.get(tmpl["category"], "General Grievance Cell"),
            })

        return scenarios
