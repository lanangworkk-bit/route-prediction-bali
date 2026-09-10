import logging

import requests

from app.config import get_settings
from app.models.route import Coordinate
from app.utils.geo import haversine_distance

logger = logging.getLogger(__name__)

MODIFIER_TRANSLATIONS = {
    "left": "Belok kiri",
    "slight left": "Belok kiri ringan",
    "sharp left": "Belok kiri tajam",
    "right": "Belok kanan",
    "slight right": "Belok kanan ringan",
    "sharp right": "Belok kanan tajam",
    "straight": "Lurus",
    "uturn": "Putar balik",
    "depart": "Berangkat",
    "arrive": "Anda telah tiba",
}

TYPE_TRANSLATIONS = {
    "depart": "Berangkat",
    "turn": "Belok",
    "continue": "Lanjut",
    "new name": "Lanjut di jalan",
    "roundabout": "Masuk bundaran",
    "rotary": "Masuk bundaran",
    "fork": "Bercabang, ambil jalan",
    "merge": "Gabung jalan",
    "on ramp": "Masuk jalan tol",
    "off ramp": "Keluar jalan tol",
    "end of road": "Ikuti ujung jalan",
    "use lane": "Gunakan lajur",
    "traffic signal": "Ikuti lampu lalu lintas",
}


