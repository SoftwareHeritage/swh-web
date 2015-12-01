# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Functions defined here are NOT DESIGNED FOR PRODUCTION


from swh.storage.api.client import RemoteStorage as Storage
from swh.web.ui import renderers, main


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


def create_app(base_url='https://somewhere.org:4321'):
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

    # inject the mock data
    conf = {'storage': storage,
            'upload_folder': '/some/upload-dir',
            'upload_allowed_extensions': ['txt'],
            'max_upload_size': 1024}

    main.app.config['TESTING'] = True
    main.app.config.update({'conf': conf})
    main.app.config['MAX_CONTENT_LENGTH'] = conf['max_upload_size']
    main.app.config['DEFAULT_RENDERERS'] = renderers.RENDERERS
    main.load_controllers()

    return main.app.test_client(), main.app.config, storage, main.app
