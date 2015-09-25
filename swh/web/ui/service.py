# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui import main


def search(hashes):
    """Search a content with given hashes.

    Args:
         hashes, dictionary of hash indexed by key, sha1, sha256, etc...

    Returns:
         None if no content is found.
         An enriched content if the content is found.

    Raises:
         OSError (no route to host), etc... Network issues in general
    """
    return main.storage().content_present(hashes)
