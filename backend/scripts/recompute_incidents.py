"""
CivicMind AI — Incident Recompute CLI Script (Module 4)
Usage:
  python backend/scripts/recompute_incidents.py --all
  python backend/scripts/recompute_incidents.py --since 72
  python backend/scripts/recompute_incidents.py --category water --since 48
  python backend/scripts/recompute_incidents.py --since 24 --dry-run
"""
import sys
import argparse
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.incident_service import incident_service
from scripts.seed_module4_demo import generate_module4_demo_complaints
from app.services.muril_classifier import muril_classifier_service


def main():
    parser = argparse.ArgumentParser(description="CivicMind AI — Recompute Spatio-Temporal Civic Incidents")
    parser.add_argument("--all", action="store_true", help="Recompute incidents across all historical complaints")
    parser.add_argument("--since", type=int, default=72, help="Time window in hours to look back (default: 72)")
    parser.add_argument("--category", type=str, default=None, help="Filter by specific civic category (e.g. water, roads)")
    parser.add_argument("--dry-run", action="store_true", help="Calculate incident clusters without mutating database")
    args = parser.parse_args()

    hours = 720 if args.all else args.since
    print(f"\n=======================================================")
    print(f"CIVICMIND AI INCIDENT RECOMPUTATION ENGINE (Module 4)")
    print(f"=======================================================")
    print(f"  Time Window : Past {hours} hours")
    print(f"  Category    : {args.category or 'ALL'}")
    print(f"  Dry Run     : {args.dry_run}")
    print(f"-------------------------------------------------------")

    # Ensure store has complaints
    if not incident_service._complaints_store:
        complaints = generate_module4_demo_complaints()
        for c in complaints:
            if not c.get("embedding"):
                c["embedding"] = muril_classifier_service.get_embedding(c["text"])
        incident_service.seed_complaints(complaints)

    result = incident_service.recompute_all_incidents(
        time_window_hours=hours,
        category=args.category,
        dry_run=args.dry_run,
    )

    print(f"\n[OK] Analyzed {result['analyzed_complaints_count']} complaints in {result['runtime_ms']:.2f}ms")
    print(f"[OK] Discovered {result['formed_incidents_count']} Civic Incidents\n")

    for inc in result["incidents"]:
        print(f"  * {inc['title']} ({inc['incident_code']})")
        print(f"     Category : {inc['category'].upper()} | Priority: {inc['priority'].upper()} | Status: {inc['status'].upper()}")
        print(f"     Volume   : {inc['complaint_count']} complaints | Languages: {', '.join(inc['languages'])}")
        print(f"     Trend    : {inc['trend']} ({inc['complaints_per_hour']} complaints/hr) | Emerging: {inc['is_emerging']}")
        print(f"     Centroid : ({inc['center_latitude']}, {inc['center_longitude']})")
        print(f"     Signals  : Confidence {inc['confidence']*100:.1f}% (Sem: {inc['confidence_signals']['semantic_cohesion']*100:.0f}%, Geo: {inc['confidence_signals']['geographic_cohesion']*100:.0f}%)")
        print(f"     Lead Dept: {inc['primary_department']}\n")

    print(f"=======================================================\n")


if __name__ == "__main__":
    main()
