"""
services/weather_service.py — Open-Meteo Weather Service

Manages real-time weather data for the Smart Irrigation module.
This is the EXACT same logic from Irrigation/app.py, reorganized.

Key design:
  - Uses threading.Lock() for thread-safe state updates
  - Background thread fetches weather every 10 minutes
  - Another thread monitors sensor connection status
  - All state is stored in module-level dicts (no database needed)

Routes access weather via get_weather_data() and sensor state via get_sensor_data().
"""

import threading
import time
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────
DEFAULT_THRESHOLD  = 30
WEATHER_UPDATE_MIN = 10
RAIN_BLOCK_PERCENT = 70

# Crop moisture thresholds (same as original Irrigation/app.py)
CROP_THRESHOLDS = {
    "tomato": 60, "potato": 55, "rice": 80, "corn": 50, "onion": 40,
    "cabbage": 65, "mustard": 45, "eggplant": 55, "spinach": 70,
    "strawberry": 65, "chili": 50, "watermelon": 45, "wheat": 55,
    "garlic": 40, "ginger": 60, "cucumber": 65, "lentil": 45,
    "sunflower": 50, "carrot": 55, "radish": 50, "pumpkin": 55,
    "bitter_gourd": 60, "bottle_gourd": 65, "beans": 55,
}

# ── Thread-safe State ─────────────────────────────────────────────────
_lock = threading.Lock()

sensor_data = {
    "raw": 0, "moisture": 0, "pump": "OFF",
    "timestamp": "Waiting for data...", "connected": False,
    "mode": "manual", "manual_pump": "OFF",
    "threshold": DEFAULT_THRESHOLD, "crop": "custom",
}

weather_data = {
    "temp": "--", "humidity": "--",
    "description": "Enter your location →",
    "rain_chance": 0, "rain_blocked": False,
    "icon": "🌍", "last_update": "—",
    "city": "", "lat": None, "lon": None, "error": "",
}

location_state = {
    "city": "", "lat": None, "lon": None, "pending": False,
}

# Track background threads so we don't start them twice
_threads_started = False


# ── Public API ───────────────────────────────────────────────────────

def get_sensor_data() -> dict:
    """Return a copy of the current sensor state (thread-safe)."""
    with _lock:
        return dict(sensor_data)


def get_weather_data() -> dict:
    """Return a copy of the current weather state (thread-safe)."""
    with _lock:
        return dict(weather_data)


def get_crop_thresholds() -> dict:
    """Return the crop threshold map."""
    return CROP_THRESHOLDS


def update_sensor(raw: int, moisture: int):
    """
    Update sensor readings from IoT device POST.
    Called by routes/irrigation.py @ POST /irrigation/sensor
    """
    ts = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    with _lock:
        thr          = sensor_data["threshold"]
        rain_blocked = weather_data["rain_blocked"]
        sensor_data.update({
            "raw": raw, "moisture": moisture,
            "timestamp": ts, "connected": True,
        })
        if sensor_data["mode"] == "auto":
            sensor_data["pump"] = "OFF" if rain_blocked else ("ON" if moisture < thr else "OFF")
        else:
            sensor_data["pump"] = sensor_data["manual_pump"]


def set_mode(mode: str):
    """Set irrigation mode: 'auto' or 'manual'."""
    with _lock:
        sensor_data["mode"] = mode
        if mode == "manual":
            sensor_data["manual_pump"] = "OFF"
            sensor_data["pump"]        = "OFF"


def set_pump(state: str) -> bool:
    """Set pump state (manual mode only). Returns True if accepted."""
    state = state.upper()
    if state not in ("ON", "OFF"):
        return False
    with _lock:
        if sensor_data["mode"] == "manual":
            sensor_data["manual_pump"] = state
            sensor_data["pump"]        = state
            return True
    return False


def set_crop(crop: str, threshold: int = None):
    """Set crop type and auto-apply its moisture threshold."""
    crop = crop.lower().replace(" ", "_")
    thr  = threshold if threshold is not None else DEFAULT_THRESHOLD
    if crop in CROP_THRESHOLDS:
        thr = CROP_THRESHOLDS[crop]
    with _lock:
        sensor_data["crop"]      = crop
        sensor_data["threshold"] = thr
    return {"crop": crop, "threshold": thr}


def set_location(city: str, lat: float, lon: float):
    """
    Update the weather fetch location (triggers immediate weather refresh).
    Called when the user sets their location in the irrigation UI.
    """
    with _lock:
        location_state.update({"city": city, "lat": lat, "lon": lon, "pending": True})
        weather_data.update({
            "description": "Loading...", "icon": "🌀", "error": "", "city": city,
        })


