# Krishi-Sahayak — Professional Flask Architecture Refactor

## Background & Problem Analysis

The project currently exists as **4 separate, independently running Flask applications** with loose HTML files on disk:

| Current Module | Location | Status |
|---|---|---|
| Crop + Fertilizer + Mandi | `crop_recommendation_system/app.py` | Standalone Flask app (port 5000) |
| Disease Detection | `plant-disease-detection-system-main/app.py` | Standalone Flask app (port 5000) |
| Smart Irrigation | `Irrigation/app.py` | Standalone Flask app (port 5000) |
| AI Chatbot (Dialogflow webhook) | `Ai_bot_backend_agri/app.py` | Standalone Flask app (port 5000) |
| Landing / Login / Dashboard | Root `.html` files | **Direct file-system access** |
| Weather | `weather.html` | **Direct file-system access** |
| Nearby Finder | `nearby_finder.html` | **Direct file-system access** |
| Expense Calculator | `expense_calculator.html` | **Direct file-system access** |

**Core problems identified:**
- All 4 apps fight over port 5000 — only one can run at a time
- `dashboard.html` is file-opened directly — Firebase client auth doesn't protect it from URL bypass
- `login.js` redirects to `dashboard.html` (file path) not a Flask route
- API keys are scattered across 4 different `.env` files
- No centralized session or `@login_required`
- No service layer — business logic is mixed into routes

---

## User Review Required

> [!IMPORTANT]
> **Firebase Admin SDK**: The current architecture uses Firebase *client-side* JS auth only. The new backend session system requires the **Firebase Admin SDK** (`firebase-admin` Python package). This means you need to download your **Firebase Service Account JSON** from your Firebase Console → Project Settings → Service Accounts → Generate new private key. This JSON file must be placed in `instance/firebase_service_account.json` (never committed to git).

> [!IMPORTANT]
> **Chatbot Pivot**: The existing chatbot (`Ai_bot_backend_agri/app.py`) uses **Dialogflow Webhook + Groq LLaMA**. In the new unified app, the `/chatbot` route will serve the Dialogflow messenger UI (already embedded in dashboard.html), and the `/webhook` route will proxy the Groq LLM backend. The Dialogflow integration stays intact.

> [!WARNING]
> **IoT Sensor Endpoint**: The irrigation system has a `/sensor` POST endpoint that receives data from real hardware (ESP8266/Arduino). After migration, this endpoint moves to `/irrigation/sensor`. If you have physical hardware sending to `http://<ip>:5000/sensor`, you must update the hardware firmware URL to match.

> [!WARNING]
> **Disease Detection — 178 MB Keras Model**: `best_model_resume.keras` is very large. The new `MLService` will load it **once at startup**. First server start will be slower (~10–20 seconds depending on hardware). Subsequent requests will be fast.

---

## Open Questions

> [!IMPORTANT]
> **Q1 — Gemini API Key**: You have two different Gemini API keys across modules. `crop_recommendation_system/.env` uses `gemini_api = AIzaSyAOo...` and `plant-disease-detection-system-main/.env` / `Ai_bot_backend_agri/.env` use `api = AIzaSyDPk...`. Which key should be canonical? Or are they the same project key? Please verify before I write the `.env`.

> [!IMPORTANT]
> **Q2 — Profile Photo Storage**: Firebase Storage (frontend JS upload) or server-side upload to `uploads/` folder? The plan defaults to server-side upload saved to `uploads/` since no Firebase Storage SDK is currently in use.

> [!NOTE]
> **Q3 — Chatbot Type**: The dashboard embeds a **Dialogflow Messenger** widget (df-messenger), while `Ai_bot_backend_agri` is a Dialogflow **webhook backend**. Do you want the new `/chatbot` page to be a full-page embedded Dialogflow widget, or a custom chat interface backed directly by Groq LLaMA?

---

## Proposed Changes

The new project lives in **one directory** — `Krishi-Sahayak/` — as a single, unified Flask application. All old sub-app directories stay as-is (their models and assets will be referenced by path), but only one `app.py` runs.

### Final Folder Structure

