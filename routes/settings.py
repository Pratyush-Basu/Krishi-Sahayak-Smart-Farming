"""
routes/settings.py — Application Settings Blueprint

Routes:
  GET /settings → Settings page (protected)

Settings are currently placeholders (theme, language, notifications, etc.)
as specified in the requirements. Ready to be wired up when needed.
"""

from flask import Blueprint, render_template
from utils.decorators import login_required
from utils.session_manager import get_current_user

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
@login_required
def settings_page():
    """Display the application settings page."""
    user = get_current_user()
    return render_template("settings/index.html", user=user)
