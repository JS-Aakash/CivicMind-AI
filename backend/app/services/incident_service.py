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


import json
import os
import numpy as np

class IncidentService:
    """
    Manages civic incidents, cluster formation, lifecycle transitions, and merges/splits
    with persistent disk serialization.
    """

    def __init__(self):
        # In-memory store for incidents and membership (with JSON persistence capability)
        self._incidents_store: Dict[str, Dict[str, Any]] = {}
        self._incident_memberships: Dict[str, List[str]] = {}  # incident_id -> list of complaint_ids
        self._complaint_to_incident: Dict[str, str] = {}      # complaint_id -> incident_id
        self._complaints_store: Dict[str, Dict[str, Any]] = {}
        self._persistence_file = os.path.join(os.path.dirname(__file__), "..", "data", "persisted_store.json")
        self.load_from_disk()

    def save_to_disk(self) -> None:
        """Saves current complaints, incidents, and mappings to disk for full persistence across restarts."""
        try:
            os.makedirs(os.path.dirname(self._persistence_file), exist_ok=True)
            data = {
                "complaints": self._complaints_store,
                "incidents": self._incidents_store,
                "incident_memberships": self._incident_memberships,
                "complaint_to_incident": self._complaint_to_incident,
            }
            # Custom JSON serializer for datetimes
            def _default_serializer(obj):
                if isinstance(obj, (datetime,)):
                    return obj.isoformat()
                return str(obj)

            with open(self._persistence_file, "w", encoding="utf-8") as f:
                json.dump(data, f, default=_default_serializer, indent=2)
            logger.debug("Successfully saved store to disk")
        except Exception as e:
            logger.warning(f"Failed to persist store to disk: {e}")

    def load_from_disk(self) -> bool:
        """Loads complaints and incidents from disk if persistence file exists."""
        if not os.path.exists(self._persistence_file):
            return False
        try:
            with open(self._persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._complaints_store = data.get("complaints", {})
            self._incidents_store = data.get("incidents", {})
            self._incident_memberships = data.get("incident_memberships", {})
            self._complaint_to_incident = data.get("complaint_to_incident", {})
            logger.info(f"Loaded {len(self._complaints_store)} complaints and {len(self._incidents_store)} incidents from persistent storage.")
            return True
        except Exception as e:
            logger.warning(f"Failed to load store from disk: {e}")
            return False

    def seed_complaints(self, complaints: List[Dict[str, Any]]) -> None:
        """Loads complaints into the working memory pool for clustering."""
        for c in complaints:
            c_id = str(c.get("id"))
            self._complaints_store[c_id] = c
        self.save_to_disk()

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

            self.save_to_disk()

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
            self.save_to_disk()
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
                    self.save_to_disk()
                    return new_inc

        self.save_to_disk()
        return None

    # Backward compatibility alias
    add_complaint_incremental = process_new_complaint_incremental

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
        merged = IncidentDetector.form_incident_from_cluster(
            all_members,
            existing_code=tgt.get("incident_code"),
            existing_id=tgt_id,
        )
        merged["merged_from_ids"] = list(set((tgt.get("merged_from_ids") or []) + [src_id]))
        merged["status"] = tgt.get("status", "investigating")

        self._incidents_store[tgt_id] = merged
        self._incident_memberships[tgt_id] = combined_member_ids

        # Delete source incident
        if src_id in self._incidents_store:
            del self._incidents_store[src_id]
        if src_id in self._incident_memberships:
            del self._incident_memberships[src_id]

        for cid in combined_member_ids:
            self._complaint_to_incident[cid] = tgt_id

        self.save_to_disk()
        logger.info(f"Merged incident {src_id} into {tgt_id} ({reason})")
        return merged

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

        self.save_to_disk()
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
        self.save_to_disk()
        logger.info(f"Updated incident {i_id} status to {new_status}")
        return inc

    def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
        actor: str = "Municipal Officer",
        notes: Optional[str] = None,
        assigned_officer: Optional[str] = None,
        department_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transitions single complaint across real 9-stage lifecycle:
        SUBMITTED -> AI_ANALYSIS -> TRIAGED -> ROUTED -> ASSIGNED -> IN_PROGRESS -> FIELD_VERIFICATION -> RESOLVED -> CLOSED (or REOPENED)
        """
        target = None
        for c in self._complaints_store.values():
            if str(c.get("id")) == complaint_id or str(c.get("complaint_code")) == complaint_id:
                target = c
                break

        if not target:
            raise ValueError(f"Complaint {complaint_id} not found.")

        old_status = target.get("status", "submitted")
        target["status"] = new_status.lower()
        target["updated_at"] = datetime.now(timezone.utc).isoformat()
        if assigned_officer:
            target["assigned_officer"] = assigned_officer
        if department_name:
            target["department_name"] = department_name

        # Append to audit trail
        try:
            from app.api.routes.command_center import record_audit_event
            record_audit_event(
                event_type="COMPLAINT_STATUS_CHANGED",
                target_type="complaint",
                target_id=target.get("complaint_code", complaint_id),
                actor=actor,
                summary=f"Status changed from {old_status.upper()} to {new_status.upper()}" + (f": {notes}" if notes else ""),
                details={
                    "previous_status": old_status,
                    "new_status": new_status.lower(),
                    "assigned_officer": assigned_officer,
                    "notes": notes,
                },
            )
        except Exception as aud_err:
            logger.warning(f"Status change audit error: {aud_err}")

        self.save_to_disk()
        return target

    def resolve_complaint(
        self,
        complaint_id: str,
        resolution_note: str,
        resolver_id: str = "officer-01",
        resolver_name: str = "Ward Inspection Officer",
        resolution_photo: Optional[str] = None,
        resolver_lat: Optional[float] = None,
        resolver_lng: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Resolves individual complaint with mandatory resolution note, evidence, and optional geofence verification.
        """
        import math
        from app.core.config import Settings
        cfg = Settings()

        target = None
        for c in self._complaints_store.values():
            if str(c.get("id")) == complaint_id or str(c.get("complaint_code")) == complaint_id:
                target = c
                break

        if not target:
            raise ValueError(f"Complaint {complaint_id} not found.")

        target_lat = target.get("latitude")
        target_lng = target.get("longitude")
        dist_meters = None
        geofence_verified = False

        if target_lat is not None and target_lng is not None and resolver_lat is not None and resolver_lng is not None:
            # Haversine distance
            R = 6371000.0
            p1 = math.radians(target_lat)
            p2 = math.radians(resolver_lat)
            dp = math.radians(resolver_lat - target_lat)
            dl = math.radians(resolver_lng - target_lng)
            a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
            c_val = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            dist_meters = round(R * c_val, 1)
            geofence_verified = dist_meters <= cfg.RESOLUTION_GEOFENCE_RADIUS_METERS

        if cfg.RESOLUTION_GEOFENCE_ENABLED:
            if resolver_lat is None or resolver_lng is None:
                raise ValueError("GPS device location is required for field verification before resolving.")
            if not geofence_verified:
                raise ValueError(
                    f"You must be near the incident location to verify resolution. Measured distance: {dist_meters}m (Allowed: {cfg.RESOLUTION_GEOFENCE_RADIUS_METERS}m)."
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        res_payload = {
            "resolved_at": now_iso,
            "resolver_id": resolver_id,
            "resolver_name": resolver_name,
            "resolution_note": resolution_note,
            "resolution_photo": resolution_photo,
            "geofence_verified": geofence_verified,
            "resolver_coordinates": {"latitude": resolver_lat, "longitude": resolver_lng} if resolver_lat else None,
            "target_coordinates": {"latitude": target_lat, "longitude": target_lng} if target_lat else None,
            "distance_meters": dist_meters,
        }

        old_status = target.get("status", "in_progress")
        target["status"] = "resolved"
        target["resolved_at"] = now_iso
        target["resolution_info"] = res_payload
        target["updated_at"] = now_iso

        # Log audit
        try:
            from app.api.routes.command_center import record_audit_event
            record_audit_event(
                event_type="COMPLAINT_RESOLVED",
                target_type="complaint",
                target_id=target.get("complaint_code", complaint_id),
                actor=resolver_name,
                summary=f"Complaint resolved by {resolver_name}: {resolution_note[:100]}",
                details={
                    "previous_status": old_status,
                    "new_status": "resolved",
                    "resolution_note": resolution_note,
                    "resolution_photo": resolution_photo,
                    "geofence_verified": geofence_verified,
                    "distance_meters": dist_meters,
                    "resolver_coordinates": {"latitude": resolver_lat, "longitude": resolver_lng} if resolver_lat else None,
                },
            )
        except Exception as aud_err:
            logger.warning(f"Resolution audit error: {aud_err}")

        self.save_to_disk()
        return target

    def resolve_incident(
        self,
        incident_id: str,
        resolution_note: str,
        resolver_id: str = "officer-01",
        resolver_name: str = "Municipal Incident Commander",
        resolution_photo: Optional[str] = None,
        resolver_lat: Optional[float] = None,
        resolver_lng: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Resolves an incident with proof/geofencing and AUTOMATICALLY propagates resolution to ALL linked member complaints.
        """
        import math
        from app.core.config import Settings
        cfg = Settings()

        inc = self.get_incident(incident_id)
        if not inc:
            raise ValueError(f"Incident {incident_id} not found.")

        target_lat = inc.get("center_latitude")
        target_lng = inc.get("center_longitude")
        dist_meters = None
        geofence_verified = False

        if target_lat is not None and target_lng is not None and resolver_lat is not None and resolver_lng is not None:
            R = 6371000.0
            p1 = math.radians(target_lat)
            p2 = math.radians(resolver_lat)
            dp = math.radians(resolver_lat - target_lat)
            dl = math.radians(resolver_lng - target_lng)
            a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
            c_val = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            dist_meters = round(R * c_val, 1)
            geofence_verified = dist_meters <= cfg.RESOLUTION_GEOFENCE_RADIUS_METERS

        if cfg.RESOLUTION_GEOFENCE_ENABLED:
            if resolver_lat is None or resolver_lng is None:
                raise ValueError("GPS device location is required for field verification before resolving.")
            if not geofence_verified:
                raise ValueError(
                    f"You must be near the incident location to verify resolution. Measured distance: {dist_meters}m (Allowed: {cfg.RESOLUTION_GEOFENCE_RADIUS_METERS}m)."
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        res_payload = {
            "resolved_at": now_iso,
            "resolver_id": resolver_id,
            "resolver_name": resolver_name,
            "resolution_note": resolution_note,
            "resolution_photo": resolution_photo,
            "geofence_verified": geofence_verified,
            "resolver_coordinates": {"latitude": resolver_lat, "longitude": resolver_lng} if resolver_lat else None,
            "target_coordinates": {"latitude": target_lat, "longitude": target_lng} if target_lat else None,
            "distance_meters": dist_meters,
            "resolved_via_incident": inc.get("incident_code") or str(inc["id"]),
        }

        i_id = str(inc["id"])
        inc["status"] = "resolved"
        inc["resolved_at"] = now_iso
        inc["resolution_info"] = res_payload
        inc["updated_at"] = now_iso
        self._incidents_store[i_id] = inc

        # Propagate to ALL confirmed member complaints
        linked_cids = inc.get("complaint_ids", [])
        resolved_complaints_count = 0
        for cid in linked_cids:
            c = self._complaints_store.get(str(cid))
            if c:
                c["status"] = "resolved"
                c["resolved_at"] = now_iso
                c["resolution_info"] = res_payload
                c["updated_at"] = now_iso
                resolved_complaints_count += 1
                try:
                    from app.api.routes.command_center import record_audit_event
                    record_audit_event(
                        event_type="COMPLAINT_RESOLVED_VIA_INCIDENT",
                        target_type="complaint",
                        target_id=c.get("complaint_code", str(cid)),
                        actor=resolver_name,
                        summary=f"Resolved via parent Incident {inc.get('incident_code') or i_id}: {resolution_note[:80]}",
                        details={
                            "incident_id": i_id,
                            "incident_code": inc.get("incident_code"),
                            "resolution_note": resolution_note,
                            "resolution_photo": resolution_photo,
                        },
                    )
                except Exception as aud_err:
                    logger.warning(f"Linked complaint resolution audit error: {aud_err}")

        # Incident Audit
        try:
            from app.api.routes.command_center import record_audit_event
            record_audit_event(
                event_type="INCIDENT_RESOLVED",
                target_type="incident",
                target_id=inc.get("incident_code") or i_id,
                actor=resolver_name,
                summary=f"Incident resolved by {resolver_name} ({resolved_complaints_count} member complaints auto-resolved)",
                details={
                    "resolution_note": resolution_note,
                    "resolution_photo": resolution_photo,
                    "linked_complaints_count": resolved_complaints_count,
                    "geofence_verified": geofence_verified,
                    "distance_meters": dist_meters,
                    "resolver_coordinates": {"latitude": resolver_lat, "longitude": resolver_lng} if resolver_lat else None,
                },
            )
        except Exception as aud_err:
            logger.warning(f"Incident resolution audit error: {aud_err}")

        self.save_to_disk()
        logger.info(f"Resolved incident {i_id} and propagated resolution to {resolved_complaints_count} complaints.")
        return inc

    def reopen_complaint(
        self,
        complaint_id: str,
        reason: str,
        citizen_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reopens a resolved complaint when citizen feedback indicates issue is unresolved.
        """
        target = None
        for c in self._complaints_store.values():
            if str(c.get("id")) == complaint_id or str(c.get("complaint_code")) == complaint_id:
                target = c
                break

        if not target:
            raise ValueError(f"Complaint {complaint_id} not found.")

        old_status = target.get("status", "resolved")
        target["status"] = "reopened"
        target["updated_at"] = datetime.now(timezone.utc).isoformat()
        target["reopen_reason"] = reason
        target["citizen_feedback"] = citizen_feedback

        try:
            from app.api.routes.command_center import record_audit_event
            record_audit_event(
                event_type="COMPLAINT_REOPENED",
                target_type="complaint",
                target_id=target.get("complaint_code", complaint_id),
                actor="Citizen Feedback Loop",
                summary=f"Citizen marked issue as UNRESOLVED. Reopened for municipal review: {reason[:100]}",
                details={
                    "previous_status": old_status,
                    "new_status": "reopened",
                    "reason": reason,
                    "citizen_feedback": citizen_feedback,
                },
            )
        except Exception as aud_err:
            logger.warning(f"Reopen audit error: {aud_err}")

        self.save_to_disk()
        return target


incident_service = IncidentService()
