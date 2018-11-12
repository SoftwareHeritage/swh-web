# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


"""
Django common settings for swh-web.
"""

import os

from swh.web.config import get_config

swh_web_config = get_config()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = swh_web_config['secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = swh_web_config['debug']
DEBUG_PROPAGATE_EXCEPTIONS = swh_web_config['debug']

ALLOWED_HOSTS = ['127.0.0.1', 'localhost'] + swh_web_config['allowed_hosts']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'swh.web.common',
    'swh.web.api',
    'swh.web.browse',
    'webpack_loader',
    'django_js_reverse'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'swh.web.common.middlewares.ThrottlingHeadersMiddleware'
]

# Compress all assets (static ones and dynamically generated html)
# served by django in a local development environment context.
# In a production environment, assets compression will be directly
# handled by web servers like apache or nginx.
if swh_web_config['serve_assets']:
    MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

ROOT_URLCONF = 'swh.web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, "../templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'swh.web.common.utils.context_processor'
            ],
            'libraries': {
                'swh_templatetags': 'swh.web.common.swh_templatetags',
            },
        },
    },
]

WSGI_APPLICATION = 'swh.web.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # noqa
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "../static")
]

INTERNAL_IPS = ['127.0.0.1']

throttle_rates = {}

http_requests = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']

throttling = swh_web_config['throttling']
for limiter_scope, limiter_conf in throttling['scopes'].items():
    if 'default' in limiter_conf['limiter_rate']:
        throttle_rates[limiter_scope] = limiter_conf['limiter_rate']['default']
    # for backward compatibility
    else:
        throttle_rates[limiter_scope] = limiter_conf['limiter_rate']
    # register sub scopes specific for HTTP request types
    for http_request in http_requests:
        if http_request in limiter_conf['limiter_rate']:
            throttle_rates[limiter_scope + '_' + http_request.lower()] = \
                limiter_conf['limiter_rate'][http_request]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'swh.web.api.renderers.YAMLRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer'
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'swh.web.common.throttling.SwhWebRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': throttle_rates
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] [%(levelname)s] %(request)s %(status_code)s', # noqa
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': os.path.join(swh_web_config['log_dir'], 'swh-web.log'),
            'formatter': 'verbose'
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False
        }
    },
}

WEBPACK_LOADER = { # noqa
    'DEFAULT': {
        'CACHE': False,
        'BUNDLE_DIR_NAME': './',
        'STATS_FILE': os.path.join(PROJECT_DIR, '../static/webpack-stats.json'), # noqa
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map']
    }
}

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = 'admin'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
