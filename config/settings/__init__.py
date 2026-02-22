"""
По умолчанию используются настройки для разработки (dev).
Для production установите DJANGO_SETTINGS_MODULE=config.settings.prod
"""
from .dev import *  # noqa: F401, F403
