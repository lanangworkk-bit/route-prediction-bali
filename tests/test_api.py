import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Prediksi Rute" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


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


def test_predict_route():
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


def test_predict_route_same_origin_dest():
    request_data = {
        "origin": {"lat": -8.6500, "lng": 115.2167},
        "destination": {"lat": -8.6500, "lng": 115.2167},
    }

    response = client.post("/api/v1/route/predict", json=request_data)
    assert response.status_code == 400
