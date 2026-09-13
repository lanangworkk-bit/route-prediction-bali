import contextlib
import time
import uuid
from dataclasses import dataclass, field

from app.config import get_settings
from app.services.realtime_feed import incident_feed

INCIDENT_TYPES = {
    "macet": {"label": "Macet", "icon": "🚗", "color": "#c62828"},
    "banjir": {"label": "Banjir", "icon": "🌊", "color": "#1565c0"},
    "tutup_jalan": {"label": "Tutup Jalan", "icon": "⛔", "color": "#333333"},
    "kecelakaan": {"label": "Kecelakaan", "icon": "💥", "color": "#e53935"},
    "konstruksi": {"label": "Konstruksi", "icon": "🚧", "color": "#ef6c00"},
    "upacara_adat": {
        "label": "Upacara Adat",
        "icon": "🛕",
        "color": "#6a1b9a",
        "hint": "Penutupan/pengeretasan jalan karena upacara adat"},
    "lainnya": {"label": "Lainnya", "icon": "📢", "color": "#795548"},
}


@dataclass
class Incident:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    lat: float = 0.0
    lng: float = 0.0
    incident_type: str = "macet"
    description: str = ""
    reporter: str = "anonym"
    created_at: float = field(default_factory=time.time)
    expires_in_seconds: int = 2 * 3600
    start_at: int | None = None
    end_at: int | None = None

    @property
    def expired(self) -> bool:
        if self.end_at and time.time() > self.end_at:
            return True
        return time.time() - self.created_at > self.expires_in_seconds

    def to_dict(self) -> dict:
        now = time.time()
        return {
            "id": self.id,
            "lat": self.lat,
            "lng": self.lng,
            "incident_type": self.incident_type,
            "type_label": INCIDENT_TYPES.get(self.incident_type, {}).get(
                "label", self.incident_type
            ),
            "icon": INCIDENT_TYPES.get(self.incident_type, {}).get("icon", "📢"),
            "color": INCIDENT_TYPES.get(self.incident_type, {}).get("color", "#795548"),
            "description": self.description,
            "reporter": self.reporter,
            "created_at": round(self.created_at),
            "age_minutes": round((now - self.created_at) / 60),
            "scheduled": self.start_at is not None,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "upcoming": (
                bool(self.start_at and 0 <= self.start_at - now <= 6 * 3600)
            ),
        }


class IncidentService:
    """In-memory crowd-sourced hazard reports (configurable TTL)."""

    def __init__(self):
        self._incidents: dict[str, Incident] = {}
        self._ttl_seconds = get_settings().incident_ttl_hours * 3600

    def _prune(self):
        for inc_id in list(self._incidents):
            if self._incidents[inc_id].expired:
                self._broadcast({"type": "incident_resolved", "payload": {"id": inc_id}})
                del self._incidents[inc_id]

    def _broadcast(self, data: dict):
        with contextlib.suppress(Exception):
            incident_feed.publish(data)

    def report(
        self,
        lat: float,
        lng: float,
        incident_type: str = "macet",
        description: str = "",
        reporter: str = "anonym",
        start_at: int | None = None,
        end_at: int | None = None,
    ) -> Incident:
        if incident_type not in INCIDENT_TYPES:
            incident_type = "lainnya"
        inc = Incident(
            lat=round(lat, 6),
            lng=round(lng, 6),
            incident_type=incident_type,
            description=description.strip(),
            reporter=reporter.strip() or "anonym",
            start_at=start_at,
            end_at=end_at,
        )
        inc.expires_in_seconds = self._ttl_seconds
        self._prune()
        self._incidents[inc.id] = inc
        self._broadcast({"type": "incident_new", "payload": inc.to_dict()})
        return inc

    def list_incidents(self, lat=None, lng=None, radius_km: float = 25.0) -> list[dict]:
        self._prune()
        from app.models.route import Coordinate
        from app.utils.geo import haversine_distance

        center = Coordinate(lat=lat, lng=lng) if lat is not None and lng is not None else None
        items = []
        for inc in self._incidents.values():
            data = inc.to_dict()
            if center and radius_km > 0:
                d = haversine_distance(center, Coordinate(lat=inc.lat, lng=inc.lng))
                if d > radius_km:
                    continue
                data["distance_km"] = round(d, 2)
            items.append(data)
        items.sort(key=lambda x: x.get("distance_km", 0))
        return items

    def resolve(self, inc_id: str) -> bool:
        if inc_id in self._incidents:
            del self._incidents[inc_id]
            self._broadcast({
                "type": "incident_resolved",
                "payload": {"id": inc_id},
            })
            return True
        return False

    def route_penalty(self, coordinates: list, radius_km: float = 2.0) -> float:
        """Return 0..1 penalty for active incidents crossing the route."""
        from app.models.route import Coordinate
        from app.utils.geo import haversine_distance

        self._prune()
        if not coordinates or not self._incidents:
            return 0.0

        _ROUTE_HIT_TYPES = (
            "macet",
            "kecelakaan",
            "tutup_jalan",
            "banjir",
            "upacara_adat",
        )
        incidents = [
            i for i in self._incidents.values() if i.incident_type in _ROUTE_HIT_TYPES
        ]
        if not incidents:
            return 0.0

        penalties = []
        for inc in incidents:
            inc_pt = Coordinate(lat=inc.lat, lng=inc.lng)
            closest = min(haversine_distance(inc_pt, pt) for pt in coordinates)
            if closest <= radius_km:
                severity = 0.35 if inc.incident_type in ("kecelakaan", "tutup_jalan") else 0.2
                if inc.incident_type == "upacara_adat" and inc.scheduled:
                    severity = 0.28
                penalties.append(severity * (1 - closest / radius_km + 0.5))
        return min(0.8, sum(penalties))


incident_service = IncidentService()
