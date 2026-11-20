import requests
from agents import function_tool


@function_tool
def get_weather(city: str) -> str:
    """Get the current conditions and up to seven days of forecast for a city."""
    city = city.strip()
    if not city:
        return "Please provide a city name so I can check the weather."

    try:
        location_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        location_response.raise_for_status()
        locations = location_response.json().get("results") or []
        if not locations:
            return f"I couldn't find a location for '{city}'. Please check the city name."

        location = locations[0]
        forecast_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 7,
                "timezone": "auto",
            },
            timeout=10,
        )
        forecast_response.raise_for_status()
        data = forecast_response.json()
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        return f"Sorry, I couldn't retrieve the weather for {city} right now ({exc}). Please try again later."

    current = data.get("current")
    if not current:
        return f"Sorry, the weather service returned no current forecast for {city}."

    place = ", ".join(part for part in (location.get("name"), location.get("country")) if part)
    lines = [
        f"Weather for {place or city} (Open-Meteo):",
        f"Now: {current.get('temperature_2m', 'N/A')}°C, feels like {current.get('apparent_temperature', 'N/A')}°C; "
        f"humidity {current.get('relative_humidity_2m', 'N/A')}%, wind {current.get('wind_speed_10m', 'N/A')} km/h.",
    ]
    daily = data.get("daily") or {}
    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []
    rain_chances = daily.get("precipitation_probability_max") or []
    for index, date in enumerate(dates):
        high = highs[index] if index < len(highs) else "N/A"
        low = lows[index] if index < len(lows) else "N/A"
        rain = rain_chances[index] if index < len(rain_chances) else "N/A"
        lines.append(f"{date}: {low}–{high}°C, precipitation chance up to {rain}%.")
    lines.append("Forecast coverage is limited to the dates listed; longer-range weather is not a live forecast.")
    return "\n".join(lines)
