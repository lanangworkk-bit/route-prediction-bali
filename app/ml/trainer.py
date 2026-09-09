import logging

import pandas as pd

from app.ml.feature_engineer import feature_engineer
from app.ml.route_scorer import route_scorer
from app.ml.traffic_predictor import traffic_predictor
from app.services.history_service import history_service

logger = logging.getLogger(__name__)

MIN_HISTORY_SAMPLES = 10


def retrain_models() -> dict:
    """Retrain traffic + route models, blending recorded trips with synthetic data.

    Real usage history acts as a bias-correction layer on top of the synthetic
    base dataset. Returns an evaluation report per model.
    """
    traffic_df, scorer_df = history_service.to_training_frames()
    traffic_samples = len(traffic_df)
    scorer_samples = len(scorer_df)

    report = {
        "traffic_history_samples": traffic_samples,
        "route_history_samples": scorer_samples,
        "used_history": traffic_samples >= MIN_HISTORY_SAMPLES,
    }

    # Traffic model: synthetic base + real history (if enough).
    traffic_data = feature_engineer.create_training_data(n_samples=2000)
    if report["used_history"]:
        required = feature_engineer.feature_names + ["congestion"]
        history_subset = traffic_df[required]
        traffic_data = pd.concat([traffic_data, history_subset], ignore_index=True)
        logger.info(f"Blending {traffic_samples} historical traffic samples into training data")

    report["traffic"] = traffic_predictor.train(data=traffic_data)

    # Route scorer: synthetic base + real history (if enough).
    scorer_data = route_scorer._generate_training_data(n_samples=1000)
    if scorer_samples >= MIN_HISTORY_SAMPLES:
        scorer_data = pd.concat(
            [scorer_data, scorer_df], ignore_index=True
        )
        logger.info(f"Blending {scorer_samples} historical route samples into training data")

    report["route_scorer"] = route_scorer.train(data=scorer_data)

    return report
