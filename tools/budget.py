import math

from agents import function_tool


@function_tool
def calculate_trip_budget(
    days: int,
    travelers: int,
    flight: float,
    hotel_per_night: float,
    food_per_day: float,
    transport_per_day: float,
    activities: float,
    shopping: float,
    emergency_percent: float,
) -> str:
    """Estimate a trip budget; all amounts must use one currency."""
    if days < 1 or travelers < 1:
        return "Please enter at least one trip day and one traveler."
    amounts = {
        "flight": flight,
        "hotel per night": hotel_per_night,
        "food per day": food_per_day,
        "transport per day": transport_per_day,
        "activities": activities,
        "shopping": shopping,
        "emergency percentage": emergency_percent,
    }
    if any(not math.isfinite(value) or value < 0 for value in amounts.values()):
        return "Please enter finite, non-negative costs and an emergency percentage."
    if emergency_percent > 100:
        return "Please keep the emergency percentage at or below 100."

    nights = max(days - 1, 0)
    costs = {
        "Flights": flight * travelers,
        "Hotel": hotel_per_night * nights,
        "Food": food_per_day * days * travelers,
        "Transport": transport_per_day * days,
        "Activities": activities,
        "Shopping": shopping,
    }
    subtotal = sum(costs.values())
    costs["Emergency fund"] = subtotal * emergency_percent / 100
    total = sum(costs.values())
    per_day = total / days

    lines = [
        "Estimated trip budget (all amounts are in the same currency unit you entered):",
        *[f"- {label}: {value:,.2f}" for label, value in costs.items()],
        f"- Subtotal before emergency fund: {subtotal:,.2f}",
        f"Estimated total: {total:,.2f}",
        f"Estimated per day: {per_day:,.2f}",
        (
            "Assumptions: flight, food, and transport are per traveler/day where applicable; "
            "one shared hotel room is priced per night; activities and shopping are total-trip amounts. "
            f"Hotel nights are {nights} for a {days}-day trip."
        ),
    ]
    return "\n".join(lines)
