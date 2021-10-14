# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import subprocess


def test_random_fixtures():
    """Check random fixture values will be different when random seed
    is not explicitly provided.
    """
    result_first = subprocess.run(
        ["pytest", "-s", "random_fixtures_test.py"],
        capture_output=True,
        cwd=os.path.dirname(__file__),
    )
    result_second = subprocess.run(
        ["pytest", "-s", "random_fixtures_test.py"],
        capture_output=True,
        cwd=os.path.dirname(__file__),
    )
    assert result_first.stderr != result_second.stderr
    assert b'Use "pytest --swh-web-random-seed=' in result_first.stdout


def test_random_fixtures_with_seed():
    """Check random fixture values will be the same when random seed
    is explicitly provided through a custom pytest option.
    """
    result_first = subprocess.run(
        ["pytest", "-s", "--swh-web-random-seed=2021", "random_fixtures_test.py"],
        capture_output=True,
        cwd=os.path.dirname(__file__),
    )
    result_second = subprocess.run(
        ["pytest", "-s", "--swh-web-random-seed=2021", "random_fixtures_test.py"],
        capture_output=True,
        cwd=os.path.dirname(__file__),
    )
    assert result_first.stderr == result_second.stderr
    assert b'Use "pytest --swh-web-random-seed=2021' in result_first.stdout
