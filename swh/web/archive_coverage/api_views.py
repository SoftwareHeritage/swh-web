# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from rest_framework.request import Request

from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.archive_coverage import get_coverage_data

coverage_api_urls = APIUrls()


@api_route(r"/stat/coverage/", "api-1-stat-coverage", api_urls=coverage_api_urls)
@api_doc("/stat/coverage/", category="Miscellaneous", noargs=True)
@format_docstring()
def api_stats(request: Request):
    """
    .. http:get:: /api/1/stat/coverage/

        Get statistics about what origins are covered by the archive.

        {common_headers}

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`stat/coverage/`
    """

    coverage_data = get_coverage_data()

    if coverage_data:
        root_url = request.build_absolute_uri("")
        for origins_data in coverage_data.values():
            for origins in origins_data["origins"]:
                if "search_urls" in origins:
                    for visit_type in origins["search_urls"]:
                        origins["search_urls"][visit_type] = (
                            root_url + origins["search_urls"][visit_type]
                        )
                elif "instances" in origins:
                    for instance_data in origins["instances"].values():
                        for visit_type in instance_data.get("visit_types", {}):
                            search_url = instance_data["visit_types"][visit_type].get(
                                "search_url"
                            )
                            if not search_url:
                                continue
                            instance_data["visit_types"][visit_type]["search_url"] = (
                                root_url + search_url
                            )

    return (
        {
            "listed": coverage_data["Regular crawling"],
            "legacy": coverage_data["Discontinued hosting"],
            "deposited": coverage_data["On demand archival"],
        }
        if coverage_data
        else {}
    )
