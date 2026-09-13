from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.ml.registry import registry
from app.ml.trainer import retrain_models
from app.ml.travel_time_model import TravelTimeModel, travel_time_model
from app.services.ai_eta_service import blend, is_enabled, refine_eta
from app.services.history_service import history_service


def _rows(n: int = 40) -> list[dict]:
    rows = []
    for i in range(n):
        dist = 5.0 + (i % 20)
        rows.append({
            "distance_km": dist,
            "traffic_score": 0.4 + (i % 5) * 0.1,
            "weather_impact": 0.8 + (i % 3) * 0.05,
            "hour": i % 24,
            "day_of_week": i % 7,
            "is_peak": 1 if 7 <= i % 24 <= 9 or 17 <= i % 24 <= 19 else 0,
            "mode_factor": [1.0, 0.85, 4.0][i % 3],
            "estimated_time_minutes": dist * 2.0 * [1.0, 0.85, 4.0][i % 3] + (i % 5),
        })
    return rows


def test_travel_time_not_trained_by_default():
    assert travel_time_model.samples == 0
    assert travel_time_model.predict({
        "distance_km": 10,
        "traffic_score": 0.5,
        "weather_impact": 1.0,
        "hour": 8,
        "day_of_week": 0,
        "is_peak": 1,
        "mode_factor": 1.0,
    }) is None


def test_travel_time_trains_and_predicts():
    model = TravelTimeModel()
    report = model.train(_rows(40))
    assert report["trained"] is True
    assert report["mae_minutes"] > 0
    assert model.can_predict() is True
    pred = model.predict({
        "distance_km": 12.0,
        "traffic_score": 0.6,
        "weather_impact": 0.9,
        "hour": 8,
        "day_of_week": 0,
        "is_peak": 1,
        "mode_factor": 1.0,
    })
    assert pred is not None and pred > 0
    assert model.blend_weight() > 0 and model.blend_weight() <= 1.0


def test_travel_time_requires_minimum_samples():
    model = TravelTimeModel()
    model.train(_rows(3))
    assert model.can_predict() is False


def test_retrain_report_includes_all_models():
    report = retrain_models()
    assert "traffic" in report
    assert "route_scorer" in report
    assert "travel_time" in report


def test_registry_info_shape():
    info = registry.info()
    assert "history_count" in info
    assert "travel_time" in info
    assert "traffic" in info
    assert "auto_retrain_threshold" in info


def test_travel_time_clock_features_match_history_feature_set():
    now = datetime.now()
    assert travel_time_model.info()["features"] == [
        "distance_km",
        "traffic_score",
        "weather_impact",
        "hour",
        "day_of_week",
        "is_peak",
        "mode_factor",
    ]
    assert now.hour in range(24)


@pytest.mark.parametrize("n_rows,expected", [(0, False), (50, True)])
def test_blend_weight_scales_with_samples(n_rows, expected):
    model = TravelTimeModel()
    if n_rows:
        model.train(_rows(n_rows))
    if expected:
        assert model.blend_weight() > 0
    else:
        assert model.blend_weight() == 0


def test_history_time_rows_schema():
    history_service.record_trip(
        origin_lat=-8.6525,
        origin_lng=115.2193,
        dest_lat=-8.5069,
        dest_lng=115.2624,
        distance_km=20.82,
        estimated_time_minutes=25.0,
        overall_score=70.0,
        traffic_score=0.5,
        weather_impact=1.0,
        priority="time",
        traffic_level="Sedang",
        weather_condition="Cerah",
        route_source="osrm",
    )
    rows = history_service.to_time_rows()
    assert len(rows) >= 1
    for row in rows:
        assert set(travel_time_model.info()["features"]) <= set(row.keys())
        assert "estimated_time_minutes" in row


def test_travel_time_persistence_roundtrip(tmp_path):
    first = TravelTimeModel()
    first.model_path = str(tmp_path / "model.pkl")
    first._meta_path = str(tmp_path / "meta.json")
    first.train(_rows(40))

    restored = TravelTimeModel()
    restored.model_path = first.model_path
    restored._meta_path = first._meta_path
    restored._load_model()

    assert restored.is_trained is True
    assert restored.samples == first.samples
    assert restored.info()["blend_weight"] == first.info()["blend_weight"]
    pred = restored.predict({
        "distance_km": 12.0,
        "traffic_score": 0.6,
        "weather_impact": 0.9,
        "hour": 8,
        "day_of_week": 0,
        "is_peak": 1,
        "mode_factor": 1.0,
    })
    assert pred is not None and pred > 0


# ============ Antigravity / Gemini ETA ============


def test_gemini_blend_returns_original_when_none():
    assert blend(60.0, None) == (60.0, {})


def test_gemini_blend_weighted():
    blended, meta = blend(60.0, 80.0, weight=0.5)
    assert blended == 70.0
    assert meta["provider"] == "antigravity"
    assert meta["gemini_weight"] == 0.5


def test_gemini_blend_clamps_extreme():
    blended, meta = blend(60.0, 1000.0, weight=0.5)
    assert blended < 120  # clamped by 1.8x


def test_gemini_disabled_without_key(monkeypatch):
    monkeypatch.setattr(
        "app.services.gemini_client.get_settings",
        lambda: Settings(gemini_api_key="", gemini_model="gemini-3.6-flash"),
    )
    assert is_enabled() is False
    assert refine_eta({"distance_km": 10}) == (None, None)


def test_refine_eta_parses_mocked_response(monkeypatch):
    fake_settings = Settings(gemini_api_key="test-key", gemini_model="gemini-3.6-flash")
    monkeypatch.setattr("app.services.gemini_client.get_settings", lambda: fake_settings)
    monkeypatch.setattr("app.services.ai_eta_service.is_enabled", lambda: True)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"eta_minutes": 42.5}'}]}}]
    }
    with patch("requests.post", return_value=mock_resp):
        eta, source = refine_eta({"distance_km": 10})
    assert eta == 42.5
    assert source == "gemini:gemini-3.6-flash"
