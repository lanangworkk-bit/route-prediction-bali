import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.ml.trainer import retrain_models
from app.models.route import (
    Coordinate,
    RouteInfo,
    RouteMode,
    RouteRequest,
    RouteResponse,
)
from app.services.area_service import area_service
from app.services.favorites_service import favorites_service
from app.services.history_service import history_service
from app.services.incident_service import incident_service
from app.services.map_service import map_service
from app.services.place_service import place_service
from app.services.poi_service import poi_service
from app.services.route_optimizer import route_optimizer
from app.services.track_service import track_service
from app.services.traffic_service import traffic_service
from app.services.visualization import visualization_service
from app.services.weather_service import weather_service
from app.utils.validators import is_within_bali, validate_route_request

router = APIRouter(prefix="/api/v1", tags=["routes"])


class FavoriteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)
    origin: Coordinate
    destination: Coordinate
    waypoints: list[Coordinate] = Field(default_factory=list)
    priority: str = "time"
    mode: str = "car"


class IncidentCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    incident_type: str = "macet"
    description: str = ""
    reporter: str = "anonym"


class TrackStartRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    waypoints: list[Coordinate] = Field(default_factory=list)
    priority: str = "time"
    mode: RouteMode = RouteMode.CAR


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
    mode: str = Query("car", description="car | motorcycle | walking"),
    priority: str = Query("time", description="time | distance | traffic"),
):
    """GeoJSON-style route data for live Leaflet rendering (no HTML file)."""
    request = RouteRequest(
        origin=Coordinate(lat=origin_lat, lng=origin_lng),
        destination=Coordinate(lat=dest_lat, lng=dest_lng),
        waypoints=_parse_waypoints(waypoints),
        preferences={"priority": priority, "mode": mode},
    )

    try:
        validate_route_request(request)
    except ValueError as e:
        raise _handle_validation_error(e) from e

    response = await route_optimizer.find_best_route(request, record_history=False)

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
            "mode_label": route.road_conditions.get("mode_label", ""),
            "incident_penalty": route.road_conditions.get("incident_penalty", 0),
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


# ===================== POI (Lokasi Spesifik) =====================

@router.get("/pois")
async def list_pois(
    category: str = Query("", description="Filter by category id"),
    q: str = Query("", description="Search POI name or note"),
    regency: str = Query("", description="Filter by regency name"),
    limit: int = Query(50, ge=1, le=300),
):
    pois = poi_service.list_pois(
        category=category or None, q=q, regency=regency or None, limit=limit
    )
    return {"total": len(pois), "pois": pois}


@router.get("/pois/categories")
async def poi_categories():
    return {"categories": poi_service.categories()}


@router.get("/pois/near")
async def pois_near(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(15, ge=1, le=50),
    limit: int = Query(60, ge=1, le=200),
):
    return {
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "total": len(poi_service.near(lat, lng, radius_km, limit)),
        "pois": poi_service.near(lat, lng, radius_km, limit),
    }


@router.get("/pois/{poi_id}")
async def get_poi(poi_id: str):
    poi = poi_service.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi


# ===================== Insight Crowd =====================

@router.get("/incidents")
async def list_incidents(
    lat: float = Query(None, ge=-90, le=90),
    lng: float = Query(None, ge=-180, le=180),
    radius_km: float = Query(25, ge=0, le=100),
):
    return {
        "total": len(incident_service.list_incidents(lat, lng, radius_km)),
        "incidents": incident_service.list_incidents(lat, lng, radius_km),
    }


@router.post("/incidents")
async def report_incident(body: IncidentCreate):
    if not is_within_bali(Coordinate(lat=body.lat, lng=body.lng)):
        raise HTTPException(status_code=400, detail="Location is outside Bali coverage area")
    incident = incident_service.report(
        body.lat, body.lng, body.incident_type, body.description, body.reporter
    )
    return {"message": "Insiden dilaporkan", "incident": incident.to_dict()}


@router.delete("/incidents/{incident_id}")
async def resolve_incident(incident_id: str):
    if not incident_service.resolve(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Insiden ditandai selesai"}


# ===================== Favorit & Riwayat =====================

@router.get("/history/last")
async def get_recent_trips(limit: int = Query(5, ge=1, le=20)):
    records = history_service.get_history(limit=limit)
    recent = []
    for r in records:
        try:
            waypoints = json.loads(r["waypoints_json"] or "[]")
        except (ValueError, KeyError, TypeError):
            waypoints = []
        recent.append({
            "id": r["id"],
            "origin": {"lat": r["origin_lat"], "lng": r["origin_lng"]},
            "destination": {"lat": r["dest_lat"], "lng": r["dest_lng"]},
            "waypoints": waypoints,
            "distance_km": r["distance_km"],
            "estimated_time_minutes": r["estimated_time_minutes"],
            "priority": r["priority"],
            "created_at": r["created_at"],
        })
    return {"total": len(recent), "trips": recent}


@router.get("/favorites")
async def list_favorites():
    return {"favorites": favorites_service.list_all()}


@router.post("/favorites")
async def create_favorite(body: FavoriteCreate):
    try:
        validate_route_request(
            RouteRequest(
                origin=body.origin,
                destination=body.destination,
                waypoints=body.waypoints,
            )
        )
    except ValueError as e:
        raise _handle_validation_error(e) from e
    favorite = favorites_service.add(
        name=body.name,
        origin_lat=body.origin.lat,
        origin_lng=body.origin.lng,
        dest_lat=body.destination.lat,
        dest_lng=body.destination.lng,
        waypoints=body.waypoints,
        priority=body.priority,
        mode=body.mode,
    )
    return {"message": "Rute disimpan ke favorit", "favorite": favorite}


@router.patch("/favorites/{favorite_id}")
async def update_favorite(
    favorite_id: int,
    name: str = Query(None, max_length=60),
    priority: str = Query(None),
    mode: str = Query(None),
):
    favorite = favorites_service.update(favorite_id, name=name, priority=priority, mode=mode)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return favorite


@router.delete("/favorites/{favorite_id}")
async def delete_favorite(favorite_id: int):
    if not favorites_service.delete(favorite_id):
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Favorit dihapus"}


# ===================== Realtime Tracking (SSE) =====================

@router.post("/track/start")
async def track_start(body: TrackStartRequest):
    request = RouteRequest(
        origin=body.origin,
        destination=body.destination,
        waypoints=body.waypoints,
        preferences={
            "priority": body.priority,
            "mode": body.mode.value,
        },
    )
    try:
        validate_route_request(request)
    except ValueError as e:
        raise _handle_validation_error(e) from e

    response = await route_optimizer.find_best_route(request, record_history=False)
    session = track_service.create(
        request,
        response.best_route,
        coordinates=response.best_route.coordinates,
        instructions=[i.model_dump() for i in response.best_route.instructions],
    )
    return {
        "message": "Sesi tracking dimulai",
        "session_id": session.session_id,
        "share_url": track_service.share_url(session.session_id),
        "snapshot": session.snapshot(),
    }


@router.get("/track/{session_id}/status")
async def track_status(session_id: str):
    session = track_service.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")
    return session.snapshot()


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.get("/track/{session_id}/stream")
async def track_stream(session_id: str):
    session = track_service.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")

    async def event_generator():
        while True:
            snap = session.snapshot()
            yield _sse_event(snap)
            if snap["status"] == "arrived":
                yield _sse_event({"type": "end", **snap})
                break
            yield "event: ping\ndata: keepalive\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
