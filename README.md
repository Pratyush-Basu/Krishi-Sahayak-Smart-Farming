# 🌱 Krishi–সহায়ক &nbsp;|&nbsp; Smart Farming Platform

> **AI + IoT–powered decision-support system for Indian farmers.**
> Crop recommendation, fertilizer optimization, plant disease detection, smart irrigation, live mandi prices, weather intelligence, and an AI chatbot — unified into a single Flask web application.

---

## 📌 Project Overview

**Krishi–সহায়ক** (Krishi-Sahayak) is a full-stack smart farming platform built with Flask, designed to help farmers make data-driven decisions. The system integrates machine learning models, large language models (Gemini & Groq LLaMA-3), real-time IoT sensor data, and government market-price APIs into a cohesive web dashboard.

### What It Does

| Problem                                  | Our Solution                                                              |
|------------------------------------------|---------------------------------------------------------------------------|
| Which crop should I grow?                | ML model analyzes soil NPK, pH, temperature, humidity & rainfall → top-5 crops |
| How much fertilizer do I need?           | NPK deficiency calculator + Gemini AI explanation in English/Hindi/Bengali |
| Is my plant diseased?                    | CNN (Keras) classifies 15 disease classes from leaf photos + Gemini treatment plan |
| When should I irrigate?                  | ESP8266 soil-moisture sensor → auto/manual pump control with rain-blocking  |
| What's the market price today?           | Live Agmarknet API integration — prices, trends, best mandis             |
| I need farming advice                    | Dialogflow chatbot backed by Groq LLaMA-3.1-8B for agricultural Q&A     |
| What's the weather forecast?             | Open-Meteo API — current conditions + 6-hour rain probability            |

---

## 🎯 Key Features

- 🌾 **Crop Recommendation** — Scikit-learn model predicts top-5 crops from 7 soil/climate features with confidence scores
- 🧪 **Fertilizer Optimization** — NPK deficiency analysis against ideal values, per-acre fertilizer calculation, with Gemini AI-generated farmer-friendly explanations (multilingual: EN/HI/BN)
- 🍃 **Plant Disease Detection** — TensorFlow/Keras CNN (178 MB, 15 classes) classifies leaf images and generates treatment recommendations via Gemini
- 💧 **Smart Irrigation** — Real-time ESP8266 soil-moisture monitoring, crop-specific thresholds, auto/manual pump control, rain-based blocking (≥70% probability)
- 📊 **Live Mandi Prices** — Government Agmarknet API for current commodity prices, price trends, and best-market rankings across Indian states
- 🤖 **AI Chatbot** — Dialogflow Messenger widget with Groq LLaMA-3.1-8B backend for agriculture Q&A and Open-Meteo weather queries
- 🌤️ **Weather Intelligence** — Open-Meteo forecast integration with geocoding, reverse-geocoding, and background polling
- 💰 **Profit Calculator** — Farm expense and profit estimation tool
- 📍 **Nearby Services** — Agricultural service finder using geolocation
- 👤 **User Profiles** — Firebase Authentication, profile management, photo uploads, password reset
- 📜 **Prediction History** — MongoDB-backed history of all crop, fertilizer, and disease predictions per user
- ⚙️ **Settings** — Theme, language, and notification preferences

---

## 🏗️ Architecture

The application follows the **Flask App Factory** pattern (`create_app()` in `app.py`) with a clean separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                    Flask App (app.py)                │
│  create_app() → Config → Firebase → ML Models →     │
│  Background Threads → Blueprints → Error Handlers   │
├──────────┬──────────┬──────────┬────────────────────┤
│  routes/ │ services/│  models/ │  utils/            │
│ 14 BPs   │ 8 svcs   │ 3 schemas│ decorators/helpers │
├──────────┴──────────┴──────────┴────────────────────┤
│                    templates/ (Jinja2)               │
│  13 feature directories + index.html + dashboard    │
├─────────────────────────────────────────────────────┤
│             static/ (CSS + JS + images)             │
└─────────────────────────────────────────────────────┘
         ↕                ↕               ↕
   Firebase Auth    MongoDB (local)   ESP8266 IoT
   (client+admin)   (prediction logs) (soil moisture)
