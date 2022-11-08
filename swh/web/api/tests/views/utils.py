# Copyright (C) 2015-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from requests.utils import parse_header_links

from swh.web.tests.helpers import check_api_get_responses


def scroll_results(api_client, url):
    """Iterates through pages of results, and returns them all."""
    results = []

    while True:
        rv = check_api_get_responses(api_client, url, status_code=200)

        results.extend(rv.data)

        if "Link" in rv:
            for link in parse_header_links(rv["Link"]):
                if link["rel"] == "next":
                    # Found link to next page of results
                    url = link["url"]
                    break
            else:
                # No link with 'rel=next'
                break
        else:
            # No Link header
            break

    return results
