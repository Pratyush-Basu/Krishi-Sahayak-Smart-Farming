"""
routes/disease.py — Plant Disease Detection Blueprint

Routes:
  GET  /disease         → Upload form page
  POST /disease/predict → Upload image, run Keras model, get Gemini treatment

Business logic delegated to:
  - current_app.extensions['ml'].predict_disease()
  - services/gemini_service.generate_disease_treatment()
"""

import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, current_app
)
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from utils.helpers import allowed_file
from utils.session_manager import get_current_user
from services.gemini_service import generate_disease_treatment
from services.mongodb_service import save_disease_prediction

disease_bp = Blueprint("disease", __name__)

@disease_bp.route("/disease")
@login_required
def disease_page():
    """Display the plant disease detection upload form."""
    return render_template(
        "disease/index.html",
        prediction=None, confidence=None,
        treatment_summary=None, treatment_details=None,
    )


@disease_bp.route("/disease/predict", methods=["POST"])
@login_required
def predict():
    """
    Receive an uploaded leaf image, run the Keras CNN model,
    and fetch treatment suggestions from Gemini.

    Same logic as original plant-disease-detection-system-main/app.py @/predict.
    """
    file = request.files.get("file")

    if not file or not file.filename:
        return redirect(url_for("disease.disease_page"))

    if not allowed_file(file.filename):
        return render_template(
            "disease/index.html",
            prediction=None, confidence=None,
            treatment_summary="Invalid file type",
            treatment_details="Please upload a JPG, PNG, or JPEG image.",
        )

    # Save uploaded image temporarily
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    filename   = secure_filename(file.filename)
    image_path = os.path.join(upload_folder, f"disease_temp_{filename}")
    file.save(image_path)

    try:
        # Run ML prediction via ModelManager
        ml = current_app.extensions["ml"]
        prediction, confidence = ml.predict_disease(image_path)

        # Remove temp file after prediction
        if os.path.exists(image_path):
            os.remove(image_path)

        if prediction is None:
            return render_template(
                "disease/index.html",
                prediction=None, confidence=None,
                treatment_summary="Model not available",
                treatment_details="Disease detection model is not loaded. Check trained_models/ folder.",
            )

        # Parse plant type and disease from class name (e.g., "tomato_early blight")
        parts      = prediction.split("_", 1)
        plant_type = parts[0] if parts else "plant"
        disease    = parts[1] if len(parts) > 1 else prediction

        # Get Gemini treatment suggestions
        treatment_summary, treatment_details = generate_disease_treatment(plant_type, disease)

        user = get_current_user()
        if user:
            save_disease_prediction(
                user_id=user["uid"],
                image_name=filename,
                disease_name=disease,
                confidence=confidence,
                treatment_summary=treatment_summary,
                treatment_details=treatment_details,
            )

        return render_template(
            "disease/index.html",
            prediction=prediction,
            confidence=confidence,
            treatment_summary=treatment_summary,
            treatment_details=treatment_details,
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(image_path):
            os.remove(image_path)
        current_app.logger.exception("Disease prediction error")
        return render_template(
            "disease/index.html",
            prediction=None, confidence=None,
            treatment_summary=f"Prediction failed: {e}",
            treatment_details="Please try again with a clearer image.",
        )
