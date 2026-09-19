"""
CivicMind AI — Priority Normalization & Context Rules
Standardizes temporal duration, population scope, vulnerable groups,
and critical infrastructure indicators into structured numerical/ordinal values.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class NormalizedDuration:
    """Normalized duration context."""
    raw_value: Optional[int] = None
    raw_unit: Optional[str] = None
    normalized_hours: Optional[float] = None
    is_prolonged: bool = False  # >= 72 hours (3 days)
    is_chronic: bool = False    # >= 336 hours (14 days)


@dataclass
class NormalizedPopulation:
    """Normalized affected population context."""
    scope: str = "single_household"  # "single_household", "multiple_households", "whole_street", "neighborhood", "critical_community"
    estimated_count: Optional[int] = None
    is_widespread: bool = False


@dataclass
class ContextualCivicSignals:
    """Consolidated contextual signals for priority evaluation."""
    duration: NormalizedDuration = field(default_factory=NormalizedDuration)
    population: NormalizedPopulation = field(default_factory=NormalizedPopulation)
    is_vulnerable_impact: bool = False
    vulnerable_groups: List[str] = field(default_factory=list)
    is_critical_infrastructure: bool = False
    infrastructure_types: List[str] = field(default_factory=list)
    is_night_time: bool = False
    location_category: str = "general"  # "residential", "commercial", "institutional", "arterial_road", "unknown"
    safety_risk: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_hours": self.duration.normalized_hours,
            "is_prolonged": self.duration.is_prolonged,
            "affected_population": self.population.scope,
            "estimated_population": self.population.estimated_count,
            "safety_risk": self.safety_risk,
            "vulnerable_population": self.is_vulnerable_impact,
            "vulnerable_groups": self.vulnerable_groups,
            "critical_infrastructure": self.is_critical_infrastructure,
            "infrastructure_types": self.infrastructure_types,
            "is_night_time": self.is_night_time,
            "location_category": self.location_category,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict().get(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)



class PriorityRulesEngine:
    """Deterministic extractor and normalizer for priority reasoning."""

    # Duration parsing regex with unit conversions
    DURATION_MAPPINGS = [
        (r"(\d+)\s*(?:minutes?|mins?|nimidam|minute)", 1.0 / 60.0, "minutes"),
        (r"(\d+)\s*(?:hours?|hrs?|mani\s*neram|ghante)", 1.0, "hours"),
        (r"(\d+)\s*(?:days?|naal|naala|dino?|din|roju)", 24.0, "days"),
        (r"(\d+)\s*(?:weeks?|vaaram|saptaah|hafte|hafta)", 168.0, "weeks"),
        (r"(\d+)\s*(?:months?|maasam|mahine|maheena)", 720.0, "months"),
        (r"(?:since\s*yesterday|nethelerndhu|kal\s*se)", 24.0, "days"),
        (r"(?:since\s*morning|kaalailerndhu|subah\s*se)", 8.0, "hours"),
        (r"(?:today|innaiku|aaj)", 6.0, "hours"),
        (r"(?:a\s*week|one\s*week|oru\s*vaaram|ek\s*hafta)", 168.0, "weeks"),
        (r"(?:a\s*month|one\s*month|oru\s*maasam|ek\s*mahina)", 720.0, "months"),
        (r"(?:few\s*days|sila\s*naatkal|kuch\s*din)", 72.0, "days"),
    ]

    # Population scope patterns
    POPULATION_SCOPE_PATTERNS = [
        (r"(\d+)\s*(?:families|veedugal|parivar|houses|homes|veedu)", "multiple_households"),
        (r"(\d+)\s*(?:people|persons|aalu|log|janangal|citizens)", "multiple_households"),
        (r"(?:whole\s*street|entire\s*street|oru\s*theru\s*fulla|saari\s*gali|poora\s*street)", "whole_street"),
        (r"(?:entire\s*colony|whole\s*village|oru\s*ooru\s*fulla|poora\s*area|poora\s*mohalla|whole\s*ward|entire\s*area)", "neighborhood"),
        (r"(?:my\s*house|en\s*veedu|mera\s*ghar|my\s*home|in\s*front\s*of\s*my\s*house)", "single_household"),
    ]

    # Vulnerable group indicators
    VULNERABLE_PATTERNS = [
        (r"(school|palli|vidyalaya|kindergarten|anganwadi|creche|daycare)", "school"),
        (r"(children|kids|students|students\s*crossing|kulandhaigal|bachon|bachhe)", "children"),
        (r"(hospital|gh\s*hospital|maruthuvamanai|aspatal|clinic|icu|health\s*centre|maternity)", "hospital"),
        (r"(elderly|old\s*age\s*home|senior\s*citizens|vayasana|vriddha\s*ashram)", "elderly"),
        (r"(pregnant|thai\s*sei|delivery\s*case|gasping|patient|disabled)", "patients"),
    ]

    # Critical infrastructure patterns
    INFRASTRUCTURE_PATTERNS = [
        (r"(hospital|gh\s*hospital|maruthuvamanai|aspatal|clinic)", "hospital"),
        (r"(school|palli|vidyalaya|college)", "school"),
        (r"(main\s*road|arterial\s*road|highway|nh\s*\d+|bypass|flyover|bridge|junction|signal)", "major_transit_artery"),
        (r"(bus\s*stand|bus\s*terminus|railway\s*station|metro\s*station|transit\s*hub)", "public_transport_hub"),
        (r"(substation|power\s*station|transformer|water\s*treatment|pumping\s*station|water\s*main|pipeline)", "utility_infrastructure"),
    ]

    # Time of day indicators (e.g. night time without light)
    NIGHT_PATTERNS = r"(night|iravu|raat|dark|darkness|evening|iruttula|raat\s*ko)"

    @classmethod
    def extract_context(cls, text: str) -> ContextualCivicSignals:
        if not text:
            return ContextualCivicSignals()

        text_lower = text.lower()

        # 1. Duration Normalization
        duration = NormalizedDuration()
        for pattern, hours_multiplier, unit_name in cls.DURATION_MAPPINGS:
            m = re.search(pattern, text_lower, re.IGNORECASE)
            if m:
                val = 1
                if m.groups() and m.group(1):
                    try:
                        val = int(m.group(1))
                    except ValueError:
                        val = 1
                duration.raw_value = val
                duration.raw_unit = unit_name
                duration.normalized_hours = float(val * hours_multiplier)
                duration.is_prolonged = duration.normalized_hours >= 72.0
                duration.is_chronic = duration.normalized_hours >= 336.0
                break

        # 2. Population Scope Normalization
        population = NormalizedPopulation()
        for item in cls.POPULATION_SCOPE_PATTERNS:
            pattern = item[0]
            scope_name = item[1]
            m = re.search(pattern, text_lower, re.IGNORECASE)
            if m:
                cnt = None
                if m.groups() and m.group(1):
                    try:
                        cnt = int(m.group(1))
                    except ValueError:
                        cnt = None
                population.scope = scope_name
                population.estimated_count = cnt
                population.is_widespread = scope_name in ["whole_street", "neighborhood", "critical_community"] or (cnt is not None and cnt >= 50)
                break

        # 3. Vulnerable Groups
        vulnerable_groups = []
        for pattern, group_name in cls.VULNERABLE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if group_name not in vulnerable_groups:
                    vulnerable_groups.append(group_name)

        # 4. Critical Infrastructure
        infra_types = []
        for pattern, infra_name in cls.INFRASTRUCTURE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if infra_name not in infra_types:
                    infra_types.append(infra_name)

        # 5. Night time context
        is_night = bool(re.search(cls.NIGHT_PATTERNS, text_lower))

        # 6. Location category
        loc_cat = "general"
        if "school_facility" in vulnerable_groups or "healthcare_facility" in vulnerable_groups:
            loc_cat = "institutional"
        elif "major_transit_artery" in infra_types or "public_transport_hub" in infra_types:
            loc_cat = "arterial_road"
        elif population.scope in ["single_household", "multiple_households", "whole_street"]:
            loc_cat = "residential"

        return ContextualCivicSignals(
            duration=duration,
            population=population,
            is_vulnerable_impact=len(vulnerable_groups) > 0,
            vulnerable_groups=vulnerable_groups,
            is_critical_infrastructure=len(infra_types) > 0,
            infrastructure_types=infra_types,
            is_night_time=is_night,
            location_category=loc_cat,
        )


# Module-level convenience functions
def normalize_duration_to_hours(text: str) -> Optional[float]:
    signals = PriorityRulesEngine.extract_context(text)
    return signals.duration.normalized_hours


def normalize_population_scope(text: str) -> Tuple[str, Optional[int]]:
    signals = PriorityRulesEngine.extract_context(text)
    return signals.population.scope, signals.population.estimated_count


def detect_vulnerable_population(text: str) -> Tuple[bool, List[str]]:
    signals = PriorityRulesEngine.extract_context(text)
    return signals.is_vulnerable_impact, signals.vulnerable_groups


def detect_critical_infrastructure(text: str) -> Tuple[bool, List[str]]:
    signals = PriorityRulesEngine.extract_context(text)
    return signals.is_critical_infrastructure, signals.infrastructure_types


def compute_context_priority_score(signals: ContextualCivicSignals, weights: Optional[Dict[str, float]] = None) -> float:
    w = weights or {
        "duration": 0.9,
        "population": 1.0,
        "vulnerable": 1.2,
        "infrastructure": 1.1,
    }
    score = 0.0
    if signals.duration.is_chronic:
        score += 2.0 * w.get("duration", 0.9)
    elif signals.duration.is_prolonged:
        score += 1.2 * w.get("duration", 0.9)
    elif signals.duration.normalized_hours:
        score += 0.5 * w.get("duration", 0.9)

    if signals.population.is_widespread:
        score += 1.5 * w.get("population", 1.0)

    if signals.is_vulnerable_impact:
        score += 1.4 * w.get("vulnerable", 1.2)

    if signals.is_critical_infrastructure:
        score += 1.2 * w.get("infrastructure", 1.1)

    return score

