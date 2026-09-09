#!/usr/bin/env python3
"""Script to train ML models and generate sample visualization."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ml.traffic_predictor import traffic_predictor
from app.ml.route_scorer import route_scorer
from app.ml.feature_engineer import feature_engineer
from app.services.map_service import map_service
from app.services.route_optimizer import route_optimizer
from app.services.visualization import visualization_service
from app.models.route import RouteRequest, Coordinate, RoutePreferences


def train_models():
    print("=" * 50)
    print("Training ML Models")
    print("=" * 50)

    print("\n[1/2] Training Traffic Predictor...")
    traffic_metrics = traffic_predictor.train()
    print(f"  - MSE: {traffic_metrics['mse']:.4f}")
    print(f"  - R2: {traffic_metrics['r2']:.4f}")

    print("\n[2/2] Training Route Scorer...")
    route_metrics = route_scorer.train()
    print(f"  - Accuracy: {route_metrics['accuracy']:.4f}")

    print("\nModels trained successfully!")
    return traffic_metrics, route_metrics


def generate_sample_route():
    print("\n" + "=" * 50)
    print("Generating Sample Route Visualization")
    print("=" * 50)

    print("\n[1/4] Loading map graph for Bali...")
    try:
        map_service.load_graph("Bali, Indonesia")
        print("  - Map graph loaded")
    except Exception as e:
        print(f"  - Warning: {e}")
        print("  - Using fallback routing")

    print("\n[2/4] Creating route request...")
    request = RouteRequest(
        origin=Coordinate(lat=-8.6500, lng=115.2167),  # Denpasar
        destination=Coordinate(lat=-8.3405, lng=115.0920),  # Kuta
        preferences=RoutePreferences(priority="time"),
    )
    print(f"  - Origin: {request.origin}")
    print(f"  - Destination: {request.destination}")

    print("\n[3/4] Finding best route...")
    import asyncio
    response = asyncio.run(route_optimizer.find_best_route(request))

    print(f"  - Best route found!")
    print(f"    * Distance: {response.best_route.distance_km} km")
    print(f"    * Estimated time: {response.best_route.estimated_time_minutes} min")
    print(f"    * Score: {response.best_route.overall_score}/100")
    print(f"    * Traffic: {response.best_route.road_conditions.get('traffic_level', 'N/A')}")
    print(f"    * Weather: {response.weather_summary.get('condition', 'N/A')}")

    print("\n[4/4] Creating map visualization...")
    map_obj = visualization_service.create_route_map(response)

    output_file = "data/processed/sample_route.html"
    visualization_service.save_map(map_obj, output_file)
    print(f"  - Map saved to: {output_file}")

    return output_file


def main():
    try:
        train_models()
        output_file = generate_sample_route()

        print("\n" + "=" * 50)
        print("DONE!")
        print("=" * 50)
        print(f"\nOpen the visualization: {output_file}")
        print("Start the API server: uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
