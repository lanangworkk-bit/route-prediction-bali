from fastapi import APIRouter, HTTPException, Query

from app.ml.trainer import retrain_models
from app.models.route import (
    Coordinate,
    RouteInfo,
    RouteRequest,
    RouteResponse,
)
from app.services.area_service import area_service
from app.services.history_service import history_service
from app.services.map_service import map_service
from app.services.place_service import place_service
from app.services.route_optimizer import route_optimizer
from app.services.traffic_service import traffic_service
from app.services.visualization import visualization_service
from app.services.weather_service import weather_service
from app.utils.validators import is_within_bali, validate_route_request

router = APIRouter(prefix="/api/v1", tags=["routes"])


def _handle_validation_error(e: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(e))


@router.get("/areas")
async def list_areas(
    q: str = Query("", description="Search area by name or regency"),
):
    """All Bali areas: regencies, cities, beaches, temples and more."""
    areas = area_service.search(q)
    return {
        "total": len(areas),
        "regencies": area_service.REGENCIES,
        "areas": areas,
    }


@router.get("/areas/regencies")
async def list_regencies():
    """Bali areas grouped by regency (for region-based dropdowns)."""
    return area_service.list_regencies()


def _parse_waypoints(waypoints_str: str) -> list[Coordinate]:
    waypoints = []
    for chunk in waypoints_str.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(",")
        if len(parts) != 2:
            raise HTTPException(
                status_code=400,
                detail="Invalid waypoint format. Expected lat,lng separated by ';'",
            )
        try:
            waypoints.append(Coordinate(lat=float(parts[0]), lng=float(parts[1])))
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid waypoint coordinate: {chunk}"
            ) from e
    return waypoints


@router.get("/map/status")
async def map_status():
    return {
        "loaded": map_service.is_loaded,
        "place": map_service.place_name if map_service.is_loaded else None,
        "nodes": len(map_service.graph.nodes) if map_service.is_loaded else 0,
        "edges": len(map_service.graph.edges) if map_service.is_loaded else 0,
    }


@router.post("/map/load")
async def load_map():
    if not map_service.is_loaded:
        map_service.load_graph()
    return {
        "loaded": map_service.is_loaded,
        "place": map_service.place_name,
        "nodes": len(map_service.graph.nodes) if map_service.is_loaded else 0,
        "edges": len(map_service.graph.edges) if map_service.is_loaded else 0,
        "message": "Map loaded, real road routing enabled" if map_service.is_loaded
        else "Map load failed, using fallback routing",
    }


@router.post("/route/predict", response_model=RouteResponse)
async def predict_route(request: RouteRequest):
    try:
        validate_route_request(request)
    except ValueError as e:
        raise _handle_validation_error(e) from e

    response = await route_optimizer.find_best_route(request)
    return response


@router.get("/route/visualize")
async def visualize_route(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180),
    waypoints: str = Query(
        "", description="Optional stops 'lat,lng;lat,lng' in order"
    ),
):
    request = RouteRequest(
        origin=Coordinate(lat=origin_lat, lng=origin_lng),
        destination=Coordinate(lat=dest_lat, lng=dest_lng),
        waypoints=_parse_waypoints(waypoints),
    )

    try:
        validate_route_request(request)
    except ValueError as e:
        raise _handle_validation_error(e) from e

    response = await route_optimizer.find_best_route(request)
    map_obj = visualization_service.create_route_map(response)

    slug = "_".join(f"{w.lat}_{w.lng}" for w in request.waypoints)
    suffix = f"via_{slug}_to_" if slug else "_to_"
    filename = (
        f"data/processed/route_{origin_lat}_{origin_lng}{suffix}"
        f"{dest_lat}_{dest_lng}.html"
    )
    visualization_service.save_map(map_obj, filename)

    return {
        "message": "Route visualization created",
        "file": filename,
        "route_summary": {
            "distance_km": response.best_route.distance_km,
            "estimated_time": response.best_route.estimated_time_minutes,
            "score": response.best_route.overall_score,
            "stops": 2 + len(request.waypoints),
        },
    }


@router.get("/places/search")
async def search_places(
    q: str = Query(..., min_length=2, description="Place name, e.g. 'Pura Luhur'"),
    limit: int = Query(5, ge=1, le=10),
):
    """Place search (geocoding) restricted to Bali via Nominatim."""
    results = place_service.search(q, limit=limit)
    return {"query": q, "total": len(results), "results": results}


