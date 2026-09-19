"""
CivicMind AI — Incident Candidate Formation & Aggregation (Module 4)
Handles:
- Centroid calculation & Convex Hull boundary polygon
- Deterministic title generation (NO LLM)
- Contextual priority aggregation
- Department routing aggregation
- Trend detection (RISING, STABLE, DECLINING)
- Emerging incident early warning flags
- Cohesion metrics & confidence scoring
"""
import uuid
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import numpy as np

from app.services.duplicate_service import duplicate_detection_service

logger = logging.getLogger(__name__)

CATEGORY_TITLES = {
    "water": "Water Supply Disruption",
    "roads": "Road Damage Cluster",
    "drainage": "Drainage & Waterlogging Incident",
    "electricity": "Electrical Hazard & Power Outage",
    "sanitation": "Garbage Accumulation Cluster",
    "streetlighting": "Streetlight Failure Cluster",
    "public_safety": "Public Safety Hazard",
    "health": "Public Health & Sanitation Cluster",
    "revenue": "Civic Property & Revenue Issue",
    "other": "Civic Infrastructure Issue",
}

DEPARTMENT_MAP = {
    "water": "Water Supply Department",
    "roads": "Roads & Highways Department",
    "drainage": "Drainage & Stormwater Department",
    "electricity": "Electricity & Power Board",
    "sanitation": "Sanitation & Solid Waste Management",
    "streetlighting": "Electrical & Streetlighting Department",
    "public_safety": "Public Safety & Disaster Response",
    "health": "Public Health Department",
    "revenue": "Revenue Department",
    "other": "General Grievance Cell",
}


