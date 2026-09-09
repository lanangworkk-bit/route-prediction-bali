import os
from contextlib import suppress

os.environ["DATABASE_URL"] = "sqlite:///./test_route_prediction.db"
os.environ["TOMTOM_API_KEY"] = ""
os.environ["OPENWEATHERMAP_API_KEY"] = ""

import pytest


@pytest.fixture(autouse=True)
def clean_test_database():
    yield
    with suppress(FileNotFoundError):
        os.remove("test_route_prediction.db")
