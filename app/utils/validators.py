from app.models.route import Coordinate, RouteRequest


def validate_route_request(request: RouteRequest) -> RouteRequest:
    same_lat = request.origin.lat == request.destination.lat
    same_lng = request.origin.lng == request.destination.lng
    if same_lat and same_lng:
        raise ValueError("Origin and destination cannot be the same")

    return request


def validate_coordinates(lat: float, lng: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lng <= 180


def is_within_bali(coord: Coordinate) -> bool:
    bali_bounds = {
        "min_lat": -8.8,
        "max_lat": -8.0,
        "min_lng": 114.4,
        "max_lng": 115.8,
    }
    return (
        bali_bounds["min_lat"] <= coord.lat <= bali_bounds["max_lat"]
        and bali_bounds["min_lng"] <= coord.lng <= bali_bounds["max_lng"]
    )