```
Krishi-Sahayak/
│
├── run.py                          # [NEW] Entry point: python run.py
├── app.py                          # [NEW] App factory: create_app()
├── config.py                       # [NEW] Config classes (Dev/Prod)
├── requirements.txt                # [MODIFY] Unified requirements
├── .env                            # [NEW] Single .env for all secrets
├── .gitignore                      # [MODIFY] Add .env, instance/, uploads/
│
├── instance/                       # [NEW] Instance folder (git-ignored)
│   └── firebase_service_account.json
│
├── routes/                         # [NEW] All Blueprints
│   ├── __init__.py
│   ├── main.py                     # / and /dashboard
│   ├── auth.py                     # /login /register /logout /forgot-password
│   ├── crop.py                     # /crop  /crop/predict /crop/fertilizer-entry
│   ├── fertilizer.py               # /fertilizer /fertilizer/result
│   ├── disease.py                  # /disease /disease/predict
│   ├── irrigation.py               # /irrigation + all irrigation API routes
│   ├── mandi.py                    # /mandi + all mandi API routes
│   ├── weather.py                  # /weather
│   ├── chatbot.py                  # /chatbot /webhook (Dialogflow)
│   ├── profit.py                   # /profit
│   ├── nearby.py                   # /nearby
│   ├── profile.py                  # /profile /profile/edit /profile/upload-photo
│   └── settings.py                 # /settings
│
├── services/                       # [NEW] Service layer
│   ├── __init__.py
│   ├── firebase_service.py         # Firebase Admin SDK init
│   ├── auth_service.py             # verify_token(), create_session_cookie()
│   ├── ml_service.py               # ModelManager: loads all models once
│   ├── gemini_service.py           # Gemini API calls
│   ├── groq_service.py             # Groq LLaMA calls
│   ├── mandi_service.py            # Mandi API fetch logic
│   ├── weather_service.py          # Weather fetch (Open-Meteo)
│   └── profile_service.py          # Profile read/write (file-based, MongoDB-ready)
│
├── utils/                          # [NEW] Utilities
│   ├── __init__.py
│   ├── decorators.py               # @login_required, @role_required
│   ├── session_manager.py          # get_current_user(), set_session(), clear_session()
│   ├── validators.py               # Form validation helpers
│   └── helpers.py                  # format_text, secure_upload, etc.
│
├── templates/                      # [NEW] Unified Jinja2 templates
│   ├── base.html                   # Base layout with navbar + session user
│   ├── index.html                  # Landing page (/)
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── forgot_password.html
│   ├── dashboard.html
│   ├── crop/
│   │   ├── index.html
│   │   ├── fertilizer.html
│   │   └── fertilizer_result.html
│   ├── disease/
│   │   └── index.html
│   ├── irrigation/
│   │   └── index.html
│   ├── mandi/
│   │   └── index.html
│   ├── weather/
│   │   └── index.html
│   ├── chatbot/
│   │   └── index.html
│   ├── profit/
│   │   └── index.html
│   ├── nearby/
│   │   └── index.html
│   ├── profile/
│   │   ├── view.html
│   │   └── edit.html
│   └── settings/
│       └── index.html
│
├── static/                         # [NEW] Unified static assets
│   ├── css/
│   │   ├── styles.css              # (copy from root)
│   │   ├── log.css                 # (copy from root)
│   │   └── irrigation/style.css    # (copy from Irrigation/static/)
│   ├── js/
│   │   ├── firebase.js             # (updated config)
│   │   ├── dashboard.js
│   │   ├── irrigation/script.js    # (copy from Irrigation/static/)
│   │   └── wb-cold-storage-data.js
│   └── images/
│       ├── logo.png
│       ├── forest-agriculture.jpg
│       ├── img1.jpeg ... img4.jpeg
│       └── default_avatar.png
│
├── uploads/                        # [NEW] Profile photo uploads (git-ignored)
│
├── trained_models/                 # [NEW] Symlink / copy of all model files
│   ├── crop_model.pkl
│   ├── crop_le.pkl
│   ├── ideal_npk.csv
│   └── disease_model.keras         # (symlink to avoid duplicating 178 MB)
│
└── logs/                           # [NEW] Application logs
    └── app.log
```

---

### Component 1 — Entry Point & App Factory

#### [NEW] run.py
Simple entry point that calls `create_app()` and runs the server.

#### [NEW] app.py (App Factory)
- `create_app(config_name)` function
- Registers all Blueprints
- Initializes Firebase Admin SDK via `firebase_service.py`
- Loads all ML models via `ml_service.py` (stored in `app.extensions`)
- Configures Flask session (secret key from `.env`)
- Registers error handlers (403, 404, 500)

