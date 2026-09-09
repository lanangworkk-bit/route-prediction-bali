from app.models.route import Coordinate, RouteRequest


def validate_route_request(request: RouteRequest) -> RouteRequest:
    same_lat = request.origin.lat == request.destination.lat
    same_lng = request.origin.lng == request.destination.lng
    if same_lat and same_lng:
        raise ValueError("Origin and destination cannot be the same")

    all_stops = [request.origin, *request.waypoints, request.destination]
    seen = set()
    for stop in all_stops:
        key = (round(stop.lat, 6), round(stop.lng, 6))
        if key in seen:
            raise ValueError("Duplicate stop coordinates are not allowed")
        seen.add(key)
        if not is_within_bali(stop):
            raise ValueError("All route stops must be within the Bali coverage area")

    return request


def validate_coordinates(lat: float, lng: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lng <= 180


def is_within_bali(coord: Coordinate) -> bool:
    bali_bounds = {
        "min_lat": -8.85,  # Meliputi Uluwatu & Semenanjung Bukit
        "max_lat": -8.0,
        "min_lng": 114.4,  # Meliputi Gilimanuk (ujung barat)
        "max_lng": 115.8,
    }
    return (
        bali_bounds["min_lat"] <= coord.lat <= bali_bounds["max_lat"]
        and bali_bounds["min_lng"] <= coord.lng <= bali_bounds["max_lng"]
    )
