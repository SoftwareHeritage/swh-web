# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import glob
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

yarn = os.environ.get("YARN", "yarnpkg" if shutil.which("yarnpkg") else "yarn")


def needs_regen(output_dirs, sources) -> bool:
    """Returns whether any of the sources files was modified after generated
    assets in output_dirs."""
    if any(not os.path.exists(dest) for dest in output_dirs):
        return True

    dest_mtimes = [
        os.stat(dest).st_mtime
        for output_dir in output_dirs
        for dest in glob.glob(f"{output_dir}/**")
        if os.path.isfile(dest)
    ]

    if dest_mtimes:
        max_dest_mtime = max(dest_mtimes)
        return any(os.stat(source).st_mtime > max_dest_mtime for source in sources)
    else:
        return True


class CustomBuildHook(BuildHookInterface):

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:

        if self.target_name == "sdist":
            # generated static assets are not included in sdist
            return

        if os.environ.get("TOX_ENV_DIR"):
            # no need to generate assets when executing tox environments
            # but some generated dirs and files must exist or hatch will
            # fail to install swh-web otherwise
            for assets_dir in ("css", "js", "fonts", "jssources", "img/thirdParty"):
                (Path(self.root) / "swh/web/static" / assets_dir).mkdir(exist_ok=True)
            (Path(self.root) / "swh/web/static/webpack-stats.json").write_text("{}")
            (Path(self.root) / "swh/web/static/robots.txt").touch(exist_ok=True)
            return

        # always generate static assets when building a wheel
        regen_assets = True
        if version == "editable":
            # except when using an editable install where assets
            # are regenerated only when source files were modified
            output_dirs = [
                os.path.join(self.root, "swh/web/static", output_dir)
                for output_dir in ("css", "js", "fonts")
            ]
            sources = [
                source
                for pattern in (
                    "swh/web/**/assets/**",
                    "assets/**",
                    "*.js",
                    "*.json",
                )
                for source in glob.glob(
                    os.path.join(self.root, pattern), recursive=True
                )
                if os.path.isfile(source) and "swh/web/static/" not in source
            ]
            regen_assets = needs_regen(output_dirs, sources)

        if regen_assets:
            print("Generating static assets for swh-web", flush=True)

            try:
                subprocess.run(
                    [yarn, "--mutex", "file", "install", "--frozen-lockfile"],
                    check=True,
                )
            except subprocess.CalledProcessError:
                subprocess.run([yarn, "--mutex", "file", "install"], check=True)

            if version == "editable":
                subprocess.run(
                    [yarn, "--mutex", "file", "run", "build-dev"], check=True
                )
            else:
                subprocess.run([yarn, "--mutex", "file", "run", "build"], check=True)
