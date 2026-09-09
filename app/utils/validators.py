from app.models.route import RouteRequest, Coordinate


def validate_route_request(request: RouteRequest) -> RouteRequest:
    if request.origin.lat == request.destination.lat and request.origin.lng == request.destination.lng:
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
