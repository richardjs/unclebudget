from datetime import date, datetime
from os import environ
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
YES = ["yes", "y", "true", "t"]


INSECURE_KEY = "django-insecure-2p_)_n&x8(6)v5s62+o)3+vyu@_g1*u0*ug4_pimk3%y#(#i3f"
SECRET_KEY = environ.get("UNCLEBUDGET_SECRET_KEY", INSECURE_KEY)

DEBUG = environ.get("UNCLEBUDGET_DEBUG", "false").lower() in YES
if not DEBUG and SECRET_KEY == INSECURE_KEY:
    raise ImproperlyConfigured("UNCLEBUDGET_SECRET_KEY needs to be set")

ALLOWED_HOSTS = []
if environ.get("UNCLEBUDGET_HOST"):
    ALLOWED_HOSTS = [environ.get("UNCLEBUDGET_HOST")]

INTERNAL_IPS = [
    "127.0.0.1",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "unclebudget",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "unclebudget.context_processors.debug",
                "unclebudget.context_processors.theme",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": environ.get("UNCLEBUDGET_DB_FILE", BASE_DIR / "db.sqlite3"),
    }
}

USE_TZ = True
TIME_ZONE = environ.get("UNCLEBUDGET_TIMEZONE", "America/Chicago")

STATIC_URL = "static/"
STATIC_ROOT = environ.get("UNCLEBUDGET_STATIC_ROOT", BASE_DIR / "www/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache",
        "OPTIONS": {
            "MAX_ENTRIES": 2000,
        },
    }
}

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"

UNCLEBUDGET_LOADERS = [
    "loaders.first",
    "loaders.second",
]

# Single user mode: automatically log in as the user with the specified ID
UNCLEBUDGET_SINGLE_USER = environ.get("UNCLEBUDGET_SINGLE_USER", None)
