"""
Development settings for MiniSocial.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# CSRF trusted origins для AJAX запросов в development
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://localhost',
]

# Для development отключаем проверку Referer
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

# Whitenoise для статики в development
INSTALLED_APPS += ['whitenoise.runserver_nostatic']  # noqa: F405
