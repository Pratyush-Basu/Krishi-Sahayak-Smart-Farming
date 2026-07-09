"""
routes/mandi.py — Live Mandi Price Blueprint

Routes:
  GET  /mandi                  → Mandi price page
  GET  /mandi/api/prices       → JSON: current prices
  GET  /mandi/api/trend        → JSON: 30-day price trend
  GET  /mandi/api/best-mandis  → JSON: top 5 markets by price
  GET  /mandi/api/crop-price   → JSON: quick price for one crop

All API routes preserved with same URL structure.
Business logic delegated to services/mandi_service.py.
"""

from flask import Blueprint, render_template, request, jsonify
from utils.decorators import login_required
from services.mandi_service import (
    fetch_prices, fetch_trend, fetch_best_mandis,
    quick_crop_price, resolve_commodity_name, MANDI_CROP_MAP,
)

mandi_bp = Blueprint("mandi", __name__)

ALL_CROPS = [
    "apple", "banana", "blackgram", "chickpea", "coconut", "coffeea",
    "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize",
    "mango", "mothbeans", "mungbean", "muskmelon", "orange",
    "papaya", "pigeonpeas", "pomegranate", "rice", "watermelon",
]


@mandi_bp.route("/mandi")
@login_required
def mandi_page():
    """Display the mandi price page."""
    return render_template("mandi/index.html", all_crops=ALL_CROPS)


@mandi_bp.route("/mandi/api/prices")
@login_required
def mandi_prices():
    """Return current mandi prices as JSON. Same as original @/mandi/api/prices."""
    state     = request.args.get("state", "West Bengal")
    commodity = request.args.get("commodity", None)
    limit     = int(request.args.get("limit", 50))

    # Map internal crop name → Agmarknet name
    if commodity and commodity.lower() in MANDI_CROP_MAP:
        commodity = MANDI_CROP_MAP[commodity.lower()]

    result = fetch_prices(state=state, commodity=commodity, limit=limit)
    return jsonify(result)


@mandi_bp.route("/mandi/api/trend")
@login_required
def mandi_trend():
    """Return price trend data as JSON. Same as original @/mandi/api/trend."""
    commodity = request.args.get("commodity", "Rice")
    state     = request.args.get("state", "West Bengal")
    days      = int(request.args.get("days", 30))

    if commodity.lower() in MANDI_CROP_MAP:
        commodity = MANDI_CROP_MAP[commodity.lower()]

    result = fetch_trend(commodity=commodity, state=state, days=days)
    return jsonify(result)


@mandi_bp.route("/mandi/api/best-mandis")
@login_required
def mandi_best():
    """Return top 5 markets for a commodity. Same as original @/mandi/api/best-mandis."""
    commodity = request.args.get("commodity", "Rice")
    state     = request.args.get("state", "West Bengal")

    if commodity.lower() in MANDI_CROP_MAP:
        commodity = MANDI_CROP_MAP[commodity.lower()]

    result = fetch_best_mandis(commodity=commodity, state=state)
    return jsonify(result)


@mandi_bp.route("/mandi/api/crop-price")
@login_required
def crop_price_quick():
    """Quick price lookup for a single crop. Same as original @/mandi/api/crop-price."""
    crop  = request.args.get("crop", "").lower()
    state = request.args.get("state", "West Bengal")
    result = quick_crop_price(crop=crop, state=state)
    return jsonify(result)
