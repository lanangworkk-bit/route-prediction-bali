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


def test_list_areas():
    response = client.get("/api/v1/areas")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 30
    names = {a["name"] for a in data["areas"]}
    assert {"Denpasar", "Kuta", "Ubud", "Singaraja", "Negara"} <= names
    assert len(data["regencies"]) == 9
    for area in data["areas"]:
        assert -8.85 <= area["lat"] <= -8.0
        assert 114.4 <= area["lng"] <= 115.8


def test_search_areas():
    response = client.get("/api/v1/areas", params={"q": "kintamani"})
    assert response.status_code == 200
    data = response.json()
    assert any(a["name"] == "Kintamani" for a in data["areas"])


def test_areas_grouped_by_regency():
    response = client.get("/api/v1/areas/regencies")
    assert response.status_code == 200
    groups = response.json()
    assert len(groups) == 9
    badung = next(g for g in groups if g["name"] == "Badung")
    assert {"name": "Kuta"}.get("name") and any(
        a["name"] == "Kuta" for a in badung["areas"]
    )


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
    assert "travel_time" in data["report"]


def test_models_info():
    response = client.get("/api/v1/models/info")
    assert response.status_code == 200
    data = response.json()
    assert "history_count" in data
    assert "travel_time" in data
    assert "traffic" in data
    assert "route_scorer" in data
    assert "training" in data


def test_traffic_now_endpoint():
    ok = client.get("/api/v1/traffic/now", params={"lat": -8.65, "lng": 115.22})
    assert ok.status_code == 200
    data = ok.json()
    assert "congestion" in data
    assert "level" in data
    assert "source" in data
    assert "model" in data
    bad = client.get("/api/v1/traffic/now", params={"lat": -6.2, "lng": 106.8})
    assert bad.status_code == 400


