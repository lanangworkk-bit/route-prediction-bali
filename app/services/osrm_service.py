import logging

import requests

from app.config import get_settings
from app.models.route import Coordinate
from app.utils.geo import haversine_distance

logger = logging.getLogger(__name__)


class OsrmService:
    """Real road routing via OSRM public API (or self-hosted instance)."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.osrm_base_url.rstrip("/")

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        alternatives: bool = True,
        max_routes: int = 3,
    ) -> list[dict]:
        """Return list of route dicts with real road geometry.

        Each route: {
            distance_km, time_minutes, coordinates: [Coordinate, ...]
        }
        """
        url = (
            f"{self.base_url}/route/v1/driving/"
            f"{origin.lng},{origin.lat};{destination.lng},{destination.lat}"
        )
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
            "alternatives": "true" if alternatives else "false",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok" or not data.get("routes"):
                logger.warning(f"OSRM returned no valid routes: {data.get('code')}")
                return []

            routes = []
            for route in data["routes"][:max_routes]:
                coords = [
                    Coordinate(lat=lng_lat[1], lng=lng_lat[0])
                    for lng_lat in route["geometry"]["coordinates"]
                ]
                routes.append({
                    "distance_km": round(route["distance"] / 1000, 2),
                    "time_minutes": round(route["duration"] / 60, 2),
                    "coordinates": coords,
                })

            return routes

        except Exception as e:
            logger.warning(f"OSRM request failed: {e}")
            return []

    def fallback_direct_route(
        self, origin: Coordinate, destination: Coordinate
    ) -> dict:
        """Straight-line fallback when OSRM is unavailable."""
        distance = haversine_distance(origin, destination)
        avg_speed_kmh = 40
        time_hours = distance / avg_speed_kmh

        coordinates = [
            origin,
            Coordinate(
                lat=(origin.lat + destination.lat) / 2,
                lng=(origin.lng + destination.lng) / 2,
            ),
            destination,
        ]

        return {
            "distance_km": round(distance, 2),
            "time_minutes": round(time_hours * 60, 2),
            "coordinates": coordinates,
        }


osrm_service = OsrmService()