#### [NEW] config.py
```python
class Config:              # Base
class DevelopmentConfig:   # DEBUG=True
class ProductionConfig:    # DEBUG=False, SESSION_COOKIE_SECURE=True
```
All secrets loaded from `.env` via `python-dotenv`.

#### [NEW] .env
```ini
# Flask
SECRET_KEY=your-very-long-random-secret
FLASK_ENV=development
FLASK_DEBUG=True

# Firebase
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=smart-agriculture-637af.firebaseapp.com
FIREBASE_PROJECT_ID=smart-agriculture-637af
FIREBASE_STORAGE_BUCKET=smart-agriculture-637af.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=1075169089402
FIREBASE_APP_ID=1:1075169089402:web:6d021a17bf2ca7457b28c3
FIREBASE_SERVICE_ACCOUNT_PATH=instance/firebase_service_account.json

# ML Models
CROP_MODEL_PATH=trained_models/crop_model.pkl
CROP_LE_PATH=trained_models/crop_le.pkl
CROP_NPK_CSV=trained_models/ideal_npk.csv
DISEASE_MODEL_PATH=trained_models/disease_model.keras

# External APIs
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
MANDI_API_KEY=579b464db66ec23bdd...

# Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=5242880   # 5MB
```

---

### Component 2 — Services Layer

#### [NEW] services/firebase_service.py
- Initializes Firebase Admin SDK with service account JSON
- Exposes `verify_id_token(id_token)` → returns user dict

#### [NEW] services/auth_service.py
- `login_user(id_token)` → calls Firebase Admin `verify_id_token`, builds session dict
- `logout_user()` → clears Flask session
- `get_firebase_config()` → returns dict of public Firebase config (for Jinja2 templates)

#### [NEW] services/ml_service.py — ModelManager
```python
class ModelManager:
    def load_all(self):           # Called once at app startup
        self.crop_model   = pickle.load(...)
        self.crop_le      = pickle.load(...)
        self.npk_df       = pd.read_csv(...)
        self.disease_model = tf.keras.models.load_model(...)
    
    def predict_crop(self, features) -> dict
    def predict_disease(self, img_path) -> tuple[str, float]
    def recommend_fertilizer(self, crop, area, soil) -> dict
```
Stored in `app.extensions['ml']` — injected into blueprints via `current_app.extensions['ml']`.

#### [NEW] services/gemini_service.py
- `generate_fertilizer_explanation(crop, area, soil, ideal, fertilizer, language)` → text
- `generate_disease_treatment(plant_type, disease)` → (summary, details)

#### [NEW] services/groq_service.py
- `ask_agriculture_llm(user_query)` → text (from Groq LLaMA)
- `dialogflow_webhook_handler(req_json)` → Dialogflow fulfillment JSON

#### [NEW] services/mandi_service.py
- `fetch_prices(state, commodity, limit)` → dict
- `fetch_trend(commodity, state, days)` → dict
- `fetch_best_mandis(commodity, state)` → dict
- `quick_crop_price(crop, state)` → dict

#### [NEW] services/weather_service.py
- Weather thread + state management extracted from Irrigation app
- `get_weather_data()`, `set_location(city, lat, lon)` etc.

#### [NEW] services/profile_service.py
- File-based user profile store (JSON in `instance/profiles/`)
- Interface designed so MongoDB can replace it later:
  - `get_profile(uid)`, `update_profile(uid, data)`, `upload_photo(uid, file)`
- No route logic, no Flask imports

---

### Component 3 — Utils

#### [NEW] utils/decorators.py
```python
def login_required(f):
    """Redirect to /login if session has no uid."""

def role_required(*roles):
    """Check session role against allowed roles."""
```

#### [NEW] utils/session_manager.py
```python
def set_session(user_dict):
    """Store uid, email, display_name, photo_url, role, login_time."""

def get_current_user():
    """Return session dict or None."""

def clear_session():
    """Pop all session keys."""
```

#### [NEW] utils/validators.py
- `validate_email(email)`, `validate_password(pwd)` — used in auth routes

#### [NEW] utils/helpers.py
- `format_treatment_text(text)` → HTML (from disease app)
- `allowed_file(filename)` → bool
- `secure_upload(file, upload_folder)` → saved filename

---

### Component 4 — Blueprints (Routes)

