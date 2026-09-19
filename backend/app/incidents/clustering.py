"""
CivicMind AI — Geo-Temporal Semantic Incident Clustering (Module 4)
Uses DBSCAN / HDBSCAN with a custom composite distance metric:
D_ij = w_s * (1 - semantic_sim) + w_g * (geo_dist / max_geo) + w_t * (time_diff / max_time) + w_c * (cat_mismatch)
"""
import math
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.cluster import DBSCAN

from app.services.duplicate_service import duplicate_detection_service

logger = logging.getLogger(__name__)


class IncidentClusteringEngine:
    """
    Spatio-temporal & semantic clustering algorithm for civic complaints.
    Prevents artificial cross-city or cross-year clustering.
    """

    def __init__(
        self,
        eps: float = 0.42,
        min_samples: int = 2,
        max_geo_dist_m: float = 2500.0,
        max_time_window_hours: float = 72.0,
        w_semantic: float = 0.45,
        w_geo: float = 0.30,
        w_temporal: float = 0.15,
        w_category: float = 0.10,
    ):
        self.eps = eps
        self.min_samples = min_samples
        self.max_geo_dist_m = max_geo_dist_m
        self.max_time_window_hours = max_time_window_hours
        self.w_semantic = w_semantic
        self.w_geo = w_geo
        self.w_temporal = w_temporal
        self.w_category = w_category

    def _parse_timestamp(self, ts: Any) -> datetime:
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
        return datetime.now(timezone.utc)

    def build_distance_matrix(self, complaints: List[Dict[str, Any]]) -> np.ndarray:
        """
        Builds NxN symmetric composite distance matrix using vectorized NumPy operations.
        """
        n = len(complaints)
        if n == 0:
            return np.zeros((0, 0), dtype=np.float32)

        # 1. Semantic Distance (Vectorized Matrix Multiplication)
        emb_list = []
        for c in complaints:
            e = c.get("embedding")
            if e is not None and len(e) == 768:
                emb_list.append(e)
            else:
                emb_list.append([0.0] * 768)
        
        E = np.array(emb_list, dtype=np.float32)
        # Normalize rows
        norms = np.linalg.norm(E, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        E_normed = E / norms
        
        cosine_sim = np.clip(np.dot(E_normed, E_normed.T), 0.0, 1.0)
        sem_dist = 1.0 - cosine_sim

        # 2. Temporal Distance (Vectorized Array Broadcasting)
        epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)
        timestamps_hrs = np.array([
            (self._parse_timestamp(c.get("created_at")) - epoch).total_seconds() / 3600.0
            for c in complaints
        ], dtype=np.float32)

        delta_hrs = np.abs(timestamps_hrs[:, None] - timestamps_hrs[None, :])
        temp_dist = np.clip(delta_hrs / self.max_time_window_hours, 0.0, 1.0)
        temp_dist[delta_hrs > 168.0] = 2.0  # Force cluster separation

        # 3. Geographic Distance (Vectorized Haversine)
        coords = [
            duplicate_detection_service.validate_coordinates(c.get("latitude"), c.get("longitude"))
            for c in complaints
        ]
        has_coords = np.array([pt is not None for pt in coords], dtype=bool)
        
        # Default geo distance: 0.60 when coords missing
        geo_dist = np.full((n, n), 0.60, dtype=np.float32)

        if np.any(has_coords):
            valid_idx = np.where(has_coords)[0]
            lat_rad = np.array([math.radians(coords[i][0]) for i in valid_idx], dtype=np.float32)
            lng_rad = np.array([math.radians(coords[i][1]) for i in valid_idx], dtype=np.float32)

            dlat = lat_rad[:, None] - lat_rad[None, :]
            dlng = lng_rad[:, None] - lng_rad[None, :]

            a = np.sin(dlat / 2.0) ** 2 + np.cos(lat_rad[:, None]) * np.cos(lat_rad[None, :]) * (np.sin(dlng / 2.0) ** 2)
            a = np.clip(a, 0.0, 1.0)
            c_meters = 6371000.0 * (2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a)))

            sub_geo_dist = np.where(c_meters <= self.max_geo_dist_m, c_meters / self.max_geo_dist_m, 2.5)
            # Insert back into full geo_dist matrix
            geo_dist[np.ix_(valid_idx, valid_idx)] = sub_geo_dist

        # 4. Category Distance (Matrix Matching)
        categories = [str(c.get("category", "")).lower() for c in complaints]
        cat_dist = np.ones((n, n), dtype=np.float32) * 0.90
        
        from app.services.duplicate_service import COMPATIBLE_CATEGORIES
        for i in range(n):
            c_i = categories[i]
            for j in range(i, n):
                c_j = categories[j]
                if c_i == c_j and c_i != "":
                    score = 1.0
                elif c_j in COMPATIBLE_CATEGORIES.get(c_i, set()) or c_i in COMPATIBLE_CATEGORIES.get(c_j, set()):
                    score = 0.60
                else:
                    score = 0.10
                cd = 1.0 - score
                cat_dist[i, j] = cd
                cat_dist[j, i] = cd

        # 5. Composite Distance Matrix
        dist_matrix = (
            self.w_semantic * sem_dist
            + self.w_geo * geo_dist
            + self.w_temporal * temp_dist
            + self.w_category * cat_dist
        )
        np.fill_diagonal(dist_matrix, 0.0)
        return dist_matrix.astype(np.float32)

    def cluster_complaints(self, complaints: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Executes DBSCAN clustering on complaints.
        Returns mapping from cluster_id (-1 for noise, >=0 for incident clusters) to list of complaints.
        """
        if not complaints:
            return {}

        if len(complaints) < self.min_samples:
            # Single or too few complaints
            return {-1: complaints}

        dist_matrix = self.build_distance_matrix(complaints)

        dbscan = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric="precomputed",
        )
        labels = dbscan.fit_predict(dist_matrix)

        clusters: Dict[int, List[Dict[str, Any]]] = {}
        for idx, label in enumerate(labels):
            lbl = int(label)
            if lbl not in clusters:
                clusters[lbl] = []
            clusters[lbl].append(complaints[idx])

        return clusters


clustering_engine = IncidentClusteringEngine()
