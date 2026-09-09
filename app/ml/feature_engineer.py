from datetime import datetime

import numpy as np
import pandas as pd


class FeatureEngineer:
    def __init__(self):
        self.feature_names = [
            "hour",
            "day_of_week",
            "is_weekend",
            "is_morning_peak",
            "is_evening_peak",
            "lat",
            "lng",
            "distance_to_center",
            "temperature",
            "humidity",
            "wind_speed",
            "visibility",
        ]

    def extract_time_features(self, timestamp: datetime) -> dict:
        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        return {
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": 1 if day_of_week >= 5 else 0,
            "is_morning_peak": 1 if 7 <= hour <= 9 else 0,
            "is_evening_peak": 1 if 17 <= hour <= 19 else 0,
        }

    def extract_location_features(
        self, lat: float, lng: float, center_lat: float = -8.6500, center_lng: float = 115.2167
    ) -> dict:
        distance_to_center = ((lat - center_lat) ** 2 + (lng - center_lng) ** 2) ** 0.5

        return {
            "lat": lat,
            "lng": lng,
            "distance_to_center": distance_to_center,
        }

    def extract_weather_features(
        self, temperature: float, humidity: float, wind_speed: float, visibility: float
    ) -> dict:
        return {
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "visibility": visibility,
        }

    def create_feature_vector(
        self,
        timestamp: datetime,
        lat: float,
        lng: float,
        temperature: float = 28.0,
        humidity: float = 75.0,
        wind_speed: float = 12.0,
        visibility: float = 10.0,
    ) -> np.ndarray:
        time_features = self.extract_time_features(timestamp)
        location_features = self.extract_location_features(lat, lng)
        weather_features = self.extract_weather_features(
            temperature, humidity, wind_speed, visibility
        )

        all_features = {**time_features, **location_features, **weather_features}

        return np.array([all_features[name] for name in self.feature_names]).reshape(1, -1)

    def create_training_data(self, n_samples: int = 1000) -> pd.DataFrame:
        np.random.seed(42)

        data = {
            "hour": np.random.randint(0, 24, n_samples),
            "day_of_week": np.random.randint(0, 7, n_samples),
            "lat": np.random.uniform(-8.8, -8.0, n_samples),
            "lng": np.random.uniform(114.4, 115.8, n_samples),
            "temperature": np.random.uniform(22, 35, n_samples),
            "humidity": np.random.uniform(40, 95, n_samples),
            "wind_speed": np.random.uniform(0, 40, n_samples),
            "visibility": np.random.uniform(1, 15, n_samples),
        }

        df = pd.DataFrame(data)
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["is_morning_peak"] = ((df["hour"] >= 7) & (df["hour"] <= 9)).astype(int)
        df["is_evening_peak"] = ((df["hour"] >= 17) & (df["hour"] <= 19)).astype(int)

        center_lat, center_lng = -8.6500, 115.2167
        dist_lat = df["lat"] - center_lat
        dist_lng = df["lng"] - center_lng
        df["distance_to_center"] = ((dist_lat**2) + (dist_lng**2)) ** 0.5

        df["congestion"] = self._generate_synthetic_congestion(df)

        return df

    def _generate_synthetic_congestion(self, df: pd.DataFrame) -> np.ndarray:
        congestion = np.zeros(len(df))

        congestion += df["is_morning_peak"] * 0.3
        congestion += df["is_evening_peak"] * 0.35
        congestion += df["is_weekend"] * (-0.1)

        congestion += (df["distance_to_center"] < 0.05).astype(int) * 0.2
        congestion += (df["distance_to_center"] < 0.1).astype(int) * 0.1

        congestion += (df["humidity"] > 80).astype(int) * 0.05
        congestion += (df["visibility"] < 3).astype(int) * 0.1

        noise = np.random.normal(0, 0.05, len(df))
        congestion = np.clip(congestion + noise, 0, 1)

        return congestion


feature_engineer = FeatureEngineer()
