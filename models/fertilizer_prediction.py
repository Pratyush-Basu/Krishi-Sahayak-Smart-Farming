"""Fertilizer prediction document schema for MongoDB."""

from datetime import datetime, timezone


def _format_fertilizer_dict(fertilizer):
    """Format fertilizer recommendations as readable strings."""
    if not fertilizer:
        return "", ""
    names = []
    dosages = []
    for name, qty in fertilizer.items():
        names.append(str(name))
        dosages.append(f"{name}: {qty} kg")
    return ", ".join(names), "; ".join(dosages)


def build_fertilizer_prediction(
    user_id,
    crop_type,
    land_area_acre,
    nitrogen,
    phosphorus,
    potassium,
    language,
    fertilizer,
    ai_explanation="",
):
    """Build a fertilizer prediction document dict."""
    recommended_fertilizer, dosage = _format_fertilizer_dict(fertilizer)
    return {
        "user_id": user_id,
        "crop_type": crop_type,
        "land_area_acre": float(land_area_acre),
        "nitrogen": float(nitrogen),
        "phosphorus": float(phosphorus),
        "potassium": float(potassium),
        "language": language,
        "recommended_fertilizer": recommended_fertilizer or "None required",
        "dosage": dosage or "None required",
        "application_method": ai_explanation or "",
        "precautions": "",
        "created_at": datetime.now(timezone.utc),
    }
