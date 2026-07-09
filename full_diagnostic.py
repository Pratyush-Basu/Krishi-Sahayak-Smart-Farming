"""Full diagnostic: test every route, template, service, import, and config."""
import warnings, os, sys
warnings.filterwarnings("ignore")

errors = []
warnings_list = []

def err(msg): errors.append(msg); print(f"  [FAIL] {msg}")
def warn(msg): warnings_list.append(msg); print(f"  [WARN] {msg}")
def ok(msg): print(f"  [OK]   {msg}")

print("=" * 60)
print("KRISHI-SAHAYAK FULL PROJECT DIAGNOSTIC")
print("=" * 60)

# ── 1. Check all imports ──────────────────────────────────────────
print("\n--- 1. IMPORT CHECKS ---")
modules = [
    ("flask", "Flask framework"),
    ("dotenv", "python-dotenv"),
    ("werkzeug", "Werkzeug utils"),
]
for mod, desc in modules:
    try:
        __import__(mod)
        ok(f"{desc} ({mod})")
    except ImportError:
        err(f"Missing: {desc} ({mod})")

# Optional modules
for mod, desc in [
    ("google.generativeai", "Gemini AI"),
    ("groq", "Groq API"),
    ("sklearn", "scikit-learn"),
    ("numpy", "NumPy"),
    ("pandas", "Pandas"),
]:
    try:
        __import__(mod)
        ok(f"{desc} ({mod})")
    except ImportError:
        warn(f"Optional missing: {desc} ({mod})")

# TF/Keras check
print("\n--- 1b. TENSORFLOW/KERAS CHECK ---")
tf_ok = False
try:
    import keras
    ok(f"Standalone keras: {keras.__version__}")
    tf_ok = True
except (ImportError, AttributeError):
    warn("Standalone keras not available")

if not tf_ok:
    try:
        import tensorflow as tf
        v = getattr(tf, '__version__', 'unknown')
        ok(f"TensorFlow: {v}")
        try:
            _ = tf.keras.models
            ok("tf.keras accessible")
            tf_ok = True
        except AttributeError:
            err("tf.keras NOT accessible (broken TF install)")
    except ImportError:
        warn("TensorFlow not installed - disease detection unavailable")

# ── 2. Check config and .env ─────────────────────────────────────
print("\n--- 2. CONFIG CHECK ---")
from config import get_config
cfg = get_config()
for key in ["SECRET_KEY", "FIREBASE_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY", "MANDI_API_KEY"]:
    val = getattr(cfg, key, "")
    if val:
        ok(f"{key} = {val[:8]}...")
    else:
        warn(f"{key} is empty")

# ── 3. Check file existence ──────────────────────────────────────
print("\n--- 3. FILE EXISTENCE ---")
required_files = {
    # Routes
    "routes/__init__.py": "Routes package",
    "routes/main.py": "Main blueprint",
    "routes/auth.py": "Auth blueprint",
    "routes/crop.py": "Crop blueprint",
    "routes/fertilizer.py": "Fertilizer blueprint",
    "routes/mandi.py": "Mandi blueprint",
    "routes/disease.py": "Disease blueprint",
    "routes/irrigation.py": "Irrigation blueprint",
    "routes/chatbot.py": "Chatbot blueprint",
    "routes/weather.py": "Weather blueprint",
    "routes/profit.py": "Profit blueprint",
    "routes/nearby.py": "Nearby blueprint",
    "routes/profile.py": "Profile blueprint",
    "routes/settings.py": "Settings blueprint",
    # Services
    "services/__init__.py": "Services package",
    "services/firebase_service.py": "Firebase service",
    "services/ml_service.py": "ML service",
    "services/gemini_service.py": "Gemini service",
    "services/groq_service.py": "Groq service",
    "services/mandi_service.py": "Mandi service",
    "services/weather_service.py": "Weather service",
    "services/profile_service.py": "Profile service",
    # Utils
    "utils/__init__.py": "Utils package",
    "utils/decorators.py": "Decorators",
    "utils/session_manager.py": "Session manager",
    "utils/helpers.py": "Helpers",
    "utils/validators.py": "Validators",
    # Templates
    "templates/index.html": "Landing page",
    "templates/dashboard.html": "Dashboard",
    "templates/auth/login.html": "Login page",
    "templates/auth/register.html": "Register page",
    "templates/auth/forgot_password.html": "Forgot password",
    "templates/crop/index.html": "Crop page",
    "templates/crop/fertilizer.html": "Fertilizer form",
    "templates/crop/fertilizer_result.html": "Fertilizer result",
    "templates/disease/index.html": "Disease page",
    "templates/irrigation/index.html": "Irrigation page",
    "templates/mandi/index.html": "Mandi page",
    "templates/chatbot/index.html": "Chatbot page",
    "templates/weather/index.html": "Weather page",
    "templates/profit/index.html": "Profit page",
    "templates/nearby/index.html": "Nearby page",
    "templates/profile/view.html": "Profile view",
    "templates/profile/edit.html": "Profile edit",
    "templates/settings/index.html": "Settings page",
    "templates/errors/403.html": "403 error page",
    "templates/errors/404.html": "404 error page",
    "templates/errors/500.html": "500 error page",
    # Static
    "static/css/log.css": "Login CSS",
    "static/css/styles.css": "Main CSS",
    "static/css/irrigation.css": "Irrigation CSS",
    "static/images/logo.png": "Logo",
    "static/images/default_avatar.svg": "Default avatar",
    "static/js/irrigation_script.js": "Irrigation JS",
    "static/js/wb-cold-storage-data.js": "Cold storage data",
    # ML Models
    "trained_models/crop_model.pkl": "Crop ML model",
    "trained_models/crop_le.pkl": "Crop label encoder",
    "trained_models/ideal_npk.csv": "NPK CSV",
    "trained_models/disease_model.keras": "Disease model",
    # Core
    "app.py": "App factory",
    "config.py": "Configuration",
    "run.py": "Entry point",
    ".env": "Environment vars",
}

