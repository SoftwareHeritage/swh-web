#!/usr/bin/env python3
# Copyright (C) 2015-2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License v3 or later
# See top-level LICENSE file for more information

import os

from setuptools import setup

# package generated static assets as module data files
data_files = []
for folder in ("static/", "assets/"):
    for root, _, files in os.walk(folder):
        root_files = [os.path.join(root, i) for i in files]
        data_files.append((os.path.join("share/swh/web", root), root_files))

# TODO: data_files usage has been deprecated, we should move away from using it...
setup(
    data_files=data_files,
)
