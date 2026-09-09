"""Standalone retraining script.

Usage:
    python scripts/retrain.py [--min-samples N]

Retrains both ML models on a blend of synthetic data and recorded trip history.
"""

import argparse
import logging
import sys
from pathlib import Path

# Make `app` importable regardless of the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Retrain prediction models")
    parser.add_argument(
        "--min-samples",
        type=int,
        default=10,
        help="Minimum recorded trips required to blend history into training",
    )
    args = parser.parse_args()

    from app.ml import trainer

    trainer.MIN_HISTORY_SAMPLES = args.min_samples
    report = trainer.retrain_models()

    print("\n=== Retraining Report ===")
    for key, value in report.items():
        print(f"{key}: {value}")

    print("\nRetraining complete. Models saved to data/processed/.")


if __name__ == "__main__":
    main()
