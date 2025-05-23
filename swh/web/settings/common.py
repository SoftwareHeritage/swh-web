# Copyright (C) 2017-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


"""
Django common settings for swh-web.
"""

from importlib.metadata import version
from importlib.util import find_spec
import os
from typing import Any, Dict
import warnings

from django.utils import encoding

from swh.web.config import get_config, oidc_enabled

# Fix django-js-reverse 0.9.1 compatibility with django 4.x
# TODO: Remove that hack once a new django-js-reverse release
# is available on PyPI
if not hasattr(encoding, "force_text"):
    setattr(encoding, "force_text", encoding.force_str)

swh_web_config = get_config()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = swh_web_config["secret_key"]
SECRET_KEY_FALLBACKS = swh_web_config["secret_key_fallbacks"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = swh_web_config["debug"]
DEBUG_PROPAGATE_EXCEPTIONS = swh_web_config["debug"]

ALLOWED_HOSTS = ["127.0.0.1", "localhost"] + swh_web_config["allowed_hosts"]
UNAUTHENTICATED_HOSTS = ["127.0.0.1", "localhost"] + swh_web_config[
    "unauthenticated_api_hosts"
]

# Applications definition

SWH_BASE_DJANGO_APPS = [
    "swh.web.api",
    "swh.web.auth",
    "swh.web.browse",
    "swh.web.tests",
    "swh.web.utils",
    "swh.web.webapp",
]
SWH_EXTRA_DJANGO_APPS = [
    app
    for app in swh_web_config["swh_extra_django_apps"]
    if app not in SWH_BASE_DJANGO_APPS and app != "swh.web.banners"
]

SWH_DJANGO_APPS = SWH_BASE_DJANGO_APPS + SWH_EXTRA_DJANGO_APPS

SWH_MIRROR_CONFIG = swh_web_config.get("mirror_config", {})
if SWH_MIRROR_CONFIG:
    assert "partner_name" in SWH_MIRROR_CONFIG
    assert "static_path" in SWH_MIRROR_CONFIG
    assert "partner_logo_static_path" in SWH_MIRROR_CONFIG
    assert "templates_path" in SWH_MIRROR_CONFIG

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "webpack_loader",
    "django_js_reverse",
    "corsheaders",
    "django_bootstrap5",
] + SWH_DJANGO_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "swh.web.utils.middlewares.ThrottlingHeadersMiddleware",
    "swh.web.utils.middlewares.ExceptionMiddleware",
]

# Compress all assets (static ones and dynamically generated html)
# served by django in a local development environment context.
# In a production environment, assets compression will be directly
# handled by web servers like apache or nginx.
if swh_web_config["serve_assets"]:
    MIDDLEWARE.insert(0, "django.middleware.gzip.GZipMiddleware")

ROOT_URLCONF = "swh.web.urls"

SWH_APP_TEMPLATES = [os.path.join(PROJECT_DIR, "../templates")]
# Add templates directory from each SWH Django application as even
# if an app is not enabled, others might need some of its templates
apps_dir = os.path.join(os.path.dirname(__file__), "../")
_, apps, _ = next(os.walk(apps_dir))  # type: ignore[assignment]
for app in apps:
    app_templates_dir = os.path.join(apps_dir, app, "templates")
    if os.path.exists(app_templates_dir):
        SWH_APP_TEMPLATES.append(app_templates_dir)

# for mirror version of swh-web, we need access to the Save Code Now templates
# even if the django application is not enabled
if SWH_MIRROR_CONFIG and "swh.web.save_code_now" not in SWH_DJANGO_APPS:
    app_spec = find_spec("swh.web.save_code_now")
    assert app_spec is not None and app_spec.origin is not None
    SWH_APP_TEMPLATES.append(
        os.path.join(os.path.dirname(app_spec.origin), "templates")
    )

if SWH_MIRROR_CONFIG:
    mirror_templates_path = SWH_MIRROR_CONFIG["templates_path"]
    assert os.path.exists(os.path.join(mirror_templates_path, "mirror-homepage.html"))
    assert os.path.exists(os.path.join(mirror_templates_path, "mirror-footer.html"))
    SWH_APP_TEMPLATES.append(SWH_MIRROR_CONFIG["templates_path"])

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": SWH_APP_TEMPLATES,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "swh.web.utils.context_processor",
            ],
            "libraries": {
                "swh_templatetags": "swh.web.utils.swh_templatetags",
            },
            "builtins": [
                "django.templatetags.i18n",
                "django_bootstrap5.templatetags.django_bootstrap5",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": swh_web_config.get("development_db", ""),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"
# static folder location when swh-web has been installed with pip
STATIC_DIR = os.path.join(PROJECT_DIR, "../static")

if not os.path.exists(STATIC_DIR):
    warnings.warn(
        "Unable to find the static assets directory. Check your installation of swh.web."
    )

STATICFILES_DIRS = [STATIC_DIR]

if "static_path" in SWH_MIRROR_CONFIG:
    STATICFILES_DIRS.append(SWH_MIRROR_CONFIG["static_path"])

INTERNAL_IPS = ["127.0.0.1"]

throttle_rates = {}

http_requests = ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]