#### [NEW] routes/auth.py — `auth_bp` prefix: `/`
| Method | Route | Description |
|---|---|---|
| GET | `/` | Landing page (public) |
| GET | `/login` | Login page |
| POST | `/login` | Firebase ID token → Flask session |
| GET | `/register` | Register page |
| POST | `/register` | Firebase ID token → session (after signup) |
| GET | `/logout` | Clear session → redirect `/` |
| GET | `/forgot-password` | Forgot password page |

**Auth flow (hybrid Firebase + Flask session):**
1. Frontend JS uses Firebase SDK to `signInWithEmailAndPassword`
2. On success, JS gets `user.getIdToken()` and POSTs it to `/login`
3. Flask backend calls Firebase Admin `verify_id_token(id_token)`
4. On success, Flask sets session: `{uid, email, display_name, photo_url, role, login_time}`
5. Returns JSON `{success: true}`, frontend JS redirects to `/dashboard`
6. All subsequent pages: `@login_required` checks `session['uid']`

#### [NEW] routes/main.py — `main_bp`
| GET | `/dashboard` | Protected — farmer dashboard |

#### [NEW] routes/crop.py — `crop_bp` prefix: `/crop`
| Method | Route | Description |
|---|---|---|
| GET | `/crop` | Crop recommendation form |
| POST | `/crop/predict` | Run ML model → results |
| POST | `/crop/fertilizer-entry` | Pre-fill fertilizer from crop result |

#### [NEW] routes/fertilizer.py — `fertilizer_bp` prefix: `/fertilizer`
| GET | `/fertilizer` | Direct fertilizer page |
| POST | `/fertilizer/result` | Compute + Gemini explanation |

#### [NEW] routes/disease.py — `disease_bp` prefix: `/disease`
| GET | `/disease` | Upload form |
| POST | `/disease/predict` | Run Keras model + Gemini treatment |

#### [NEW] routes/irrigation.py — `irrigation_bp` prefix: `/irrigation`
All existing irrigation routes moved under `/irrigation/` prefix:
- `/irrigation` (dashboard page)
- `/irrigation/data`, `/irrigation/sensor`, `/irrigation/command`
- `/irrigation/set_mode`, `/irrigation/set_pump`, `/irrigation/set_crop`
- `/irrigation/geo_search`, `/irrigation/geo_reverse`, `/irrigation/set_location`
- `/irrigation/ping`

IoT background threads started in `create_app()`.

#### [NEW] routes/mandi.py — `mandi_bp` prefix: `/mandi`
- `/mandi` (page)
- `/mandi/api/prices`, `/mandi/api/trend`, `/mandi/api/best-mandis`, `/mandi/api/crop-price`

#### [NEW] routes/weather.py — `weather_bp`
- `/weather` — serves the weather page template

#### [NEW] routes/chatbot.py — `chatbot_bp`
- `/chatbot` — serves Dialogflow messenger embed page
- `/webhook` — Dialogflow fulfillment webhook (Groq LLaMA handler)

#### [NEW] routes/profit.py — `profit_bp`
- `/profit` — Farm expense & profit calculator

#### [NEW] routes/nearby.py — `nearby_bp`
- `/nearby` — Nearby finder

#### [NEW] routes/profile.py — `profile_bp` prefix: `/profile`
- `GET /profile` — View profile
- `GET/POST /profile/edit` — Edit name, phone, state, district, language
- `POST /profile/upload-photo` — Upload profile picture
- `POST /profile/change-password` — Firebase `sendPasswordResetEmail` trigger

#### [NEW] routes/settings.py — `settings_bp`
- `GET /settings` — Settings page (theme, language, notifications, about)

---

### Component 5 — Templates Strategy

**All existing HTML templates are preserved — only minimal changes:**
1. Wrap each in Jinja2 `{% extends "base.html" %}` block (or inline the base layout)
2. Replace hardcoded `href="http://127.0.0.1:5000/..."` with `{{ url_for(...) }}`
3. Replace `href="dashboard.html"` with `{{ url_for('main.dashboard') }}`
4. Add `{{ config.FIREBASE_CONFIG | tojson }}` injection for firebase.js

**base.html** provides:
- Navbar with `{{ session.display_name }}` and profile photo
- Flash message rendering
- Consistent `<head>` (Bootstrap, fonts, CSS)

---

### Component 6 — Security Improvements

