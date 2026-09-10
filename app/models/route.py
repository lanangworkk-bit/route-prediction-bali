from enum import Enum

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lng: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class RoutePriority(str, Enum):
    TIME = "time"
    DISTANCE = "distance"
    TRAFFIC = "traffic"


class RouteMode(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    WALKING = "walking"


class RoutePreferences(BaseModel):
    avoid_tolls: bool = False
    avoid_highways: bool = False
    priority: RoutePriority = RoutePriority.TIME
    mode: RouteMode = RouteMode.CAR


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    waypoints: list[Coordinate] = Field(
        default_factory=list,
        description="Optional intermediate stops in order (multi-stop routing)",
    )
    preferences: RoutePreferences = RoutePreferences()


class Instruction(BaseModel):
    type: str = ""
    modifier: str = ""
    road_name: str = ""
    instruction: str
    distance_km: float = 0
    time_minutes: float = 0


class LegSummary(BaseModel):
    start_lat: float = 0
    start_lng: float = 0
    distance_km: float = 0
    time_minutes: float = 0
    steps: int = 0


class RouteInfo(BaseModel):
    distance_km: float
    estimated_time_minutes: float
    traffic_score: float = Field(..., ge=0, le=1)
    weather_impact: float = Field(..., ge=0, le=1)
    overall_score: float = Field(..., ge=0, le=100)
    coordinates: list[Coordinate]
    instructions: list[Instruction] = []
    legs: list[LegSummary] = []
    road_conditions: dict = {}


class RouteResponse(BaseModel):
    best_route: RouteInfo
    alternative_routes: list[RouteInfo]
    waypoints: list[Coordinate] = []
    weather_summary: dict
    generated_at: str
