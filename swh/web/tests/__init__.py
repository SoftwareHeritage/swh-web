# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# this configuration is needed to successfully run the tests locally
# when calling 'make test'

import django
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "swh.web.settings.tests"
django.setup()
