"""
services/gemini_service.py — Gemini AI Integration

Handles two use cases:
  1. Fertilizer explanation — explains NPK recommendations to farmers
     (originally in crop_recommendation_system/gemini_helper.py)

  2. Disease treatment — provides treatment suggestions for detected diseases
     (originally in plant-disease-detection-system-main/app.py)

Uses the Gemini API key from .env (GEMINI_API_KEY).
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

# Gemini client — initialized once when module is first imported
_gemini_model = None


def _get_model():
    """Lazy-initialize the Gemini model (only when first called)."""
    global _gemini_model
    if _gemini_model is None:
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                logger.warning("GEMINI_API_KEY not set in .env")
                return None
            genai.configure(api_key=api_key)
            _gemini_model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("Gemini model initialized")
        except ImportError:
            logger.warning("google-generativeai not installed")
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
    return _gemini_model


def generate_fertilizer_explanation(
    crop: str, area: float, soil: dict, ideal: dict, fertilizer: dict, language: str = "english"
) -> str:
    """
    Generate a farmer-friendly fertilizer explanation using Gemini.

    Exact same logic as original crop_recommendation_system/gemini_helper.py.
    Moved here so the route stays clean.

    Args:
        crop:       crop name
        area:       land area in acres
        soil:       dict with N, P, K soil values
        ideal:      dict with ideal N, P, K values
        fertilizer: dict of fertilizer_name → quantity_kg
        language:   'english', 'hindi', or 'bengali'

    Returns:
        Formatted explanation string (markdown removed)
    """
    model = _get_model()
    if model is None:
        return "AI explanation unavailable. Please check your GEMINI_API_KEY in .env"

    fertilizer_text = ""
    if fertilizer:
        for name, qty in fertilizer.items():
            fertilizer_text += f"- {name}: {qty} kg\n"
    else:
        fertilizer_text = "No fertilizer required"

    prompt = f"""
You are an agriculture expert helping Indian farmers.

Explain the fertilizer recommendation in VERY SIMPLE language.
Avoid scientific or technical words.

Crop: {crop}
Land size: {area} acre

Soil nutrients:
Nitrogen: {soil['N']}
Phosphorus: {soil['P']}
Potassium: {soil['K']}

Ideal nutrients:
Nitrogen: {ideal['N']}
Phosphorus: {ideal['P']}
Potassium: {ideal['K']}

Recommended fertilizers:
{fertilizer_text}

Explain:
- What nutrient is low
- Which fertilizer to use
- How to apply
- When to apply
- After how many days apply again
- Advice for next 30-45 days
"""

    if language == "bengali":
        prompt += "\nExplain everything in very simple Bengali language."
    elif language == "hindi":
        prompt += "\nExplain everything in very simple Hindi language."
    else:
        prompt += "\nExplain everything in very simple English."

    try:
        response = model.generate_content(prompt)
        text = response.text
        text = text.replace("**", "")   # Remove markdown bold
        return text
    except Exception as e:
        logger.error(f"Gemini fertilizer explanation failed: {e}")
        return f"Could not generate AI explanation: {e}"


def generate_disease_treatment(plant_type: str, disease: str) -> tuple:
    """
    Generate treatment suggestions for a detected plant disease.

    Exact same logic as plant-disease-detection-system-main/app.py.
    Returns (summary, formatted_details).

    Args:
        plant_type: e.g. "tomato", "potato"
        disease:    e.g. "early blight"

    Returns:
        (short_summary: str, detailed_html: str) or (None, None) if healthy
    """
    if "healthy" in disease.lower():
        return None, None

    model = _get_model()
    if model is None:
        return "AI unavailable", "Check GEMINI_API_KEY in .env"

    summary_prompt = f"""You are an agricultural expert. A farmer detected {disease} in their {plant_type} plant.

Provide a SHORT summary (2-3 sentences max, under 50 words) of the most critical immediate action needed."""

    detail_prompt = f"""You are an agricultural expert. A farmer has detected {disease} in their {plant_type} plant.

Provide a detailed treatment recommendation with:
1. Immediate Actions (2-3 steps)
2. Chemical/Organic Treatment options
3. Preventive Measures (2-3 steps)

Keep it practical and actionable. Use bullet points."""

    try:
        summary_resp = model.generate_content(summary_prompt)
        summary = summary_resp.text.strip()

        detail_resp = model.generate_content(detail_prompt)
        details = _format_treatment_text(detail_resp.text)

        return summary, details

    except Exception as e:
        logger.error(f"Gemini disease treatment failed: {e}")
        return "Unable to fetch treatment suggestions.", "Please consult a local agricultural expert."


def _format_treatment_text(text: str) -> str:
    """
    Format Gemini markdown response to HTML.
    Exact same logic as plant-disease-detection-system-main/app.py.
    """
    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

    lines = text.split('\n')
    formatted = []
    in_list = False

    for line in lines:
        line = line.strip()
        if line.startswith('* '):
            if not in_list:
                formatted.append('<ul style="margin-left: 20px; margin-top: 10px;">')
                in_list = True
            formatted.append(f'<li style="margin-bottom: 8px;">{line[2:]}</li>')
        else:
            if in_list:
                formatted.append('</ul>')
                in_list = False
            if line:
                formatted.append(f'<p style="margin-bottom: 10px;">{line}</p>')

    if in_list:
        formatted.append('</ul>')

    return ''.join(formatted)
