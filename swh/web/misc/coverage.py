# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.conf.urls import url
from django.core.cache import caches
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_exempt

from swh.web.common import service
from swh.web.common.exc import handle_view_exception
from swh.web.config import get_config


# Current coverage list of the archive
# TODO: Retrieve that list dynamically instead of hardcoding it
_code_providers = [
    {
        "provider_id": "bitbucket",
        "provider_url": "https://bitbucket.org/",
        "provider_logo": "img/logos/bitbucket.png",
        "provider_info": "public repositories from Bitbucket "
        "(continuously archived)",
        "origin_url_regexp": "^https://bitbucket.org/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "cran",
        "provider_url": "https://cran.r-project.org/",
        "provider_logo": "img/logos/cran.svg",
        "provider_info": "source packages from The Comprehensive R Archive "
        "Network (continuously archived)",
        "origin_url_regexp": "^https://cran.r-project.org/",
        "origin_types": "packages",
    },
    {
        "provider_id": "debian",
        "provider_url": "https://www.debian.org/",
        "provider_logo": "img/logos/debian.png",
        "provider_info": "source packages from the Debian distribution "
        "(continuously archived)",
        "origin_url_regexp": "^deb://",
        "origin_types": "packages",
    },
    {
        "provider_id": "framagit",
        "provider_url": "https://framagit.org/",
        "provider_logo": "img/logos/framagit.png",
        "provider_info": "public repositories from Framagit " "(continuously archived)",
        "origin_url_regexp": "^https://framagit.org/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "github",
        "provider_url": "https://github.com",
        "provider_logo": "img/logos/github.png",
        "provider_info": "public repositories from GitHub " "(continuously archived)",
        "origin_url_regexp": "^https://github.com/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "gitlab",
        "provider_url": "https://gitlab.com",
        "provider_logo": "img/logos/gitlab.svg",
        "provider_info": "public repositories from GitLab " "(continuously archived)",
        "origin_url_regexp": "^https://gitlab.com/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "gitorious",
        "provider_url": "https://gitorious.org/",
        "provider_logo": "img/logos/gitorious.png",
        "provider_info": "public repositories from the former Gitorious code "
        "hosting service",
        "origin_url_regexp": "^https://gitorious.org/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "googlecode",
        "provider_url": "https://code.google.com/archive/",
        "provider_logo": "img/logos/googlecode.png",
        "provider_info": "public repositories from the former Google Code "
        "project hosting service",
        "origin_url_regexp": "^http.*.googlecode.com/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "gnu",
        "provider_url": "https://www.gnu.org",
        "provider_logo": "img/logos/gnu.png",
        "provider_info": "releases from the GNU project (as of August 2015)",
        "origin_url_regexp": "^rsync://ftp.gnu.org/",
        "origin_types": "releases",
    },
    {
        "provider_id": "hal",
        "provider_url": "https://hal.archives-ouvertes.fr/",
        "provider_logo": "img/logos/hal.png",
        "provider_info": "scientific software source code deposited in the "
        "open archive HAL",
        "origin_url_regexp": "^https://hal.archives-ouvertes.fr/",
        "origin_types": "deposits",
    },
    {
        "provider_id": "inria",
        "provider_url": "https://gitlab.inria.fr",
        "provider_logo": "img/logos/inria.jpg",
        "provider_info": "public repositories from Inria GitLab "
        "(continuously archived)",
        "origin_url_regexp": "^https://gitlab.inria.fr/",
        "origin_types": "repositories",
    },
    {
        "provider_id": "ipol",
        "provider_url": "https://www.ipol.im/",
        "provider_logo": "img/logos/ipol.png",
        "provider_info": "software artifacts associated to the articles "
        "IPOL publishes",
        "origin_url_regexp": "^https://doi.org/10.5201/ipol",
        "origin_types": "tarballs",
    },
    {
        "provider_id": "npm",
        "provider_url": "https://www.npmjs.com/",
        "provider_logo": "img/logos/npm.png",
        "provider_info": "public packages from the package registry for "
        "javascript (continuously archived)",
        "origin_url_regexp": "^https://www.npmjs.com/",
        "origin_types": "packages",
    },
    {
        "provider_id": "nixos",
        "provider_url": "https://nixos.org/",
        "provider_logo": "img/logos/nixos.png",
        "provider_info": "source code tarballs used to build the Nix package "
        "collection",
        "origin_url_regexp": "^https://nix-community.github.io/nixpkgs-swh",
        "origin_types": "tarballs",
    },
    {
        "provider_id": "pypi",
        "provider_url": "https://pypi.org",
        "provider_logo": "img/logos/pypi.svg",
        "provider_info": "source packages from the Python Packaging Index "
        "(continuously archived)",
        "origin_url_regexp": "^https://pypi.org/",
        "origin_types": "packages",
    },
]


@xframe_options_exempt
def _swh_coverage(request):
    count_origins = get_config()["coverage_count_origins"]
    return render(
        request,
        "misc/coverage.html",
        {"providers": _code_providers, "count_origins": count_origins},
    )


@never_cache
def _swh_coverage_count(request):
    """Internal browse endpoint to count the number of origins associated
    to each code provider declared in the archive coverage list.
    As this operation takes some times, we execute it once per day and
    cache its results to database. The cached origin counts are then served.
    Cache management is handled in the implementation to avoid sending
    the same count query twice to the storage database.
    """
    try:
        cache = caches["db_cache"]
        results = []
        for code_provider in _code_providers:
            provider_id = code_provider["provider_id"]
            url_regexp = code_provider["origin_url_regexp"]
            cache_key = "%s_origins_count" % provider_id
            prev_cache_key = "%s_origins_prev_count" % provider_id
            # get cached origin count
            origin_count = cache.get(cache_key, -2)
            # cache entry has expired or does not exist
            if origin_count == -2:
                # mark the origin count as processing
                cache.set(cache_key, -1, timeout=10 * 60)
                # execute long count query
                origin_count = service.storage.origin_count(url_regexp, regexp=True)
                # cache count result
                cache.set(cache_key, origin_count, timeout=24 * 60 * 60)
                cache.set(prev_cache_key, origin_count, timeout=None)
            # origin count is currently processing
            elif origin_count == -1:
                # return previous count if it exists
                origin_count = cache.get(prev_cache_key, -1)
            results.append(
                {
                    "provider_id": provider_id,
                    "origin_count": origin_count,
                    "origin_types": code_provider["origin_types"],
                }
            )
        results = json.dumps(results)
    except Exception as exc:
        return handle_view_exception(request, exc, html_response=False)

    return HttpResponse(results, content_type="application/json")


urlpatterns = [
    url(r"^coverage/$", _swh_coverage, name="swh-coverage"),
    url(r"^coverage/count/$", _swh_coverage_count, name="swh-coverage-count"),
]
