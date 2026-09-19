"""
CivicMind AI — Duplicate Detection Service (Module 4)
Multi-factor duplicate and related grievance discovery:
- 768-dim normalized MuRIL embeddings + cosine similarity search
- PostGIS / Haversine spatial proximity calculation
- Temporal proximity decay
- Category compatibility matrix
- Non-destructive complaint relationship recording
- Deterministic explainability (NO LLM)
"""
import math
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any, Tuple
import numpy as np

from app.schemas.schemas import DuplicateDecisionResponse, ComplaintRelationshipItem

logger = logging.getLogger(__name__)

# Configurable relationship weights and thresholds
DEFAULT_WEIGHTS_WITH_GEO = {
    "semantic": 0.55,
    "geographic": 0.20,
    "temporal": 0.15,
    "category": 0.10,
}

DEFAULT_WEIGHTS_NO_GEO = {
    "semantic": 0.65,
    "geographic": 0.00,
    "temporal": 0.20,
    "category": 0.15,
}

DEFAULT_THRESHOLDS = {
    "duplicate_score": 0.82,
    "related_score": 0.65,
    "max_duplicate_distance_meters": 500.0,
    "max_related_distance_meters": 3000.0,
    "temporal_decay_half_life_hours": 36.0,
    "candidate_top_k": 20,
}

COMPATIBLE_CATEGORIES = {
    "roads": {"drainage", "sanitation", "public_safety"},
    "drainage": {"roads", "water", "sanitation"},
    "water": {"drainage", "sanitation"},
    "electricity": {"public_safety", "streetlighting"},
    "streetlighting": {"electricity", "public_safety"},
    "sanitation": {"drainage", "water", "health"},
}