1. **Flask session** signed with `SECRET_KEY` — cannot be tampered
2. **`@login_required`** on every blueprint route except auth
3. **File upload security**: `allowed_file()` extension check + `secure_filename()` + size limit
4. **No direct HTML access**: All pages served via Flask routes
5. **CSRF protection**: Flask-WTF (optional, can be added per form)
6. **Session cookie flags**: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`

---

### Component 7 — Role System (Prepared)

```python
# In session:
session['role'] = 'farmer'   # 'guest', 'farmer', 'admin'

# Decorator:
@role_required('farmer', 'admin')
def crop_page(): ...
```

Default flow:
- Unauthenticated → role = `guest` (can only see `/`, `/login`, `/register`, `/forgot-password`)
- After login → role = `farmer` (full access)
- Admin role prepared but not activated

---

### Component 8 — MongoDB Readiness

`profile_service.py` is designed with a clean interface:
```python
class ProfileServiceBase:
    def get_profile(self, uid: str) -> dict: ...
    def update_profile(self, uid: str, data: dict) -> bool: ...

class FileProfileService(ProfileServiceBase):    # Current implementation
    ...

class MongoProfileService(ProfileServiceBase):   # Future — drop-in replacement
    ...
```

Routes call `profile_service.get_profile(uid)` — **zero route changes needed** when swapping to MongoDB.

---

## Verification Plan

### Automated Tests
After each migration phase, run:
```bash
python run.py                    # Server starts without errors
curl http://localhost:5000/      # Landing page loads
curl http://localhost:5000/dashboard  # Returns 302 redirect to /login
```

### Manual Verification Checklist
- [ ] Landing page loads at `/`
- [ ] `/login` page loads, Firebase JS auth works, session is set
- [ ] `/dashboard` redirects to `/login` if not authenticated
- [ ] `/dashboard` loads correctly when authenticated
- [ ] `/crop` form submits and shows top-5 predictions
- [ ] `/fertilizer` form submits and shows Gemini explanation
- [ ] `/disease` file upload and prediction works
- [ ] `/irrigation` page loads, sensor data endpoint responds
- [ ] `/mandi` page loads with live prices
- [ ] `/weather` page loads
- [ ] `/chatbot` Dialogflow messenger renders
- [ ] `/webhook` returns valid Dialogflow fulfillment
- [ ] `/profit` expense calculator works
- [ ] `/nearby` finder page loads
- [ ] `/profile` shows user info
- [ ] `/profile/edit` saves changes
- [ ] `/settings` page loads
- [ ] `/logout` clears session and redirects

---

## Step-by-Step Migration Plan

> [!IMPORTANT]
> Each phase is **independently testable**. The project is never broken between phases.

### Phase 1 — Scaffold (Day 1)
Create all directories, `config.py`, `run.py`, app factory `app.py`, `.env`, `requirements.txt`. No routes yet — just a "Hello Krishi" at `/`.

### Phase 2 — Static Assets & Templates (Day 1)
Copy/reorganize CSS, JS, images into `static/`. Create `base.html`. Copy existing templates into `templates/` folders.

### Phase 3 — Service Layer & ML Manager (Day 2)
Write all `services/` files. `ml_service.py` loads models. Test model loading in isolation.

### Phase 4 — Utils (Day 2)
Write `decorators.py`, `session_manager.py`, `validators.py`, `helpers.py`.

### Phase 5 — Auth Blueprint (Day 3)
Implement auth routes. Update `login.js` to POST id_token to `/login`. Test login → session → redirect.

### Phase 6 — Main & Dashboard Blueprint (Day 3)
Dashboard route with `@login_required`. Session user passed to template.

### Phase 7 — Crop & Fertilizer Blueprints (Day 4)
Migrate all crop/fertilizer/mandi routes. Test each individually.

### Phase 8 — Disease Blueprint (Day 4)
Migrate disease detection. Test Keras model loading + prediction.

### Phase 9 — Irrigation Blueprint (Day 5)
Migrate all irrigation routes + background threads. Update hardware URL note.

### Phase 10 — Chatbot, Weather, Profit, Nearby (Day 5)
Migrate remaining informational/tool pages.

### Phase 11 — Profile & Settings (Day 6)
Full profile module with photo upload and edit.

### Phase 12 — Security Hardening & Final Review (Day 6)
Cookie flags, error handlers, upload validation, session timeout.
