from enum import Enum

from pydantic import BaseModel, Field


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    FOG = "fog"
    STORM = "storm"


class WeatherData(BaseModel):
    temperature: float
    humidity: float
    condition: WeatherCondition
    visibility: float = Field(..., ge=0, description="Visibility in km")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    rain_probability: float = Field(..., ge=0, le=100)


class WeatherImpact(BaseModel):
    speed_factor: float = Field(
        ..., ge=0, le=1, description="Factor to multiply base speed"
    )
    visibility_impact: float = Field(..., ge=0, le=1)
    risk_level: str
    recommendation: str