@router.get("/traffic/overlay")
async def traffic_overlay(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(12, ge=2, le=50),
    grid: int = Query(9, ge=3, le=15),
):
    """Traffic heat grid around a point (feeds the 'Traffic' map layer)."""
    if not is_within_bali(Coordinate(lat=lat, lng=lng)):
        raise HTTPException(
            status_code=400,
            detail="Location is outside Bali coverage area",
        )

    km_per_deg_lat = 111.0
    dlat = radius_km / km_per_deg_lat
    dlng = radius_km / (km_per_deg_lat * max(1e-6, abs(lat) or 1e-6))

    points = []
    for row in range(grid):
        for col in range(grid):
            # Spread grid slightly wider than radius for smooth coverage.
            f = (grid - 1) / 2 if grid > 1 else 1
            p_lat = lat + dlat * (row - grid / 2 + 0.5) / f
            p_lng = lng + dlng * (col - grid / 2 + 0.5) / f
            congestion = traffic_service.get_traffic_congestion(p_lat, p_lng)
            points.append({
                "lat": round(p_lat, 5),
                "lng": round(p_lng, 5),
                "congestion": congestion,
                "level": traffic_service._level_for(congestion),
            })

    return {
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "points": points,
    }


@router.get("/route/geometry")
async def route_geometry(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180),
    waypoints: str = Query("", description="Optional stops 'lat,lng;lat,lng'"),
):
    """GeoJSON-style route data for live Leaflet rendering (no HTML file)."""
    request = RouteRequest(
        origin=Coordinate(lat=origin_lat, lng=origin_lng),
        destination=Coordinate(lat=dest_lat, lng=dest_lng),
        waypoints=_parse_waypoints(waypoints),
    )

    try:
        validate_route_request(request)
    except ValueError as e:
        raise _handle_validation_error(e) from e

    response = await route_optimizer.find_best_route(request)

    def serialize(route: RouteInfo) -> dict:
        return {
            "coordinates": [
                [c.lng, c.lat] for c in route.coordinates
            ],
            "distance_km": route.distance_km,
            "estimated_time_minutes": route.estimated_time_minutes,
            "overall_score": route.overall_score,
            "traffic_score": route.traffic_score,
            "traffic_level": route.road_conditions.get("traffic_level", ""),
            "instructions": [i.model_dump() for i in route.instructions],
            "legs": [leg.model_dump() for leg in route.legs],
        }

    return {
        "origin": {"lat": origin_lat, "lng": origin_lng},
        "destination": {"lat": dest_lat, "lng": dest_lng},
        "waypoints": [{"lat": w.lat, "lng": w.lng} for w in response.waypoints],
        "best": serialize(response.best_route),
        "alternatives": [serialize(a) for a in response.alternative_routes],
        "traffic_segments": traffic_service.get_segment_traffic(
            response.best_route.coordinates, segments=6
        ),
        "weather_summary": response.weather_summary,
    }


@router.get("/traffic/{lat}/{lng}")
async def get_traffic(lat: float, lng: float):
    if not is_within_bali(Coordinate(lat=lat, lng=lng)):
        raise HTTPException(
            status_code=400,
            detail="Location is outside Bali coverage area",
        )

    congestion = traffic_service.get_traffic_congestion(lat, lng)
    prediction = traffic_service.predict_traffic(lat, lng)

    return {
        "location": {"lat": lat, "lng": lng},
        "current_congestion": congestion,
        "prediction": prediction.model_dump(),
    }


@router.get("/weather/{lat}/{lng}")
async def get_weather(lat: float, lng: float):
    weather = await weather_service.get_current_weather(lat, lng)
    impact = weather_service.calculate_weather_impact(weather)

    return {
        "location": {"lat": lat, "lng": lng},
        "weather": weather.model_dump(),
        "impact": impact.model_dump(),
    }


@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    records = history_service.get_history(limit=limit, offset=offset)
    return {
        "total": history_service.get_count(),
        "records": records,
    }


@router.get("/history/stats")
async def get_history_stats():
    return history_service.get_stats()


@router.post("/models/retrain")
async def retrain():
    try:
        report = retrain_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {e}") from e

    return {"status": "ok", "report": report}
