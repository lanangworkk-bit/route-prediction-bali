from fastapi import APIRouter, HTTPException, Query

from app.models.route import Coordinate, RouteRequest, RouteResponse
from app.services.route_optimizer import route_optimizer
from app.services.traffic_service import traffic_service
from app.services.visualization import visualization_service
from app.services.weather_service import weather_service
from app.utils.validators import is_within_bali, validate_route_request

router = APIRouter(prefix="/api/v1", tags=["routes"])


def _handle_validation_error(e: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(e))


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
):
    request = RouteRequest(
        origin=Coordinate(lat=origin_lat, lng=origin_lng),
        destination=Coordinate(lat=dest_lat, lng=dest_lng),
    )

    try:
        validate_route_request(request)
    except ValueError as e:
        raise _handle_validation_error(e) from e

    response = await route_optimizer.find_best_route(request)
    map_obj = visualization_service.create_route_map(response)

    filename = f"data/processed/route_{origin_lat}_{origin_lng}_to_{dest_lat}_{dest_lng}.html"
    visualization_service.save_map(map_obj, filename)

    return {
        "message": "Route visualization created",
        "file": filename,
        "route_summary": {
            "distance_km": response.best_route.distance_km,
            "estimated_time": response.best_route.estimated_time_minutes,
            "score": response.best_route.overall_score,
        },
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
