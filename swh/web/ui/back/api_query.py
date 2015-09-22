# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui.back import http


def api_storage_content_present(hashes):
    """Create the api call query for checking the hashes are present in backend.

    Args:
        hashes: dictionary of hashed indexed by keys (sha1, sha256, etc...)

    Returns:
        A http query ready to be executed.

    Raises:
        Nothing
    """
    return http.create_request("post", "/content/present", data=hashes)
