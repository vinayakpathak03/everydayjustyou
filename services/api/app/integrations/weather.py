from functools import lru_cache

import httpx

from app.core.config import get_settings

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherClient:
    """OpenWeatherMap, free tier. Degrades gracefully rather than erroring: a
    missing API key or a failed request just means the Stylist proceeds without
    live weather context (falls back to the season the user/context supplies),
    not a broken chat turn — see app/services/stylist_tools.py."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def current(self, lat: float, lng: float) -> dict | None:
        if not self._api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    OPENWEATHERMAP_URL,
                    params={"lat": lat, "lon": lng, "appid": self._api_key, "units": "metric"},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError:
            return None
        return {
            "temp_c": data.get("main", {}).get("temp"),
            "condition": (data.get("weather") or [{}])[0].get("main"),
            "description": (data.get("weather") or [{}])[0].get("description"),
        }


@lru_cache
def get_weather_client() -> WeatherClient:
    settings = get_settings()
    return WeatherClient(settings.openweathermap_api_key)