for path, desc in required_files.items():
    if os.path.exists(path):
        ok(f"{desc}: {path}")
    else:
        err(f"MISSING: {desc}: {path}")

# ── 4. Create app and test routes ────────────────────────────────
print("\n--- 4. APP CREATION ---")
try:
    from app import create_app
    app = create_app()
    ok(f"App created, {len(list(app.url_map.iter_rules()))} routes registered")
except Exception as e:
    err(f"App creation FAILED: {e}")
    print("\nDIAGNOSTIC ABORTED - app cannot start")
    sys.exit(1)

# ── 5. Test all routes ───────────────────────────────────────────
print("\n--- 5. ROUTE TESTS (unauthenticated) ---")
public = [("/", 200), ("/login", 200), ("/register", 200), ("/forgot-password", 200), ("/irrigation/ping", 200)]
protected = ["/dashboard", "/crop", "/fertilizer", "/mandi", "/disease",
             "/irrigation", "/chatbot", "/weather", "/profit", "/nearby",
             "/profile", "/settings"]

with app.test_client() as c:
    for path, expected in public:
        try:
            r = c.get(path)
            if r.status_code == expected:
                ok(f"GET {path} -> {r.status_code}")
            else:
                err(f"GET {path} -> {r.status_code} (expected {expected})")
        except Exception as e:
            err(f"GET {path} CRASHED: {e}")

    for path in protected:
        try:
            r = c.get(path, follow_redirects=False)
            loc = r.headers.get("Location", "")
            if r.status_code == 302 and "/login" in loc:
                ok(f"GET {path} -> 302 /login (protected)")
            else:
                err(f"GET {path} -> {r.status_code} (expected 302 redirect)")
        except Exception as e:
            err(f"GET {path} CRASHED: {e}")

    # Test with session
    print("\n--- 6. ROUTE TESTS (authenticated) ---")
    with c.session_transaction() as sess:
        sess["uid"] = "test_user_123"
        sess["email"] = "test@test.com"
        sess["display_name"] = "Test Farmer"
        sess["photo_url"] = ""
        sess["role"] = "farmer"
        sess["login_time"] = "2025-01-01T00:00:00"
        sess["is_authenticated"] = True

    for path in protected:
        try:
            r = c.get(path)
            if r.status_code == 200:
                ok(f"GET {path} -> 200 (authed)")
            else:
                err(f"GET {path} -> {r.status_code} (authed, expected 200)")
        except Exception as e:
            err(f"GET {path} CRASHED (authed): {e}")

    # Test POST routes
    print("\n--- 7. POST ROUTE TESTS ---")
    post_routes = [
        ("/auth/session", {"idToken": "", "uid": "t", "email": "t@t.com", "display_name": "T"}, "json"),
        ("/crop/predict", {"Nitrogen": "90", "Phosphorus": "42", "Potassium": "43",
                           "temperature": "25", "humidity": "80", "ph": "6.5", "rainfall": "120"}, "form"),
        ("/irrigation/sensor", {"raw": 500, "moisture": 45}, "json"),
    ]
    for path, data, kind in post_routes:
        try:
            if kind == "json":
                r = c.post(path, json=data)
            else:
                r = c.post(path, data=data)
            if r.status_code in (200, 302):
                ok(f"POST {path} -> {r.status_code}")
            else:
                err(f"POST {path} -> {r.status_code}")
        except Exception as e:
            err(f"POST {path} CRASHED: {e}")

    # Test API routes
    print("\n--- 8. API ROUTE TESTS ---")
    api_routes = [
        "/mandi/api/prices?state=West+Bengal",
        "/mandi/api/crop-price?crop=rice&state=West+Bengal",
        "/irrigation/data",
        "/irrigation/command",
    ]
    for path in api_routes:
        try:
            r = c.get(path)
            if r.status_code == 200:
                ok(f"GET {path} -> 200")
            else:
                err(f"GET {path} -> {r.status_code}")
        except Exception as e:
            err(f"GET {path} CRASHED: {e}")

    # Test error pages
    print("\n--- 9. ERROR PAGES ---")
    r404 = c.get("/nonexistent-page-xyz")
    if r404.status_code == 404:
        ok("404 page works")
    else:
        err(f"404 page -> {r404.status_code}")

# ── 10. Check template url_for references ────────────────────────
print("\n--- 10. TEMPLATE URL_FOR CHECK ---")
import re
template_dir = "templates"
for root, dirs, files in os.walk(template_dir):
    for fname in files:
        if fname.endswith(".html"):
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Check for url_for references
            refs = re.findall(r"url_for\(['\"]([^'\"]+)['\"]\s*(?:,|\))", content)
            for ref in refs:
                # Check if the endpoint exists
                try:
                    with app.test_request_context():
                        from flask import url_for
                        url_for(ref)
                    # ok - endpoint exists
                except Exception:
                    err(f"Broken url_for('{ref}') in {fpath}")

# ── Summary ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"ERRORS:   {len(errors)}")
print(f"WARNINGS: {len(warnings_list)}")
if errors:
    print("\nERRORS TO FIX:")
    for i, e in enumerate(errors, 1):
        print(f"  {i}. {e}")
if warnings_list:
    print("\nWARNINGS (non-critical):")
    for i, w in enumerate(warnings_list, 1):
        print(f"  {i}. {w}")
if not errors:
    print("\nRESULT: ALL PASS - PROJECT IS FUNCTIONAL")
else:
    print(f"\nRESULT: {len(errors)} ISSUES NEED FIXING")
print("=" * 60)