def get_pump_command() -> str:
    """
    Return the pump command string for the IoT device to poll.
    Returns 'PUMP:ON' or 'PUMP:OFF'.
    """
    with _lock:
        mode         = sensor_data["mode"]
        moisture     = sensor_data["moisture"]
        manual       = sensor_data["manual_pump"]
        thr          = sensor_data["threshold"]
        rain_blocked = weather_data["rain_blocked"]

    if mode == "auto":
        return "PUMP:OFF" if rain_blocked else ("PUMP:ON" if moisture < thr else "PUMP:OFF")
    return f"PUMP:{manual}"


# ── Background Threads ────────────────────────────────────────────────

def start_background_threads():
    """
    Start weather fetch and connection monitor threads.
    Called ONCE from create_app(). Safe to call multiple times (idempotent).
    """
    global _threads_started
    if _threads_started:
        return
    _threads_started = True

    t1 = threading.Thread(target=_weather_loop, daemon=True)
    t2 = threading.Thread(target=_connection_monitor, daemon=True)
    t1.start()
    t2.start()
    logger.info("Irrigation background threads started")


def _weather_loop():
    """Periodically fetch weather for the current location."""
    while True:
        with _lock:
            lat     = location_state["lat"]
            lon     = location_state["lon"]
            city    = location_state["city"]
            if location_state["pending"]:
                location_state["pending"] = False

        if lat is not None and lon is not None:
            _do_fetch_weather(lat, lon, city)

        # Wait WEATHER_UPDATE_MIN minutes, but wake early if location changes
        for _ in range(WEATHER_UPDATE_MIN * 60 // 5):
            time.sleep(5)
            with _lock:
                if location_state["pending"]:
                    break


def _do_fetch_weather(lat: float, lon: float, city_name: str):
    """Fetch weather from Open-Meteo (no API key needed)."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code"
            f"&hourly=precipitation_probability"
            f"&forecast_days=1&timezone=auto"
        )
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            d       = r.json()
            current = d.get("current", {})
            temp    = round(current.get("temperature_2m", 0), 1)
            humidity = current.get("relative_humidity_2m", 0)
            wcode   = current.get("weather_code", 0)
            desc, icon = _parse_wmo(wcode)

            probs       = d.get("hourly", {}).get("precipitation_probability", [])
            rain_chance = round(max(probs[:6])) if probs else 0
            rain_blocked = rain_chance >= RAIN_BLOCK_PERCENT

            with _lock:
                weather_data.update({
                    "temp": temp, "humidity": humidity,
                    "description": desc, "rain_chance": rain_chance,
                    "rain_blocked": rain_blocked, "icon": icon,
                    "last_update": datetime.now().strftime("%H:%M"),
                    "city": city_name, "lat": lat, "lon": lon, "error": "",
                })
            logger.debug(f"Weather updated: {city_name} {desc} {temp}C Rain:{rain_chance}%")
        else:
            with _lock:
                weather_data["error"] = f"Weather API error {r.status_code}"
    except Exception as e:
        with _lock:
            weather_data["error"] = str(e)
        logger.warning(f"Weather fetch error: {e}")


def _connection_monitor():
    """Monitor if IoT sensor is still sending data (checks every 15 seconds)."""
    last_ts = ""
    while True:
        time.sleep(15)
        with _lock:
            cur = sensor_data["timestamp"]
        if cur == last_ts and cur != "Waiting for data...":
            with _lock:
                sensor_data["connected"] = False
        last_ts = cur


def _parse_wmo(code: int) -> tuple:
    """Map WMO weather code to (description, emoji)."""
    wmo = {
        0:  ("Clear Sky", "☀️"), 1: ("Mainly Clear", "🌤️"),
        2:  ("Partly Cloudy", "⛅"), 3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"), 48: ("Icy Fog", "🌫️"),
        51: ("Light Drizzle", "🌦️"), 53: ("Drizzle", "🌧️"),
        55: ("Heavy Drizzle", "🌧️"), 61: ("Slight Rain", "🌧️"),
        63: ("Rain", "🌧️"), 65: ("Heavy Rain", "🌧️"),
        71: ("Slight Snow", "❄️"), 73: ("Snow", "❄️"),
        75: ("Heavy Snow", "❄️"), 80: ("Rain Showers", "🌦️"),
        81: ("Rain Showers", "🌧️"), 82: ("Heavy Showers", "⛈️"),
        95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm+Hail", "⛈️"),
        99: ("Heavy Thunderstorm", "⛈️"),
    }
    return wmo.get(code, ("Unknown", "🌤️"))
