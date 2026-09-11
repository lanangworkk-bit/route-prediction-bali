import os
from contextlib import suppress

os.environ["DATABASE_URL"] = "sqlite:///./test_route_prediction.db"
os.environ["TOMTOM_API_KEY"] = ""
os.environ["OPENWEATHERMAP_API_KEY"] = ""

import pytest

from app.ml import travel_time_model as tt_model


@pytest.fixture(autouse=True)
def clean_test_database():
    tt_model.travel_time_model.reset()
    yield
    with suppress(FileNotFoundError):
        os.remove("test_route_prediction.db")
