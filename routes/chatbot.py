"""
routes/chatbot.py — Dialogflow Chatbot Blueprint

Routes:
  GET  /chatbot  → Chatbot page (Dialogflow Messenger widget embedded)
  POST /webhook  → Dialogflow fulfillment webhook (Groq LLaMA backend)

The /chatbot page shows the same Dialogflow df-messenger widget
that was on the dashboard. /webhook is the backend Dialogflow calls.
"""

from flask import Blueprint, render_template, request, current_app
from utils.decorators import login_required
from services.groq_service import handle_dialogflow_webhook

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot")
@login_required
def chatbot_page():
    """Display the full-page chatbot with Dialogflow messenger widget."""
    return render_template("chatbot/index.html")


@chatbot_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    Dialogflow webhook fulfillment endpoint.

    Dialogflow calls this URL with a POST request when:
      - Intent "get weather" is triggered → fetches Open-Meteo weather
      - Any other intent → sends to Groq LLaMA-3 for agriculture Q&A

    No @login_required — Dialogflow is a server-to-server call.
    Same behavior as original Ai_bot_backend_agri/app.py @/webhook.
    """
    req_json = request.get_json(silent=True) or {}
    return handle_dialogflow_webhook(req_json)
