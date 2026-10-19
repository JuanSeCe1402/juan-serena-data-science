"""Loaded automatically by `gunicorn app:app` from the application root."""
import os

port = int(os.environ.get("PORT") or "8000")
if not 1 <= port <= 65535:
    raise ValueError("PORT must be an integer between 1 and 65535")
bind = f"0.0.0.0:{port}"
workers = 2
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
