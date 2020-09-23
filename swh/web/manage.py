#!/usr/bin/env python

# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import sys

from swh.web import config

if __name__ == "__main__":
    swh_web_config = config.get_config()
    # the serving of static assets in development mode is handled
    # in swh/web/urls.py, we pass the nostatic options to runserver
    # in order to have gzip compression enabled.
    swh_web_config["serve_assets"] = "--nostatic" in sys.argv
    # import root urls module for swh-web before running the django dev server
    # in order to ensure it will be automatically reloaded when source files
    # are modified (as django autoreload feature only works if the modules are
    # in sys.modules)
    try:
        from swh.web import urls  # noqa
    except Exception:
        pass
    try:
        from django.core.management import execute_from_command_line
        from django.core.management.commands.runserver import Command as runserver
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    runserver.default_port = swh_web_config["port"]
    runserver.default_addr = swh_web_config["host"]
    execute_from_command_line(sys.argv)
