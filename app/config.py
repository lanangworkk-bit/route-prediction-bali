from functools import lru_cache

from pydantic_settings import BaseSettings

BALI_LAT_MIN, BALI_LAT_MAX = -8.85, -8.0
BALI_LNG_MIN, BALI_LNG_MAX = 114.4, 115.8


class Settings(BaseSettings):
    app_name: str = "Route Prediction API"
    debug: bool = True

    openweathermap_api_key: str = ""
    default_lat: float = -8.4095
    default_lng: float = 115.1889

    tomtom_api_key: str = ""
    tomtom_base_url: str = (
        "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative"
    )

    osrm_base_url: str = "https://router.project-osrm.org"
    map_load_timeout: int = 30

    database_url: str = "sqlite:///./route_prediction.db"

    traffic_weight: float = 0.35
    distance_weight: float = 0.25
    time_weight: float = 0.25
    weather_weight: float = 0.15

    max_alternative_routes: int = 3

    # -------- Realtime engine --------
    track_stream_interval_s: float = 5.0
    realtime_traffic_interval_s: float = 30.0
    ai_refresh_interval_s: float = 45.0

    # -------- AI / ML --------
    ml_min_history_samples: int = 10
    auto_retrain_threshold: int = 20
    ai_blend_max_samples: int = 100
    traffic_ml_blend_samples: int = 50

    # -------- Antigravity / Gemini ETA --------
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_eta_weight: float = 0.5

    # -------- Crowd-sourced hazard reports --------
    incident_ttl_hours: int = 2

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def public_config(self) -> dict:
        """Safe subset of settings exposed for the UI."""
        return {
            "app_name": self.app_name,
            "debug": self.debug,
            "tomtom_enabled": bool(self.tomtom_api_key),
            "openweathermap_enabled": bool(self.openweathermap_api_key),
            "osrm_base_url": self.osrm_base_url,
            "traffic_weight": self.traffic_weight,
            "distance_weight": self.distance_weight,
            "time_weight": self.time_weight,
            "weather_weight": self.weather_weight,
            "max_alternative_routes": self.max_alternative_routes,
            "track_stream_interval_s": self.track_stream_interval_s,
            "realtime_traffic_interval_s": self.realtime_traffic_interval_s,
            "ai_refresh_interval_s": self.ai_refresh_interval_s,
            "ml_min_history_samples": self.ml_min_history_samples,
            "auto_retrain_threshold": self.auto_retrain_threshold,
            "ai_blend_max_samples": self.ai_blend_max_samples,
            "gemini_enabled": bool(self.gemini_api_key),
            "gemini_model": self.gemini_model,
            "ai_provider": "antigravity" if self.gemini_api_key else "local",
            "incident_ttl_hours": self.incident_ttl_hours,
            "coverage": {
                "lat_min": BALI_LAT_MIN,
                "lat_max": BALI_LAT_MAX,
                "lng_min": BALI_LNG_MIN,
                "lng_max": BALI_LNG_MAX,
            },
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
