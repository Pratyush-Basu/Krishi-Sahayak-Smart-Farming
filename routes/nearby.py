"""
routes/nearby.py — Nearby Finder Blueprint

Routes:
  GET /nearby → Nearby agri-service finder page (protected)
"""

from flask import Blueprint, render_template
from utils.decorators import login_required

nearby_bp = Blueprint("nearby", __name__)


@nearby_bp.route("/nearby")
@login_required
def nearby_page():
    """Display the nearby agricultural services finder."""
    return render_template("nearby/index.html")