```

### Auth Flow

```
Browser → Firebase signInWithEmailAndPassword()
       → user.getIdToken() → JWT
       → POST /auth/session → Flask verifies via Firebase Admin SDK
       → Server-side session created → redirect to /dashboard
```

---

## 🗂️ Project Structure

```
Krishi-Sahayak/
│
├── app.py                      # App factory — create_app()
├── config.py                   # Config classes (Dev/Prod) + .env loading
├── run.py                      # Entry point — python run.py → localhost:5000
├── requirements.txt            # Pinned Python dependencies
├── .env                        # Environment variables (git-ignored)
├── .gitignore                  # Comprehensive ignore rules
│
├── routes/                     # Flask Blueprints (14 total)
│   ├── main.py                 # GET / (landing) + GET /dashboard
│   ├── auth.py                 # Login, register, forgot-password, sessions
│   ├── crop.py                 # Crop recommendation form + ML prediction
│   ├── fertilizer.py           # Fertilizer calculator + Gemini AI explanation
│   ├── disease.py              # Disease detection (image upload → Keras CNN)
│   ├── irrigation.py           # IoT irrigation dashboard (10 endpoints)
│   ├── mandi.py                # Live mandi prices (4 API endpoints)
│   ├── chatbot.py              # Dialogflow widget + /webhook fulfillment
│   ├── weather.py              # Weather information page
│   ├── profit.py               # Farm expense & profit calculator
│   ├── nearby.py               # Nearby agri-service finder
│   ├── profile.py              # User profile CRUD + photo upload
│   ├── settings.py             # App settings (theme, language, notifications)
│   └── history.py              # Prediction history (crop, fertilizer, disease)
│
├── services/                   # Business logic layer (8 services)
│   ├── firebase_service.py     # Firebase Admin SDK — token verification
│   ├── ml_service.py           # ModelManager — loads all ML models at startup
│   ├── gemini_service.py       # Gemini AI — fertilizer explanations + disease treatment
│   ├── groq_service.py         # Groq LLaMA-3 — Dialogflow webhook handler
│   ├── weather_service.py      # Open-Meteo — background weather polling + sensor state
│   ├── mandi_service.py        # Agmarknet API — prices, trends, best markets
│   ├── mongodb_service.py      # MongoDB — prediction history persistence
│   └── profile_service.py      # Profile CRUD — JSON file storage
│
├── models/                     # Data models / document schemas
│   ├── crop_prediction.py      # Crop prediction document builder
│   ├── fertilizer_prediction.py# Fertilizer prediction document builder
│   └── disease_prediction.py   # Disease prediction document builder
│
├── utils/                      # Shared utilities
│   ├── decorators.py           # @login_required, @role_required
│   ├── session_manager.py      # Flask session get/set/clear helpers
│   ├── helpers.py              # File upload, Firebase config helpers
│   └── validators.py           # Input validation utilities
│
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Public landing page
│   ├── dashboard.html          # Authenticated farmer dashboard
│   ├── auth/                   # Login, register, forgot-password
│   ├── crop/                   # Crop recommendation + fertilizer forms/results
│   ├── disease/                # Disease detection upload + results
│   ├── irrigation/             # Smart irrigation control panel
│   ├── mandi/                  # Live mandi price explorer
│   ├── chatbot/                # Dialogflow Messenger widget
│   ├── weather/                # Weather information
│   ├── profit/                 # Profit calculator
│   ├── nearby/                 # Nearby services finder
│   ├── profile/                # Profile view + edit
│   ├── settings/               # Settings page
│   ├── history/                # Prediction history
│   └── errors/                 # 403, 404, 500 error pages
│
├── static/
│   ├── css/                    # styles.css, log.css, irrigation.css
│   ├── js/                     # dashboard.js, firebase.js, irrigation_script.js
│   └── images/                 # Logo, landing page images, default avatar
│
├── trained_models/             # ML model binaries (git-ignored)
│   ├── crop_model.pkl          # Scikit-learn crop classifier (~3.5 MB)
│   ├── crop_le.pkl             # Label encoder
│   ├── ideal_npk.csv           # Ideal NPK values per crop
│   └── disease_model.keras     # Keras CNN for disease detection (~179 MB)
│
├── Ai_bot_backend_agri/        # Original chatbot backend (reference)
├── Irrigation/                 # Original irrigation module (reference)
│
├── instance/                   # Secrets directory (git-ignored)
│   └── firebase_service_account.json
├── uploads/                    # User uploads (git-ignored)
└── logs/                       # Application logs (git-ignored)
```

---

## 🛠️ Technology Stack

| Layer                  | Technology                                                     |
|------------------------|----------------------------------------------------------------|
| **Backend Framework**  | Flask 3.0.3 (App Factory pattern)                              |
| **Authentication**     | Firebase Auth (client-side) + Firebase Admin SDK (server-side)  |
| **Database**           | MongoDB (prediction history via PyMongo 4.10)                  |
| **ML — Crop**          | Scikit-learn 1.5.2 (Random Forest classifier)                  |
| **ML — Disease**       | TensorFlow 2.16 / Keras (CNN, 15-class, 256×256 input)        |
| **AI — Explanations**  | Google Gemini 2.5 Flash (`google-generativeai` 0.8.4)          |
| **AI — Chatbot**       | Groq LLaMA-3.1-8B (`groq` 0.12.0) + Dialogflow Messenger     |
| **Market Prices**      | data.gov.in Agmarknet REST API                                 |
| **Weather**            | Open-Meteo API (no API key required)                           |
| **Geocoding**          | Open-Meteo Geocoding + OpenStreetMap Nominatim                 |
| **IoT Hardware**       | ESP8266 + Soil Moisture Sensor + Relay + Water Pump      |
| **Frontend**           | Jinja2 templates, vanilla HTML/CSS/JS, Chart.js                |
| **Production Server**  | Gunicorn 23.0                                                  |
| **Configuration**      | python-dotenv (.env) + class-based config (Dev/Prod)           |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **MongoDB** — running locally on `localhost:27017` (optional — app works without it, history won't persist)
- **Firebase Project** — with Authentication enabled (Email/Password provider)
- **API Keys** — Gemini, Groq, Mandi (data.gov.in)

### 1. Clone & Create Virtual Environment

```bash
git clone https://github.com/Pratyush-Basu/Krishi-Sahayak-Smart-Farming.git
cd Krishi-Sahayak

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (use `.env.example` as reference):