class DuplicateDetectionService:
    """
    Production-grade multi-factor duplicate & related grievance discovery engine.
    """

    def __init__(
        self,
        weights_with_geo: Optional[Dict[str, float]] = None,
        weights_no_geo: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ):
        self.weights_with_geo = weights_with_geo or DEFAULT_WEIGHTS_WITH_GEO.copy()
        self.weights_no_geo = weights_no_geo or DEFAULT_WEIGHTS_NO_GEO.copy()
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()
        self.algorithm_version = "duplicate-v1.0"

    @staticmethod
    def validate_coordinates(lat: Any, lng: Any) -> Optional[Tuple[float, float]]:
        """
        Validates latitude [-90, 90] and longitude [-180, 180].
        Rejects NaN, Infinity, None, or out-of-range values.
        """
        if lat is None or lng is None:
            return None
        try:
            f_lat = float(lat)
            f_lng = float(lng)
            if math.isnan(f_lat) or math.isnan(f_lng) or math.isinf(f_lat) or math.isinf(f_lng):
                return None
            if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lng <= 180.0:
                return (f_lat, f_lng)
            return None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates Great-Circle distance between two points on Earth in meters.
        """
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    @staticmethod
    def compute_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        Cosine similarity between two vectors bounded to [0.0, 1.0].
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = float(np.dot(v1, v2) / (norm1 * norm2))
        return max(0.0, min(1.0, dot))

    def compute_geographic_score(self, dist_meters: Optional[float]) -> Optional[float]:
        """
        Converts distance in meters to a proximity score [0.0, 1.0].
        <= 100m -> 1.0
        <= 500m -> 0.90 to 1.0
        <= 2000m -> 0.40 to 0.90
        > 5000m -> 0.0
        """
        if dist_meters is None:
            return None
        if dist_meters <= 100.0:
            return 1.0
        if dist_meters >= 5000.0:
            return 0.0
        # Smooth exponential decay
        score = math.exp(-dist_meters / 1200.0)
        return float(max(0.0, min(1.0, score)))

    def compute_temporal_score(self, time_diff_hours: Optional[float]) -> float:
        """
        Converts temporal gap in hours to proximity score [0.0, 1.0].
        Same hour -> 1.0
        24 hours -> ~0.63
        72 hours -> ~0.25
        > 168 hours (7 days) -> ~0.04
        """
        if time_diff_hours is None or time_diff_hours < 0:
            return 1.0
        half_life = self.thresholds.get("temporal_decay_half_life_hours", 36.0)
        decay_constant = math.log(2.0) / half_life
        score = math.exp(-decay_constant * time_diff_hours)
        return float(max(0.0, min(1.0, score)))

    def compute_category_score(self, cat1: Optional[str], cat2: Optional[str]) -> float:
        """
        Category compatibility score.
        Exact match -> 1.0
        Cross-issue related -> 0.60
        Unrelated -> 0.10
        """
        if not cat1 or not cat2:
            return 0.50
        c1 = cat1.strip().lower()
        c2 = cat2.strip().lower()
        if c1 == c2:
            return 1.0
        if c2 in COMPATIBLE_CATEGORIES.get(c1, set()) or c1 in COMPATIBLE_CATEGORIES.get(c2, set()):
            return 0.60
        return 0.10

    def evaluate_pair(
        self,
        source: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluates similarity between a source complaint and a candidate complaint.
        """
        # 1. Semantic similarity
        src_emb = source.get("embedding")
        cand_emb = candidate.get("embedding")
        if src_emb and cand_emb:
            semantic_sim = self.compute_cosine_similarity(src_emb, cand_emb)
        else:
            # Fallback string overlap if embedding not computed
            from app.services.muril_classifier import muril_classifier_service
            e1 = muril_classifier_service.get_embedding(source.get("text", ""))
            e2 = muril_classifier_service.get_embedding(candidate.get("text", ""))
            semantic_sim = self.compute_cosine_similarity(e1, e2)

        # 2. Geographic proximity
        src_coords = self.validate_coordinates(source.get("latitude"), source.get("longitude"))
        cand_coords = self.validate_coordinates(candidate.get("latitude"), candidate.get("longitude"))

        geo_score = None
        dist_meters = None
        has_geo = False
        if src_coords and cand_coords:
            dist_meters = self.haversine_distance_meters(
                src_coords[0], src_coords[1], cand_coords[0], cand_coords[1]
            )
            geo_score = self.compute_geographic_score(dist_meters)
            has_geo = True

        # 3. Temporal proximity
        src_time = source.get("created_at") or datetime.now(timezone.utc)
        cand_time = candidate.get("created_at") or datetime.now(timezone.utc)
        if isinstance(src_time, str):
            try:
                src_time = datetime.fromisoformat(src_time.replace("Z", "+00:00"))
            except Exception:
                src_time = datetime.now(timezone.utc)
        if isinstance(cand_time, str):
            try:
                cand_time = datetime.fromisoformat(cand_time.replace("Z", "+00:00"))
            except Exception:
                cand_time = datetime.now(timezone.utc)

        # Ensure tz-aware comparison
        if src_time.tzinfo is None:
            src_time = src_time.replace(tzinfo=timezone.utc)
        if cand_time.tzinfo is None:
            cand_time = cand_time.replace(tzinfo=timezone.utc)

        time_diff_hours = abs((src_time - cand_time).total_seconds()) / 3600.0
        temporal_score = self.compute_temporal_score(time_diff_hours)

        # 4. Category compatibility
        cat_score = self.compute_category_score(source.get("category"), candidate.get("category"))

        # 5. Composite score calculation
        if has_geo:
            weights = self.weights_with_geo
            combined_score = (
                weights["semantic"] * semantic_sim
                + weights["geographic"] * (geo_score or 0.0)
                + weights["temporal"] * temporal_score
                + weights["category"] * cat_score
            )
        else:
            weights = self.weights_no_geo
            combined_score = (
                weights["semantic"] * semantic_sim
                + weights["temporal"] * temporal_score
                + weights["category"] * cat_score
            )

        # 6. Relationship classification
        dup_thresh = self.thresholds["duplicate_score"]
        rel_thresh = self.thresholds["related_score"]

        # Classification rule: DUPLICATE requires exact category match (cat_score == 1.0)
        if has_geo:
            if (
                cat_score >= 1.0
                and combined_score >= dup_thresh
                and semantic_sim >= 0.78
                and dist_meters <= self.thresholds["max_duplicate_distance_meters"]
                and time_diff_hours <= 96.0
            ):
                rel_type = "DUPLICATE"
            elif combined_score >= rel_thresh or (semantic_sim >= 0.75 and dist_meters <= self.thresholds["max_related_distance_meters"]):
                rel_type = "RELATED"
            else:
                rel_type = "NEW"
        else:
            # Without geo confirmation: higher semantic requirement to call duplicate
            if cat_score >= 1.0 and combined_score >= 0.88 and semantic_sim >= 0.85 and time_diff_hours <= 48.0:
                rel_type = "DUPLICATE"
            elif combined_score >= rel_thresh:
                rel_type = "RELATED"
            else:
                rel_type = "NEW"

        explanation = self._build_relationship_explanation(
            rel_type=rel_type,
            combined_score=combined_score,
            semantic_sim=semantic_sim,
            dist_meters=dist_meters,
            time_diff_hours=time_diff_hours,
            cat1=source.get("category"),
            cat2=candidate.get("category"),
        )

        return {
            "relationship": rel_type,
            "similarity_score": round(combined_score, 4),
            "semantic_similarity": round(semantic_sim, 4),
            "geographic_score": round(geo_score, 4) if geo_score is not None else None,
            "temporal_score": round(temporal_score, 4),
            "category_score": round(cat_score, 4),
            "geo_distance_meters": round(dist_meters, 1) if dist_meters is not None else None,
            "time_diff_hours": round(time_diff_hours, 1),
            "explanation": explanation,
            "algorithm_version": self.algorithm_version,
            "matched_complaint_id": candidate.get("id"),
            "matched_complaint_code": candidate.get("complaint_code"),
            "matched_text_preview": candidate.get("text", "")[:120],
        }

    def _build_relationship_explanation(
        self,
        rel_type: str,
        combined_score: float,
        semantic_sim: float,
        dist_meters: Optional[float],
        time_diff_hours: float,
        cat1: Optional[str],
        cat2: Optional[str],
    ) -> str:
        """
        Builds transparent deterministic explanation for duplicate/related decisions.
        """
        reasons = []
        reasons.append(f"{semantic_sim*100:.1f}% semantic similarity")

        if cat1 and cat2:
            if cat1.lower() == cat2.lower():
                reasons.append(f"same category ({cat1.title()})")
            else:
                reasons.append(f"compatible categories ({cat1.title()} ↔ {cat2.title()})")

        if dist_meters is not None:
            if dist_meters < 1000:
                reasons.append(f"{int(dist_meters)}m geographic distance")
            else:
                reasons.append(f"{dist_meters/1000.0:.2f}km geographic distance")
        else:
            reasons.append("no spatial coordinates recorded")

        if time_diff_hours < 1.0:
            reasons.append("submitted within same hour")
        elif time_diff_hours < 24.0:
            reasons.append(f"{time_diff_hours:.1f}h temporal interval")
        else:
            reasons.append(f"{time_diff_hours/24.0:.1f} days apart")

        if rel_type == "DUPLICATE":
            return f"Identified as DUPLICATE ({combined_score*100:.1f}% composite confidence) based on: " + "; ".join(reasons) + "."
        elif rel_type == "RELATED":
            return f"Identified as RELATED ({combined_score*100:.1f}% composite confidence) based on: " + "; ".join(reasons) + "."
        else:
            return f"Distinct complaint record ({combined_score*100:.1f}% similarity below thresholds). Factors: " + "; ".join(reasons) + "."

    def find_best_match(
        self,
        source: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> DuplicateDecisionResponse:
        """
        Finds the closest duplicate or related match across a list of candidates.
        """
        if not candidates:
            return DuplicateDecisionResponse(
                relationship="NEW",
                similarity_score=0.0,
                semantic_similarity=0.0,
                explanation="No historical complaints found within comparison pool.",
                algorithm_version=self.algorithm_version,
            )

        scored_candidates = []
        for cand in candidates:
            if str(cand.get("id")) == str(source.get("id")):
                continue
            res = self.evaluate_pair(source, cand)
            scored_candidates.append(res)

        if not scored_candidates:
            return DuplicateDecisionResponse(
                relationship="NEW",
                similarity_score=0.0,
                semantic_similarity=0.0,
                explanation="No distinct historical candidates available for comparison.",
                algorithm_version=self.algorithm_version,
            )

        # Sort by combined similarity score descending
        scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        best = scored_candidates[0]

        return DuplicateDecisionResponse(
            relationship=best["relationship"],
            similarity_score=best["similarity_score"],
            semantic_similarity=best["semantic_similarity"],
            geographic_score=best["geographic_score"],
            temporal_score=best["temporal_score"],
            category_score=best["category_score"],
            geo_distance_meters=best["geo_distance_meters"],
            time_diff_hours=best["time_diff_hours"],
            matched_complaint_id=str(best["matched_complaint_id"]) if best["matched_complaint_id"] else None,
            matched_complaint_code=best["matched_complaint_code"],
            matched_text_preview=best["matched_text_preview"],
            explanation=best["explanation"],
            algorithm_version=self.algorithm_version,
        )

    def find_all_relationships(
        self,
        source: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns all (duplicates, related) relationships for a given complaint.
        """
        duplicates = []
        related = []
        for cand in candidates:
            if str(cand.get("id")) == str(source.get("id")):
                continue
            res = self.evaluate_pair(source, cand)
            if res["relationship"] == "DUPLICATE":
                duplicates.append(res)
            elif res["relationship"] == "RELATED":
                related.append(res)

        duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
        related.sort(key=lambda x: x["similarity_score"], reverse=True)
        return duplicates, related


duplicate_detection_service = DuplicateDetectionService()
