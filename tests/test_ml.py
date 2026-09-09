import pytest
from datetime import datetime
from app.ml.feature_engineer import feature_engineer
from app.ml.traffic_predictor import traffic_predictor
from app.ml.route_scorer import route_scorer


def test_feature_engineer_time_features():
    timestamp = datetime(2024, 1, 15, 8, 30)
    features = feature_engineer.extract_time_features(timestamp)

    assert features["hour"] == 8
    assert features["day_of_week"] == 0
    assert features["is_weekend"] == 0
    assert features["is_morning_peak"] == 1


def test_feature_engineer_location_features():
    features = feature_engineer.extract_location_features(-8.6500, 115.2167)

    assert features["lat"] == -8.6500
    assert features["lng"] == 115.2167
    assert features["distance_to_center"] == 0.0


def test_feature_engineer_create_vector():
    timestamp = datetime(2024, 1, 15, 8, 30)
    vector = feature_engineer.create_feature_vector(timestamp, -8.6500, 115.2167)

    assert vector.shape == (1, 12)


def test_feature_engineer_training_data():
    data = feature_engineer.create_training_data(n_samples=100)

    assert len(data) == 100
    assert "congestion" in data.columns
    assert data["congestion"].between(0, 1).all()


def test_traffic_predictor_train():
    metrics = traffic_predictor.train()

    assert "mse" in metrics
    assert "r2" in metrics
    assert metrics["r2"] > 0


def test_traffic_predictor_predict():
    timestamp = datetime.now()
    prediction = traffic_predictor.predict(timestamp, -8.6500, 115.2167)

    assert 0 <= prediction <= 1


def test_route_scorer_train():
    metrics = route_scorer.train()

    assert "accuracy" in metrics
    assert metrics["accuracy"] > 0


def test_route_scorer_score():
    result = route_scorer.score_route(
        distance_km=15.0,
        time_minutes=25.0,
        traffic_score=0.7,
        weather_impact=0.9,
    )

    assert "score" in result
    assert "class" in result
    assert 0 <= result["score"] <= 100
