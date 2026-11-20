import json
import os
from pathlib import Path

from agents import function_tool


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/tmp") if os.getenv("VERCEL") == "1" else BASE_DIR
PROFILE_PATH = DATA_DIR / "user_profile.json"
ALLOWED_PREFERENCES = {"budget_level", "food_preference", "travel_style", "home_currency"}


def _read_preferences() -> dict[str, str]:
    if not PROFILE_PATH.exists():
        return {}
    with PROFILE_PATH.open("r", encoding="utf-8") as profile_file:
        data = json.load(profile_file)
    if not isinstance(data, dict):
        raise ValueError("The saved profile must contain a JSON object.")
    return {str(key): str(value) for key, value in data.items()}


@function_tool
def save_preference(key: str, value: str) -> str:
    """Save a lasting budget_level, food_preference, travel_style, or home_currency."""
    normalized_key = key.strip().lower()
    normalized_value = value.strip()
    if normalized_key not in ALLOWED_PREFERENCES:
        return "Please use one of these preference keys: budget_level, food_preference, travel_style, home_currency."
    if not normalized_value:
        return "Please provide a non-empty preference value."

    try:
        preferences = _read_preferences()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f"I couldn't read the saved preferences ({exc}); no preference was changed."

    preferences[normalized_key] = normalized_value
    try:
        with PROFILE_PATH.open("w", encoding="utf-8") as profile_file:
            json.dump(preferences, profile_file, ensure_ascii=False, indent=2)
            profile_file.write("\n")
    except OSError as exc:
        return f"I couldn't save that preference ({exc}). Please check the project's file permissions."
    return f"Saved preference: {normalized_key} = {normalized_value}."


@function_tool
def get_preferences() -> str:
    """Load saved budget, food, travel-style, and home-currency preferences."""
    try:
        preferences = _read_preferences()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f"I couldn't read the saved preferences ({exc})."
    if not preferences:
        return "No saved travel preferences yet."
    return "Saved travel preferences:\n" + "\n".join(
        f"- {key}: {value}" for key, value in sorted(preferences.items())
    )
