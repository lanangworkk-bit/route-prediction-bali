import json
import logging
import sqlite3
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)


class FavoritesService:
    """Persist user-saved routes in SQLite."""

    def __init__(self):
        self.settings = get_settings()
        db_url = self.settings.database_url
        self.db_path = (
            db_url.replace("sqlite:///", "", 1)
            if db_url.startswith("sqlite:///")
            else "route_prediction.db"
        )
        self._init_db()

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
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                origin_lat REAL NOT NULL,
                origin_lng REAL NOT NULL,
                dest_lat REAL NOT NULL,
                dest_lng REAL NOT NULL,
                waypoints_json TEXT DEFAULT '[]',
                priority TEXT DEFAULT 'time',
                mode TEXT DEFAULT 'car',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def add(
        self,
        *,
        name: str,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        waypoints: list = None,
        priority: str = "time",
        mode: str = "car",
    ) -> dict:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO favorites (
                    name, origin_lat, origin_lng, dest_lat, dest_lng,
                    waypoints_json, priority, mode, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name.strip()[:60] or "Rute Tanpa Nama",
                    origin_lat,
                    origin_lng,
                    dest_lat,
                    dest_lng,
                    json.dumps([{"lat": w.lat, "lng": w.lng} for w in (waypoints or [])]),
                    priority,
                    mode,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return self.get_by_id(cur.lastrowid)
        finally:
            conn.close()

    def get_by_id(self, fav_id: int) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM favorites WHERE id = ?", (int(fav_id),)
            ).fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def list_all(self) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM favorites ORDER BY id DESC"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def update(
        self,
        fav_id: int,
        *,
        name: str = None,
        priority: str = None,
        mode: str = None,
    ) -> dict | None:
        conn = self._connect()
        try:
            sets, params = [], []
            if name is not None:
                sets.append("name = ?")
                params.append(name.strip()[:60])
            if priority is not None:
                sets.append("priority = ?")
                params.append(priority)
            if mode is not None:
                sets.append("mode = ?")
                params.append(mode)
            if not sets:
                return self.get_by_id(fav_id)
            params.append(int(fav_id))
            conn.execute(f"UPDATE favorites SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()
            return self.get_by_id(fav_id)
        finally:
            conn.close()

    def delete(self, fav_id: int) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute("DELETE FROM favorites WHERE id = ?", (int(fav_id),))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        data = dict(row)
        data["waypoints"] = json.loads(data.pop("waypoints_json") or "[]")
        return data


favorites_service = FavoritesService()
