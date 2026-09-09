import json
import logging
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

from app.config import get_settings

logger = logging.getLogger(__name__)


class HistoryService:
    """Persist every route prediction to SQLite for auditing and ML retraining."""

    def __init__(self):
        self.settings = get_settings()
        self.db_path = self._parse_db_path(self.settings.database_url)
        self._init_db()

    @staticmethod
    def _parse_db_path(database_url: str) -> str:
        if database_url.startswith("sqlite:///"):
            return database_url.replace("sqlite:///", "", 1)
        return "route_prediction.db"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self._init_db(conn)
        return conn

    def _init_db(self, conn: sqlite3.Connection = None):
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            try:
                self._create_schema(conn)
            finally:
                conn.close()
        else:
            self._create_schema(conn)

    def _create_schema(self, conn: sqlite3.Connection):
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trip_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_lat REAL NOT NULL,
                origin_lng REAL NOT NULL,
                dest_lat REAL NOT NULL,
                dest_lng REAL NOT NULL,
                waypoints_json TEXT DEFAULT '[]',
                distance_km REAL,
                estimated_time_minutes REAL,
                overall_score REAL,
                traffic_score REAL,
                weather_impact REAL,
                priority TEXT,
                traffic_level TEXT,
                weather_condition TEXT,
                route_source TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def record_trip(
        self,
        *,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        waypoints: list = None,
        distance_km: float,
        estimated_time_minutes: float,
        overall_score: float,
        traffic_score: float,
        weather_impact: float,
        priority: str,
        traffic_level: str,
        weather_condition: str,
        route_source: str,
    ):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO trip_history (
                    origin_lat, origin_lng, dest_lat, dest_lng, waypoints_json,
                    distance_km, estimated_time_minutes, overall_score,
                    traffic_score, weather_impact, priority, traffic_level,
                    weather_condition, route_source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    origin_lat,
                    origin_lng,
                    dest_lat,
                    dest_lng,
                    json.dumps(
                        [{"lat": w.lat, "lng": w.lng} for w in (waypoints or [])]
                    ),
                    distance_km,
                    estimated_time_minutes,
                    overall_score,
                    traffic_score,
                    weather_impact,
                    priority,
                    traffic_level,
                    weather_condition,
                    route_source,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
        except Exception:
            logger.exception("Failed to record trip history")
        finally:
            conn.close()

    def get_history(self, limit: int = 50, offset: int = 0) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM trip_history
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (int(limit), int(offset)),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_count(self) -> int:
        conn = self._connect()
        try:
            return conn.execute("SELECT COUNT(*) FROM trip_history").fetchone()[0]
        finally:
            conn.close()

    def get_stats(self) -> dict:
        conn = self._connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM trip_history").fetchone()[0]
            if total == 0:
                return {
                    "total_trips": 0,
                    "avg_score": None,
                    "avg_distance_km": None,
                    "avg_time_minutes": None,
                    "priority_counts": {},
                    "traffic_level_counts": {},
                    "last_24h_trips": 0,
                }

            avg = conn.execute(
                """
                SELECT AVG(overall_score), AVG(distance_km), AVG(estimated_time_minutes)
                FROM trip_history
                """
            ).fetchone()

            priority_counts = {
                r["priority"]: r["c"]
                for r in conn.execute(
                    "SELECT priority, COUNT(*) c FROM trip_history GROUP BY priority"
                ).fetchall()
                if r["priority"]
            }
            traffic_counts = {
                r["traffic_level"]: r["c"]
                for r in conn.execute(
                    "SELECT traffic_level, COUNT(*) c FROM trip_history GROUP BY traffic_level"
                ).fetchall()
                if r["traffic_level"]
            }
            last_24h = conn.execute(
                "SELECT COUNT(*) FROM trip_history WHERE created_at >= ?",
                ((datetime.now() - timedelta(hours=24)).isoformat(),),
            ).fetchone()[0]

            return {
                "total_trips": total,
                "avg_score": round(avg[0] or 0, 2),
                "avg_distance_km": round(avg[1] or 0, 2),
                "avg_time_minutes": round(avg[2] or 0, 2),
                "priority_counts": priority_counts,
                "traffic_level_counts": traffic_counts,
                "last_24h_trips": last_24h,
            }
        finally:
            conn.close()

    def to_training_frames(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Build (traffic_df, scorer_df) from recorded trips for model retraining."""
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM trip_history").fetchall()
        finally:
            conn.close()

        if not rows:
            return pd.DataFrame(), pd.DataFrame()

        records = []
        for row in rows:
            try:
                dt = datetime.fromisoformat(row["created_at"])
            except (ValueError, TypeError):
                dt = datetime.now()

            hour = dt.hour
            day = dt.weekday()
            congestion = 1.0 - (row["traffic_score"] or 0.5)

            lat = row["origin_lat"]
            lng = row["origin_lng"]
            centering = ((lat + 8.6500) ** 2 + (lng - 115.2167) ** 2) ** 0.5

            records.append({
                "hour": hour,
                "day_of_week": day,
                "is_weekend": 1 if day >= 5 else 0,
                "is_morning_peak": 1 if 7 <= hour <= 9 else 0,
                "is_evening_peak": 1 if 17 <= hour <= 19 else 0,
                "lat": lat,
                "lng": lng,
                "distance_to_center": centering,
                "temperature": 28.0,
                "humidity": 75.0,
                "wind_speed": 12.0,
                "visibility": 10.0,
                "congestion": min(1.0, max(0.0, congestion)),
            })

        traffic_df = pd.DataFrame(records)

        scorer_rows = []
        for row in rows:
            score = row["overall_score"]
            if score is None:
                continue
            scorer_rows.append({
                "distance_km": row["distance_km"],
                "time_minutes": row["estimated_time_minutes"],
                "traffic_score": row["traffic_score"],
                "weather_impact": row["weather_impact"],
                "road_quality": 0.8,
                "score_class": 3 if score >= 80 else 2 if score >= 60 else 1 if score >= 40 else 0,
            })

        scorer_df = (
            pd.DataFrame(scorer_rows) if scorer_rows else pd.DataFrame()
        )
        return traffic_df, scorer_df


history_service = HistoryService()
