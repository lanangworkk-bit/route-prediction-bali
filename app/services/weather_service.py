import requests
import logging
from datetime import datetime
from app.config import get_settings
from app.models.weather import WeatherData, WeatherCondition, WeatherImpact

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def get_current_weather(self, lat: float, lng: float) -> WeatherData:
        api_key = self.settings.openweathermap_api_key

        if not api_key:
            logger.warning("No OpenWeatherMap API key, using mock weather data")
            return self._get_mock_weather()

        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lng,
                "appid": api_key,
                "units": "metric",
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return WeatherData(
                temperature=data["main"]["temp"],
                humidity=data["main"]["humidity"],
                condition=self._map_condition(data["weather"][0]["main"]),
                visibility=data.get("visibility", 10000) / 1000,
                wind_speed=data["wind"]["speed"] * 3.6,
                rain_probability=data.get("rain", {}).get("1h", 0),
            )
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return self._get_mock_weather()

    def calculate_weather_impact(self, weather: WeatherData) -> WeatherImpact:
        speed_factor = 1.0
        visibility_impact = 0.0

        if weather.condition in [WeatherCondition.RAIN, WeatherCondition.HEAVY_RAIN]:
            speed_factor *= 0.7 if weather.condition == WeatherCondition.RAIN else 0.5
            visibility_impact = 0.3 if weather.condition == WeatherCondition.RAIN else 0.6
        elif weather.condition == WeatherCondition.FOG:
            speed_factor *= 0.6
            visibility_impact = 0.7
        elif weather.condition == WeatherCondition.STORM:
            speed_factor *= 0.4
            visibility_impact = 0.8

        if weather.visibility < 1:
            speed_factor *= 0.7
            visibility_impact = max(visibility_impact, 0.5)

        if weather.wind_speed > 50:
            speed_factor *= 0.8

        risk_level = "low"
        recommendation = "Kondisi cuaca normal, rute dapat dilalui dengan aman."

        if speed_factor < 0.6:
            risk_level = "high"
            recommendation = "Kondisi cuaca buruk. Pertimbangkan untuk menunda perjalanan."
        elif speed_factor < 0.8:
            risk_level = "medium"
            recommendation = "Hati-hati berkendara, kurangi kecepatan."

        return WeatherImpact(
            speed_factor=round(speed_factor, 2),
            visibility_impact=round(visibility_impact, 2),
            risk_level=risk_level,
            recommendation=recommendation,
        )

    def _map_condition(self, api_condition: str) -> WeatherCondition:
        mapping = {
            "Clear": WeatherCondition.CLEAR,
            "Clouds": WeatherCondition.CLOUDY,
            "Rain": WeatherCondition.RAIN,
            "Drizzle": WeatherCondition.RAIN,
            "Thunderstorm": WeatherCondition.STORM,
            "Snow": WeatherCondition.HEAVY_RAIN,
            "Mist": WeatherCondition.FOG,
            "Fog": WeatherCondition.FOG,
            "Haze": WeatherCondition.FOG,
        }
        return mapping.get(api_condition, WeatherCondition.CLEAR)

    def _get_mock_weather(self) -> WeatherData:
        return WeatherData(
            temperature=28.0,
            humidity=75.0,
            condition=WeatherCondition.CLEAR,
            visibility=10.0,
            wind_speed=12.0,
            rain_probability=10.0,
        )


weather_service = WeatherService()
