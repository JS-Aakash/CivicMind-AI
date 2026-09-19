"""
CivicMind AI — Lightweight Civic Entity & Hazard Extractor
Fast, zero-latency deterministic extraction for durations, affected population,
safety hazards, and sensitive facilities across EN/HI/TA/Tanglish/Hinglish.
No generative LLMs used.
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from app.ml.priority.priority_signal import ExtractedCivicEntities


class LightweightCivicExtractor:
    """
    Regex and lexicon-driven entity extractor specialized for Indic & code-mixed civic texts.
    """

    # Hazard keywords / patterns across scripts and romanized code-mix
    HAZARD_PATTERNS = [
        (r"(live\s*wire|open\s*wire|wire\s*arundhu|kambi\s*arundhu|nanga\s*taar|bijli\s*ka\s*taar|sparking|short\s*circuit|thee\s*pidi|aag\s*lagi)", "electrical_hazard"),
        (r"(open\s*manhole|manhole\s*moodi\s*illa|manhole\s*khula|open\s*drain|gutter\s*open|pot\s*hole\s*deep|periya\s*pallam)", "open_manhole_pit"),
        (r"(transformer\s*burst|cylinder\s*blast|gas\s*leak|toxic\s*fumes|poisonous\s*smell|vishakattu|visha\s*vaayu)", "chemical_explosion_hazard"),
        (r"(building\s*collapse|suvar\s*idiyuthu|wall\s*falling|deewar\s*gir|bridge\s*crack|kattidam\s*collapse)", "structural_collapse"),
        (r"(flood\s*water\s*entered\s*house|veetukulla\s*thanni|gharon\s*mein\s*pani|sewage\s*in\s*drinking\s*water|kudineeril\s*saakadai|peene\s*ke\s*pani\s*mein\s*ganda)", "contamination_flooding"),
        (r"(dengue\s*outbreak|cholera|malaria\s*paravuthoru|illness\s*spreading|marana\s*bayam|patient\s*critical)", "public_health_emergency"),
    ]

    # Sensitive / Vulnerable Facility keywords
    VULNERABLE_PATTERNS = [
        r"(hospital|gh\s*hospital|maruthuvamanai|aspatal|clinic|icu|emergency\s*ward|school|palli|vidyalaya|college|old\s*age\s*home|daycare|anganwadi|creche)",
    ]

    # Duration parsing
    DURATION_PATTERNS = [
        (r"(\d+)\s*(?:days?|naal|naala|din|roju|dino)", 1),
        (r"(\d+)\s*(?:weeks?|vaaram|saptaah|hafte|hafta)", 7),
        (r"(\d+)\s*(?:months?|maasam|mahine|maheena)", 30),
        (r"(?:a\s*week|one\s*week|oru\s*vaaram|ek\s*hafta)", 7),
        (r"(?:a\s*month|one\s*month|oru\s*maasam|ek\s*mahina)", 30),
        (r"(?:since\s*yesterday|nethelerndhu|kal\s*se)", 1),
        (r"(?:today|innaiku|aaj)", 1),
    ]

    # Affected population parsing
    POPULATION_PATTERNS = [
        (r"(\d+)\s*(?:families|veedugal|veedu|ghar|parivar|houses|homes)", 4),  # multiply by 4 per family
        (r"(\d+)\s*(?:people|persons|aalu|aatkallu|log|janangal)", 1),
        (r"(?:whole\s*street|entire\s*street|oru\s*theru\s*fulla|saari\s*gali|poora\s*area)", 150),
        (r"(?:entire\s*colony|whole\s*village|oru\s*ooru\s*fulla|poora\s*gaon|entire\s*ward)", 500),
    ]

    # Street / Location mention patterns
    LOCATION_PATTERNS = [
        r"(?:near|opposite|opp\s*to|behind|pakkathula|aduthu|ke\s*paas|ke\s*peeche)\s+([A-Z0-9a-z\s]+(?:Street|Road|Salai|Nagar|Colony|Cross|Main|Lane|Bazaar|Marg|Gali|Mohalla|Palli))",
        r"([A-Za-z0-9\s]+(?:Street|Road|Salai|Nagar|Colony|Cross|Main\s*Road|Lane|Bazaar|Marg|Gali|Mohalla))\s*(?:il|la|mein|pe|near)",
    ]

    @classmethod
    def extract_entities(cls, text: str) -> ExtractedCivicEntities:
        """Runs fast regex extraction over the grievance text."""
        if not text:
            return ExtractedCivicEntities()

        text_lower = text.lower()

        # 1. Hazard detection
        hazards = []
        is_hazard = False
        for pattern, hazard_name in cls.HAZARD_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                hazards.append(hazard_name)
                is_hazard = True

        # 2. Vulnerable facility
        vulnerable = False
        for pattern in cls.VULNERABLE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                vulnerable = True
                break

        # 3. Duration
        duration_days = None
        for pattern, multiplier in cls.DURATION_PATTERNS:
            m = re.search(pattern, text_lower, re.IGNORECASE)
            if m:
                if m.groups() and m.group(1):
                    try:
                        duration_days = int(m.group(1)) * multiplier
                    except ValueError:
                        duration_days = multiplier
                else:
                    duration_days = multiplier
                break

        # 4. Population affected
        affected_count = None
        for pattern, multiplier in cls.POPULATION_PATTERNS:
            m = re.search(pattern, text_lower, re.IGNORECASE)
            if m:
                if m.groups() and m.group(1):
                    try:
                        affected_count = int(m.group(1)) * multiplier
                    except ValueError:
                        affected_count = multiplier
                else:
                    affected_count = multiplier
                break

        # 5. Location mentions
        locations = []
        for pattern in cls.LOCATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                loc = match.group(1).strip()
                if len(loc) > 3 and loc not in locations:
                    locations.append(loc)

        return ExtractedCivicEntities(
            duration_days=duration_days,
            affected_count=affected_count,
            safety_hazard=is_hazard,
            vulnerable_impact=vulnerable,
            location_mentions=locations[:3],
            hazard_types=hazards,
        )

    @classmethod
    def determine_escalation_rules(
        cls,
        text: str,
        entities: ExtractedCivicEntities,
        predicted_priority: str,
        predicted_severity: str,
        primary_category: str,
    ) -> Tuple[bool, List[str], int]:
        """
        Synthesizes neural priority and deterministic risk signals to decide auto-escalation & SLA.
        Returns: (recommended_escalation, reasons, suggested_sla_hours)
        """
        reasons = []
        is_escalated = False
        sla_hours = 48  # Default standard SLA

        # Safety hazard override
        if entities.safety_hazard:
            is_escalated = True
            reasons.append(f"Immediate safety hazard detected ({', '.join(entities.hazard_types)})")
            sla_hours = min(sla_hours, 4)

        # Vulnerable institution impact
        if entities.vulnerable_impact:
            reasons.append("Impacts sensitive civic institution (hospital/school/elderly care)")
            sla_hours = min(sla_hours, 12)
            if predicted_severity in ["high", "critical"] or predicted_priority in ["high", "critical"]:
                is_escalated = True

        # Prolonged unresolved duration
        if entities.duration_days and entities.duration_days >= 7:
            reasons.append(f"Prolonged unresolved issue ({entities.duration_days} days reported)")
            if entities.duration_days >= 14:
                is_escalated = True
                sla_hours = min(sla_hours, 12)

        # High population impact
        if entities.affected_count and entities.affected_count >= 100:
            reasons.append(f"Large community impact (~{entities.affected_count}+ citizens affected)")
            sla_hours = min(sla_hours, 24)

        # Critical neural priority
        if predicted_priority == "critical":
            is_escalated = True
            reasons.append("Model neural assessment: Critical urgency")
            sla_hours = min(sla_hours, 6)
        elif predicted_priority == "high":
            sla_hours = min(sla_hours, 24)

        return is_escalated, reasons, sla_hours
