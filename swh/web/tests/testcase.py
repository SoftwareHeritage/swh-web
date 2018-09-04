# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Functions defined here are NOT DESIGNED FOR PRODUCTION

from django.core.cache import cache
from django.test import TestCase

from swh.storage.api.client import RemoteStorage as Storage

from swh.web import config


# Because the Storage's __init__ function does side effect at startup...
class RemoteStorageAdapter(Storage):
    def __init__(self, base_url):
        self.base_url = base_url


def _init_mock_storage(base_url='https://somewhere.org:4321'):
    """Instantiate a remote storage whose goal is to be mocked in a test
    context.

    NOT FOR PRODUCTION

    Returns:
        An instance of swh.storage.api.client.RemoteStorage destined to be
        mocked (it does not do any rest call)

    """
    return RemoteStorageAdapter(base_url)  # destined to be used as mock


def create_config(base_url='https://somewhere.org:4321'):
    """Function to initiate swh-web config with storage designed to be mocked.

    Returns:
        dict containing swh-web config for tests

    NOT FOR PRODUCTION

    """
    storage = _init_mock_storage(base_url)

    swh_config = config.get_config()

    # inject the mock data
    swh_config.update({'storage': storage})

    return swh_config


class SWHWebTestCase(TestCase):
    """Testing API class.

    """
    @classmethod
    def setUpClass(cls):
        super(SWHWebTestCase, cls).setUpClass()
        cls.test_config = create_config()
        cls.maxDiff = None

    @classmethod
    def storage(cls):
        return cls.test_config['storage']

    def setUp(self):
        cache.clear()
