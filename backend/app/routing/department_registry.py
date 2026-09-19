"""
CivicMind AI — Central Department Registry (Single Source of Truth)
Defines the authoritative configuration of all municipal departments,
their assigned civic categories, subcategories, default SLA turnaround windows,
contact channels, and escalation policies.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class DepartmentConfig:
    """Configuration for a municipal department."""
    id: str  # Unique slug identifier e.g. "water_supply"
    code: str  # Official short code e.g. "WATER_SUPPLY"
    name: str  # Official display name e.g. "Water Supply Department"
    description: str
    categories: List[str]  # Primary civic categories handled
    subcategories: List[str] = field(default_factory=list)  # Explicit subcategories
    default_sla_hours: Dict[str, int] = field(default_factory=lambda: {
        "critical": 6,
        "high": 24,
        "medium": 48,
        "low": 120,
    })
    escalation_tier: str = "field_operations"
    contact_email: str = "grievance@civicmind.gov.in"
    contact_phone: str = "1800-425-0000"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "categories": self.categories,
            "subcategories": self.subcategories,
            "default_sla_hours": self.default_sla_hours,
            "escalation_tier": self.escalation_tier,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "enabled": self.enabled,
        }


# Canonical registry of all 10 departments
DEPARTMENTS: List[DepartmentConfig] = [
    DepartmentConfig(
        id="water_supply",
        code="WATER_SUPPLY",
        name="Water Supply Department",
        description="Responsible for municipal drinking water distribution, piped connections, tanker supply, and pipeline maintenance.",
        categories=["water"],
        subcategories=["no_water_supply", "low_water_pressure", "water_leakage", "contaminated_water", "pipeline_damage", "irregular_supply", "water_tanker_issue", "other"],
        default_sla_hours={"critical": 4, "high": 24, "medium": 48, "low": 96},
        contact_email="water@civicmind.gov.in",
        contact_phone="1800-425-1111",
    ),
    DepartmentConfig(
        id="roads_highways",
        code="ROADS_HIGHWAYS",
        name="Municipal Engineering / Roads Department",
        description="Oversees road paving, pothole repairs, footpath maintenance, traffic signage, and structural road safety.",
        categories=["roads"],
        subcategories=["pothole", "damaged_road", "road_blockage", "broken_footpath", "missing_road_sign", "traffic_signal_issue", "road_flooding", "other"],
        default_sla_hours={"critical": 12, "high": 48, "medium": 72, "low": 168},
        contact_email="roads@civicmind.gov.in",
        contact_phone="1800-425-2222",
    ),
    DepartmentConfig(
        id="sanitation",
        code="SANITATION",
        name="Sanitation & Waste Management Department",
        description="Handles doorstep waste collection, commercial garbage bins, illegal dumping clearance, public toilet hygiene, and debris.",
        categories=["sanitation"],
        subcategories=["garbage_not_collected", "overflowing_bin", "illegal_dumping", "public_toilet_issue", "waste_disposal", "other"],
        default_sla_hours={"critical": 8, "high": 24, "medium": 48, "low": 96},
        contact_email="sanitation@civicmind.gov.in",
        contact_phone="1800-425-3333",
    ),
    DepartmentConfig(
        id="electricity_board",
        code="ELECTRICITY_BOARD",
        name="Electricity Distribution Board",
        description="Manages power grid reliability, transformer health, voltage surges, streetlights, and live line electrical hazards.",
        categories=["electricity"],
        subcategories=["power_outage", "voltage_issue", "fallen_wire", "transformer_issue", "street_light_failure", "electrical_hazard", "other"],
        default_sla_hours={"critical": 2, "high": 12, "medium": 24, "low": 72},
        contact_email="electricity@civicmind.gov.in",
        contact_phone="1800-425-4444",
    ),
    DepartmentConfig(
        id="drainage",
        code="DRAINAGE",
        name="Drainage & Stormwater Management Department",
        description="Maintains stormwater drains, open culverts, sewage overflow clearance, desilting, and flood mitigation.",
        categories=["drainage"],
        subcategories=["blocked_drain", "sewage_overflow", "broken_drain_cover", "waterlogging", "foul_smell", "other"],
        default_sla_hours={"critical": 6, "high": 24, "medium": 48, "low": 96},
        contact_email="drainage@civicmind.gov.in",
        contact_phone="1800-425-5555",
    ),
    DepartmentConfig(
        id="public_transport",
        code="PUBLIC_TRANSPORT",
        name="Public Transport Authority",
        description="Oversees city bus routes, bus shelter infrastructure, transit timing irregularities, and passenger safety.",
        categories=["transport"],
        subcategories=["bus_frequency_issue", "overcrowding", "reckless_driving", "broken_bus_shelter", "route_deviation", "other"],
        default_sla_hours={"critical": 12, "high": 48, "medium": 72, "low": 120},
        contact_email="transport@civicmind.gov.in",
        contact_phone="1800-425-6666",
    ),
    DepartmentConfig(
        id="health_services",
        code="HEALTH_SERVICES",
        name="Public Health & Healthcare Services",
        description="Manages primary health centers (PHCs), vector control, disease outbreak response, food safety, and clinic hygiene.",
        categories=["healthcare"],
        subcategories=["phc_service_issue", "vector_control", "stray_animal_menace", "dead_animal_removal", "medical_waste_dump", "other"],
        default_sla_hours={"critical": 4, "high": 18, "medium": 36, "low": 72},
        contact_email="health@civicmind.gov.in",
        contact_phone="1800-425-7777",
    ),
    DepartmentConfig(
        id="street_infrastructure",
        code="STREET_INFRASTRUCTURE",
        name="Street Infrastructure Department",
        description="Maintains road barriers, medians, street name boards, pedestrian zebra crossings, and public encroachment removal.",
        categories=["street_infrastructure"],
        subcategories=["damaged_street_furniture", "encroachment", "fallen_tree", "damaged_footpath", "missing_signboard", "other"],
        default_sla_hours={"critical": 8, "high": 36, "medium": 72, "low": 144},
        contact_email="infrastructure@civicmind.gov.in",
        contact_phone="1800-425-8888",
    ),
    DepartmentConfig(
        id="public_safety",
        code="PUBLIC_SAFETY",
        name="Public Safety & Emergency Response",
        description="Coordinates quick response for acute hazards, fire risks, building structural collapse, open manholes, and life safety threats.",
        categories=["public_safety"],
        subcategories=["fire_hazard", "structural_damage", "open_manhole", "accident_prone_spot", "chemical_fumes", "other"],
        default_sla_hours={"critical": 1, "high": 6, "medium": 24, "low": 48},
        contact_email="safety@civicmind.gov.in",
        contact_phone="1800-425-9999",
    ),
    DepartmentConfig(
        id="citizen_helpdesk",
        code="CITIZEN_HELPDESK",
        name="Citizen Information & Helpdesk",
        description="Central reception and administrative inquiry desk for procedural requests, welfare schemes, contact queries, and non-grievance inquiries.",
        categories=["other", "general"],
        subcategories=["general_inquiry", "procedural_query", "scheme_info", "feedback", "other"],
        default_sla_hours={"critical": 24, "high": 48, "medium": 72, "low": 120},
        contact_email="helpdesk@civicmind.gov.in",
        contact_phone="1800-425-0000",
    ),
]


class DepartmentRegistry:
    """
    Singleton registry managing all department configurations and fast lookups.
    """

    def __init__(self, departments: Optional[List[DepartmentConfig]] = None):
        self._departments = {dept.id: dept for dept in (departments or DEPARTMENTS)}
        self._code_index = {dept.code: dept for dept in self._departments.values()}
        self._category_index: Dict[str, List[DepartmentConfig]] = {}
        self._subcategory_index: Dict[str, List[DepartmentConfig]] = {}

        for dept in self._departments.values():
            for cat in dept.categories:
                self._category_index.setdefault(cat, []).append(dept)
            for sub in dept.subcategories:
                self._subcategory_index.setdefault(sub, []).append(dept)

    def get_by_id(self, dept_id: str) -> Optional[DepartmentConfig]:
        return self._departments.get(dept_id)

    def get_by_code(self, code: str) -> Optional[DepartmentConfig]:
        return self._code_index.get(code)

    def get_by_category(self, category: str) -> List[DepartmentConfig]:
        return self._category_index.get(category, [self.get_by_id("citizen_helpdesk")])

    def get_primary_department(self, category: str, subcategory: Optional[str] = None) -> DepartmentConfig:
        """Finds best matching primary department based on category and subcategory."""
        # Special hazard subcategories override to Public Safety
        if subcategory in ["open_manhole", "fire_hazard", "chemical_fumes", "structural_damage"]:
            return self.get_by_id("public_safety")

        if subcategory in ["fallen_wire", "electrical_hazard"]:
            return self.get_by_id("electricity_board")

        # Standard category match
        depts = self._category_index.get(category)
        if depts and len(depts) > 0:
            return depts[0]

        return self.get_by_id("citizen_helpdesk")

    def get_all(self) -> List[DepartmentConfig]:
        return list(self._departments.values())


# Global singleton
department_registry = DepartmentRegistry()
DEPARTMENT_REGISTRY = department_registry


def get_department_by_id(dept_id: str) -> Optional[DepartmentConfig]:
    return department_registry.get_by_id(dept_id)


def get_department_for_issue(category: str, subcategory: Optional[str] = None) -> DepartmentConfig:
    return department_registry.get_primary_department(category, subcategory)

