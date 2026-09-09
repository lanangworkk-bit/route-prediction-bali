#!/usr/bin/env python3
"""Generate sample route visualization (without downloading full map)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.traffic_service import traffic_service
from app.services.weather_service import weather_service
from app.services.visualization import visualization_service
from app.models.route import RouteResponse, RouteInfo, Coordinate
import asyncio


def create_sample_route():
    print("Generating sample route visualization...")

    origin = Coordinate(lat=-8.6500, lng=115.2167)  # Denpasar
    destination = Coordinate(lat=-8.3405, lng=115.0920)  # Kuta

    coords = [
        origin,
        Coordinate(lat=-8.6200, lng=115.2000),
        Coordinate(lat=-8.5800, lng=115.1800),
        Coordinate(lat=-8.5200, lng=115.1500),
        Coordinate(lat=-8.4500, lng=115.1200),
        destination,
    ]

    traffic_score = traffic_service.get_route_traffic_score(coords)

    weather = asyncio.run(weather_service.get_current_weather(origin.lat, origin.lng))
    weather_impact = weather_service.calculate_weather_impact(weather)

    if traffic_score >= 0.8:
        traffic_level = "Lancar"
    elif traffic_score >= 0.6:
        traffic_level = "Sedang"
    elif traffic_score >= 0.4:
        traffic_level = "Padat"
    else:
        traffic_level = "Macet"

    best_route = RouteInfo(
        distance_km=25.5,
        estimated_time_minutes=35.0,
        traffic_score=traffic_score,
        weather_impact=weather_impact.speed_factor,
        overall_score=78.5,
        coordinates=coords,
        road_conditions={
            "traffic_level": traffic_level,
            "weather_condition": weather.condition.value,
        },
    )

    alt_coords = [
        origin,
        Coordinate(lat=-8.6300, lng=115.2500),
        Coordinate(lat=-8.5500, lng=115.2200),
        Coordinate(lat=-8.4800, lng=115.1600),
        destination,
    ]

    alt_route = RouteInfo(
        distance_km=32.0,
        estimated_time_minutes=42.0,
        traffic_score=traffic_score * 0.9,
        weather_impact=weather_impact.speed_factor,
        overall_score=65.2,
        coordinates=alt_coords,
        road_conditions={
            "traffic_level": "Sedang",
            "weather_condition": weather.condition.value,
        },
    )

    response = RouteResponse(
        best_route=best_route,
        alternative_routes=[alt_route],
        weather_summary={
            "temperature": weather.temperature,
            "condition": weather.condition.value,
            "wind_speed": weather.wind_speed,
            "impact": weather_impact.recommendation,
        },
        generated_at="2024-01-15T10:30:00",
    )

    print(f"\nRoute Summary:")
    print(f"  Distance: {best_route.distance_km} km")
    print(f"  Estimated time: {best_route.estimated_time_minutes} min")
    print(f"  Traffic score: {best_route.traffic_score:.2f}")
    print(f"  Overall score: {best_route.overall_score}/100")
    print(f"  Weather: {weather.condition.value}")

    print("\nCreating map visualization...")
    map_obj = visualization_service.create_route_map(response)

    output_file = "data/processed/sample_route.html"
    visualization_service.save_map(map_obj, output_file)
    print(f"Map saved to: {output_file}")

    return output_file


if __name__ == "__main__":
    create_sample_route()
