"""Disease prediction document schema for MongoDB."""

from datetime import datetime, timezone


def build_disease_prediction(
    user_id,
    image_name,
    disease_name,
    confidence,
    treatment_summary,
    treatment_details,
):
    """Build a disease prediction document dict."""
    return {
        "user_id": user_id,
        "image_name": image_name,
        "disease_name": disease_name,
        "confidence": float(confidence),
        "treatment_summary": treatment_summary,
        "treatment_details": treatment_details,
        "created_at": datetime.now(timezone.utc),
    }
