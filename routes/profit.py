"""
routes/profit.py — Farm Expense & Profit Calculator Blueprint

Routes:
  GET /profit → Farm expense and profit calculator page (protected)
"""

from flask import Blueprint, render_template
from utils.decorators import login_required

profit_bp = Blueprint("profit", __name__)


@profit_bp.route("/profit")
@login_required
def profit_page():
    """Display the farm expense & profit calculator."""
    return render_template("profit/index.html")
