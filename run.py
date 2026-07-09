"""
run.py — Entry point for Krishi-Sahayak Flask Application

Usage:
    python run.py

This file simply calls create_app() from app.py and starts the server.
All configuration is loaded from .env via config.py.
"""
import sys

print("RUN.PY Python:", sys.executable)
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        
        debug=True,
        use_reloader=True
    )
