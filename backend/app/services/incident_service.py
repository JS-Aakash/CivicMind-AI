"""
CivicMind AI — Incident Management Service (Module 4)
Handles:
- Full cluster recomputation & detection
- Incremental complaint-to-incident assignment
- Incident lifecycle management
- Incident merging & splitting with audit logs
- Incident statistics & GeoJSON polygon updates
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.incidents.clustering import clustering_engine
from app.incidents.incident_detector import IncidentDetector
from app.services.duplicate_service import duplicate_detection_service

logger = logging.getLogger(__name__)


class IncidentService:
    """
    Manages civic incidents, cluster formation, lifecycle transitions, and merges/splits.
    """

    def __init__(self):
        # In-memory store for incidents and membership (with DB sync capability)
        self._incidents_store: Dict[str, Dict[str, Any]] = {}
        self._incident_memberships: Dict[str, List[str]] = {}  # incident_id -> list of complaint_ids
        self._complaint_to_incident: Dict[str, str] = {}      # complaint_id -> incident_id
        self._complaints_store: Dict[str, Dict[str, Any]] = {}

    def seed_complaints(self, complaints: List[Dict[str, Any]]) -> None:
        """Loads complaints into the working memory pool for clustering."""
        for c in complaints:
            c_id = str(c.get("id"))
            self._complaints_store[c_id] = c

    def get_all_incidents(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        trend: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns list of incidents with optional filtering."""
        results = list(self._incidents_store.values())

        if status:
            results = [inc for inc in results if str(inc.get("status")).lower() == status.lower()]
        if priority:
            results = [inc for inc in results if str(inc.get("priority")).lower() == priority.lower()]
        if category:
            results = [inc for inc in results if str(inc.get("category")).lower() == category.lower()]
        if trend:
            results = [inc for inc in results if str(inc.get("trend")).upper() == trend.upper()]

        # Sort by complaint_count descending, then priority (critical -> high -> medium -> low)
        prio_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        results.sort(
            key=lambda x: (
                prio_order.get(str(x.get("priority")).lower(), 0),
                x.get("complaint_count", 0),
            ),
            reverse=True,
        )
        return results

    def get_incident(self, incident_id_or_code: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single incident by ID or incident_code."""
        for inc in self._incidents_store.values():
            if str(inc.get("id")) == str(incident_id_or_code) or str(inc.get("incident_code")) == str(incident_id_or_code):
                # Enrich with member complaints
                member_ids = self._incident_memberships.get(str(inc["id"]), [])
                members = [self._complaints_store[cid] for cid in member_ids if cid in self._complaints_store]
                
                # Build timeline events
                timeline = self._build_incident_timeline(inc, members)
                
                res = dict(inc)
                res["member_complaints"] = members
                res["timeline"] = timeline
                return res
        return None

    def _build_incident_timeline(self, inc: Dict[str, Any], members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Builds chronological audit timeline from real event and complaint timestamps."""
        timeline = []
        
        # 1. First report
        if members:
            ts_list = [c.get("created_at") for c in members if c.get("created_at")]
            if ts_list:
                first_ts = min(ts_list)
                timeline.append({
                    "event": "First citizen grievance reported",
                    "timestamp": first_ts,
                    "description": f"Initial report received in {inc.get('category', 'general').title()}.",
                    "color": "#6366f1",
                })
        
        # 2. Incident formation
        timeline.append({
            "event": "Civic Incident Formed",
            "timestamp": inc.get("created_at") or datetime.now(timezone.utc),
            "description": f"DBSCAN spatio-temporal cluster detected {inc.get('complaint_count', 0)} related grievances.",
            "color": "#f97316",
        })

        # 3. Department dispatch
        if inc.get("primary_department"):
            timeline.append({
                "event": f"Dispatched to {inc['primary_department']}",
                "timestamp": inc.get("created_at") or datetime.now(timezone.utc),
                "description": "Smart multi-department routing assigned lead operational jurisdiction.",
                "color": "#06b6d4",
            })

        # 4. Status progress
        status = str(inc.get("status", "detected")).lower()
        if status in ["in_progress", "resolved", "closed"]:
            timeline.append({
                "event": f"Status updated to {status.replace('_', ' ').title()}",
                "timestamp": inc.get("updated_at") or datetime.now(timezone.utc),
                "description": "Field inspection team deployed to affected radius.",
                "color": "#22c55e",
            })

        timeline.sort(key=lambda x: str(x.get("timestamp", "")))
        return timeline

    def recompute_all_incidents(
        self,
        time_window_hours: int = 72,
        category: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes full reclustering on the complaints database.
        """
        start_time = datetime.now(timezone.utc)
        complaints_list = list(self._complaints_store.values())

        # Filter by time window if applicable
        cutoff = start_time - timedelta(hours=time_window_hours)
        filtered = []
        for c in complaints_list:
            c_time = c.get("created_at")
            if isinstance(c_time, str):
                try:
                    c_time = datetime.fromisoformat(c_time.replace("Z", "+00:00"))
                except Exception:
                    c_time = start_time
            if c_time and c_time.tzinfo is None:
                c_time = c_time.replace(tzinfo=timezone.utc)
            if c_time and c_time >= cutoff:
                if category is None or str(c.get("category", "")).lower() == category.lower():
                    filtered.append(c)

        if not filtered:
            return {
                "status": "completed",
                "dry_run": dry_run,
                "time_window_hours": time_window_hours,
                "analyzed_complaints_count": 0,
                "formed_incidents_count": 0,
                "merged_incidents_count": 0,
                "incidents": [],
                "runtime_ms": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Cluster complaints using spatio-temporal DBSCAN
        clusters = clustering_engine.cluster_complaints(filtered)

        formed_incidents = []
        for label, member_complaints in clusters.items():
            if label < 0:
                # Noise points (isolated complaints)
                continue

            # Form full incident entity
            inc = IncidentDetector.form_incident_from_cluster(member_complaints)
            formed_incidents.append(inc)

        if not dry_run:
            # Overwrite active incidents store
            self._incidents_store.clear()
            self._incident_memberships.clear()
            self._complaint_to_incident.clear()

            for inc in formed_incidents:
                i_id = str(inc["id"])
                self._incidents_store[i_id] = inc
                member_ids = [str(c["id"]) for c in inc["member_complaints"]]
                self._incident_memberships[i_id] = member_ids
                for cid in member_ids:
                    self._complaint_to_incident[cid] = i_id

        end_time = datetime.now(timezone.utc)
        runtime_ms = (end_time - start_time).total_seconds() * 1000.0

        return {
            "status": "completed",
            "dry_run": dry_run,
            "time_window_hours": time_window_hours,
            "analyzed_complaints_count": len(filtered),
            "formed_incidents_count": len(formed_incidents),
            "merged_incidents_count": 0,
            "incidents": formed_incidents,
            "runtime_ms": round(runtime_ms, 2),
            "timestamp": end_time.isoformat(),
        }

    def process_new_complaint_incremental(self, complaint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Incrementally assigns a new incoming complaint to an existing incident cluster
        or forms a new incident if threshold is satisfied.
        """
        c_id = str(complaint.get("id", uuid.uuid4()))
        complaint["id"] = c_id
        self._complaints_store[c_id] = complaint

        # Find candidate active incidents in the same or compatible category
        best_incident = None
        best_score = 0.0

        for inc_id, inc in self._incidents_store.items():
            if inc.get("status") in ["resolved", "closed", "false_positive"]:
                continue

            # Calculate membership score against incident centroid & semantic center
            cand_members = [
                self._complaints_store[cid]
                for cid in self._incident_memberships.get(inc_id, [])
                if cid in self._complaints_store
            ]
            if not cand_members:
                continue

            # Check similarity against incident members
            member_scores = [
                duplicate_detection_service.evaluate_pair(complaint, m)["similarity_score"]
                for m in cand_members
            ]
            avg_sim = float(np.mean(member_scores))
            max_sim = float(np.max(member_scores))
            composite_member_score = 0.6 * max_sim + 0.4 * avg_sim

            if composite_member_score > best_score:
                best_score = composite_member_score
                best_incident = inc

        # Membership threshold for attaching to existing incident
        if best_incident and best_score >= 0.70:
            inc_id = str(best_incident["id"])
            if c_id not in self._incident_memberships[inc_id]:
                self._incident_memberships[inc_id].append(c_id)
            self._complaint_to_incident[c_id] = inc_id

            # Recalculate incident stats with the new member
            all_members = [
                self._complaints_store[cid]
                for cid in self._incident_memberships[inc_id]
                if cid in self._complaints_store
            ]
            updated_inc = IncidentDetector.form_incident_from_cluster(
                all_members,
                existing_code=best_incident.get("incident_code"),
                existing_id=inc_id,
            )
            updated_inc["status"] = best_incident.get("status", "detected")
            self._incidents_store[inc_id] = updated_inc
            logger.info(f"Attached complaint {c_id} to existing incident {best_incident.get('incident_code')} (score: {best_score:.2f})")
            return updated_inc

        # Check if this new complaint clusters with other unassigned recent complaints
        unassigned = [
            c for cid, c in self._complaints_store.items()
            if cid not in self._complaint_to_incident
        ]
        if len(unassigned) >= 2:
            clusters = clustering_engine.cluster_complaints(unassigned)
            for label, members in clusters.items():
                if label >= 0 and any(str(m["id"]) == c_id for m in members):
                    new_inc = IncidentDetector.form_incident_from_cluster(members)
                    new_id = str(new_inc["id"])
                    self._incidents_store[new_id] = new_inc
                    member_ids = [str(m["id"]) for m in members]
                    self._incident_memberships[new_id] = member_ids
                    for mid in member_ids:
                        self._complaint_to_incident[mid] = new_id
                    logger.info(f"Formed new incident {new_inc['incident_code']} with {len(members)} complaints")
                    return new_inc

        return None

    def merge_incidents(self, source_incident_id: str, target_incident_id: str, reason: str = "Manual merge") -> Dict[str, Any]:
        """
        Merges source incident into target incident. Preserves audit history in merged_from_ids.
        """
        src = self.get_incident(source_incident_id)
        tgt = self.get_incident(target_incident_id)

        if not src or not tgt:
            raise ValueError("One or both incidents not found for merging.")

        src_id = str(src["id"])
        tgt_id = str(tgt["id"])

        # Combine member complaints
        src_members = self._incident_memberships.get(src_id, [])
        tgt_members = self._incident_memberships.get(tgt_id, [])
        combined_member_ids = list(set(src_members + tgt_members))

        all_members = [self._complaints_store[cid] for cid in combined_member_ids if cid in self._complaints_store]

        # Recompute merged incident
        merged_inc = IncidentDetector.form_incident_from_cluster(
            all_members,
            existing_code=tgt.get("incident_code"),
            existing_id=tgt_id,
        )
        merged_inc["detection_method"] = "MERGED_CLUSTER"
        merged_inc["merged_from_ids"] = list(set(tgt.get("merged_from_ids", []) + [src_id]))
        merged_inc["status"] = tgt.get("status", "investigating")

        # Update stores
        self._incidents_store[tgt_id] = merged_inc
        self._incident_memberships[tgt_id] = combined_member_ids
        for cid in combined_member_ids:
            self._complaint_to_incident[cid] = tgt_id

        # Mark source incident as closed / merged
        if src_id in self._incidents_store:
            del self._incidents_store[src_id]
        if src_id in self._incident_memberships:
            del self._incident_memberships[src_id]

        logger.info(f"Merged incident {src_id} into {tgt_id} ({reason})")
        return merged_inc

    def split_incident(self, incident_id: str, complaint_ids_for_new: List[str], reason: str = "Manual split") -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Splits specified complaints out of an existing incident into a new child incident.
        """
        orig_inc = self.get_incident(incident_id)
        if not orig_inc:
            raise ValueError(f"Incident {incident_id} not found.")

        orig_id = str(orig_inc["id"])
        all_member_ids = self._incident_memberships.get(orig_id, [])

        remaining_ids = [cid for cid in all_member_ids if cid not in complaint_ids_for_new]
        new_member_ids = [cid for cid in complaint_ids_for_new if cid in all_member_ids]

        if not remaining_ids or not new_member_ids:
            raise ValueError("Split would result in an empty incident.")

        remaining_complaints = [self._complaints_store[cid] for cid in remaining_ids if cid in self._complaints_store]
        new_complaints = [self._complaints_store[cid] for cid in new_member_ids if cid in self._complaints_store]

        # Recompute remaining incident
        updated_orig = IncidentDetector.form_incident_from_cluster(
            remaining_complaints,
            existing_code=orig_inc.get("incident_code"),
            existing_id=orig_id,
        )
        self._incidents_store[orig_id] = updated_orig
        self._incident_memberships[orig_id] = remaining_ids

        # Form new split incident
        new_inc = IncidentDetector.form_incident_from_cluster(new_complaints)
        new_inc["split_from_id"] = orig_id
        new_inc["detection_method"] = "MANUAL_SPLIT"
        new_id = str(new_inc["id"])

        self._incidents_store[new_id] = new_inc
        self._incident_memberships[new_id] = new_member_ids
        for cid in new_member_ids:
            self._complaint_to_incident[cid] = new_id

        logger.info(f"Split incident {orig_id} into {new_id} ({reason})")
        return updated_orig, new_inc

    def update_status(self, incident_id: str, new_status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Transitions incident status across lifecycle:
        DETECTED -> INVESTIGATING -> ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED -> CLOSED (or FALSE_POSITIVE)
        """
        inc = self.get_incident(incident_id)
        if not inc:
            raise ValueError(f"Incident {incident_id} not found.")

        i_id = str(inc["id"])
        inc["status"] = new_status.lower()
        inc["updated_at"] = datetime.now(timezone.utc)
        if new_status.lower() in ["resolved", "closed"]:
            inc["resolved_at"] = datetime.now(timezone.utc)

        self._incidents_store[i_id] = inc
        logger.info(f"Updated incident {i_id} status to {new_status}")
        return inc


incident_service = IncidentService()
