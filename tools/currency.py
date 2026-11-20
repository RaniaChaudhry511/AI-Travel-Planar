import math
import re

import requests
from agents import function_tool


@function_tool
def convert_currency(amount: float, from_code: str, to_code: str) -> str:
    """Convert an amount using the free open.er-api.com exchange-rate endpoint."""
    if not math.isfinite(amount) or amount < 0:
        return "Please provide a finite, non-negative amount to convert."

    source = from_code.strip().upper()
    target = to_code.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", source) or not re.fullmatch(r"[A-Z]{3}", target):
        return "Please use three-letter currency codes, such as PKR, USD, or EUR."
    if source == target:
        return f"{amount:,.2f} {source} = {amount:,.2f} {target}."

    try:
        response = requests.get(
            f"https://open.er-api.com/v6/latest/{source}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        return f"Sorry, I couldn't retrieve the exchange rate right now ({exc}). Please try again later."

    if not isinstance(data, dict):
        return "Sorry, the exchange-rate service returned an unexpected response. Please try again later."
    if data.get("result") != "success":
        return f"Sorry, the exchange-rate service couldn't convert {source}. Please check the currency code."
    rates = data.get("rates") or {}
    if not isinstance(rates, dict):
        return "Sorry, the exchange-rate service returned an unexpected response. Please try again later."
    rate = rates.get(target)
    if not isinstance(rate, (int, float)) or not math.isfinite(rate):
        return f"Sorry, no exchange rate for {target} is currently available."

    converted = amount * rate
    updated = data.get("time_last_update_utc", "unknown")
    return (
        f"{amount:,.2f} {source} ≈ {converted:,.2f} {target} "
        f"(rate: 1 {source} = {rate:,.6f} {target}; updated {updated}). "
        "Provider rates are indicative; your bank or card may use a different rate or fees."
    )
