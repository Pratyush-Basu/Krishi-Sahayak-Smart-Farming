"""
services/mandi_service.py — Live Mandi Price Service

All Mandi (agricultural market) price logic extracted from
crop_recommendation_system/app.py.

Functions:
  - fetch_prices()    : current prices for a commodity in a state
  - fetch_trend()     : 30-day price history for trend charts
  - fetch_best_mandis(): top 5 markets by modal price
  - quick_crop_price(): fast single-crop price lookup
"""

import os
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MANDI_BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# Internal crop name → Agmarknet API name (same as original)
MANDI_CROP_MAP = {
    "rice": "Rice", "maize": "Maize", "jute": "Jute",
    "cotton": "Cotton", "banana": "Banana", "mango": "Mango",
    "grapes": "Grapes", "watermelon": "Water Melon",
    "muskmelon": "Musk Melon", "papaya": "Papaya",
    "coconut": "Coconut", "orange": "Orange", "lentil": "Lentil",
    "blackgram": "Black Gram", "mungbean": "Green Gram",
    "kidneybeans": "Rajma", "chickpea": "Gram",
    "pigeonpeas": "Arhar (Tur/Red Gram)(Whole)",
    "mothbeans": "Moth", "pomegranate": "Pomegranate", "apple": "Apple",
}


def _get_api_key() -> str:
    """Get Mandi API key from environment."""
    return os.getenv("MANDI_API_KEY", "579b464db66ec23bdd0000014f18ed9dd8d74eeb7c8e0e65c8ce349c")


def resolve_commodity_name(crop_name: str) -> str | None:
    """
    Convert internal crop name to Agmarknet commodity name.
    Returns None if crop is not in the mandi map.
    """
    return MANDI_CROP_MAP.get(crop_name.lower())


def fetch_prices(state: str = "West Bengal", commodity: str = None, limit: int = 50) -> dict:
    """
    Fetch current mandi prices.

    Args:
        state:      Indian state name
        commodity:  Agmarknet commodity name (use resolve_commodity_name first)
        limit:      max number of records

    Returns:
        {"success": True, "data": [...]} or {"success": False, "error": "..."}
    """
    params = {
        "api-key": _get_api_key(),
        "format":  "json",
        "limit":   limit,
        "filters[state.keyword]": state,
    }
    if commodity:
        params["filters[commodity]"] = commodity

    try:
        res = requests.get(MANDI_BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        return {"success": True, "data": data.get("records", [])}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "API timeout. Please try again."}
    except Exception as e:
        logger.error(f"Mandi price fetch failed: {e}")
        return {"success": False, "error": str(e)}


def fetch_trend(commodity: str, state: str = "West Bengal", days: int = 30) -> dict:
    """
    Fetch price trend over last N days.

    Args:
        commodity: Agmarknet commodity name
        state:     Indian state name
        days:      number of past days to fetch

    Returns:
        {"success": True, "data": [{date, modal_price, min_price, max_price}, ...]}
    """
    all_records = []
    today = datetime.today()

    for i in range(days):
        date_str = (today - timedelta(days=i)).strftime("%d/%m/%Y")
        params = {
            "api-key": _get_api_key(),
            "format":  "json",
            "limit":   5,
            "filters[state.keyword]":  state,
            "filters[commodity]":      commodity,
            "filters[arrival_date]":   date_str,
        }
        try:
            res  = requests.get(MANDI_BASE_URL, params=params, timeout=15)
            recs = res.json().get("records", [])
            if recs:
                all_records.append({
                    "date":        date_str,
                    "modal_price": recs[0].get("modal_price", 0),
                    "min_price":   recs[0].get("min_price",   0),
                    "max_price":   recs[0].get("max_price",   0),
                })
        except Exception:
            pass

    all_records.reverse()
    return {"success": True, "data": all_records}


def fetch_best_mandis(commodity: str, state: str = "West Bengal") -> dict:
    """
    Get top 5 markets by modal price for a commodity.

    Returns:
        {"success": True, "data": [...top 5 records sorted by price...]}
    """
    result = fetch_prices(state=state, commodity=commodity, limit=100)
    if not result["success"]:
        return result

    sorted_records = sorted(
        result["data"],
        key=lambda x: float(x.get("modal_price", 0) or 0),
        reverse=True,
    )
    return {"success": True, "data": sorted_records[:5]}


def quick_crop_price(crop: str, state: str = "West Bengal") -> dict:
    """
    Quick single-crop price lookup for the crop recommendation result page.

    Args:
        crop:  internal crop name (e.g., "rice", "tomato")
        state: Indian state name

    Returns:
        dict with commodity, market, modal_price, min_price, max_price, date
    """
    commodity = MANDI_CROP_MAP.get(crop.lower())
    if not commodity:
        return {"success": False, "error": "Crop not in mandi list"}

    result = fetch_prices(state=state, commodity=commodity, limit=5)
    if not result["success"] or not result["data"]:
        return {"success": False, "error": "No price data found"}

    r = result["data"][0]
    return {
        "success":     True,
        "commodity":   r.get("commodity"),
        "market":      r.get("market"),
        "modal_price": r.get("modal_price"),
        "min_price":   r.get("min_price"),
        "max_price":   r.get("max_price"),
        "date":        r.get("arrival_date"),
    }
