import logging
import os
import time

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.config import get_settings

logger = logging.getLogger(__name__)

# Features derivable from recorded real trips (trip_history).
FEATURE_COLS = [
    "distance_km",
    "traffic_score",
    "weather_impact",
    "hour",
    "day_of_week",
    "is_peak",
    "mode_factor",
]

# Outlier guards (menit/km) — di luar batas ini dianggap data rusak/multi-route.
MAX_MIN_PER_KM = 60.0
MAX_TRIP_MINUTES = 900.0
MAX_TRIP_KM = 200.0


class TravelTimeModel:
    """Supervised travel-time regression trained on REAL recorded trips.

    Predicts ETA (minutes) from {distance, traffic, weather, time-of-day}
    using Gradient Boosting. Confidence grows with the number of observed
    samples via a blend weight until it saturates at ai_blend_max_samples.
    """

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.is_trained = False
        self.samples = 0
        self.metrics: dict = {}
        self.trained_at: float | None = None
        self.model_path = "data/processed/travel_time_model.pkl"

    def can_predict(self) -> bool:
        return self.is_trained and self.samples >= self.settings.ml_min_history_samples

    def reset(self) -> None:
        self.model = None
        self.is_trained = False
        self.samples = 0
        self.metrics = {}
        self.trained_at = None

    def blend_weight(self) -> float:
        if self.samples <= 0:
            return 0.0
        return round(
            min(1.0, self.samples / self.settings.ai_blend_max_samples), 3
        )

    def train(self, rows: list[dict]) -> dict:
        clean = [
            r
            for r in rows
            if r.get("distance_km") and r.get("estimated_time_minutes")
            and r["distance_km"] > 0
            and 0 < r["estimated_time_minutes"] <= MAX_TRIP_MINUTES
            and r["distance_km"] <= MAX_TRIP_KM
            and r["estimated_time_minutes"] / r["distance_km"] <= MAX_MIN_PER_KM
        ]
        if len(clean) < 5:
            logger.info(
                f"Travel-time model needs >=5 real samples, found {len(clean)}"
            )
            self.samples = len(clean)
            return {"samples": self.samples, "trained": False}

        df = pd.DataFrame(clean)
        X = df[FEATURE_COLS].astype(float)
        y = df["estimated_time_minutes"].astype(float)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = GradientBoostingRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        self.is_trained = True
        self.samples = len(clean)
        self.trained_at = time.time()
        self.metrics = {
            "mae_minutes": round(float(mae), 2),
            "r2": round(float(r2), 3),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
        }
        self._save_model()
        logger.info(
            f"Travel-time model trained on {self.samples} real trips "
            f"(MAE {mae:.2f} min, R2 {r2:.3f})"
        )
        return {"samples": self.samples, "trained": True, **self.metrics}

    def predict(self, features: dict) -> float | None:
        """Predict travel time minutes; returns None if model unusable."""
        if not self.can_predict():
            return None
        try:
            frame = pd.DataFrame([{c: features[c] for c in FEATURE_COLS}])
            pred = float(self.model.predict(frame)[0])
            return max(1.0, round(pred, 2))
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"Travel-time predict failed: {e}")
            return None

    def info(self) -> dict:
        return {
            "trained": self.is_trained,
            "can_predict": self.can_predict(),
            "samples": self.samples,
            "blend_weight": self.blend_weight(),
            "metrics": self.metrics,
            "trained_at": self.trained_at,
            "features": FEATURE_COLS,
        }

    def _save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.is_trained = True
            logger.info(f"Travel-time model loaded from {self.model_path}")


travel_time_model = TravelTimeModel()
