"""
routes/irrigation.py — Smart Irrigation Blueprint

All original Irrigation/app.py routes preserved under /irrigation/ prefix.
IoT hardware URL change: http://<ip>:5000/sensor → http://<ip>:5000/irrigation/sensor

Routes:
  GET  /irrigation              → Dashboard page
  GET  /irrigation/data         → JSON: sensor + weather data
  POST /irrigation/sensor       → IoT device sends soil moisture readings
  GET  /irrigation/command      → IoT device polls for pump command
  POST /irrigation/set_mode     → Switch auto/manual mode
  POST /irrigation/set_pump     → Toggle pump (manual mode)
  POST /irrigation/set_crop     → Set crop type + threshold
  GET  /irrigation/geo_search   → City search (Open-Meteo geocoding)
  GET  /irrigation/geo_reverse  → Reverse geocode lat/lon
  POST /irrigation/set_location → Set weather location
  GET  /irrigation/ping         → Health check for IoT device

State is managed by services/weather_service.py (thread-safe dicts).
"""

from flask import Blueprint, render_template, request, jsonify
from utils.decorators import login_required
from services import weather_service as ws
import requests

irrigation_bp = Blueprint("irrigation", __name__)


@irrigation_bp.route("/irrigation")
@login_required
def irrigation_page():
    """Display the smart irrigation control dashboard."""
    return render_template(
        "irrigation/index.html",
        crop_thresholds=ws.get_crop_thresholds(),
    )


@irrigation_bp.route("/irrigation/data")
@login_required
def data():
    """Return current sensor + weather state as JSON (polled by frontend JS)."""
    payload        = ws.get_sensor_data()
    wd             = ws.get_weather_data()
    thr            = payload["threshold"]
    payload["soil_status"] = (
        "Soil is Dry 🌵" if payload["moisture"] < thr else "Soil is Wet 💧"
    )
    payload["weather"] = wd
    return jsonify(payload)


@irrigation_bp.route("/irrigation/sensor", methods=["POST"])
def sensor():
    """
    IoT device (ESP8266/Arduino) POSTs soil moisture readings here.
    No @login_required — hardware devices can't authenticate via browser session.
    Uses a fixed endpoint the hardware firmware can call.
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"status": "error"}), 400
    ws.update_sensor(
        raw=int(body.get("raw", 0)),
        moisture=int(body.get("moisture", 0)),
    )
    return jsonify({"status": "ok"})


@irrigation_bp.route("/irrigation/command")
def command():
    """IoT device polls this to get pump ON/OFF command."""
    cmd = ws.get_pump_command()
    return cmd, 200, {"Content-Type": "text/plain"}


@irrigation_bp.route("/irrigation/set_mode", methods=["POST"])
@login_required
def set_mode():
    """Switch between 'auto' and 'manual' irrigation modes."""
    body = request.get_json()
    mode = body.get("mode", "auto") if body else "auto"
    ws.set_mode(mode)
    return jsonify({"status": "ok", "mode": mode})


@irrigation_bp.route("/irrigation/set_pump", methods=["POST"])
@login_required
def set_pump():
    """Toggle pump ON/OFF (manual mode only)."""
    body  = request.get_json()
    state = (body.get("pump", "OFF") if body else "OFF").upper()
    if state not in ("ON", "OFF"):
        return jsonify({"status": "error"}), 400
    success = ws.set_pump(state)
    return jsonify({"status": "ok" if success else "error (auto mode active)", "pump": state})


@irrigation_bp.route("/irrigation/set_crop", methods=["POST"])
@login_required
def set_crop():
    """Set the crop type and apply its recommended moisture threshold."""
    body = request.get_json()
    if not body:
        return jsonify({"status": "error"}), 400
    crop = body.get("crop", "custom")
    thr  = int(body.get("threshold", ws.DEFAULT_THRESHOLD))
    result = ws.set_crop(crop, thr)
    return jsonify({"status": "ok", **result})


@irrigation_bp.route("/irrigation/geo_search")
def geo_search():
    """City name autocomplete using Open-Meteo geocoding (no API key needed)."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=6&language=en&format=json"
        r   = requests.get(url, timeout=6)
        if r.status_code == 200:
            results = []
            for c in r.json().get("results", []):
                name    = c.get("name", "")
                state   = c.get("admin1", "")
                country = c.get("country", "")
                lat     = c.get("latitude")
                lon     = c.get("longitude")
                label   = f"{name}, {state}, {country}" if state else f"{name}, {country}"
                results.append({"label": label, "city": name, "country": country, "lat": lat, "lon": lon})
            return jsonify(results)
    except Exception as e:
        pass
    return jsonify([])


@irrigation_bp.route("/irrigation/geo_reverse")
def geo_reverse():
    """Reverse geocode lat/lon to city name using Nominatim."""
    try:
        lat = float(request.args.get("lat", 0))
        lon = float(request.args.get("lon", 0))
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10"
        headers = {"User-Agent": "KrishiSahayak/1.0"}
        r = requests.get(url, timeout=8, headers=headers)
        if r.status_code == 200:
            addr = r.json().get("address", {})
            city = (addr.get("city") or addr.get("town") or
                    addr.get("district") or addr.get("county") or
                    addr.get("state_district") or "")
            if city:
                return jsonify({"status": "ok", "city": city, "lat": lat, "lon": lon})
    except Exception as e:
        pass
    return jsonify({"status": "error", "city": ""})


@irrigation_bp.route("/irrigation/set_location", methods=["POST"])
def set_location():
    """Set the weather fetch location (city name or lat/lon coordinates)."""
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"status": "error"}), 400

    city = body.get("city", "").strip()
    lat  = body.get("lat")
    lon  = body.get("lon")

    if lat is not None and lon is not None:
        ws.set_location(city or f"{lat:.2f},{lon:.2f}", float(lat), float(lon))
        return jsonify({"status": "ok", "city": city})

    if not city:
        return jsonify({"status": "error", "msg": "City or coordinates required"}), 400

    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        r   = requests.get(url, timeout=6)
        if r.status_code == 200 and r.json().get("results"):
            c    = r.json()["results"][0]
            lat  = c["latitude"]
            lon  = c["longitude"]
            name = c.get("name", city)
            ws.set_location(name, lat, lon)
            return jsonify({"status": "ok", "city": name})
        return jsonify({"status": "error", "msg": f"City not found: {city}"}), 404
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@irrigation_bp.route("/irrigation/ping")
def ping():
    """Health check endpoint for IoT device."""
    return "pong", 200
