import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swh.web.settings.development")
django.setup()

from swh.docs.sphinx.conf import *  # NoQA
