from enum import Enum

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lng: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class RoutePriority(str, Enum):
    TIME = "time"
    DISTANCE = "distance"
    TRAFFIC = "traffic"


class RoutePreferences(BaseModel):
    avoid_tolls: bool = False
    avoid_highways: bool = False
    priority: RoutePriority = RoutePriority.TIME


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    preferences: RoutePreferences = RoutePreferences()


class RouteInfo(BaseModel):
    distance_km: float
    estimated_time_minutes: float
    traffic_score: float = Field(..., ge=0, le=1)
    weather_impact: float = Field(..., ge=0, le=1)
    overall_score: float = Field(..., ge=0, le=100)
    coordinates: list[Coordinate]
    road_conditions: dict = {}


class RouteResponse(BaseModel):
    best_route: RouteInfo
    alternative_routes: list[RouteInfo]
    weather_summary: dict
    generated_at: str