throttling = swh_web_config["throttling"]
for limiter_scope, limiter_conf in throttling["scopes"].items():
    if "default" in limiter_conf["limiter_rate"]:
        throttle_rates[limiter_scope] = limiter_conf["limiter_rate"]["default"]
    # for backward compatibility
    else:
        throttle_rates[limiter_scope] = limiter_conf["limiter_rate"]
    # register sub scopes specific for HTTP request types
    for http_request in http_requests:
        if http_request in limiter_conf["limiter_rate"]:
            throttle_rates[limiter_scope + "_" + http_request.lower()] = limiter_conf[
                "limiter_rate"
            ][http_request]

REST_FRAMEWORK: Dict[str, Any] = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "swh.web.api.renderers.YAMLRenderer",
        "rest_framework.renderers.TemplateHTMLRenderer",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "swh.web.api.throttling.SwhWebRateThrottle",
        "swh.web.api.throttling.SwhWebUserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": throttle_rates,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "swh.auth.django.backends.OIDCBearerTokenAuthentication",
    ],
    "EXCEPTION_HANDLER": "swh.web.api.apiresponse.error_response_handler",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "request": {
            "format": "[%(asctime)s] [%(levelname)s] %(request)s %(status_code)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {
            "format": "[%(asctime)s] [%(levelname)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "verbose": {
            "format": (
                "[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s:%(lineno)s "
                "- %(message)s"
            ),
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "filename": os.path.join(swh_web_config["log_dir"], "swh-web.log"),
            "formatter": "simple",
        },
        "file_request": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "filename": os.path.join(swh_web_config["log_dir"], "swh-web.log"),
            "formatter": "request",
        },
        "console_verbose": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file_verbose": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "filename": os.path.join(swh_web_config["log_dir"], "swh-web.log"),
            "formatter": "verbose",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console_verbose", "file_verbose"],
            "level": "DEBUG" if DEBUG else "WARNING",
        },
        "django": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_request"],
            "level": "DEBUG" if DEBUG else "WARNING",
            "propagate": False,
        },
        "django.db.backends": {"handlers": ["null"], "propagate": False},
        "django.utils.autoreload": {
            "level": "INFO",
        },
        "swh.core.statsd": {
            "level": "INFO",
        },
        "urllib3": {
            "level": "INFO",
        },
    },
}

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": False,
        "BUNDLE_DIR_NAME": "./",
        "STATS_FILE": os.path.join(STATIC_DIR, "webpack-stats.json"),
        "POLL_INTERVAL": 0.1,
        "TIMEOUT": None,
        "IGNORE": [".+\\.hot-update.js", ".+\\.map"],
    }
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

if not oidc_enabled():
    LOGIN_URL = "login"
    LOGOUT_URL = "logout"
else:
    LOGIN_URL = "oidc-login"
    LOGOUT_URL = "oidc-logout"
    AUTHENTICATION_BACKENDS.append(
        "swh.auth.django.backends.OIDCAuthorizationCodePKCEBackend",
    )
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.contrib.auth.middleware.AuthenticationMiddleware") + 1,
        "swh.auth.django.middlewares.OIDCSessionExpiredMiddleware",
    )

LOGIN_REDIRECT_URL = "swh-web-homepage"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "VERSION": version("swh.web"),
    },
    "rate-limit": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

JS_REVERSE_JS_MINIFY = False

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(badge|api)/.*$"

OIDC_SWH_WEB_CLIENT_ID = "swh-web"
SWH_AUTH_SERVER_URL = swh_web_config["keycloak"]["server_url"]
SWH_AUTH_REALM_NAME = swh_web_config["keycloak"]["realm_name"]
SWH_AUTH_CLIENT_ID = OIDC_SWH_WEB_CLIENT_ID
SWH_AUTH_SESSION_EXPIRED_REDIRECT_VIEW = "logout-page"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

RATELIMIT_USE_CACHE = "rate-limit"
RATELIMIT_ENABLE = False
# get real client IP address when behind production reverse proxy
RATELIMIT_IP_META_KEY = lambda request: request.META.get(  # noqa
    "HTTP_X_ORIGINAL_FORWARDED_FOR", request.META["REMOTE_ADDR"]
).split(",", maxsplit=1)[0]

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10Mb

# XXX Transitional setting that will be removed in Django 6.0
FORMS_URLFIELD_ASSUME_HTTPS = True

EMAIL_BACKEND = swh_web_config["email_setup"]["backend"]
EMAIL_HOST = swh_web_config["email_setup"].get("host")
EMAIL_PORT = swh_web_config["email_setup"].get("port")
EMAIL_HOST_USER = swh_web_config["email_setup"].get("username")
EMAIL_HOST_PASSWORD = swh_web_config["email_setup"].get("password")
EMAIL_USE_TLS = swh_web_config["email_setup"].get("use_tls", False)
EMAIL_USE_SSL = swh_web_config["email_setup"].get("use_ssl", False)
DEFAULT_FROM_EMAIL = swh_web_config["email_setup"].get("default_from_email")

ALTER_SETTINGS = swh_web_config.get("alter_settings", {})
