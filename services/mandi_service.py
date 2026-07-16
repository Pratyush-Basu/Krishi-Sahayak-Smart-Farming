"""
services/mandi_service.py — Live Mandi Price Service

All Mandi (agricultural market) price logic extracted from
crop_recommendation_system/app.py.

Functions:
  - fetch_prices()     : current prices for a commodity in a state
  - fetch_trend()      : price trend, bucketed by date from a single API call
  - fetch_best_mandis(): top 5 markets by modal price
  - quick_crop_price() : fast single-crop price lookup

NOTE ON THE User-Agent HEADER:
Manual curl tests against this API consistently succeeded in under a
second, while identical requests from Python's `requests` library
(default User-Agent: "python-requests/x.x.x") were timing out. Many
government/gateway APIs slow-path or throttle traffic that
self-identifies as a common scraping library, since that's a frequent
signature for bots — while curl's User-Agent doesn't trigger the same
treatment. Setting a browser-like/curl-like User-Agent below is a
direct test of that theory; if timeouts stop after this change, that
was the cause.

NOTE ON fetch_trend:
The upstream Agmarknet dataset ("Current Daily Price of Various
Commodities") has been observed to only return CURRENT-DAY records —
every record's arrival_date matches today, regardless of what date
filter is sent. So in practice, fetch_trend will usually return a
single data point (today) until the government dataset itself starts
carrying more than one day of history.
"""

import os
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MANDI_BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# Sent with every request — see note above. Mimics curl's default
# User-Agent, since curl reliably got fast responses in manual testing.
DEFAULT_HEADERS = {
    "User-Agent": "curl/8.4.0",
    "Accept": "*/*",
}

# Internal crop name → Agmarknet API name
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
    return os.getenv("MANDI_API_KEY", "579b464db66ec23bdd0000012220fcf4dbbb45c150f80cc50135581a")


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
        limit:      max number of records. Keep this modest (<=100) —
                    the upstream API has shown instability with very
                    large limits even when the total available records
                    is far smaller.

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
        res = requests.get(MANDI_BASE_URL, params=params, headers=DEFAULT_HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        return {"success": True, "data": data.get("records", [])}
    except requests.exceptions.Timeout:
        logger.error(f"Mandi price fetch timed out for state={state}, commodity={commodity}")
        return {"success": False, "error": "API timeout. Please try again."}
    except requests.exceptions.HTTPError as e:
        logger.error(f"Mandi price fetch HTTP error: {e}")
        return {"success": False, "error": f"Upstream API error: {e}"}
    except Exception as e:
        logger.error(f"Mandi price fetch failed: {e}")
        return {"success": False, "error": str(e)}


def fetch_trend(commodity: str, state: str = "West Bengal", days: int = 30) -> dict:
    """
    Fetch price trend, bucketed by date, from a single API call.

    Pulls the full available dataset for the state+commodity in one
    call, then buckets it by date in Python, rather than making one
    API call per day.

    Args:
        commodity: Agmarknet commodity name
        state:     Indian state name
        days:      cap on how far back to include, if the upstream
                    data ever carries more than one day

    Returns:
        {"success": True, "data": [{date, modal_price, min_price, max_price}, ...]}
        or {"success": False, "error": "..."}
    """
    params = {
        "api-key": _get_api_key(),
        "format":  "json",
        "limit":   100,  # comfortably covers a single state+commodity combo
        "filters[state.keyword]": state,
        "filters[commodity]":     commodity,
    }

    try:
        res = requests.get(MANDI_BASE_URL, params=params, headers=DEFAULT_HEADERS, timeout=15)
        res.raise_for_status()
        records = res.json().get("records", [])
    except requests.exceptions.Timeout:
        logger.error(f"Trend fetch timed out for {commodity}/{state}")
        return {"success": False, "error": "API timeout. Please try again."}
    except Exception as e:
        logger.error(f"Trend fetch failed for {commodity}/{state}: {e}")
        return {"success": False, "error": str(e)}

    # Group by date, average modal/min/max price across markets on that day
    by_date = {}
    for r in records:
        date_str = r.get("arrival_date")
        if not date_str:
            continue
        by_date.setdefault(date_str, []).append(r)

    trend = []
    for date_str, recs in by_date.items():
        modal_vals = [float(x.get("modal_price", 0) or 0) for x in recs]
        min_vals   = [float(x.get("min_price", 0) or 0) for x in recs]
        max_vals   = [float(x.get("max_price", 0) or 0) for x in recs]
        trend.append({
            "date":        date_str,
            "modal_price": round(sum(modal_vals) / len(modal_vals), 2),
            "min_price":   round(sum(min_vals) / len(min_vals), 2),
            "max_price":   round(sum(max_vals) / len(max_vals), 2),
        })

    # Sort chronologically and cap to requested window
    trend.sort(key=lambda r: datetime.strptime(r["date"], "%d/%m/%Y"))
    cutoff = datetime.today() - timedelta(days=days)
    trend = [r for r in trend if datetime.strptime(r["date"], "%d/%m/%Y") >= cutoff]

    return {"success": True, "data": trend}


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