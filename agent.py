from agents import Agent
from config import gemini_model
from memory import get_preferences, save_preference
from prompts import SYSTEM_PROMPT
from tools import calculate_trip_budget, convert_currency, get_weather, web_search


agent = Agent(
    name="Travel Planner",
    instructions=SYSTEM_PROMPT,
    model=gemini_model,
    tools=[
        get_weather,
        convert_currency,
        calculate_trip_budget,
        web_search,
        save_preference,
        get_preferences,
    ],
)
