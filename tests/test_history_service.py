from app.services.history_service import history_service


def test_record_and_get_history():
    history_service.record_trip(
        origin_lat=-8.6500,
        origin_lng=115.2167,
        dest_lat=-8.3405,
        dest_lng=115.0920,
        distance_km=25.0,
        estimated_time_minutes=40.0,
        overall_score=82.0,
        traffic_score=0.8,
        weather_impact=0.9,
        priority="time",
        traffic_level="Lancar",
        weather_condition="clear",
        route_source="osrm",
    )

    history = history_service.get_history()
    assert len(history) == 1
    assert history[0]["distance_km"] == 25.0
    assert history[0]["overall_score"] == 82.0
    assert history[0]["route_source"] == "osrm"


def test_stats_empty():
    stats = history_service.get_stats()
    assert stats["total_trips"] == 0


def test_training_frames_empty_without_history():
    traffic_df, scorer_df = history_service.to_training_frames()
    assert traffic_df.empty
    assert scorer_df.empty


def test_training_frames_populated():
    history_service.record_trip(
        origin_lat=-8.6500,
        origin_lng=115.2167,
        dest_lat=-8.3405,
        dest_lng=115.0920,
        distance_km=30.0,
        estimated_time_minutes=50.0,
        overall_score=70.0,
        traffic_score=0.6,
        weather_impact=0.8,
        priority="traffic",
        traffic_level="Sedang",
        weather_condition="cloudy",
        route_source="osrm",
    )

    traffic_df, scorer_df = history_service.to_training_frames()

    assert not traffic_df.empty
    assert "congestion" in traffic_df.columns
    assert not scorer_df.empty
    assert "score_class" in scorer_df.columns
    assert scorer_df.iloc[0]["score_class"] == 2
    assert "road_quality" in scorer_df.columns