class IncidentDetector:
    """
    Synthesizes member complaints into an auditable Civic Incident.
    """

    @staticmethod
    def _parse_timestamp(ts: Any) -> datetime:
        if isinstance(ts, datetime):
            return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except Exception:
                pass
        return datetime.now(timezone.utc)

    @classmethod
    def calculate_centroid(cls, complaints: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculates geometric center of valid complaint points.
        """
        valid_coords = []
        for c in complaints:
            coords = duplicate_detection_service.validate_coordinates(c.get("latitude"), c.get("longitude"))
            if coords:
                valid_coords.append(coords)

        if not valid_coords:
            return None, None
        if len(valid_coords) == 1:
            return valid_coords[0][0], valid_coords[0][1]

        lats = [pt[0] for pt in valid_coords]
        lngs = [pt[1] for pt in valid_coords]
        return round(float(np.mean(lats)), 6), round(float(np.mean(lngs)), 6)

    @classmethod
    def calculate_geometry(cls, complaints: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Generates GeoJSON polygon representing the incident affected footprint.
        """
        valid_coords = []
        for c in complaints:
            coords = duplicate_detection_service.validate_coordinates(c.get("latitude"), c.get("longitude"))
            if coords:
                valid_coords.append(coords)

        if not valid_coords:
            return None

        # Format coordinates as [lng, lat] for GeoJSON standard
        pts = [[pt[1], pt[0]] for pt in valid_coords]

        if len(pts) == 1:
            # 1 point: Buffer circle represented as 8-point polygon (approx 200m radius)
            lng, lat = pts[0]
            d_lat = 200.0 / 111320.0
            d_lng = 200.0 / (111320.0 * math.cos(math.radians(lat)))
            poly_coords = []
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                poly_coords.append([round(lng + d_lng * math.sin(rad), 6), round(lat + d_lat * math.cos(rad), 6)])
            poly_coords.append(poly_coords[0])
            return {"type": "Polygon", "coordinates": [poly_coords]}

        if len(pts) == 2:
            # 2 points: Expanded bounding box with margin
            min_lng = min(pts[0][0], pts[1][0]) - 0.002
            max_lng = max(pts[0][0], pts[1][0]) + 0.002
            min_lat = min(pts[0][1], pts[1][1]) - 0.002
            max_lat = max(pts[0][1], pts[1][1]) + 0.002
            poly_coords = [
                [round(min_lng, 6), round(min_lat, 6)],
                [round(max_lng, 6), round(min_lat, 6)],
                [round(max_lng, 6), round(max_lat, 6)],
                [round(min_lng, 6), round(max_lat, 6)],
                [round(min_lng, 6), round(min_lat, 6)],
            ]
            return {"type": "Polygon", "coordinates": [poly_coords]}

        # >= 3 points: Convex Hull
        try:
            from scipy.spatial import ConvexHull
            arr = np.array(pts)
            # Check if all points are collinear
            if np.linalg.matrix_rank(arr - arr[0]) < 2:
                # Collinear points fallback
                min_lng, max_lng = np.min(arr[:, 0]) - 0.002, np.max(arr[:, 0]) + 0.002
                min_lat, max_lat = np.min(arr[:, 1]) - 0.002, np.max(arr[:, 1]) + 0.002
                poly_coords = [
                    [round(min_lng, 6), round(min_lat, 6)],
                    [round(max_lng, 6), round(min_lat, 6)],
                    [round(max_lng, 6), round(max_lat, 6)],
                    [round(min_lng, 6), round(max_lat, 6)],
                    [round(min_lng, 6), round(min_lat, 6)],
                ]
                return {"type": "Polygon", "coordinates": [poly_coords]}

            hull = ConvexHull(arr)
            hull_pts = [arr[idx].tolist() for idx in hull.vertices]
            hull_pts.append(hull_pts[0])  # Close the polygon loop
            return {"type": "Polygon", "coordinates": [[[round(p[0], 6), round(p[1], 6)] for p in hull_pts]]}
        except Exception:
            # Fallback bounding box
            lats = [pt[1] for pt in pts]
            lngs = [pt[0] for pt in pts]
            poly_coords = [
                [round(min(lngs) - 0.001, 6), round(min(lats) - 0.001, 6)],
                [round(max(lngs) + 0.001, 6), round(min(lats) - 0.001, 6)],
                [round(max(lngs) + 0.001, 6), round(max(lats) + 0.001, 6)],
                [round(min(lngs) - 0.001, 6), round(max(lats) + 0.001, 6)],
                [round(min(lngs) - 0.001, 6), round(min(lats) - 0.001, 6)],
            ]
            return {"type": "Polygon", "coordinates": [poly_coords]}

    @classmethod
    def generate_title(cls, category: str, complaints: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
        """
        Generates deterministic title and affected locality string.
        """
        base_title = CATEGORY_TITLES.get(category.lower(), f"{category.title()} Issue Cluster")

        # Extract locality mentions from location_text or ward
        locations = []
        for c in complaints:
            loc = c.get("location_text") or c.get("ward")
            if loc and loc.strip():
                # Clean up locality name
                clean_loc = loc.strip().split(",")[0].strip()
                if len(clean_loc) >= 3:
                    locations.append(clean_loc)

        locality_str = None
        if locations:
            most_common = Counter(locations).most_common(1)[0][0]
            locality_str = most_common
            title = f"{base_title} — {most_common}"
        else:
            title = base_title

        return title, locality_str

    @classmethod
    def aggregate_priority(cls, complaints: List[Dict[str, Any]]) -> Tuple[str, Dict[str, int]]:
        """
        Context-aware priority aggregation.
        Considers critical safety flags, volume, and member priorities.
        """
        prio_counts = Counter()
        has_critical = False

        for c in complaints:
            p = str(c.get("priority", "medium")).lower()
            prio_counts[p] += 1
            if p == "critical" or c.get("is_immediate_hazard"):
                has_critical = True

        total = len(complaints)
        if has_critical:
            final_prio = "critical"
        elif total >= 12 or prio_counts["high"] >= 3:
            final_prio = "high"
        elif total >= 4 or prio_counts["medium"] >= 2:
            final_prio = "medium"
        else:
            final_prio = "low"

        return final_prio, dict(prio_counts)

    @classmethod
    def aggregate_departments(cls, category: str, complaints: List[Dict[str, Any]]) -> Tuple[str, List[str], Dict[str, int]]:
        """
        Aggregates primary and secondary departments from member complaints.
        """
        primary_dept = DEPARTMENT_MAP.get(category.lower(), "General Grievance Cell")
        dept_counts = Counter()
        sec_depts = set()

        for c in complaints:
            d_name = c.get("department_name")
            if d_name:
                dept_counts[d_name] += 1
                if d_name != primary_dept:
                    sec_depts.add(d_name)

            # Check secondary departments list if available
            s_depts = c.get("secondary_departments") or []
            for sd in s_depts:
                name = sd.get("name") if isinstance(sd, dict) else sd
                if name and name != primary_dept:
                    sec_depts.add(name)
                    dept_counts[name] += 1

        dept_counts[primary_dept] = max(dept_counts[primary_dept], len(complaints))
        return primary_dept, sorted(list(sec_depts)), dict(dept_counts)

    @classmethod
    def calculate_trend_and_rate(cls, complaints: List[Dict[str, Any]]) -> Tuple[str, float, bool]:
        """
        Calculates complaints/hour, trend (RISING, STABLE, DECLINING), and is_emerging flag.
        """
        if not complaints:
            return "STABLE", 0.0, False

        timestamps = [cls._parse_timestamp(c.get("created_at")) for c in complaints]
        timestamps.sort()

        now = datetime.now(timezone.utc)
        latest_time = timestamps[-1]
        first_time = timestamps[0]

        total_hours = max(1.0, (latest_time - first_time).total_seconds() / 3600.0)
        overall_rate = round(len(complaints) / total_hours, 2)

        # Recent 6 hours vs prior 6 hours
        cutoff_6h = latest_time - timedelta(hours=6)
        cutoff_12h = latest_time - timedelta(hours=12)

        recent_count = sum(1 for ts in timestamps if ts >= cutoff_6h)
        prior_count = sum(1 for ts in timestamps if cutoff_12h <= ts < cutoff_6h)

        if recent_count >= 3 and recent_count > prior_count * 1.3:
            trend = "RISING"
        elif recent_count < prior_count * 0.7 and prior_count > 0:
            trend = "DECLINING"
        else:
            trend = "STABLE"

        # Emerging Incident: Rapid growth + localized concentration
        is_emerging = (recent_count >= 3 and trend == "RISING" and len(complaints) <= 25)

        return trend, overall_rate, is_emerging

    @classmethod
    def calculate_cohesion_signals(cls, complaints: List[Dict[str, Any]], category: str) -> Dict[str, float]:
        """
        Measures semantic cohesion, geographic compactness, temporal cohesion, and category agreement.
        """
        n = len(complaints)
        if n <= 1:
            return {
                "semantic_cohesion": 1.0,
                "geographic_cohesion": 1.0,
                "temporal_cohesion": 1.0,
                "category_consistency": 1.0,
                "composite_confidence": 0.85,
            }

        # 1. Semantic cohesion: mean pairwise cosine similarity
        embeddings = [c.get("embedding") for c in complaints if c.get("embedding")]
        if len(embeddings) >= 2:
            sims = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sims.append(duplicate_detection_service.compute_cosine_similarity(embeddings[i], embeddings[j]))
            sem_cohesion = float(np.mean(sims)) if sims else 0.85
        else:
            sem_cohesion = 0.85

        # 2. Geographic cohesion: based on maximum distance between member points
        valid_coords = [
            duplicate_detection_service.validate_coordinates(c.get("latitude"), c.get("longitude"))
            for c in complaints
        ]
        valid_coords = [pt for pt in valid_coords if pt is not None]

        if len(valid_coords) >= 2:
            max_dist = 0.0
            for i in range(len(valid_coords)):
                for j in range(i + 1, len(valid_coords)):
                    d = duplicate_detection_service.haversine_distance_meters(
                        valid_coords[i][0], valid_coords[i][1], valid_coords[j][0], valid_coords[j][1]
                    )
                    if d > max_dist:
                        max_dist = d
            geo_cohesion = float(max(0.0, min(1.0, math.exp(-max_dist / 1500.0))))
        else:
            geo_cohesion = 0.80

        # 3. Temporal cohesion
        timestamps = [cls._parse_timestamp(c.get("created_at")) for c in complaints]
        time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600.0
        temp_cohesion = float(max(0.0, min(1.0, math.exp(-time_span_hours / 72.0))))

        # 4. Category consistency
        cat_matches = sum(1 for c in complaints if str(c.get("category", "")).lower() == category.lower())
        cat_consistency = cat_matches / float(n)

        # Composite confidence
        composite_conf = (
            0.40 * sem_cohesion
            + 0.30 * geo_cohesion
            + 0.15 * temp_cohesion
            + 0.15 * cat_consistency
        )

        return {
            "semantic_cohesion": round(sem_cohesion, 3),
            "geographic_cohesion": round(geo_cohesion, 3),
            "temporal_cohesion": round(temp_cohesion, 3),
            "category_consistency": round(cat_consistency, 3),
            "composite_confidence": round(composite_conf, 3),
        }

    @classmethod
    def form_incident_from_cluster(
        cls,
        complaints: List[Dict[str, Any]],
        existing_code: Optional[str] = None,
        existing_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates a list of clustered complaints into a full Incident entity.
        """
        # Primary category: most common category among members
        categories = [str(c.get("category", "other")).lower() for c in complaints]
        primary_cat = Counter(categories).most_common(1)[0][0]

        # Subcategory if present
        subcats = [c.get("subcategory") for c in complaints if c.get("subcategory")]
        primary_subcat = Counter(subcats).most_common(1)[0][0] if subcats else None

        # Title and locality
        title, locality = cls.generate_title(primary_cat, complaints)

        # Centroid & Geometry
        center_lat, center_lng = cls.calculate_centroid(complaints)
        geometry = cls.calculate_geometry(complaints)

        # Priority
        priority, priority_dist = cls.aggregate_priority(complaints)

        # Department
        primary_dept, sec_depts, dept_dist = cls.aggregate_departments(primary_cat, complaints)

        # Trend & Rate
        trend, rate, is_emerging = cls.calculate_trend_and_rate(complaints)

        # Cohesion signals
        signals = cls.calculate_cohesion_signals(complaints, primary_cat)

        # Timestamps
        timestamps = [cls._parse_timestamp(c.get("created_at")) for c in complaints]
        first_reported = min(timestamps) if timestamps else datetime.now(timezone.utc)
        last_reported = max(timestamps) if timestamps else datetime.now(timezone.utc)

        # Unique languages
        languages = list(set(str(c.get("language", "en")).lower() for c in complaints if c.get("language")))

        # Description
        description = (
            f"Civic incident spanning {len(complaints)} citizen grievances across "
            f"{len(languages)} languages ({', '.join(languages)}). "
            f"Concentrated in {locality or 'the locality'} with {signals['semantic_cohesion']*100:.0f}% semantic cohesion."
        )

        incident_id = existing_id or str(uuid.uuid4())
        incident_code = existing_code or f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

        return {
            "id": incident_id,
            "incident_code": incident_code,
            "title": title,
            "description": description,
            "category": primary_cat,
            "subcategory": primary_subcat,
            "priority": priority,
            "status": "detected",
            "complaint_count": len(complaints),
            "affected_area": locality or "Metropolitan Area",
            "center_latitude": center_lat,
            "center_longitude": center_lng,
            "geometry": geometry,
            "first_reported_at": first_reported,
            "last_reported_at": last_reported,
            "started_at": first_reported,
            "resolved_at": None,
            "primary_department": primary_dept,
            "secondary_departments": sec_depts,
            "confidence": signals["composite_confidence"],
            "confidence_signals": signals,
            "trend": trend,
            "complaints_per_hour": rate,
            "is_emerging": is_emerging,
            "languages": languages,
            "priority_distribution": priority_dist,
            "department_distribution": dept_dist,
            "detection_method": "SEMANTIC_GEO_TEMPORAL_CLUSTER",
            "algorithm_version": "incident-v1.0",
            "created_at": first_reported,
            "updated_at": datetime.now(timezone.utc),
            "member_complaints": complaints,
        }
