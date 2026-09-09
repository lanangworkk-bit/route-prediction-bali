from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Route Prediction API"
    debug: bool = True

    openweathermap_api_key: str = ""
    default_lat: float = -8.4095
    default_lng: float = 115.1889

    database_url: str = "sqlite:///./route_prediction.db"

    traffic_weight: float = 0.35
    distance_weight: float = 0.25
    time_weight: float = 0.25
    weather_weight: float = 0.15

    max_alternative_routes: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