```env
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Firebase (from Firebase Console → Project Settings → General)
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id

# Firebase Admin SDK
FIREBASE_SERVICE_ACCOUNT_PATH=instance/firebase_service_account.json

# AI APIs
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key

# Mandi (data.gov.in)
MANDI_API_KEY=your-mandi-api-key
```

### 4. Set Up Firebase Admin SDK

1. Go to **Firebase Console → Project Settings → Service Accounts**
2. Click **Generate New Private Key**
3. Save the downloaded JSON as `instance/firebase_service_account.json`

### 5. Set Up ML Models

Place the trained model files in `trained_models/`:

| File                   | Source / Description                              |
|------------------------|---------------------------------------------------|
| `crop_model.pkl`       | Scikit-learn crop classifier (pre-trained)         |
| `crop_le.pkl`          | Label encoder for crop classes                     |
| `ideal_npk.csv`        | Ideal NPK values lookup table                      |
| `disease_model.keras`  | Keras CNN for plant disease detection (~179 MB)    |

### 6. Run the Application

```bash
python run.py
```

The server starts at **http://localhost:5000**

---

## 🔌 API Reference

### Public Routes

| Method | Endpoint            | Description              |
|--------|---------------------|--------------------------|
| GET    | `/`                 | Landing page             |
| GET    | `/login`            | Login page               |
| GET    | `/register`         | Registration page        |
| GET    | `/forgot-password`  | Password reset page      |

### Protected Routes (require login)

