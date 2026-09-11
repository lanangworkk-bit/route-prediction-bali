import logging

import pandas as pd

from app.config import get_settings
from app.ml.feature_engineer import feature_engineer
from app.ml.route_scorer import route_scorer
from app.ml.traffic_predictor import traffic_predictor
from app.ml.travel_time_model import travel_time_model
from app.services.history_service import history_service

logger = logging.getLogger(__name__)


def _min_history_samples() -> int:
    return get_settings().ml_min_history_samples


def retrain_models() -> dict:
    """Retrain traffic + route + travel-time models, blending recorded trips
    with synthetic data.

    Real usage history acts as a bias-correction layer on top of the synthetic
    base dataset. Returns an evaluation report per model.
    """
    traffic_df, scorer_df = history_service.to_training_frames()
    time_rows = history_service.to_time_rows()

    traffic_samples = len(traffic_df)
    scorer_samples = len(scorer_df)
    time_samples = len(time_rows)

    min_samples = _min_history_samples()
    report = {
        "traffic_history_samples": traffic_samples,
        "route_history_samples": scorer_samples,
        "travel_time_history_samples": time_samples,
        "used_history": traffic_samples >= min_samples,
    }

    # Traffic model: synthetic base + real history (if enough).
    traffic_data = feature_engineer.create_training_data(n_samples=2000)
    if report["used_history"]:
        required = feature_engineer.feature_names + ["congestion"]
        history_subset = traffic_df[required]
        traffic_data = pd.concat([traffic_data, history_subset], ignore_index=True)
        logger.info(
            f"Blending {traffic_samples} historical traffic samples into training data"
        )

    traffic_predictor.history_samples = traffic_samples if report["used_history"] else 0
    report["traffic"] = traffic_predictor.train(data=traffic_data)

    # Route scorer: synthetic base + real history (if enough).
    scorer_data = route_scorer._generate_training_data(n_samples=1000)
    if scorer_samples >= min_samples:
        scorer_data = pd.concat([scorer_data, scorer_df], ignore_index=True)
        logger.info(
            f"Blending {scorer_samples} historical route samples into training data"
        )

    route_scorer.history_samples = scorer_samples if scorer_samples >= min_samples else 0
    report["route_scorer"] = route_scorer.train(data=scorer_data)

    # Travel-time model: purely supervised on REAL recorded trips.
    report["travel_time"] = travel_time_model.train(time_rows)

    return report
