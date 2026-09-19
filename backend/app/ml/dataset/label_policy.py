"""
CivicMind AI — Dataset Label Policy (Module 2.5)
Establishes operational rules and distinctions for Severity, Priority, and Intent.
"""
from typing import Dict, List, Any

INTENT_TYPES: List[str] = [
    "grievance",              # Actionable physical civic defect or service failure
    "information_request",   # Inquiry about rules, office numbers, timings, contacts
    "procedure_request",     # How to apply for a connection, certificate, license
    "greeting",              # Salutations and non-civic pleasantries
    "other",                 # General statements or ambiguous text
]

# Severity: Seriousness and inherent hazard of the underlying problem
SEVERITY_POLICY: Dict[str, Dict[str, Any]] = {
    "critical": {
        "description": "Immediate threat to human life, catastrophic failure, or major public emergency.",
        "examples": [
            "Fallen live electrical wire on public road",
            "Transformer explosion or active fire hazard",
            "Deep collapsed road cavity / open flooded manhole on walking path",
            "Contaminated toxic municipal drinking water supply causing illness",
            "Hospital emergency access obstruction or ambulance failure"
        ]
    },
    "high": {
        "description": "Major disruption of essential service for multiple households, extensive damage.",
        "examples": [
            "Complete water supply failure for > 48 hours for street/colony",
            "Uncollected rotting garbage causing severe sanitation hazard > 1 week",
            "Sewage overflow flooding residential street or entryways",
            "Repeated voltage surge burning home appliances across locality",
            "Large deep pothole on fast-moving arterial road"
        ]
    },
    "medium": {
        "description": "Noticeable service defect or inconvenience affecting localized area.",
        "examples": [
            "Low water supply pressure during scheduled distribution",
            "Broken streetlight on residential lane",
            "Damaged footpath curb or missing non-critical road sign",
            "Overflowing public dustbin requiring regular collection",
            "Bus delayed by 30 minutes on scheduled route"
        ]
    },
    "low": {
        "description": "Minor cosmetic, informational, or non-urgent civic inconvenience.",
        "examples": [
            "Faded street name board or milestone",
            "Non-urgent park maintenance or dry grass trimming",
            "Bus was 10-15 minutes late",
            "Procedural inquiry about property tax payment or office hours"
        ]
    }
}

# Priority: Urgency with which the civic administration must dispatch response teams
PRIORITY_POLICY: Dict[str, Dict[str, Any]] = {
    "critical": {
        "sla_hours": 4,
        "criteria": [
            "Active public safety risk to pedestrians, commuters, or children",
            "Direct proximity to schools, hospitals, or dense transit junctions",
            "High severity combined with immediate ongoing danger"
        ]
    },
    "high": {
        "sla_hours": 24,
        "criteria": [
            "Essential utility disruption affecting large population",
            "Duration > 48 hours without resolution",
            "Secondary hazard escalation (e.g. rain water mixing with sewage)"
        ]
    },
    "medium": {
        "sla_hours": 48,
        "criteria": [
            "Standard civic defect without immediate danger",
            "Moderate localized impact (single household or small lane)"
        ]
    },
    "low": {
        "sla_hours": 72,
        "criteria": [
            "Non-actionable inquiry or informational request",
            "Minor aesthetic maintenance with zero safety impact"
        ]
    }
}

def determine_intent(text: str, is_grievance: bool) -> str:
    """Classifies user intent from linguistic patterns and grievance status."""
    import re
    t = text.lower().strip()
    if not is_grievance:
        if any(w in t for w in ["how to", "procedure", "how can i", "apply for", "process"]):
            return "procedure_request"
        if any(w in t for w in ["what is", "number", "helpline", "phone", "contact", "timing", "when will", "where is"]):
            return "information_request"
        if any(w in t for w in ["hello", "hi", "good morning", "vanakkam", "namaste", "hey", "thanks"]):
            return "greeting"
        return "other"
    return "grievance"
