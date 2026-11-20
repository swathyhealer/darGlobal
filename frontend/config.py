import os

WEBSOCKET_URL = os.getenv(
    "WEBSOCKET_URL",
    "ws://localhost:8000/ws/chat"
)

TOP_K = 5

APP_TITLE = "DarGlobal AI Assistant"
APP_SUBTITLE = "DarGlobal Your Intelligent AI Assistant to help you with your queries and provide relevant information."