def test_traffic_hourly_endpoint():
    response = client.get(
        "/api/v1/traffic/hourly",
        params={"lat": -8.65, "lng": 115.22, "hour": 9, "grid": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["curve"]) == 24
    assert "hour" in data and data["hour"] == 9
    assert data["points"]


def test_public_config_endpoint():
    response = client.get("/api/v1/config/public")
    assert response.status_code == 200
    data = response.json()
    assert data["tomtom_enabled"] is False
    assert "ai_refresh_interval_s" in data
    assert "coverage" in data
    assert data["coverage"]["lat_min"] == -8.85
    assert "gemini_enabled" in data
    assert "ai_provider" in data


def test_osrm_nearest_endpoint(monkeypatch):
    from unittest.mock import patch

    from app.models.route import Coordinate
    from app.services.osrm_service import osrm_service

    with patch.object(osrm_service, "nearest", return_value=Coordinate(lat=-8.6488, lng=115.2142)):
        response = client.get("/api/v1/osrm/nearest", params={"lat": -8.65, "lng": 115.2167})
    assert response.status_code == 200
    body = response.json()
    assert body["snapped"] is True
    assert abs(body["lat"] - -8.6488) < 1e-3


def test_osrm_nearest_endpoint_fallback(monkeypatch):
    from unittest.mock import patch

    from app.services.osrm_service import osrm_service

    with patch.object(osrm_service, "nearest", return_value=None):
        response = client.get("/api/v1/osrm/nearest", params={"lat": -8.65, "lng": 115.2167})
    assert response.status_code == 200
    assert response.json()["snapped"] is False


def test_ai_search_requires_key():
    response = client.post("/api/v1/ai/search", json={"query": "cari pantai kuta"})
    assert response.status_code == 400
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_ai_search_endpoint_flow(monkeypatch):
    from unittest.mock import patch

    from app.services.place_service import place_service

    monkeypatch.setattr("app.api.routes.gemini_enabled", lambda: True)
    monkeypatch.setattr(
        "app.api.routes.search_parse",
        lambda query, **kwargs: {
            "destination": "Pantai Kuta",
            "priority": "time",
            "mode": "car",
            "note": "Rute menuju Pantai Kuta.",
        },
    )
    with patch.object(
        place_service,
        "search",
        return_value=[{"name": "Pantai Kuta", "lat": -8.7185, "lng": 115.1686}],
    ) as mock_search:
        response = client.post("/api/v1/ai/search", json={"query": "ke pantai kuta"})

    assert response.status_code == 200
    body = response.json()
    assert body["destination"] == "Pantai Kuta"
    assert body["priority"] == "time"
    assert body["mode"] == "car"
    assert body["suggestions"][0]["name"] == "Pantai Kuta"
    mock_search.assert_called_once_with("Pantai Kuta", 5)


def test_realtime_incidents_sse():
    import asyncio

    from app.api import routes as route_mod

    async def run():
        response = await route_mod.realtime_incidents()
        iterator = response.body_iterator.__aiter__()
        try:
            chunk = await asyncio.wait_for(iterator.__anext__(), timeout=3)
        finally:
            await iterator.aclose()
        return chunk

    chunk = asyncio.run(run())
    assert "event:" in (chunk.decode() if isinstance(chunk, bytes) else chunk)


def test_realtime_traffic_sse():
    import asyncio

    from app.api import routes as route_mod

    async def run():
        response = await route_mod.realtime_traffic(lat=-8.65, lng=115.22, interval_s=2)
        iterator = response.body_iterator.__aiter__()
        try:
            chunk = await asyncio.wait_for(iterator.__anext__(), timeout=3)
        finally:
            await iterator.aclose()
        return chunk

    chunk = asyncio.run(run())
    text = chunk.decode() if isinstance(chunk, bytes) else chunk
    assert "event: traffic" in text


def test_realtime_route_sse():
    import asyncio

    from app.api import routes as route_mod

    async def run():
        response = await route_mod.realtime_route(
            origin_lat=-8.65, origin_lng=115.22,
            dest_lat=-8.51, dest_lng=115.26,
            distance_km=20.0, base_minutes=30.0,
            coords="-8.65,115.22;-8.60,115.25;-8.51,115.26",
            interval_s=2,
        )
        iterator = response.body_iterator.__aiter__()
        try:
            chunk = await asyncio.wait_for(iterator.__anext__(), timeout=3)
        finally:
            await iterator.aclose()
        return chunk

    chunk = asyncio.run(run())
    text = chunk.decode() if isinstance(chunk, bytes) else chunk
    assert "event: route" in text
    assert '"eta_minutes"' in text


def test_route_geometry_endpoint(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES
    )

    response = client.get(
        "/api/v1/route/geometry"
        "?origin_lat=-8.6500&origin_lng=115.2167"
        "&dest_lat=-8.3405&dest_lng=115.0920"
    )
    assert response.status_code == 200
    data = response.json()
    assert "best" in data
    assert len(data["alternatives"]) == 1
    assert data["best"]["coordinates"][0] == [115.2167, -8.6500]
    assert "traffic_segments" in data
    assert "waypoints" in data and data["waypoints"] == []


def test_route_geometry_with_waypoints(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )

    response = client.get(
        "/api/v1/route/geometry"
        "?origin_lat=-8.6500&origin_lng=115.2167"
        "&dest_lat=-8.3405&dest_lng=115.0920"
        "&waypoints=-8.5000,115.1500"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["waypoints"]) == 1
    assert data["waypoints"][0]["lat"] == -8.5000


def test_route_geometry_rejects_sample_integration():
    response = client.get(
        "/api/v1/route/geometry"
        "?origin_lat=-6.2000&origin_lng=106.8000"
        "&dest_lat=-8.3405&dest_lng=115.0920"
    )
    assert response.status_code == 400


def test_traffic_overlay_endpoint():
    response = client.get(
        "/api/v1/traffic/overlay", params={"lat": -8.65, "lng": 115.2167, "grid": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 25
    for point in data["points"]:
        assert 0 <= point["congestion"] <= 1
        assert point["level"] in ("lancar", "normal", "padat", "macet")


def test_traffic_overlay_outside_bali_rejected():
    response = client.get(
        "/api/v1/traffic/overlay", params={"lat": -6.2, "lng": 106.8}
    )
    assert response.status_code == 400


def test_places_search(monkeypatch):
    from app.services import place_service

    def fake_search(query, limit=5):
        return [
            {
                "name": "Kuta",
                "display_name": "Kuta, Badung, Bali, Indonesia",
                "lat": -8.7234,
                "lng": 115.1723,
                "type": "town",
            }
        ]

    monkeypatch.setattr(place_service.place_service, "search", fake_search)

    response = client.get("/api/v1/places/search", params={"q": "kuta"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["name"] == "Kuta"


def test_places_search_empty_query():
    response = client.get("/api/v1/places/search", params={"q": ""})
    assert response.status_code == 422


def test_list_pois():
    response = client.get("/api/v1/pois", params={"limit": 300})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 100
    names = {p["name"] for p in data["pois"]}
    for expected in [
        "Pura Besakih", "Pantai Kuta", "Air Terjun Gitgit",
        "Gunung Batur", "Bandara I Gusti Ngurah Rai (DPS)",
    ]:
        assert expected in names
    for p in data["pois"]:
        assert -8.85 <= p["lat"] <= -8.0
        assert 114.4 <= p["lng"] <= 115.8


def test_pois_filter_category():
    response = client.get("/api/v1/pois", params={"category": "pantai"})
    data = response.json()
    assert data["total"] > 10
    assert all(p["category"] == "pantai" for p in data["pois"])


def test_pois_search_q():
    response = client.get("/api/v1/pois", params={"q": "uluwatu"})
    data = response.json()
    assert any("Uluwatu" in p["name"] for p in data["pois"])


def test_pois_categories():
    response = client.get("/api/v1/pois/categories")
    data = response.json()
    cats = {c["id"] for c in data["categories"]}
    assert {"pura", "pantai", "air_terjun", "kuliner", "kesehatan"} <= cats
    assert data["categories"][0]["count"] > 0


def test_pois_near():
    response = client.get(
        "/api/v1/pois/near", params={"lat": -8.65, "lng": 115.22, "radius_km": 15}
    )
    data = response.json()
    assert data["total"] > 5
    assert all(p["distance_km"] <= 15 for p in data["pois"])
    assert data["pois"][0]["distance_km"] <= data["pois"][-1]["distance_km"]


def test_poi_detail():
    response = client.get("/api/v1/pois/pura-besakih")
    assert response.status_code == 200
    assert response.json()["name"] == "Pura Besakih"


def test_poi_not_found():
    response = client.get("/api/v1/pois/tidak-ada")
    assert response.status_code == 404


def test_incident_flow():
    report = client.post("/api/v1/incidents", json={
        "lat": -8.65, "lng": 115.22, "incident_type": "kecelakaan",
        "description": "Kecelakaan di simpang", "reporter": "test",
    })
    assert report.status_code == 200
    inc_id = report.json()["incident"]["id"]

    listing = client.get("/api/v1/incidents", params={"lat": -8.65, "lng": 115.22})
    assert listing.status_code == 200
    assert any(i["id"] == inc_id for i in listing.json()["incidents"])

    ok = client.delete(f"/api/v1/incidents/{inc_id}")
    assert ok.status_code == 200

    gone = client.delete(f"/api/v1/incidents/{inc_id}")
    assert gone.status_code == 404


def test_incident_route_penalty(monkeypatch):
    from app.models.route import Coordinate
    from app.services.incident_service import incident_service

    inc = incident_service.report(-8.65, 115.22, "macet", "uji")
    try:
        penalty = incident_service.route_penalty([
            Coordinate(lat=-8.6501, lng=115.2201),
            Coordinate(lat=-8.6499, lng=115.2199),
        ])
        assert penalty > 0
    finally:
        incident_service.resolve(inc.id)


def test_incident_adat_schedule_flow():
    import time

    now = int(time.time())
    report = client.post("/api/v1/incidents", json={
        "lat": -8.52, "lng": 115.26, "incident_type": "upacara_adat",
        "description": "Ngaben di banjar",
        "start_at": now + 60,
        "end_at": now + 3600,
    })
    assert report.status_code == 200
    inc = report.json()["incident"]
    assert inc["incident_type"] == "upacara_adat"
    assert inc["type_label"] == "Upacara Adat"
    assert inc["scheduled"] is True
    assert inc["upcoming"] is True
    assert inc["icon"] == "🛕"
    assert client.delete(f"/api/v1/incidents/{inc['id']}").status_code == 200


def test_incident_adat_schedule_validation():
    report = client.post("/api/v1/incidents", json={
        "lat": -8.55, "lng": 115.20, "incident_type": "upacara_adat",
        "start_at": 2000,
        "end_at": 1000,
    })
    assert report.status_code == 400


def test_favorites_flow():
    create = client.post("/api/v1/favorites", json={
        "name": "Pulang Kerja",
        "origin": {"lat": -8.6525, "lng": 115.2193},
        "destination": {"lat": -8.5069, "lng": 115.2624},
        "priority": "traffic",
        "mode": "motorcycle",
    })
    assert create.status_code == 200
    fav_id = create.json()["favorite"]["id"]

    listing = client.get("/api/v1/favorites")
    assert listing.status_code == 200
    assert any(f["id"] == fav_id for f in listing.json()["favorites"])

    updated = client.patch(f"/api/v1/favorites/{fav_id}", params={"name": "Baru"})
    assert updated.status_code == 200 and updated.json()["name"] == "Baru"

    ok = client.delete(f"/api/v1/favorites/{fav_id}")
    assert ok.status_code == 200
    assert client.delete(f"/api/v1/favorites/{fav_id}").status_code == 404


def test_favorite_invalid_location_rejected():
    response = client.post("/api/v1/favorites", json={
        "name": "Jakarta",
        "origin": {"lat": -6.2, "lng": 106.8},
        "destination": {"lat": -8.5069, "lng": 115.2624},
    })
    assert response.status_code == 400


def test_history_last(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )
    client.post("/api/v1/route/predict", json={
        "origin": {"lat": -8.6525, "lng": 115.2193},
        "destination": {"lat": -8.5069, "lng": 115.2624},
        "preferences": {"priority": "time", "mode": "motorcycle"},
    })
    response = client.get("/api/v1/history/last", params={"limit": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["trips"][0]["origin"]["lat"] == -8.6525


def test_predict_with_mode(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )
    response = client.post("/api/v1/route/predict", json={
        "origin": {"lat": -8.6525, "lng": 115.2193},
        "destination": {"lat": -8.5069, "lng": 115.2624},
        "preferences": {"priority": "time", "mode": "motorcycle"},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["best_route"]["road_conditions"]["mode_label"] == "Motor"
    assert data["best_route"]["estimated_time_minutes"] < data["best_route"]["distance_km"] * 3


def test_track_start_and_status(monkeypatch):
    from app.services import osrm_service

    monkeypatch.setattr(
        osrm_service.osrm_service, "get_routes", lambda *args, **kwargs: MOCK_ROUTES[:1]
    )
    start = client.post("/api/v1/track/start", json={
        "origin": {"lat": -8.6525, "lng": 115.2193},
        "destination": {"lat": -8.5069, "lng": 115.2624},
        "mode": "car",
    })
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    assert start.json()["share_url"].endswith(session_id)

    status = client.get(f"/api/v1/track/{session_id}/status")
    assert status.status_code == 200
    snap = status.json()
    assert snap["status"] == "active"
    assert snap["progress_percent"] == 0
    assert snap["position"]["lat"] == -8.65


def test_track_status_not_found():
    response = client.get("/api/v1/track/tidak-ada/status")
    assert response.status_code == 404


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
