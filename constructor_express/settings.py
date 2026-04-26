import os
import sys
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

env_path = Path(__file__).resolve().parent.parent / ".env.production"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DEBUG", "False") == "True"
# Detectar contextos que permiten defaults de desarrollo
_TESTING = "test" in sys.argv
_IS_MANAGEMENT_CMD = len(sys.argv) > 0 and "manage.py" in sys.argv[0]

_raw_secret = os.environ.get("SECRET_KEY", "")
if not _raw_secret:
    # Permitir defaults de dev si: DEBUG=True, test, o management command
    if DEBUG or _TESTING or _IS_MANAGEMENT_CMD:
        SECRET_KEY = "dev-only-insecure-key"
    else:
        raise ImproperlyConfigured("SECRET_KEY required in production (set the SECRET_KEY environment variable)")
else:
    SECRET_KEY = _raw_secret

_raw_hosts = os.environ.get("ALLOWED_HOSTS", "")
if not _raw_hosts:
    if DEBUG or _TESTING or _IS_MANAGEMENT_CMD:
        ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    else:
        raise ImproperlyConfigured("ALLOWED_HOSTS required in production (set the ALLOWED_HOSTS environment variable)")
else:
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",")]
    if _IS_MANAGEMENT_CMD or _TESTING:
        ALLOWED_HOSTS += ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_celery_results",
    "drf_spectacular",
    "users",
    "clients",
    "catalog",
    "budgets",
    "billing",
    "auditlog",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "users.middleware.NoCacheAuthMiddleware",  # Previene back-button post-logout
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "constructor_express.urls"
WSGI_APPLICATION = "constructor_express.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # DIRS: solo templates globales (base.html, landing.html, partials/)
        # Los templates de cada app van en <app>/templates/ (cargados por APP_DIRS)
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,  # Busca automáticamente en <app>/templates/
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "users.context_processors.contractor_profile",  # ← NUEVO
            ],
            "builtins": ["budgets.templatetags.budget_filters"],
        },
    },
]

# Si existen las variables de BD → usar PostgreSQL (producción)
# Si no existen → usar SQLite (desarrollo local)
if os.environ.get("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASS"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": "5432",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "users.User"
LOGIN_URL = "/usuarios/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

STATIC_URL = "/static/"
# Solo incluir STATICFILES_DIRS si la carpeta existe
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PLAN_FREE_MAX_CLIENTS = 10
PLAN_FREE_MAX_PRODUCTS = 20
PLAN_FREE_MAX_BUDGETS_PER_MONTH = 5

DEFAULT_FROM_EMAIL = "Constructor Express <noreply@constructorexpress.cl>"

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "token_obtain": "5/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ─── Seguridad: cookies y headers (siempre activos) ──────────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ─── Seguridad: producción (requiere HTTPS) ─────────────────────────────────
if not DEBUG and not _TESTING:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ─── Seguridad: prevenir caché de páginas autenticadas ───────────────────────

# ─── Logging ─────────────────────────────────────────────────────────────────
_log_formatter = "json" if not DEBUG else "verbose"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": _log_formatter,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "budgets.email": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "users.auth": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "catalog.csv_import": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ─── Sentry (solo en producción con DSN configurado) ─────────────────────────
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=os.environ.get("SENTRY_ENV", "production"),
    )

# ─── Upload limits ───────────────────────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB

# ─── Rate limiting (django-ratelimit) ────────────────────────────────────────
RATELIMIT_VIEW = "constructor_express.views.rate_limited_view"

# ─── Mercado Pago ────────────────────────────────────────────────────────────
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
MP_PUBLIC_KEY = os.environ.get("MP_PUBLIC_KEY", "")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")

# ─── Celery ──────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
if _TESTING:
    CELERY_TASK_ALWAYS_EAGER = True

# ─── Email transaccional (Anymail / SendGrid) ────────────────────────────────
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
if SENDGRID_API_KEY and not DEBUG:
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
    ANYMAIL = {"SENDGRID_API_KEY": SENDGRID_API_KEY}
elif _TESTING:
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ─── Twilio / WhatsApp ───────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# ─── JWT (SimpleJWT) ─────────────────────────────────────────────────────────


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ─── OpenAPI / Spectacular ───────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Constructor Express API",
    "DESCRIPTION": "API para contratistas chilenos — presupuestos, clientes, catálogo.",
    "VERSION": "1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ─── SII / DTE ───────────────────────────────────────────────────────────────
SII_PROVIDER_API_KEY = os.environ.get("SII_PROVIDER_API_KEY", "")
SII_RUT_EMISOR = os.environ.get("SII_RUT_EMISOR", "")
SII_ENV = os.environ.get("SII_ENV", "sandbox")

# ─── Celery Beat ─────────────────────────────────────────────────────────────

CELERY_BEAT_SCHEDULE = {
    "scrape-retailers-weekly": {
        "task": "catalog.tasks.scrape_all_retailers",
        "schedule": crontab(hour=3, minute=0, day_of_week="sunday"),
    },
}
