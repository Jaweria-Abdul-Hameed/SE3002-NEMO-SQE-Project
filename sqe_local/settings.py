"""Reproducible local Django settings for NEMO SQE Final Project."""

import os
from pathlib import Path

from rest_framework.settings import DEFAULTS

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv("NEMO_DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "*"]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
AUTH_USER_MODEL = "NEMO.User"
WSGI_APPLICATION = "NEMO.wsgi.application"
ROOT_URLCONF = "NEMO.urls"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "landing"
LOGOUT_REDIRECT_URL = "login"

DATETIME_FORMAT = "l, F jS, Y @ g:i A"
SHORT_DATETIME_FORMAT = "m/d/Y @ g:i A"
DATE_FORMAT = "l, F jS, Y"
SHORT_DATE_FORMAT = "m/d/Y"
TIME_FORMAT = "g:i A"
DATETIME_INPUT_FORMATS = ["%m/%d/%Y %I:%M %p"]
DATE_INPUT_FORMATS = ["%m/%d/%Y"]
TIME_INPUT_FORMATS = ["%I:%M %p"]

USE_I18N = False
USE_L10N = False
USE_TZ = True
TIME_ZONE = "America/New_York"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.humanize",
    "NEMO",
    "NEMO.apps.kiosk",
    "NEMO.apps.area_access",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "mptt",
    "auditlog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "NEMO.middleware.DeviceDetectionMiddleware",
    "NEMO.middleware.NEMOAuditlogMiddleware",
    "NEMO.middleware.ImpersonateMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "NEMO.context_processors.show_logout_button",
                "NEMO.context_processors.base_context",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("NEMO.permissions.DjangoModelPermissions",),
    "DEFAULT_FILTER_BACKENDS": ("NEMO.rest_filter_backend.NEMOFilterBackend",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": DEFAULTS["DEFAULT_RENDERER_CLASSES"] + ["drf_excel.renderers.XLSXRenderer"],
    "DEFAULT_PARSER_CLASSES": DEFAULTS["DEFAULT_PARSER_CLASSES"] + ["NEMO.parsers.CSVParser"],
    "DEFAULT_PAGINATION_CLASS": "NEMO.rest_pagination.NEMOPageNumberPagination",
    "PAGE_SIZE": 1000,
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("NEMO_SQLITE_PATH", str(BASE_DIR / "sqe_nemo.db")),
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SERVER_EMAIL = "NEMO Server Administrator <nemo.admin@example.org>"
ADMINS = [("System administrator", "sysadmin@example.org")]
MANAGERS = ADMINS

STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "staticfiles")
MEDIA_ROOT = str(BASE_DIR / "resources" / "emails")
MEDIA_URL = "/media/"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "sqe-local-dev-only-key-change-for-prod")

ALLOW_CONDITIONAL_URLS = True
AUTHENTICATION_BACKENDS = ["sqe_local.auth_backend.LocalSyntheticAuthBackend"]
LDAP_SERVERS = []

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
