import logging
import time

import requests

logger = logging.getLogger(__name__)


class PlaceService:
    """Place search (autocomplete) via OpenStreetMap Nominatim, bounded to Bali."""

    BALI_VIEWBOX = "114.4,-8.85,115.8,-8.0"

    def __init__(self):
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        self._cache_ttl_seconds = 24 * 3600

    def search(self, query: str, limit: int = 5) -> list[dict]:
        q = query.strip()
        if not q:
            return []

        cache_key = q.lower()
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < self._cache_ttl_seconds:
            return cached[1]

        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": q,
                "format": "jsonv2",
                "limit": int(limit),
                "bounded": 1,
                "viewbox": self.BALI_VIEWBOX,
                "addressdetails": 0,
            }
            headers = {"User-Agent": "route-prediction-bali/1.0 (FastAPI)"}
            response = requests.get(url, params=params, headers=headers, timeout=8)
            response.raise_for_status()
            data = response.json()

            results = [
                {
                    "name": item.get("name") or item.get("display_name", "")[:60],
                    "display_name": item.get("display_name", ""),
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "type": item.get("type", ""),
                }
                for item in data
                if item.get("lat") and item.get("lon")
            ]

            self._cache[cache_key] = (time.time(), results)
            return results
        except Exception as e:
            logger.warning(f"Nominatim search failed: {e}")
            return []


place_service = PlaceService()
