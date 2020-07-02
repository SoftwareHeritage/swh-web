# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# https://github.com/pytest-dev/pytest-django/pull/709 proposes a more
# generic way to expose all asserts but it makes mypy unhappy.
# So explicitly expose the assertions we need for swh-web tests to
# avoid mypy errors

"""
Expose some Django assertions to be used with pytest
"""

from django.test import TestCase

_test_case = TestCase("run")

assert_template_used = _test_case.assertTemplateUsed
assert_contains = _test_case.assertContains
assert_not_contains = _test_case.assertNotContains
