import logging
import random
import time
from datetime import datetime, timedelta

import requests

from app.config import get_settings
from app.models.traffic import TrafficPrediction

logger = logging.getLogger(__name__)


class TrafficService:
    """Traffic congestion service.

    Uses real TomTom Traffic Flow data when TOMTOM_API_KEY is configured,
    degrades gracefully to a realistic simulation otherwise.
    """

    def __init__(self):
        self.settings = get_settings()
        self._tomtom_cache: dict[str, tuple[float, float]] = {}
        self._cache_ttl_seconds = 300
        self._historical_data = {}
        self._initialize_historical_patterns()

    def get_traffic_congestion(
        self, lat: float, lng: float, timestamp: datetime = None
    ) -> float:
        if self.settings.tomtom_api_key:
            real = self._get_tomtom_congestion(lat, lng)
            if real is not None:
                return round(real, 3)

        if timestamp is None:
            timestamp = datetime.now()

        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        base_congestion = self._get_base_congestion(hour, day_of_week)
        location_factor = self._get_location_factor(lat, lng)
        random_factor = random.uniform(0.9, 1.1)

        congestion = min(1.0, base_congestion * location_factor * random_factor)
        return round(congestion, 3)

    def _get_tomtom_congestion(self, lat: float, lng: float) -> float | None:
        cache_key = f"{lat:.4f},{lng:.4f}"
        now = time.time()
        cached = self._tomtom_cache.get(cache_key)
        if cached and now - cached[0] < self._cache_ttl_seconds:
            return cached[1]

        try:
            url = f"{self.settings.tomtom_base_url}/10/json"
            params = {
                "point": f"{lat},{lng}",
                "key": self.settings.tomtom_api_key,
            }
            response = requests.get(url, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()

            flow = data.get("flowSegmentData", {})
            current_speed = flow.get("currentSpeed")
            free_flow_speed = flow.get("freeFlowSpeed")

            if current_speed is None or free_flow_speed is None or free_flow_speed <= 0:
                return None

            congestion = max(0.0, min(1.0, 1.0 - current_speed / free_flow_speed))
            self._tomtom_cache[cache_key] = (now, congestion)
            return congestion
        except Exception as e:
            logger.debug(f"TomTom traffic request failed: {e}")
            return None

    def _initialize_historical_patterns(self):
        self._peak_hours = {
            0: {"morning": (7, 9), "evening": (17, 19)},
            1: {"morning": (7, 9), "evening": (17, 19)},
            2: {"morning": (7, 9), "evening": (17, 19)},
            3: {"morning": (7, 9), "evening": (17, 19)},
            4: {"morning": (7, 9), "evening": (17, 19)},
            5: {"morning": (8, 10), "evening": (16, 18)},
            6: {"morning": None, "evening": None},
        }

    def predict_traffic(
        self, lat: float, lng: float, future_minutes: int = 30
    ) -> TrafficPrediction:
        current_time = datetime.now()
        future_time = current_time + timedelta(minutes=future_minutes)

        current_congestion = self.get_traffic_congestion(lat, lng, current_time)
        future_congestion = self.get_traffic_congestion(lat, lng, future_time)

        trend = future_congestion - current_congestion

        confidence = 0.7 + random.uniform(0, 0.2)

        factors = {
            "time_of_day": future_time.hour,
            "day_of_week": future_time.strftime("%A"),
            "trend": "increasing" if trend > 0.1 else "decreasing" if trend < -0.1 else "stable",
        }

        return TrafficPrediction(
            road_segment=f"segment_{lat:.4f}_{lng:.4f}",
            predicted_congestion=round(future_congestion, 3),
            confidence=round(confidence, 2),
            time_window=f"{future_minutes} minutes",
            factors=factors,
        )

    def get_route_traffic_score(self, coordinates: list, samples: int = 8) -> float:
        if not coordinates:
            return 0.0

        step = max(1, len(coordinates) // samples)
        discrete = [
            c for i, c in enumerate(coordinates) if i % step == 0
        ]
        discrete = discrete[:samples]
        if len(discrete) < 2:
            discrete = [coordinates[0], coordinates[-1]]

        total_congestion = sum(
            self.get_traffic_congestion(coord.lat, coord.lng) for coord in discrete
        )
        avg_congestion = total_congestion / len(discrete)
        score = 1.0 - avg_congestion

        return round(max(0, min(1, score)), 3)

    def get_segment_traffic(self, coordinates: list, segments: int = 5) -> list[dict]:
        """Return per-segment traffic level for coloring the route on the map."""
        if not coordinates or len(coordinates) < segments:
            return []

        result = []
        step = max(1, (len(coordinates) - 1) // segments)
        for i in range(0, len(coordinates) - 1, step):
            start = coordinates[i]
            end = coordinates[min(i + step, len(coordinates) - 1)]
            congestion = self.get_traffic_congestion(start.lat, start.lng)
            result.append({
                "start": {"lat": start.lat, "lng": start.lng},
                "end": {"lat": end.lat, "lng": end.lng},
                "congestion": congestion,
                "level": self._level_for(congestion),
            })
        return result

    def _level_for(self, congestion: float) -> str:
        if congestion < 0.3:
            return "lancar"
        if congestion < 0.55:
            return "normal"
        if congestion < 0.75:
            return "padat"
        return "macet"

    def _get_base_congestion(self, hour: int, day_of_week: int) -> float:
        if day_of_week >= 5:
            if 10 <= hour <= 16:
                return 0.3
            return 0.15

        peak = self._peak_hours.get(day_of_week, {})
        morning_peak = peak.get("morning")
        evening_peak = peak.get("evening")

        if morning_peak and morning_peak[0] <= hour <= morning_peak[1]:
            return 0.7 + random.uniform(0, 0.2)
        elif evening_peak and evening_peak[0] <= hour <= evening_peak[1]:
            return 0.75 + random.uniform(0, 0.2)
        elif 11 <= hour <= 14:
            return 0.4 + random.uniform(0, 0.1)
        elif 6 <= hour <= 22:
            return 0.25 + random.uniform(0, 0.1)
        else:
            return 0.1 + random.uniform(0, 0.05)

    def _get_location_factor(self, lat: float, lng: float) -> float:
        denpasar_center = (-8.6500, 115.2167)
        distance = ((lat - denpasar_center[0]) ** 2 + (lng - denpasar_center[1]) ** 2) ** 0.5

        if distance < 0.05:
            return 1.3
        elif distance < 0.1:
            return 1.1
        elif distance < 0.2:
            return 1.0
        else:
            return 0.8


traffic_service = TrafficService()
