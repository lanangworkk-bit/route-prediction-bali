from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TrafficLevel(str, Enum):
    FREE_FLOW = "free_flow"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    CONGESTED = "congested"


class TrafficData(BaseModel):
    road_name: str
    current_speed: float
    free_flow_speed: float
    congestion_level: float = Field(..., ge=0, le=1)
    timestamp: datetime
    location: dict = {}


class TrafficPrediction(BaseModel):
    road_segment: str
    predicted_congestion: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    time_window: str
    factors: dict = {}
