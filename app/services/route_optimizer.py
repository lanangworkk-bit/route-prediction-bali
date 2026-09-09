import logging
import asyncio
from datetime import datetime
from app.models.route import (
    RouteRequest,
    RouteInfo,
    RouteResponse,
    Coordinate,
    RoutePriority,
)
from app.services.map_service import map_service
from app.services.traffic_service import traffic_service
from app.services.weather_service import weather_service
from app.config import get_settings

logger = logging.getLogger(__name__)


class RouteOptimizer:
    def __init__(self):
        self.settings = get_settings()
        self._map_load_attempted = False

    async def find_best_route(self, request: RouteRequest) -> RouteResponse:
        logger.info(f"Finding route from {request.origin} to {request.destination}")

        weather = await weather_service.get_current_weather(
            request.origin.lat, request.origin.lng
        )
        weather_impact = weather_service.calculate_weather_impact(weather)

        try:
            if not map_service.is_loaded and not self._map_load_attempted:
                self._map_load_attempted = True
                await asyncio.wait_for(self._load_map_aasync(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Map loading timed out, using fallback routing")
        except Exception as e:
            logger.warning(f"Map loading failed: {e}, using fallback routing")

        raw_routes = map_service.find_alternative_paths(
            request.origin,
            request.destination,
            num_paths=self.settings.max_alternative_routes + 1,
        )

        scored_routes = []
        for route_data in raw_routes:
            route_info = self._score_route(
                route_data, weather_impact.speed_factor, request.preferences
            )
            scored_routes.append(route_info)

        scored_routes.sort(key=lambda r: r.overall_score, reverse=True)

        best_route = scored_routes[0]
        alternative_routes = scored_routes[1:]

        weather_summary = {
            "temperature": weather.temperature,
            "condition": weather.condition.value,
            "wind_speed": weather.wind_speed,
            "impact": weather_impact.recommendation,
        }

        return RouteResponse(
            best_route=best_route,
            alternative_routes=alternative_routes,
            weather_summary=weather_summary,
            generated_at=datetime.now().isoformat(),
        )

    async def _load_map_aasync(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, map_service.load_graph)

    def _score_route(
        self, route_data: dict, weather_speed_factor: float, preferences
    ) -> RouteInfo:
        distance_km = route_data["distance_km"]
        base_time = route_data["time_minutes"]

        traffic_score = traffic_service.get_route_traffic_score(route_data["coordinates"])
        traffic_factor = 1.0 + (1.0 - traffic_score) * 0.5

        adjusted_time = base_time * traffic_factor / weather_speed_factor

        distance_score = max(0, 1 - (distance_km / 100))
        time_score = max(0, 1 - (adjusted_time / 120))

        weather_impact_score = weather_speed_factor

        if preferences.priority == RoutePriority.TIME:
            weights = {
                "traffic": self.settings.traffic_weight,
                "time": 0.35,
                "distance": 0.15,
                "weather": self.settings.weather_weight,
            }
        elif preferences.priority == RoutePriority.DISTANCE:
            weights = {
                "traffic": 0.15,
                "time": 0.15,
                "distance": 0.55,
                "weather": self.settings.weather_weight,
            }
        else:
            weights = {
                "traffic": 0.50,
                "time": 0.15,
                "distance": 0.15,
                "weather": self.settings.weather_weight,
            }

        overall_score = (
            traffic_score * weights["traffic"]
            + time_score * weights["time"]
            + distance_score * weights["distance"]
            + weather_impact_score * weights["weather"]
        ) * 100

        return RouteInfo(
            distance_km=distance_km,
            estimated_time_minutes=round(adjusted_time, 2),
            traffic_score=traffic_score,
            weather_impact=weather_speed_factor,
            overall_score=round(min(100, max(0, overall_score)), 2),
            coordinates=route_data["coordinates"],
            road_conditions={
                "traffic_level": self._get_traffic_level(traffic_score),
                "weather_condition": self._get_weather_level(weather_speed_factor),
            },
        )

    def _get_traffic_level(self, score: float) -> str:
        if score >= 0.8:
            return "Lancar"
        elif score >= 0.6:
            return "Sedang"
        elif score >= 0.4:
            return "Padat"
        else:
            return "Macet"

    def _get_weather_level(self, factor: float) -> str:
        if factor >= 0.9:
            return "Cerah"
        elif factor >= 0.7:
            return "Berawan"
        elif factor >= 0.5:
            return "Hujan"
        else:
            return "Cuaca Buruk"


route_optimizer = RouteOptimizer()
