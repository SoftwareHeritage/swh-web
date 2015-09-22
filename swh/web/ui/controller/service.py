# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui.back import http, api_query


def search(base_url, hashes):
    """Search a content with given hashes.

    Args:
         hashes, dictionary of hash indexed by key, sha1, sha256, etc...

    Returns:
         None if no content is found.
         An enriched content if the content is found.

    Raises:
         OSError (no route to host), etc... Network issues in general
    """
    def deal_with_result(res):
        print("result:", res)
        return res.data

    #return []
    #return [{'title': 'some title', 'text': 'some text'}]

    q = api_query.api_storage_content_present(hashes)
    return http.execute(base_url, q, result_fn=deal_with_result)
