import logging
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class RouteScorer:
    def __init__(self):
        self.model = None
        self.model_path = "data/processed/route_scorer.pkl"
        self.is_trained = False
        self.history_samples = 0
        self.last_metrics: dict = {}
        self.score_labels = {0: "poor", 1: "average", 2: "good", 3: "excellent"}

    def train(self, data: pd.DataFrame = None):
        if data is None:
            logger.info("Generating synthetic route training data...")
            data = self._generate_training_data()

        feature_columns = [
            "distance_km",
            "time_minutes",
            "traffic_score",
            "weather_impact",
            "road_quality",
        ]
        X = data[feature_columns]
        y = data["score_class"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        self.last_metrics = {"accuracy": round(float(accuracy), 3)}

        logger.info(f"Route scorer trained - Accuracy: {accuracy:.4f}")

        self.is_trained = True
        self._save_model()

        return {"accuracy": accuracy}

    def score_route(
        self,
        distance_km: float,
        time_minutes: float,
        traffic_score: float,
        weather_impact: float,
        road_quality: float = 0.8,
    ) -> dict:
        if not self.is_trained:
            self._load_model()

        if not self.is_trained:
            return self._fallback_scoring(
                distance_km, time_minutes, traffic_score, weather_impact
            )

        features = np.array(
            [[distance_km, time_minutes, traffic_score, weather_impact, road_quality]]
        )

        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]

        score_map = {0: 25, 1: 50, 2: 75, 3: 95}
        base_score = score_map.get(prediction, 50)

        confidence = float(max(probabilities))

        return {
            "score": base_score,
            "class": self.score_labels.get(prediction, "average"),
            "confidence": confidence,
            "probabilities": {
                self.score_labels[i]: round(float(p), 3)
                for i, p in enumerate(probabilities)
            },
        }

    def _fallback_scoring(
        self, distance_km: float, time_minutes: float, traffic_score: float, weather_impact: float
    ) -> dict:
        distance_score = max(0, 1 - (distance_km / 100))
        time_score = max(0, 1 - (time_minutes / 120))

        overall = (
            distance_score * 0.2
            + time_score * 0.2
            + traffic_score * 0.35
            + weather_impact * 0.25
        ) * 100

        if overall >= 80:
            score_class = "excellent"
        elif overall >= 60:
            score_class = "good"
        elif overall >= 40:
            score_class = "average"
        else:
            score_class = "poor"

        return {
            "score": round(overall, 2),
            "class": score_class,
            "confidence": 0.7,
            "probabilities": {},
        }

    def _generate_training_data(self, n_samples: int = 1000) -> pd.DataFrame:
        np.random.seed(42)

        data = {
            "distance_km": np.random.uniform(1, 80, n_samples),
            "time_minutes": np.random.uniform(5, 120, n_samples),
            "traffic_score": np.random.uniform(0, 1, n_samples),
            "weather_impact": np.random.uniform(0.4, 1, n_samples),
            "road_quality": np.random.uniform(0.5, 1, n_samples),
        }

        df = pd.DataFrame(data)

        score = (
            (1 - df["distance_km"] / 100) * 0.2
            + (1 - df["time_minutes"] / 120) * 0.2
            + df["traffic_score"] * 0.35
            + df["weather_impact"] * 0.25
        ) * 100

        df["score_class"] = pd.cut(
            score,
            bins=[0, 40, 60, 80, 100],
            labels=[0, 1, 2, 3],
            include_lowest=True,
        ).astype(int)

        return df

    def _save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.is_trained = True
            logger.info(f"Model loaded from {self.model_path}")


route_scorer = RouteScorer()
