import logging

import requests

from app.config import get_settings
from app.models.route import Coordinate
from app.utils.geo import haversine_distance

logger = logging.getLogger(__name__)


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
            "steps": "false",
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

        return {
            "distance_km": round(total_distance, 2),
            "time_minutes": round(time_minutes, 2),
            "coordinates": points,
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
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "time_minutes": round(route["duration"] / 60, 2),
            "coordinates": coords,
        }

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
                "steps": "false",
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
