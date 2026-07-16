"""
routes/fertilizer.py — Fertilizer Recommendation Blueprint

Routes:
  GET  /fertilizer         → Direct fertilizer input form
  POST /fertilizer/result  → Calculate NPK deficiency + Gemini explanation

Business logic delegated to:
  - current_app.extensions['ml'].recommend_fertilizer()
  - services/gemini_service.generate_fertilizer_explanation()
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from utils.decorators import login_required
from utils.session_manager import get_current_user
from services.gemini_service import generate_fertilizer_explanation
from services.mongodb_service import save_fertilizer_prediction

fertilizer_bp = Blueprint("fertilizer", __name__)

ALL_CROPS = [
    "apple", "banana", "blackgram", "chickpea", "coconut", "coffeea",
    "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize",
    "mango", "mothbeans", "mungbean", "muskmelon", "orange",
    "papaya", "pigeonpeas", "pomegranate", "rice", "watermelon",
]


@fertilizer_bp.route("/fertilizer")
@login_required
def fertilizer_page():
    """Direct access to fertilizer page (not from crop recommendation)."""
    return render_template(
        "crop/fertilizer.html",
        source="direct",
        all_crops=ALL_CROPS,
    )


@fertilizer_bp.route("/fertilizer/result", methods=["POST"])
@login_required
def fertilizer_result():
    """
    Calculate fertilizer recommendation and generate Gemini explanation.
    Same logic as original @/fertilizer-result.
    """
    crop     = request.form.get("crop")
    language = request.form.get("language", "english")

    if not crop:
        return redirect(url_for("fertilizer.fertilizer_page"))

    try:
        area = float(request.form.get("area", 1))
        soil = {
            "N": float(request.form.get("N", 0)),
            "P": float(request.form.get("P", 0)),
            "K": float(request.form.get("K", 0)),
        }
    except (TypeError, ValueError):
        return render_template("crop/fertilizer.html",
                               source="direct", all_crops=ALL_CROPS,
                               error="Invalid input values. Please enter numbers only.")

    # Get NPK recommendation from MLService
    ml     = current_app.extensions["ml"]
    result = ml.recommend_fertilizer(crop.lower(), area, soil)

    if "error" in result:
        return render_template("crop/fertilizer.html",
                               source="direct", all_crops=ALL_CROPS,
                               error=result["error"])

    # Generate Gemini AI explanation
    ai_explanation = generate_fertilizer_explanation(
        crop=crop, area=area, soil=soil,
        ideal=result["ideal"], fertilizer=result["fertilizer"],
        language=language,
    )

    user = get_current_user()
    if user:
        save_fertilizer_prediction(
            user_id=user["uid"],
            crop_type=crop,
            land_area_acre=area,
            nitrogen=soil["N"],
            phosphorus=soil["P"],
            potassium=soil["K"],
            language=language,
            fertilizer=result["fertilizer"],
            ai_explanation=ai_explanation,
        )

    return render_template(
        "crop/fertilizer_result.html",
        crop=crop, soil=soil,
        ideal=result["ideal"],
        deficiency=result["deficiency"],
        fertilizer=result["fertilizer"],
        area=area,
        ai_explanation=ai_explanation,
        language=language,
    )
