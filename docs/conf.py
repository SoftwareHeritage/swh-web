# flake8: noqa

import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swh.web.settings.development")

django.setup()

import swh.docs.sphinx.conf as sphinx_conf

from swh.web.doc_config import customize_sphinx_conf

customize_sphinx_conf(sphinx_conf)

from swh.docs.sphinx.conf import *