class OsrmService:
    """Real road routing via OSRM public API (or self-hosted instance).

    Supports multi-stop routing (waypoints) and synthesizes alternative
    routes when the OSRM response only contains a single route.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.osrm_base_url.rstrip("/")

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        waypoints: list[Coordinate] = None,
        alternatives: bool = True,
        max_routes: int = 3,
    ) -> list[dict]:
        """Return list of route dicts with real road geometry.

        Each route: {
            distance_km, time_minutes, coordinates: [Coordinate, ...]
        }
        """
        if waypoints is None:
            waypoints = []

        coordinates = [origin, *waypoints, destination]
        point_str = ";".join(f"{p.lng},{p.lat}" for p in coordinates)
        url = f"{self.base_url}/route/v1/driving/{point_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "true" if alternatives else "false",
        }

        routes = self._fetch(url, params)

        if alternatives and len(routes) < max_routes and not waypoints:
            routes = self._synthesize_alternatives(
                origin, destination, route_to_match=routes, max_routes=max_routes
            )

        return routes[:max_routes]

    def get_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        waypoints: list[Coordinate] = None,
    ) -> dict:
        routes = self.get_routes(
            origin, destination, waypoints=waypoints, alternatives=False, max_routes=1
        )
        if routes:
            return routes[0]
        return self.fallback_direct_route(origin, destination, waypoints)

    def fallback_direct_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        waypoints: list[Coordinate] = None,
    ) -> dict:
        """Straight-line fallback through all stops when OSRM is unavailable."""
        if waypoints is None:
            waypoints = []

        stops = [origin, *waypoints, destination]
        total_distance = 0.0
        points = [origin]

        for a, b in zip(stops[:-1], stops[1:], strict=False):
            leg_distance = haversine_distance(a, b)
            total_distance += leg_distance

            if len(points) == 1:
                midpoint = Coordinate(
                    lat=(a.lat + b.lat) / 2,
                    lng=(a.lng + b.lng) / 2,
                )
                points.append(midpoint)
            points.append(b)

        avg_speed_kmh = 40
        time_minutes = (total_distance / avg_speed_kmh) * 60

        legs = [
            {
                "start_lat": a.lat,
                "start_lng": a.lng,
                "distance_km": round(haversine_distance(a, b), 2),
                "time_minutes": round((haversine_distance(a, b) / avg_speed_kmh) * 60, 2),
                "steps": 1,
            }
            for a, b in zip(stops[:-1], stops[1:], strict=False)
        ]

        instructions = [
            {
                "type": "depart",
                "modifier": "depart",
                "road_name": "",
                "instruction": "Berangkat dari titik awal",
                "distance_km": 0,
                "time_minutes": 0,
            },
            *[
                {
                    "type": "continue",
                    "modifier": "straight",
                    "road_name": "",
                    "instruction": "Ikuti jalan lurus menuju titik berikutnya",
                    "distance_km": round(haversine_distance(a, b), 2),
                    "time_minutes": round(
                        (haversine_distance(a, b) / avg_speed_kmh) * 60, 2
                    ),
                }
                for a, b in zip(stops[:-1], stops[1:], strict=False)
            ],
            {
                "type": "arrive",
                "modifier": "arrive",
                "road_name": "",
                "instruction": "Anda telah tiba di tujuan",
                "distance_km": 0,
                "time_minutes": 0,
            },
        ]

        return {
            "distance_km": round(total_distance, 2),
            "time_minutes": round(time_minutes, 2),
            "coordinates": points,
            "instructions": instructions,
            "legs": legs,
        }

    def _fetch(self, url: str, params: dict) -> list[dict]:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok" or not data.get("routes"):
                logger.warning(f"OSRM returned no valid routes: {data.get('code')}")
                return []

            return [self._parse_route(route) for route in data["routes"]]
        except Exception as e:
            logger.warning(f"OSRM request failed: {e}")
            return []

    def _parse_route(self, route: dict) -> dict:
        coords = [
            Coordinate(lat=lng_lat[1], lng=lng_lat[0])
            for lng_lat in route["geometry"]["coordinates"]
        ]
        instructions = []
        legs = []
        for leg in route.get("legs", []):
            leg_steps = leg.get("steps", [])
            start_loc = leg_steps[0]["maneuver"]["location"] if leg_steps else None
            legs.append({
                "start_lat": start_loc[1] if start_loc else 0,
                "start_lng": start_loc[0] if start_loc else 0,
                "distance_km": round(leg.get("distance", 0) / 1000, 2),
                "time_minutes": round(leg.get("duration", 0) / 60, 2),
                "steps": len(leg_steps),
            })
            for step in leg_steps:
                maneuver = step.get("maneuver", {})
                instructions.append({
                    "type": maneuver.get("type", ""),
                    "modifier": maneuver.get("modifier", ""),
                    "road_name": step.get("name", "") or "",
                    "instruction": self._build_instruction(
                        maneuver.get("type", ""),
                        maneuver.get("modifier", ""),
                        step.get("name", "") or "",
                    ),
                    "distance_km": round(step.get("distance", 0) / 1000, 3),
                    "time_minutes": round(step.get("duration", 0) / 60, 2),
                })

        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "time_minutes": round(route["duration"] / 60, 2),
            "coordinates": coords,
            "instructions": instructions,
            "legs": legs,
        }

    @staticmethod
    def _build_instruction(type_: str, modifier: str, road_name: str) -> str:
        if type_ == "depart":
            text = "Berangkat dari titik awal"
        elif type_ == "arrive":
            text = "Anda telah tiba di tujuan"
        elif modifier in MODIFIER_TRANSLATIONS:
            text = MODIFIER_TRANSLATIONS[modifier]
        elif type_ in TYPE_TRANSLATIONS:
            text = TYPE_TRANSLATIONS[type_]
        else:
            text = "Lanjut perjalanan"

        if road_name:
            text += f" menuju/hingga {road_name}"
        return text

    def _synthesize_alternatives(
        self,
        origin: Coordinate,
        destination: Coordinate,
        route_to_match: list[dict],
        max_routes: int,
    ) -> list[dict]:
        """Build distinct route candidates by routing through detour via-points.

        The public OSRM instance often returns only a single route. To keep
        the multi-route scoring meaningful, we reroute origin->via->destination
        through a handful of offset points and keep distinct candidates.
        """
        results = list(route_to_match)
        via_points = self._generate_via_points(origin, destination)

        for via in via_points:
            if len(results) >= max_routes:
                break

            point_str = ";".join(
                f"{p.lng},{p.lat}" for p in (origin, via, destination)
            )
            url = f"{self.base_url}/route/v1/driving/{point_str}"
            params = {
                "overview": "full",
                "geometries": "geojson",
                "steps": "true",
                "alternatives": "false",
            }

            for route in self._fetch(url, params):
                if self._is_duplicate(route, results):
                    continue
                results.append(route)
                if len(results) >= max_routes:
                    break

        return results

    def _generate_via_points(
        self, origin: Coordinate, destination: Coordinate
    ) -> list[Coordinate]:
        """Candidate detour points perpendicular to the straight line."""
        bearing = self._bearing(origin, destination)
        perpendicular = (bearing + 90) % 360

        spacing = max(3.0, haversine_distance(origin, destination) * 0.1)

        candidates = []
        for fraction in (0.4, 0.6, 0.85, 0.3):
            mid = self._point_along(origin, destination, fraction)
            for side in (1, -1):
                offset = self._offset(mid, perpendicular, side * spacing)
                if -90 <= offset.lat <= 90 and -180 <= offset.lng <= 180:
                    candidates.append(offset)
                    break

        return candidates

    def _is_duplicate(self, route: dict, existing: list[dict]) -> bool:
        return any(abs(r["distance_km"] - route["distance_km"]) < 1.0 for r in existing)

    def _bearing(self, a: Coordinate, b: Coordinate) -> float:
        import math

        lat1 = math.radians(a.lat)
        lat2 = math.radians(b.lat)
        d_lng = math.radians(b.lng - a.lng)

        x = math.sin(d_lng) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lng)
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    def _point_along(
        self, a: Coordinate, b: Coordinate, fraction: float
    ) -> Coordinate:
        return Coordinate(
            lat=a.lat + fraction * (b.lat - a.lat),
            lng=a.lng + fraction * (b.lng - a.lng),
        )

    def _offset(self, point: Coordinate, bearing: float, distance_km: float) -> Coordinate:
        import math

        angular_distance = distance_km / 6371.0
        bearing_rad = math.radians(bearing)
        lat_rad = math.radians(point.lat)
        lng_rad = math.radians(point.lng)

        new_lat = math.asin(
            math.sin(lat_rad) * math.cos(angular_distance)
            + math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        new_lng = lng_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
            math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat),
        )

        return Coordinate(
            lat=math.degrees(new_lat),
            lng=math.degrees(new_lng),
        )


osrm_service = OsrmService()
