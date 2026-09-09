from unittest.mock import Mock, patch

from app.models.route import Coordinate
from app.services.osrm_service import osrm_service

ORIGIN = Coordinate(lat=-8.6500, lng=115.2167)
DESTINATION = Coordinate(lat=-8.3405, lng=115.0920)
WAYPOINT_1 = Coordinate(lat=-8.5000, lng=115.1500)
WAYPOINT_2 = Coordinate(lat=-8.4500, lng=115.1400)

MOCK_OSRM_RESPONSE = {
    "code": "Ok",
    "routes": [
        {
            "distance": 25000.0,
            "duration": 1500.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [115.2167, -8.65],
                    [115.2, -8.6],
                    [115.092, -8.3405],
                ],
            },
        }
    ],
}


@patch("app.services.osrm_service.requests.get")
def test_get_routes_success(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: MOCK_OSRM_RESPONSE,
    )

    routes = osrm_service.get_routes(ORIGIN, DESTINATION)

    assert len(routes) == 1
    assert routes[0]["distance_km"] == 25.0
    assert routes[0]["time_minutes"] == 25.0
    assert len(routes[0]["coordinates"]) == 3
    assert osrm_service.base_url in str(mock_get.call_args)


@patch("app.services.osrm_service.requests.get")
def test_get_routes_empty_on_error(mock_get):
    mock_get.side_effect = Exception("network down")

    routes = osrm_service.get_routes(ORIGIN, DESTINATION)
    assert routes == []


@patch("app.services.osrm_service.requests.get")
def test_get_routes_empty_on_non_ok_code(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {"code": "InvalidQuery", "routes": []},
    )

    routes = osrm_service.get_routes(ORIGIN, DESTINATION)
    assert routes == []


def test_fallback_direct_route():
    route = osrm_service.fallback_direct_route(ORIGIN, DESTINATION)

    assert route["distance_km"] > 20
    assert route["time_minutes"] > 0
    assert len(route["coordinates"]) == 3
    assert route["coordinates"][0] == ORIGIN
    assert route["coordinates"][-1] == DESTINATION


def test_fallback_direct_route_with_waypoints():
    route = osrm_service.fallback_direct_route(
        ORIGIN, DESTINATION, waypoints=[WAYPOINT_1, WAYPOINT_2]
    )

    assert route["coordinates"][0] == ORIGIN
    assert route["coordinates"][-1] == DESTINATION
    assert route["distance_km"] > 0
    assert route["time_minutes"] > 0


@patch("app.services.osrm_service.requests.get")
def test_get_routes_with_waypoints_url(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: MOCK_OSRM_RESPONSE,
    )

    osrm_service.get_routes(
        ORIGIN, DESTINATION, waypoints=[WAYPOINT_1], max_routes=1
    )

    request_url = str(mock_get.call_args)
    assert "115.2167,-8.65;115.15,-8.5;115.092,-8.3405" in request_url


@patch("app.services.osrm_service.requests.get")
def test_get_routes_synthesizes_alternatives(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: MOCK_OSRM_RESPONSE,
    )

    routes = osrm_service.get_routes(ORIGIN, DESTINATION, max_routes=3)

    assert len(routes) == 1
    assert mock_get.call_count > 1, "Expected extra OSRM requests for variants"


@patch("app.services.osrm_service.requests.get")
def test_get_route_single(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: MOCK_OSRM_RESPONSE,
    )

    route = osrm_service.get_route(ORIGIN, DESTINATION)

    assert route["distance_km"] == 25.0
    assert len(route["coordinates"]) == 3


@patch("app.services.osrm_service.requests.get")
def test_get_route_fallback_on_single_failure(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {"code": "NoRoute", "routes": []},
    )

    route = osrm_service.get_route(ORIGIN, DESTINATION)

    assert route["distance_km"] > 0
    assert route["coordinates"][0] == ORIGIN
