import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
import logging
from app.ml.feature_engineer import feature_engineer

logger = logging.getLogger(__name__)


class TrafficPredictor:
    def __init__(self):
        self.model = None
        self.model_path = "data/processed/traffic_model.pkl"
        self.is_trained = False

    def train(self, data: pd.DataFrame = None):
        if data is None:
            logger.info("Generating synthetic training data...")
            data = feature_engineer.create_training_data(n_samples=2000)

        feature_columns = feature_engineer.feature_names
        X = data[feature_columns]
        y = data["congestion"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        logger.info(f"Model trained - MSE: {mse:.4f}, R2: {r2:.4f}")

        self.is_trained = True
        self._save_model()

        return {"mse": mse, "r2": r2}

    def predict(
        self,
        timestamp,
        lat: float,
        lng: float,
        temperature: float = 28.0,
        humidity: float = 75.0,
        wind_speed: float = 12.0,
        visibility: float = 10.0,
    ) -> float:
        if not self.is_trained:
            self._load_model()

        if not self.is_trained:
            logger.warning("Model not trained, using fallback prediction")
            return self._fallback_prediction(timestamp, lat, lng)

        features = feature_engineer.create_feature_vector(
            timestamp, lat, lng, temperature, humidity, wind_speed, visibility
        )

        prediction = self.model.predict(features)[0]
        return float(np.clip(prediction, 0, 1))

    def _fallback_prediction(self, timestamp, lat: float, lng: float) -> float:
        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        base = 0.2
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base += 0.4
        if day_of_week >= 5:
            base -= 0.1

        center_lat, center_lng = -8.6500, 115.2167
        dist = ((lat - center_lat) ** 2 + (lng - center_lng) ** 2) ** 0.5
        if dist < 0.05:
            base += 0.2

        return min(1.0, max(0, base))

    def _save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.is_trained = True
            logger.info(f"Model loaded from {self.model_path}")


traffic_predictor = TrafficPredictor()
