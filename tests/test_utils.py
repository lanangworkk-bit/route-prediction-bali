import pytest
from datetime import datetime
from app.models.route import Coordinate, RouteRequest, RoutePreferences
from app.utils.geo import haversine_distance, interpolate_coordinates
from app.utils.validators import validate_coordinates, is_within_bali


def test_haversine_distance():
    baliAirport = Coordinate(lat=-8.7482, lng=115.1672)
    denpasar = Coordinate(lat=-8.6500, lng=115.2167)

    distance = haversine_distance(baliAirport, denpasar)
    assert 5 < distance < 15


def test_interpolate_coordinates():
    start = Coordinate(lat=0.0, lng=0.0)
    end = Coordinate(lat=1.0, lng=1.0)

    points = interpolate_coordinates(start, end, num_points=5)
    assert len(points) == 5
    assert points[0].lat == 0.0
    assert points[-1].lat == 1.0


def test_validate_coordinates():
    assert validate_coordinates(0, 0) is True
    assert validate_coordinates(-90, -180) is True
    assert validate_coordinates(90, 180) is True
    assert validate_coordinates(91, 0) is False
    assert validate_coordinates(0, 181) is False


def test_is_within_bali():
    denpasar = Coordinate(lat=-8.6500, lng=115.2167)
    jakarta = Coordinate(lat=-6.2088, lng=106.8456)

    assert is_within_bali(denpasar) is True
    assert is_within_bali(jakarta) is False


def test_route_request_validation():
    origin = Coordinate(lat=-8.6500, lng=115.2167)
    destination = Coordinate(lat=-8.3405, lng=115.0920)

    request = RouteRequest(origin=origin, destination=destination)
    assert request.origin.lat == -8.6500
    assert request.preferences.priority.value == "time"
