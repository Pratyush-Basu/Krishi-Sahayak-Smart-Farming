"""
services/groq_service.py — Groq LLaMA + Dialogflow Webhook Handler

Handles the Dialogflow webhook backend:
  - Receives Dialogflow webhook POST requests at /webhook
  - If intent = "get weather" → fetches Open-Meteo weather data
  - All other intents → sends to Groq LLaMA-3 for agricultural Q&A

This is the EXACT same logic from Ai_bot_backend_agri/app.py.
Only reorganized — nothing changed in the prompt or behavior.
"""

import os
import logging
import requests
from flask import jsonify

logger = logging.getLogger(__name__)

# Weather condition codes (same as original)
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 51: "Light drizzle", 61: "Rain", 63: "Moderate rain",
    65: "Heavy rain", 95: "Thunderstorm",
}


def handle_dialogflow_webhook(req_json: dict):
    """
    Main Dialogflow webhook handler.

    Called from routes/chatbot.py @ POST /webhook.
    Returns a Flask JSON response suitable for Dialogflow.

    Args:
        req_json: Parsed JSON body from Dialogflow

    Returns:
        Flask jsonify response with fulfillmentMessages
    """
    query_result = req_json.get("queryResult", {})
    intent       = query_result.get("intent", {}).get("displayName", "")
    user_query   = query_result.get("queryText", "")
    params       = query_result.get("parameters", {})

    # ── Weather Intent ───────────────────────────────────────────────
    city = params.get("geo-city")
    if intent.lower() == "get weather" and city:
        lat, lon = _get_coordinates(city)
        if not lat:
            return _df_text_response(f"City not found: {city}")
        data      = _get_weather(lat, lon)
        return _df_text_response(_format_weather(data, city))

    # ── All Other Intents → Groq LLaMA ───────────────────────────────
    return _df_text_response(_ask_llm(user_query))


# ── Internal Helpers ─────────────────────────────────────────────────

def _df_text_response(text: str):
    """
    Format a text string as a Dialogflow fulfillment response.
    Each non-empty line becomes a separate message bubble.
    """
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith(("•", "-", "*")):
            line = line[1:].strip()
        if line:
            lines.append(line)

    return jsonify({
        "fulfillmentMessages": [
            {"text": {"text": [line]}}
            for line in lines
        ]
    })


def _get_coordinates(city: str) -> tuple:
    """Get lat/lon for a city using OpenStreetMap Nominatim."""
    try:
        url     = f"https://nominatim.openstreetmap.org/search?city={city}&format=json&limit=1"
        headers = {"User-Agent": "KrishiSahayakBot"}
        data    = requests.get(url, headers=headers, timeout=6).json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.warning(f"Geocoding failed for {city}: {e}")
    return None, None


def _get_weather(lat: float, lon: float) -> dict:
    """Fetch current weather + 3-day forecast from Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true&"
        f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
        f"&timezone=auto"
    )
    return requests.get(url, timeout=8).json()


def _format_weather(data: dict, city: str) -> str:
    """Format weather data into a readable string for Dialogflow."""
    current   = data.get("current_weather", {})
    condition = WEATHER_CODES.get(current.get("weathercode", 0), "Unknown")

    daily    = data.get("daily", {})
    forecast = []
    for i in range(min(3, len(daily.get("time", [])))):
        forecast.append(
            f"{daily['time'][i]}: "
            f"{daily['temperature_2m_min'][i]}-{daily['temperature_2m_max'][i]}°C, "
            f"{daily['precipitation_sum'][i]} mm rain"
        )

    return (
        f"Weather Update – {city}\n\n"
        f"Temperature: {current.get('temperature')}°C\n"
        f"Condition: {condition}\n"
        f"Wind Speed: {current.get('windspeed')} km/h\n\n"
        f"Forecast:\n" + "\n".join(forecast)
    )


def _ask_llm(user_query: str) -> str:
    """
    Send agricultural question to Groq LLaMA-3.
    Same prompt as original Ai_bot_backend_agri/app.py.
    """
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            logger.warning("GROQ_API_KEY not set in .env")
            return "I'm unable to answer right now. Please try again later."

        client = Groq(api_key=api_key)

        prompt = f"""
You are KrishiSahayak, an agriculture assistant for Indian farmers.

Rules:
- Use very simple farmer-friendly language
- Write exactly 3 short sentences
- Each sentence must be on a new line
- Do NOT use bullets or symbols like •, -, *
- Do NOT use headings or markdown formatting
- Do NOT use emojis inside sentences

Question:
{user_query}
"""
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150,
        )
        text = completion.choices[0].message.content.strip()

        if len(text) < 30:
            raise ValueError("Response too short")

        return text

    except Exception as e:
        logger.error(f"Groq LLM error: {e}")
        return (
            "Add organic compost or manure to improve soil health.\n"
            "Practice crop rotation to maintain soil nutrients.\n"
            "Maintain proper irrigation and drainage for best results."
        )
