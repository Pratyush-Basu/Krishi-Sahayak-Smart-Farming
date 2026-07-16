"""
routes/history.py — Prediction History Blueprint

Routes:
  GET /history → Show all saved crop, fertilizer, and disease predictions
"""

from flask import Blueprint, render_template
from utils.decorators import login_required
from utils.session_manager import get_current_user
from services.mongodb_service import (
    get_crop_predictions,
    get_fertilizer_predictions,
    get_disease_predictions,
)

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
@login_required
def history_page():
    """Display prediction history for the logged-in user."""
    user = get_current_user()
    user_id = user["uid"]

    return render_template(
        "history/index.html",
        user=user,
        crop_predictions=get_crop_predictions(user_id),
        fertilizer_predictions=get_fertilizer_predictions(user_id),
        disease_predictions=get_disease_predictions(user_id),
    )
