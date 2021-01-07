# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


"""
Django common settings for swh-web.
"""

import os
import sys
from typing import Any, Dict

from swh.web.config import get_config

swh_web_config = get_config()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = swh_web_config["secret_key"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = swh_web_config["debug"]
DEBUG_PROPAGATE_EXCEPTIONS = swh_web_config["debug"]

ALLOWED_HOSTS = ["127.0.0.1", "localhost"] + swh_web_config["allowed_hosts"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "swh.web.common",
    "swh.web.api",
    "swh.web.auth",
    "swh.web.browse",
    "webpack_loader",
    "django_js_reverse",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "swh.web.auth.middlewares.OIDCSessionExpiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "swh.web.common.middlewares.ThrottlingHeadersMiddleware",
    "swh.web.common.middlewares.ExceptionMiddleware",
]

# Compress all assets (static ones and dynamically generated html)
# served by django in a local development environment context.
# In a production environment, assets compression will be directly
# handled by web servers like apache or nginx.
if swh_web_config["serve_assets"]:
    MIDDLEWARE.insert(0, "django.middleware.gzip.GZipMiddleware")

ROOT_URLCONF = "swh.web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_DIR, "../templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "swh.web.common.utils.context_processor",
            ],
            "libraries": {"swh_templatetags": "swh.web.common.swh_templatetags",},
        },
    },
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": swh_web_config["development_db"],
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
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
STATIC_DIR = os.path.join(sys.prefix, "share/swh/web/static")
if not os.path.exists(STATIC_DIR):
    # static folder location when developping swh-web
    STATIC_DIR = os.path.join(PROJECT_DIR, "../../../static")
STATICFILES_DIRS = [STATIC_DIR]

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
    "DEFAULT_THROTTLE_CLASSES": ("swh.web.api.throttling.SwhWebRateThrottle",),
    "DEFAULT_THROTTLE_RATES": throttle_rates,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "swh.web.auth.backends.OIDCBearerTokenAuthentication",
    ],
    "EXCEPTION_HANDLER": "swh.web.api.apiresponse.error_response_handler",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse",},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue",},
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
        "null": {"class": "logging.NullHandler",},
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
        "django.utils.autoreload": {"level": "INFO",},
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

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "admin"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

JS_REVERSE_JS_MINIFY = False

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(badge|api)/.*$"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "swh.web.auth.backends.OIDCAuthorizationCodePKCEBackend",
]
