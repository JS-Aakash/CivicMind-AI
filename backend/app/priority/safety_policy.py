"""
CivicMind AI — Controlled Safety Escalation Policy
Distinguishes genuine immediate hazards from passive/historical mentions
and manages emergency safety overrides with transparent justification.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import re


@dataclass
class SafetyAssessment:
    """Structured assessment of public safety risks."""
    is_immediate_hazard: bool = False
    hazard_types: List[str] = field(default_factory=list)
    risk_level: str = "none"  # "none", "moderate", "severe", "critical"
    requires_safety_override: bool = False
    justification: Optional[str] = None
    recommended_emergency_sla_hours: Optional[int] = None

    @property
    def is_acute_safety_hazard(self) -> bool:
        return self.is_immediate_hazard or self.risk_level in ["critical", "severe"]

    @property
    def override_triggered(self) -> bool:
        return self.requires_safety_override

    @property
    def forced_priority(self) -> Optional[str]:
        if self.requires_safety_override and self.risk_level == "critical":
            return "critical"
        elif self.requires_safety_override and self.risk_level == "severe":
            return "high"
        return None


def evaluate_safety_override(
    text: str,
    category: str = "general",
    subcategory: Optional[str] = None,
    entities: Optional[Dict[str, Any]] = None,
    vulnerable_impact: bool = False,
) -> SafetyAssessment:
    hazards = []
    if entities and "hazard" in entities:
        hazards.append(str(entities["hazard"]))
    return SafetyPolicy.evaluate_safety(
        text=text,
        category=category,
        subcategory=subcategory,
        extracted_hazards=hazards,
        vulnerable_impact=vulnerable_impact,
    )



class SafetyPolicy:
    """
    Evaluates contextual hazard signals to determine whether an emergency safety override applies.
    """

    # High voltage & electrical hazards
    ACUTE_ELECTRICAL = [
        (r"(live\s*(?:electric\s*|electrical\s*)?wire|open\s*wire|broken\s*wire|fallen\s*(?:electric\s*|electrical\s*)?wire|kambi\s*arundhu|taar\s*toot|sparking|short\s*circuit|transformer\s*blast|transformer\s*fire)", "Live electrical / transformer hazard"),
    ]

    # Open manholes & deep pits on public roads
    OPEN_PITS = [
        (r"(open\s*manhole|manhole\s*moodi\s*illa|manhole\s*khula|open\s*drain|deep\s*pit|open\s*gutter)", "Open manhole / drainage pit"),
    ]

    # Structural collapse & gas leaks
    STRUCTURAL_CHEMICAL = [
        (r"(building\s*collapse|wall\s*falling|suvar\s*idiyuthu|bridge\s*crack|gas\s*leak|cylinder\s*blast|poisonous\s*gas|visha\s*vaayu)", "Structural collapse / toxic gas leak"),
    ]

    # Contamination & disease outbreaks
    CONTAMINATION_EPIDEMIC = [
        (r"(sewage\s*in\s*drinking\s*water|kudineeril\s*saakadai|dengue\s*outbreak|cholera|epidemic)", "Drinking water contamination / outbreak"),
    ]

    # Contextual modifiers that aggravate or de-escalate hazard
    VULNERABLE_PROXIMITY = r"(school|hospital|children|kids|students|elderly|patients|icu|icu\s*ward|maruthuvamanai|aspatal|palli)"
    PASSIVE_MODIFIERS = r"(resolved|repaired|old|yesterday\s*fixed|already\s*done|no\s*power|dead\s*wire|disconnected)"

    @classmethod
    def evaluate_safety(
        cls,
        text: str,
        category: str,
        subcategory: Optional[str],
        extracted_hazards: List[str],
        vulnerable_impact: bool,
    ) -> SafetyAssessment:
        if not text:
            return SafetyAssessment()

        text_lower = text.lower()

        # Check for passive/de-escalated indicators (e.g., "wire has no power")
        is_passive = bool(re.search(cls.PASSIVE_MODIFIERS, text_lower))

        hazard_list = list(extracted_hazards)
        if subcategory in ["fallen_wire", "electrical_hazard"]:
            hazard_list.append("Live electrical / transformer hazard")
        elif subcategory in ["open_manhole"]:
            hazard_list.append("Open manhole / drainage pit")
        elif subcategory in ["structural_damage", "fire_hazard"]:
            hazard_list.append("Structural collapse / toxic gas leak")

        matched_hazards = []

        for pattern, label in cls.ACUTE_ELECTRICAL + cls.OPEN_PITS + cls.STRUCTURAL_CHEMICAL + cls.CONTAMINATION_EPIDEMIC:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched_hazards.append(label)
                if label not in hazard_list:
                    hazard_list.append(label)

        if not hazard_list:
            return SafetyAssessment(is_immediate_hazard=False, risk_level="none")

        # Proximity to vulnerable institution
        has_vulnerable_proximity = vulnerable_impact or bool(re.search(cls.VULNERABLE_PROXIMITY, text_lower))

        # Acute Electrical Hazard (e.g. fallen live wire, sparking near school)
        if any("Live electrical" in h or "electrical_hazard" in h for h in hazard_list):
            if not is_passive:
                justification = "Active electrical hazard posing imminent electrocution danger to pedestrians"
                if has_vulnerable_proximity:
                    justification += " near sensitive facility / children"
                return SafetyAssessment(
                    is_immediate_hazard=True,
                    hazard_types=hazard_list,
                    risk_level="critical",
                    requires_safety_override=True,
                    justification=justification,
                    recommended_emergency_sla_hours=2,
                )

        # Structural collapse / Toxic chemical
        if any("Structural collapse" in h or "toxic gas" in h or "chemical_explosion" in h for h in hazard_list):
            return SafetyAssessment(
                is_immediate_hazard=True,
                hazard_types=hazard_list,
                risk_level="critical",
                requires_safety_override=True,
                justification="Life safety threat from structural failure or hazardous chemical/gas release",
                recommended_emergency_sla_hours=1,
            )

        # Open manhole on roadway
        if any("Open manhole" in h or "open_manhole" in h for h in hazard_list):
            justification = "Uncovered manhole creating severe pedestrian and vehicular accident hazard"
            return SafetyAssessment(
                is_immediate_hazard=True,
                hazard_types=hazard_list,
                risk_level="severe" if not has_vulnerable_proximity else "critical",
                requires_safety_override=True,
                justification=justification,
                recommended_emergency_sla_hours=4 if not has_vulnerable_proximity else 2,
            )

        # Contamination in drinking water
        if any("Drinking water" in h or "contamination" in h for h in hazard_list):
            return SafetyAssessment(
                is_immediate_hazard=True,
                hazard_types=hazard_list,
                risk_level="severe",
                requires_safety_override=True,
                justification="Waterborne health hazard due to contaminated drinking supply",
                recommended_emergency_sla_hours=6,
            )

        # Moderate hazard
        return SafetyAssessment(
            is_immediate_hazard=False,
            hazard_types=hazard_list,
            risk_level="moderate",
            requires_safety_override=False,
            justification="Identified potential civic hazard without active life-safety emergency",
            recommended_emergency_sla_hours=12,
        )
