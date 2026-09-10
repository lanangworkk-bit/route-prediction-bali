import logging
import time
import uuid
from dataclasses import dataclass, field

from app.models.route import RouteRequest

logger = logging.getLogger(__name__)

MODE_SPEEDS_KMH = {
    "car": 40.0,
    "motorcycle": 50.0,
    "walking": 4.5,
}


@dataclass
class TrackSession:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    origin: tuple = None
    destination: tuple = None
    waypoints: list = field(default_factory=list)
    mode: str = "car"
    priority: str = "time"
    total_distance_km: float = 0.0
    coordinates: list = field(default_factory=list)
    instructions: list = field(default_factory=list)
    speed_kmh: float = 40.0
    started_at: float = field(default_factory=time.time)
    status: str = "active"
    eta_minutes: float = 0.0
    created_route_at: float = field(default_factory=time.time)

    def elapsed_minutes(self) -> float:
        return (time.time() - self.started_at) / 60

    def progress(self) -> float:
        if self.total_distance_km <= 0 or self.speed_kmh <= 0:
            return 0.0
        travel_hours = self.total_distance_km / self.speed_kmh
        return min(1.0, self.elapsed_minutes() / (travel_hours * 60))

    def position(self) -> dict:
        progress = self.progress()
        coords = self.coordinates
        if not coords:
            return {"lat": 0.0, "lng": 0.0}
        if progress >= 1.0:
            return {"lat": coords[-1].lat, "lng": coords[-1].lng}
        target = progress * (len(coords) - 1)
        idx = int(target)
        frac = target - idx
        a = coords[idx]
        b = coords[min(idx + 1, len(coords) - 1)]
        return {
            "lat": round(a.lat + (b.lat - a.lat) * frac, 6),
            "lng": round(a.lng + (b.lng - a.lng) * frac, 6),
        }

    def snapshot(self) -> dict:
        progress = self.progress()
        remaining_km = round(self.total_distance_km * (1 - progress), 2)
        eta_min = (
            round((remaining_km / self.speed_kmh) * 60, 1)
            if self.speed_kmh > 0
            else 0.0
        )
        self.status = "arrived" if progress >= 1.0 else "active"
        return {
            "session_id": self.session_id,
            "status": self.status,
            "origin": {"lat": self.origin[0], "lng": self.origin[1]} if self.origin else None,
            "destination": (
                {"lat": self.destination[0], "lng": self.destination[1]}
                if self.destination
                else None
            ),
            "waypoints": [{"lat": w.lat, "lng": w.lng} for w in self.waypoints],
            "mode": self.mode,
            "priority": self.priority,
            "position": self.position(),
            "total_distance_km": self.total_distance_km,
            "completed_km": round(self.total_distance_km * progress, 2),
            "remaining_km": remaining_km,
            "progress_percent": round(progress * 100, 1),
            "eta_minutes": eta_min,
            "elapsed_minutes": round(self.elapsed_minutes(), 1),
            "speed_kmh": self.speed_kmh,
            "instructions_remaining": self.instructions_remaining(),
        }

    def instructions_remaining(self) -> list[dict]:
        progress = self.progress()
        count = len(self.instructions)
        if count == 0:
            return []
        read_index = int(progress * count)
        return self.instructions[min(read_index, count - 1):]

    def timeline_eta(self) -> float:
        return time.time() + self.eta_minutes * 60


class TrackService:
    """Simulated realtime tracking sessions. Position advances with real clock."""

    def __init__(self):
        self.sessions: dict[str, TrackSession] = {}

    def create(
        self,
        request: RouteRequest,
        best_route,
        coordinates: list,
        instructions: list,
    ) -> TrackSession:
        mode = request.preferences.mode.value
        session = TrackSession(
            origin=(request.origin.lat, request.origin.lng),
            destination=(request.destination.lat, request.destination.lng),
            waypoints=list(request.waypoints),
            mode=mode,
            priority=request.preferences.priority.value,
            total_distance_km=best_route.distance_km,
            coordinates=coordinates,
            instructions=instructions,
            speed_kmh=MODE_SPEEDS_KMH.get(mode, 40.0),
            eta_minutes=best_route.estimated_time_minutes,
        )
        self.sessions[session.session_id] = session
        # keep map bounded
        if len(self.sessions) > 100:
            oldest = min(self.sessions, key=lambda k: self.sessions[k].created_route_at)
            self.sessions.pop(oldest, None)
        return session

    def get(self, session_id: str) -> TrackSession | None:
        session = self.sessions.get(session_id)
        if session:
            session.eta_minutes = session.snapshot()["eta_minutes"]
        return session

    def share_url(self, session_id: str) -> str:
        return f"/?track={session_id}"


track_service = TrackService()