| Method | Endpoint                      | Description                              |
|--------|-------------------------------|------------------------------------------|
| GET    | `/dashboard`                  | Farmer dashboard                         |
| POST   | `/auth/session`               | Create session from Firebase JWT         |
| GET    | `/logout`                     | Clear session, redirect to landing       |
| GET    | `/crop`                       | Crop recommendation form                 |
| POST   | `/crop/predict`               | Run crop ML model → top-5 results        |
| POST   | `/crop/fertilizer-entry`      | Pre-fill fertilizer form from crop data  |
| GET    | `/fertilizer`                 | Direct fertilizer input form             |
| POST   | `/fertilizer/result`          | Calculate NPK + Gemini explanation       |
| GET    | `/disease`                    | Disease detection upload page            |
| POST   | `/disease/predict`            | Upload leaf image → CNN + Gemini         |
| GET    | `/mandi`                      | Mandi price page                         |
| GET    | `/mandi/api/prices`           | JSON: current commodity prices           |
| GET    | `/mandi/api/trend`            | JSON: 30-day price trend                 |
| GET    | `/mandi/api/best-mandis`      | JSON: top-5 markets by price             |
| GET    | `/mandi/api/crop-price`       | JSON: quick single-crop price            |
| GET    | `/chatbot`                    | Dialogflow chatbot page                  |
| GET    | `/weather`                    | Weather information page                 |
| GET    | `/profit`                     | Farm profit calculator                   |
| GET    | `/nearby`                     | Nearby agri-services finder              |
| GET    | `/profile`                    | View user profile                        |
| GET/POST | `/profile/edit`             | Edit user profile                        |
| POST   | `/profile/upload-photo`       | Upload profile picture                   |
| POST   | `/profile/change-password`    | Trigger Firebase password reset          |
| GET    | `/settings`                   | Application settings                     |
| GET    | `/history`                    | Prediction history                       |

### IoT / Webhook Routes (no auth required)

| Method | Endpoint                      | Description                              |
|--------|-------------------------------|------------------------------------------|
| POST   | `/irrigation/sensor`          | ESP8266 sends soil moisture readings    |
| GET    | `/irrigation/command`         | ESP8266 polls for pump ON/OFF command      |
| GET    | `/irrigation/ping`            | Health check for IoT device              |
| POST   | `/webhook`                    | Dialogflow fulfillment webhook           |

### Irrigation Dashboard Routes (protected)

| Method | Endpoint                      | Description                              |
|--------|-------------------------------|------------------------------------------|
| GET    | `/irrigation`                 | Irrigation control dashboard             |
| GET    | `/irrigation/data`            | JSON: current sensor + weather state     |
| POST   | `/irrigation/set_mode`        | Switch auto/manual irrigation mode       |
| POST   | `/irrigation/set_pump`        | Toggle pump (manual mode only)           |
| POST   | `/irrigation/set_crop`        | Set crop type + moisture threshold       |
| GET    | `/irrigation/geo_search`      | City autocomplete (Open-Meteo)           |
| GET    | `/irrigation/geo_reverse`     | Reverse geocode lat/lon (Nominatim)      |
| POST   | `/irrigation/set_location`    | Set weather fetch location               |

---

## 🔁 Workflow Overview

### 1️⃣ Crop Recommendation
```
User inputs: N, P, K, temperature, humidity, pH, rainfall
    → Scikit-learn model predicts probabilities for 22 crops
    → Top-5 crops displayed with confidence chart
    → One-click to fertilizer form pre-filled with soil data
    → Prediction saved to MongoDB
```

### 2️⃣ Fertilizer Optimization
```
User selects crop + enters soil NPK + land area
    → System looks up ideal NPK from CSV
    → Calculates deficiency: Urea (46% N), DAP (46% P), MOP (60% K)
    → Gemini AI generates farmer-friendly explanation (EN/HI/BN)
    → Prediction saved to MongoDB
```

### 3️⃣ Disease Detection
```
Farmer uploads leaf photo (JPG/PNG, max 5 MB)
    → Image preprocessed to 256×256 RGB, normalized [0,1]
    → Keras CNN classifies into 15 classes (3 plants × 5 conditions)
    → Gemini generates treatment summary + detailed action steps
    → Prediction saved to MongoDB
```

