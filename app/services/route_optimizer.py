import logging
from datetime import datetime

from app.config import get_settings
from app.ml.registry import registry
from app.ml.travel_time_model import travel_time_model
from app.models.route import (
    Coordinate,
    Instruction,
    LegSummary,
    RouteInfo,
    RouteMode,
    RoutePriority,
    RouteRequest,
    RouteResponse,
)
from app.services.history_service import history_service
from app.services.incident_service import incident_service
from app.services.map_service import map_service
from app.services.osrm_service import osrm_service
from app.services.traffic_service import traffic_service
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)

MODE_LABELS = {
    RouteMode.CAR: "Mobil",
    RouteMode.MOTORCYCLE: "Motor",
    RouteMode.WALKING: "Jalan Kaki",
}

# Durasi OSRM dihitung untuk mobilitas mobil. Faktor koreksi per moda:
# motor sedikit lebih cepat/lincah; berjalan kaki memakai kecepatan sendiri.
MODE_TIME_FACTOR = {
    RouteMode.CAR: 1.0,
    RouteMode.MOTORCYCLE: 0.85,
    RouteMode.WALKING: None,  # dihitung dari kecepatan kaki
}
WALKING_SPEED_KMH = 4.5


class RouteOptimizer:
    def __init__(self):
        self.settings = get_settings()

    async def find_best_route(
        self, request: RouteRequest, *, record_history: bool = True
    ) -> RouteResponse:
        logger.info(
            f"Finding route from {request.origin} to {request.destination}"
            + (f" via {len(request.waypoints)} waypoints" if request.waypoints else "")
            + f" mode={request.preferences.mode.value}"
        )

        weather = await weather_service.get_current_weather(
            request.origin.lat, request.origin.lng
        )
        weather_impact = weather_service.calculate_weather_impact(weather)

        raw_routes, route_source = self._get_route_candidates(request)

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

        if record_history:
            history_service.record_trip(
                origin_lat=request.origin.lat,
                origin_lng=request.origin.lng,
                dest_lat=request.destination.lat,
                dest_lng=request.destination.lng,
                waypoints=request.waypoints,
                distance_km=best_route.distance_km,
                estimated_time_minutes=best_route.estimated_time_minutes,
                overall_score=best_route.overall_score,
                traffic_score=best_route.traffic_score,
                weather_impact=best_route.weather_impact,
                priority=request.preferences.priority.value,
                traffic_level=best_route.road_conditions.get("traffic_level", ""),
                weather_condition=weather.condition.value,
                route_source=route_source,
            )
            registry.maybe_auto_retrain(history_service.get_count())

        return RouteResponse(
            best_route=best_route,
            alternative_routes=alternative_routes,
            waypoints=request.waypoints,
            weather_summary=weather_summary,
            generated_at=datetime.now().isoformat(),
        )

    def _get_route_candidates(self, request: RouteRequest) -> tuple[list[dict], str]:
        """Try real road routing (OSRM), then local map, then straight-line.

        Returns (routes, source_label). Each route has distance_km,
        time_minutes, coordinates.
        """
        # 1. OSRM real road routes (public API / self-hosted)
        osrm_routes = osrm_service.get_routes(
            request.origin,
            request.destination,
            waypoints=request.waypoints,
            alternatives=True,
            max_routes=self.settings.max_alternative_routes + 1,
        )
        if osrm_routes:
            logger.info(f"Using OSRM routing: {len(osrm_routes)} candidate routes")
            return osrm_routes, "osrm"

        # 2. Local OSMnx graph (if loaded, e.g. via POST /api/v1/map/load)
        if map_service.is_loaded:
            logger.info("Using local OSMnx graph routing")
            if request.waypoints:
                routes = self._map_route_via_waypoints(
                    request.origin, request.destination, request.waypoints
                )
                return routes, "osmnx"
            return (
                map_service.find_alternative_paths(
                    request.origin,
                    request.destination,
                    num_paths=self.settings.max_alternative_routes + 1,
                ),
                "osmnx",
            )

        # 3. Straight-line fallback
        logger.warning("Using straight-line fallback routing")
        return [
            osrm_service.fallback_direct_route(
                request.origin, request.destination, request.waypoints
            )
        ], "fallback"

    def _map_route_via_waypoints(
        self,
        origin: Coordinate,
        destination: Coordinate,
        waypoints: list[Coordinate],
    ) -> list[dict]:
        stops = [origin, *waypoints, destination]
        legs = []
        total_distance = 0.0
        total_time = 0.0
        coordinates = []

        for a, b in zip(stops[:-1], stops[1:], strict=False):
            leg = map_service.find_shortest_path(a, b)
            legs.append(leg)
            total_distance += leg["distance_km"]
            total_time += leg["time_minutes"]
            if len(leg["coordinates"]) > 1:
                coordinates.extend(leg["coordinates"][:-1])

        if legs and legs[-1]["coordinates"]:
            coordinates.append(legs[-1]["coordinates"][-1])

        return [{
            "distance_km": round(total_distance, 2),
            "time_minutes": round(total_time, 2),
            "coordinates": coordinates,
        }]

    def _score_route(
        self, route_data: dict, weather_speed_factor: float, preferences
    ) -> RouteInfo:
        distance_km = route_data["distance_km"]
        base_time = route_data["time_minutes"]

        traffic_score = traffic_service.get_route_traffic_score(route_data["coordinates"])
        incident_penalty = incident_service.route_penalty(route_data["coordinates"])
        if incident_penalty:
            traffic_score = max(0.0, traffic_score - incident_penalty)

        traffic_factor = 1.0 + (1.0 - traffic_score) * 0.5

        mode = preferences.mode
        factor = MODE_TIME_FACTOR.get(mode, 1.0)
        if factor is None:  # walking uses own speed
            mode_time = (distance_km / WALKING_SPEED_KMH) * 60
            adjusted_time = mode_time / weather_speed_factor
        else:
            adjusted_time = (
                base_time * traffic_factor / weather_speed_factor * factor
            )

        # Real supervised travel-time AI: blends learned ETA into the heuristic.
        ai_block = {
            "model_active": False,
            "blend_weight": 0.0,
            "samples": 0,
            "predicted_minutes": None,
            "heuristic_minutes": round(adjusted_time, 2),
        }
        if factor is not None:
            now = datetime.now()
            ai_pred = travel_time_model.predict({
                "distance_km": distance_km,
                "traffic_score": traffic_score,
                "weather_impact": weather_speed_factor,
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "is_peak": 1 if (7 <= now.hour <= 9 or 17 <= now.hour <= 19) else 0,
            })
            ai_weight = travel_time_model.blend_weight()
            if ai_pred is not None and ai_weight > 0:
                ai_time = ai_pred * factor
                adjusted_time = adjusted_time * (1 - ai_weight) + ai_time * ai_weight
                ai_block = {
                    "model_active": True,
                    "blend_weight": ai_weight,
                    "samples": travel_time_model.samples,
                    "predicted_minutes": round(ai_time, 2),
                    "heuristic_minutes": round(adjusted_time, 2),
                }

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
            instructions=[Instruction(**i) for i in route_data.get("instructions", [])],
            legs=[LegSummary(**leg_data) for leg_data in route_data.get("legs", [])],
            road_conditions={
                "traffic_level": self._get_traffic_level(traffic_score),
                "weather_condition": self._get_weather_level(weather_speed_factor),
                "mode_label": MODE_LABELS.get(mode, mode.value),
                "incident_penalty": round(incident_penalty, 3),
                "ai": ai_block,
                "congestion_source": traffic_service.congestion_source(),
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
