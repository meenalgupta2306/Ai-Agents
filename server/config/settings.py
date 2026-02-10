"""Centralized configuration for the server"""
import os
from dotenv import load_dotenv

load_dotenv()

# OAuth
REDIRECT_URI = os.getenv("REDIRECT_URI")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# Meta OAuth
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI")

# Paths
DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "documents")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Server
PORT = os.getenv("PORT", "5000")
