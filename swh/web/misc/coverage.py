# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

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
        "provider_id": "guix",
        "provider_url": "https://guix.gnu.org/",
        "provider_logo": "img/logos/guix.svg",
        "provider_info": "source code tarballs used to build the Guix package "
        "collection",
        "origin_url_regexp": "^https://guix.gnu.org/",
        "origin_types": "tarballs",
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


urlpatterns = [
    url(r"^coverage/$", _swh_coverage, name="swh-coverage"),
]
