"""
app.py — Flask Application Factory for Krishi-Sahayak

The create_app() function:
  1. Creates the Flask instance
  2. Loads config from config.py / .env
  3. Registers all Blueprints (one per module)
  4. Initializes services (Firebase Admin, ML models)
  5. Registers error handlers

Why App Factory pattern?
  - Allows different configs for dev vs production
  - Prevents circular imports
  - Makes testing easier (each test can create its own app)

Phase 1: Only the 'main' blueprint is registered.
         More blueprints will be added in later phases.
"""

import os
import logging
from flask import Flask, render_template
from config import get_config

def create_app(config_class=None):
    """
    Application factory — creates and configures the Flask app.

    Args:
        config_class: Optional config class override (used in testing).

    Returns:
        Configured Flask application instance.
    """

    app = Flask(__name__)

    # ── Load Configuration ──────────────────────────────────────────
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # ── Ensure required folders exist ───────────────────────────────
    _ensure_folders(app)

    # ── Setup Logging ───────────────────────────────────────────────
    _setup_logging(app)

    # ── Initialize Firebase Admin SDK ───────────────────────────────
    from services.firebase_service import init_firebase
    init_firebase(app.config.get("FIREBASE_SERVICE_ACCOUNT_PATH", ""))

    # ── Load ML Models (once at startup) ────────────────────────────
    from services.ml_service import ModelManager
    ml_manager = ModelManager()
    ml_manager.load_all(app.config)
    app.extensions['ml'] = ml_manager

    # ── Start Irrigation Background Threads ──────────────────────────
    from services.weather_service import start_background_threads
    start_background_threads()

    # ── Register Blueprints ─────────────────────────────────────────
    _register_blueprints(app)

    # ── Register Error Handlers ─────────────────────────────────────
    _register_error_handlers(app)

    app.logger.info("Krishi-Sahayak app created successfully")
    return app


# ── Private Helper Functions ─────────────────────────────────────────

def _ensure_folders(app):
    """Create uploads/, logs/, instance/ if they don't exist."""
    folders = [
        app.config.get("UPLOAD_FOLDER", "uploads"),
        "logs",
        "instance",
        "trained_models",
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)


def _setup_logging(app):
    """Configure file + console logging."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO

    # File handler — logs/app.log
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(module)s: %(message)s"
    ))

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)


def _register_blueprints(app):
    """
    Register all route blueprints.

    Phases add blueprints here one by one:
      Phase 1:  main (landing page)
      Phase 5:  auth (login, register, logout, forgot-password)
      Phase 6:  dashboard
      Phase 7:  crop, fertilizer, mandi
      Phase 8:  disease
      Phase 9:  irrigation
      Phase 10: chatbot, weather, profit, nearby
      Phase 11: profile, settings
    """

    # ── Phase 1: Main Blueprint (landing page) ──────────────────────
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    # ── Phase 5: Auth Blueprint ─────────────────────────────────────
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # ── Phase 7: Crop, Fertilizer, Mandi Blueprints ─────────────────
    from routes.crop import crop_bp
    from routes.fertilizer import fertilizer_bp
    from routes.mandi import mandi_bp
    app.register_blueprint(crop_bp)
    app.register_blueprint(fertilizer_bp)
    app.register_blueprint(mandi_bp)

    # ── Phase 8: Disease Detection Blueprint ─────────────────────────
    from routes.disease import disease_bp
    app.register_blueprint(disease_bp)

    # ── Phase 9: Irrigation Blueprint ────────────────────────────────
    from routes.irrigation import irrigation_bp
    app.register_blueprint(irrigation_bp)

    # ── Phase 10: Chatbot, Weather, Profit, Nearby Blueprints ────────
    from routes.chatbot import chatbot_bp
    from routes.weather import weather_bp
    from routes.profit import profit_bp
    from routes.nearby import nearby_bp
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(profit_bp)
    app.register_blueprint(nearby_bp)

    # ── Phase 11: Profile and Settings Blueprints ─────────────────────
    from routes.profile import profile_bp
    from routes.settings import settings_bp
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)


def _register_error_handlers(app):
    """Register friendly error pages for 403, 404, 500."""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return render_template("errors/500.html"), 500
