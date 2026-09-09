from fastapi.testclient import TestClient

from app.main import app
from app.models.route import Coordinate

client = TestClient(app)

MOCK_ROUTES = [
    {
        "distance_km": 28.4,
        "time_minutes": 42.0,
        "coordinates": [
            Coordinate(lat=-8.6500, lng=115.2167),
            Coordinate(lat=-8.6, lng=115.18),
            Coordinate(lat=-8.55, lng=115.14),
            Coordinate(lat=-8.3405, lng=115.0920),
        ],
    },
    {
        "distance_km": 33.1,
        "time_minutes": 48.0,
        "coordinates": [
            Coordinate(lat=-8.6500, lng=115.2167),
            Coordinate(lat=-8.58, lng=115.26),
            Coordinate(lat=-8.45, lng=115.16),
            Coordinate(lat=-8.3405, lng=115.0920),
        ],
    },
]


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Prediksi Rute" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_map_status():
    response = client.get("/api/v1/map/status")
    assert response.status_code == 200
    data = response.json()
    assert "loaded" in data
    assert "nodes" in data


def test_get_weather():
    response = client.get("/api/v1/weather/-8.6500/115.2167")
    assert response.status_code == 200
    data = response.json()
    assert "weather" in data
    assert "impact" in data


def test_get_traffic():
    response = client.get("/api/v1/traffic/-8.6500/115.2167")
    assert response.status_code == 200
    data = response.json()
    assert "current_congestion" in data
    assert "prediction" in data


def test_predict_route(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES
    )

    request_data = {
        "origin": {"lat": -8.6500, "lng": 115.2167},
        "destination": {"lat": -8.3405, "lng": 115.0920},
        "preferences": {
            "avoid_tolls": False,
            "avoid_highways": False,
            "priority": "time",
        },
    }

    response = client.post("/api/v1/route/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "best_route" in data
    assert "alternative_routes" in data
    assert "weather_summary" in data
    assert data["best_route"]["distance_km"] == 28.4
    assert len(data["best_route"]["coordinates"]) == 4


def test_visualize_route(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )

    response = client.get(
        "/api/v1/route/visualize"
        "?origin_lat=-8.6500&origin_lng=115.2167"
        "&dest_lat=-8.3405&dest_lng=115.0920"
    )
    assert response.status_code == 200
    data = response.json()
    assert "file" in data
    assert data["route_summary"]["distance_km"] == 28.4


def test_predict_route_same_origin_dest():
    request_data = {
        "origin": {"lat": -8.6500, "lng": 115.2167},
        "destination": {"lat": -8.6500, "lng": 115.2167},
    }

    response = client.post("/api/v1/route/predict", json=request_data)
    assert response.status_code == 400


def test_predict_route_with_waypoints(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )

    request_data = {
        "origin": {"lat": -8.6500, "lng": 115.2167},
        "destination": {"lat": -8.3405, "lng": 115.0920},
        "waypoints": [{"lat": -8.5000, "lng": 115.1500}],
        "preferences": {"priority": "time"},
    }

    response = client.post("/api/v1/route/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["waypoints"]) == 1
    assert data["waypoints"][0]["lat"] == -8.5000


def test_predict_route_duplicate_stop_rejected():
    request_data = {
        "origin": {"lat": -8.6500, "lng": 115.2167},
        "destination": {"lat": -8.3405, "lng": 115.0920},
        "waypoints": [{"lat": -8.6500, "lng": 115.2167}],
    }

    response = client.post("/api/v1/route/predict", json=request_data)
    assert response.status_code == 400


def test_predict_route_outside_bali_rejected():
    request_data = {
        "origin": {"lat": -6.2000, "lng": 106.8000},
        "destination": {"lat": -8.3405, "lng": 115.0920},
    }

    response = client.post("/api/v1/route/predict", json=request_data)
    assert response.status_code == 400


def test_history_records_prediction(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )

    client.post(
        "/api/v1/route/predict",
        json={
            "origin": {"lat": -8.6500, "lng": 115.2167},
            "destination": {"lat": -8.3405, "lng": 115.0920},
        },
    )

    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["records"][0]["distance_km"] == 28.4


def test_history_stats():
    response = client.get("/api/v1/history/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_trips" in data
    assert "avg_score" in data


def test_retrain_models():
    response = client.post("/api/v1/models/retrain")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "traffic" in data["report"]
    assert "route_scorer" in data["report"]


def test_visualize_route_with_waypoints(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )

    response = client.get(
        "/api/v1/route/visualize"
        "?origin_lat=-8.6500&origin_lng=115.2167"
        "&dest_lat=-8.3405&dest_lng=115.0920"
        "&waypoints=-8.5000,115.1500"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route_summary"]["stops"] == 3