### 4️⃣ Smart Irrigation
```
ESP8266 soil-moisture sensor → POST /irrigation/sensor (raw + moisture %)
    → Background thread fetches Open-Meteo weather every 10 min
    → Auto mode: pump ON if moisture < threshold AND rain probability < 70%
    → Manual mode: user controls pump via dashboard
    → ESP8266 polls GET /irrigation/command for PUMP:ON or PUMP:OFF
```

### 5️⃣ AI Chatbot
```
Farmer types question in Dialogflow Messenger widget
    → Dialogflow matches intent
    → "get weather" intent → Open-Meteo current + 3-day forecast
    → All other intents → Groq LLaMA-3.1-8B with agriculture system prompt
    → Response sent back as Dialogflow fulfillment messages
```

---

## 🧪 Disease Detection — Supported Classes

| Plant        | Conditions Detected                                                                                |
|--------------|----------------------------------------------------------------------------------------------------|
| Bell Pepper  | Bacterial Spot, Healthy                                                                            |
| Potato       | Early Blight, Late Blight, Healthy                                                                 |
| Tomato       | Bacterial Spot, Early Blight, Late Blight, Leaf Mold, Septoria Leaf Spot, Spider Mites, Target Spot, Yellow Leaf Curl Virus, Mosaic Virus, Healthy |

---

## 📋 Environment Variables Reference

| Variable                         | Required | Description                                  |
|----------------------------------|----------|----------------------------------------------|
| `SECRET_KEY`                     | Yes      | Flask session encryption key                 |
| `FLASK_ENV`                      | No       | `development` (default) or `production`      |
| `FIREBASE_API_KEY`               | Yes      | Firebase Web API key                         |
| `FIREBASE_AUTH_DOMAIN`           | Yes      | Firebase Auth domain                         |
| `FIREBASE_PROJECT_ID`            | Yes      | Firebase project ID                          |
| `FIREBASE_STORAGE_BUCKET`        | Yes      | Firebase storage bucket                      |
| `FIREBASE_MESSAGING_SENDER_ID`   | Yes      | Firebase messaging sender ID                 |
| `FIREBASE_APP_ID`                | Yes      | Firebase app ID                              |
| `FIREBASE_SERVICE_ACCOUNT_PATH`  | Yes      | Path to Firebase Admin SDK JSON              |
| `GEMINI_API_KEY`                 | Yes      | Google Gemini API key                        |
| `GROQ_API_KEY`                   | Yes      | Groq API key (for LLaMA chatbot)             |
| `MANDI_API_KEY`                  | Yes      | data.gov.in API key                          |
| `CROP_MODEL_PATH`                | No       | Path to crop model (default: `trained_models/crop_model.pkl`) |
| `DISEASE_MODEL_PATH`             | No       | Path to disease model (default: `trained_models/disease_model.keras`) |
| `UPLOAD_FOLDER`                  | No       | Upload directory (default: `uploads`)        |
| `MAX_CONTENT_LENGTH`             | No       | Max upload size in bytes (default: 5 MB)     |

---

## 🔮 Future Enhancements

- [ ] Responsive mobile-first PWA
- [ ] Multilingual chatbot with voice input (Web Speech API)
- [ ] Crop yield prediction module
- [ ] ML-based adaptive irrigation thresholds
- [ ] Historical analytics dashboard with MongoDB aggregation
- [ ] Multi-tenancy support for agricultural cooperatives
- [ ] SMS/WhatsApp notification integration

---

## 👨‍💻 Team

| Name               | Role                                                        |
|--------------------|-------------------------------------------------------------|
| Pratyush Basu      | Team Lead, Full-Stack Development, ML & System Architecture |
| Soubhik Naskar     | IoT & Hardware Integration                                  |
| Trish Purkait      | ML & DL Model Development                                   |
| Arju Chakraborty   | Frontend & Testing                                          |

---

## 📜 License

This project is developed for academic and research purposes.
