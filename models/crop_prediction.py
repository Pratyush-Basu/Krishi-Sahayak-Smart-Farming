"""Crop prediction document schema for MongoDB."""

from datetime import datetime, timezone


def build_crop_prediction(
    user_id,
    nitrogen,
    phosphorus,
    potassium,
    temperature,
    humidity,
    ph,
    rainfall,
    predicted_crop,
    confidence,
):
    """Build a crop prediction document dict."""
    return {
        "user_id": user_id,
        "nitrogen": float(nitrogen),
        "phosphorus": float(phosphorus),
        "potassium": float(potassium),
        "temperature": float(temperature),
        "humidity": float(humidity),
        "ph": float(ph),
        "rainfall": float(rainfall),
        "predicted_crop": predicted_crop,
        "confidence": float(confidence),
        "created_at": datetime.now(timezone.utc),
    }
