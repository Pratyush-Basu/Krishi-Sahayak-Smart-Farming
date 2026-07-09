"""
routes/weather.py — Weather Page Blueprint

Routes:
  GET /weather → Weather information page (protected)

The weather.html page is served through Flask — no direct file access.
"""

from flask import Blueprint, render_template
from utils.decorators import login_required

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
@login_required
def weather_page():
    """Display the weather information page."""
    return render_template("weather/index.html")
