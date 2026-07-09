"""
routes/crop.py — Crop Recommendation Blueprint

Routes (all protected with @login_required):
  GET  /crop                  → Crop recommendation form
  POST /crop/predict          → Run ML model, return top-5 results
  POST /crop/fertilizer-entry → Pre-fill fertilizer form with crop data

Business logic delegated to:
  - current_app.extensions['ml'].predict_crop()   (MLService)
  - services/mandi_service.py                     (quick price lookup)
"""

import json
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from utils.decorators import login_required
from utils.session_manager import get_current_user

crop_bp = Blueprint("crop", __name__)

# Crop list (same as original app.py — keep it here for template injection)
ALL_CROPS = [
    "apple", "banana", "blackgram", "chickpea", "coconut", "coffeea",
    "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize",
    "mango", "mothbeans", "mungbean", "muskmelon", "orange",
    "papaya", "pigeonpeas", "pomegranate", "rice", "watermelon",
]


@crop_bp.route("/crop")
@login_required
def crop_page():
    """Display the crop recommendation input form."""
    return render_template("crop/index.html")


@crop_bp.route("/crop/predict", methods=["POST"])
@login_required
def predict():
    """
    Run the crop recommendation ML model.

    Reads 7 soil/climate features from the POST form,
    calls ModelManager.predict_crop(), and renders results.
    Same logic as original crop_recommendation_system/app.py @/predict.
    """
    try:
        form_values = request.form.to_dict()
        features    = [float(v) for v in form_values.values()]

        ml     = current_app.extensions["ml"]
        result = ml.predict_crop(features)

        if "error" in result:
            return render_template("crop/index.html",
                                   prediction_text=f"Error: {result['error']}")

        return render_template(
            "crop/index.html",
            top_crop=result["top_crop"],
            labels=json.dumps(result["labels"]),
            values=json.dumps(result["values"]),
            prediction_text="Here are your top 5 recommended crops",
            inputs={k: float(v) for k, v in form_values.items()},
        )
    except Exception as e:
        return render_template("crop/index.html",
                               prediction_text=f"Error: {e}")


@crop_bp.route("/crop/fertilizer-entry", methods=["POST"])
@login_required
def fertilizer_entry():
    """
    Pre-fill the fertilizer form when coming from crop recommendation results.
    Passes the recommended crop and soil NPK values to the fertilizer template.
    Same logic as original @/fertilizer-entry.
    """
    top_crop = request.form.get("crop")
    N = request.form.get("N")
    P = request.form.get("P")
    K = request.form.get("K")

    if not top_crop:
        return redirect(url_for("crop.crop_page"))

    return render_template(
        "crop/fertilizer.html",
        source="crop",
        top_crop=top_crop.lower(),
        N=N, P=P, K=K,
        all_crops=ALL_CROPS,
    )
