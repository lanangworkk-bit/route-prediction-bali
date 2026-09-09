import math
from app.models.route import Coordinate


def haversine_distance(coord1: Coordinate, coord2: Coordinate) -> float:
    R = 6371.0
    lat1_rad = math.radians(coord1.lat)
    lat2_rad = math.radians(coord2.lat)
    dlat = math.radians(coord2.lat - coord1.lat)
    dlng = math.radians(coord2.lng - coord1.lng)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_bearing(coord1: Coordinate, coord2: Coordinate) -> float:
    lat1 = math.radians(coord1.lat)
    lat2 = math.radians(coord2.lat)
    dlng = math.radians(coord2.lng - coord1.lng)

    x = math.sin(dlng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlng)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def interpolate_coordinates(
    coord1: Coordinate, coord2: Coordinate, num_points: int = 10
) -> list[Coordinate]:
    if num_points < 2:
        return [coord1, coord2]

    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        lat = coord1.lat + t * (coord2.lat - coord1.lat)
        lng = coord1.lng + t * (coord2.lng - coord1.lng)
        points.append(Coordinate(lat=lat, lng=lng))

    return points
