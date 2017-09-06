# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Functions defined here are NOT DESIGNED FOR PRODUCTION

from rest_framework.test import APITestCase

from swh.storage.api.client import RemoteStorage as Storage

from swh.web import config


# Because the Storage's __init__ function does side effect at startup...
class RemoteStorageAdapter(Storage):
    def __init__(self, base_url):
        self.base_url = base_url


def _init_mock_storage(base_url='https://somewhere.org:4321'):
    """Instanciate a remote storage whose goal is to be mocked in a test
    context.

    NOT FOR PRODUCTION

    Returns:
        An instance of swh.storage.api.client.RemoteStorage destined to be
        mocked (it does not do any rest call)

    """
    return RemoteStorageAdapter(base_url)  # destined to be used as mock


def create_config(base_url='https://somewhere.org:4321'):
    """Function to initiate a flask app with storage designed to be mocked.

    Returns:
        Tuple:
        - app test client (for testing api, client decorator from flask)
        - application's full configuration
        - the storage instance to stub and mock
        - the main app without any decoration

    NOT FOR PRODUCTION

    """
    storage = _init_mock_storage(base_url)

    swh_config = config.get_config()

    # inject the mock data
    swh_config.update({'storage': storage})

    return swh_config


class SWHApiTestCase(APITestCase):
    """Testing API class.

    """
    @classmethod
    def setUpClass(cls):
        super(SWHApiTestCase, cls).setUpClass()
        cls.test_config = create_config()
        cls.maxDiff = None

    @classmethod
    def storage(cls):
        return cls.test_config['storage']
