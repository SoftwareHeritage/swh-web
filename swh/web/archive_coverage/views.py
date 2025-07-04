# Copyright (C) 2018-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict
import copy
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import attr

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_exempt

from swh.scheduler.model import SchedulerMetrics
from swh.web.config import scheduler
from swh.web.utils import django_cache, reverse
from swh.web.utils.archive import count_origins

_swh_arch_overview_doc = (
    "https://docs.softwareheritage.org/devel/architecture/overview.html"
)

# Current coverage list of the archive in a high level overview fashion,
# categorized as follow:
#   - listed origins: origins discovered using a swh lister
#   - legacy: origins where public hosting service has closed
#   - deposited: origins coming from swh-deposit
#
# TODO: Store that list in a database table somewhere (swh-scheduler, swh-storage ?)
#       and retrieve it dynamically
listed_origins: Dict[str, Any] = {
    "info": (
        "These software origins get continuously discovered and archived using "
        f'the <a href="{_swh_arch_overview_doc}#listers" target="_blank" '
        'rel="noopener noreferrer">listers</a> implemented by Software Heritage.'
    ),
    "origins": [
        {
            "type": "arch",
            "info_url": "https://archlinux.org/",
            "info": "source packages from the Arch Linux distribution",
            "search_pattern": {
                "default": "https://archlinux.org/packages/",
            },
        },
        {
            "type": "aur",
            "info_url": "https://aur.archlinux.org/",
            "info": "source packages from the Arch Linux User Repository",
            "search_pattern": {
                "default": "https://aur.archlinux.org/packages/",
            },
        },
        {
            "type": "bioconductor",
            "info_url": "https://bioconductor.org/",
            "info": "source packages from the Bioconductor project",
            "search_pattern": {
                "default": "https://bioconductor.org/",
            },
        },
        {
            "type": "bitbucket",
            "info_url": "https://bitbucket.org",
            "info": "public repositories from Bitbucket",
            "search_pattern": {
                "default": "https://bitbucket.org/",
            },
        },
        {
            "type": "bower",
            "info_url": "https://bower.io/",
            "info": (
                "git repositories of packages referenced by Bower, "
                "a package manager for the web"
            ),
            "search_pattern": {
                "default": "",
            },
        },
        {
            "type": "cgit",
            "info_url": "https://git.zx2c4.com/cgit/about",
            "info": "public repositories from cgit instances",
            "search_pattern": {
                "default": "cgit",
            },
        },
        {
            "type": "conda",
            "info_url": "https://conda.io/",
            "info": (
                "source packages from the Conda open source package management "
                "system and environment management"
            ),
            "search_pattern": {
                "default": "https://anaconda.org/",
            },
        },
        {
            "type": "cpan",
            "info_url": "https://www.cpan.org/",
            "info": "source packages from The Comprehensive Perl Archive Network",
            "search_pattern": {
                "default": "https://metacpan.org/",
            },
        },
        {
            "type": "cran",
            "info_url": "https://cran.r-project.org",
            "info": "source packages from The Comprehensive R Archive Network",
            "search_pattern": {
                "default": "https://cran.r-project.org/",
            },
        },
        {
            "type": "crates",
            "info_url": "https://crates.io/",
            "info": "source packages from The Rust community's crate registry",
            "search_pattern": {
                "default": "https://crates.io/crates/",
            },
        },
        {
            "type": "dlang",
            "info_url": "https://dlang.org/",
            "info": "public repositories of packages for the D programming language",
            "search_pattern": {
                "default": "",
            },
        },
        {
            "type": "debian",
            "info_url": "https://www.debian.org",
            "info": "source packages from Debian and Debian-based distributions",
            "search_pattern": {
                "default": "deb://",
            },
        },
        {
            "type": "gitea",
            "info_url": "https://gitea.io",
            "info": "public repositories from Gitea instances",
            "search_pattern": {
                "default": "gitea",
            },
        },
        {
            "type": "github",
            "info_url": "https://github.com",
            "info": "public repositories from GitHub",
            "search_pattern": {
                "default": "https://github.com/",
            },
        },
        {
            "type": "gitiles",
            "info_url": "https://github.com/google/gitiles",
            "info": "public repositories from Gitiles instances",
            "search_pattern": {
                "default": "gitiles",
            },
        },
        {
            "type": "gitlab",
            "info_url": "https://gitlab.com",
            "info": "public repositories from multiple GitLab instances",
            "search_pattern": {
                "default": "gitlab",
            },
        },
        {
            "type": "gitweb",
            "info_url": "https://git-scm.com/book/en/v2/Git-on-the-Server-GitWeb",
            "info": "public repositories from GitWeb instances",
            "search_pattern": {
                "default": "gitweb",
            },
        },
        {
            "type": "gogs",
            "info_url": "https://gogs.io/",
            "info": "public repositories from multiple Gogs instances",
            "search_pattern": {
                "default": "gogs",
            },
        },
        {
            "type": "golang",
            "info_url": "https://go.dev/",
            "info": "source packages from the official Go package manager",
            "search_pattern": {
                "default": "https://pkg.go.dev/",
            },
        },
        {
            "type": "guix",
            "info_url": "https://guix.gnu.org",
            "info": "source code tarballs used to build the Guix package collection",
            "search_pattern": {
                "default": "",
                "nixguix": "https://guix.gnu.org/sources.json",
            },
        },
        {
            "type": "GNU",
            "info_url": "https://www.gnu.org",
            "info": "releases from the GNU project (as of August 2015)",
            "search_pattern": {
                "default": "gnu",
            },
        },
        {
            "type": "hackage",
            "info_url": "https://hackage.haskell.org",
            "info": "source packages from The Haskell Package Repository",
            "search_pattern": {
                "default": "https://hackage.haskell.org/package/",
            },
        },
        {
            "type": "heptapod",
            "info_url": "https://heptapod.net/",
            "info": "public repositories from multiple Heptapod instances",
            "search_pattern": {
                "default": "heptapod",
            },
        },
        {
            "type": "launchpad",
            "info_url": "https://launchpad.net",
            "logo": "img/logos/launchpad.png",
            "info": "public repositories from Launchpad",
            "search_pattern": {
                "default": "launchpad.net/",
            },
        },
        {
            "type": "maven",
            "info_url": "https://maven.apache.org/",
            "info": "java source packages from maven repositories",
            "search_pattern": {
                "default": "maven",
                "cvs": "",
                "git": "",
                "hg": "",
                "svn": "",
            },
        },
        {
            "type": "nixos",
            "info_url": "https://nixos.org",
            "info": "source code tarballs used to build the Nix package collection",
            "search_pattern": {
                "default": "",
                "nixguix": "https://nix-community.github.io/nixpkgs-swh/sources-unstable.json",
            },
        },
        {
            "type": "npm",
            "info_url": "https://www.npmjs.com",
            "info": "public packages from the package registry for javascript",
            "search_pattern": {
                "default": "https://www.npmjs.com",
            },
        },
        {
            "type": "opam",
            "info_url": "https://opam.ocaml.org/",
            "info": "public packages from the source-based package manager for OCaml",
            "search_pattern": {
                "default": "opam+https://",
            },
        },
        {
            "type": "Packagist",
            "info_url": "https://packagist.org/",
            "info": "source code repositories referenced by The PHP Package Repository",
            "search_pattern": {
                "default": "",
            },
        },
        {
            "type": "pagure",
            "info_url": "https://pagure.io/pagure",
            "info": "public repositories from multiple Pagure instances",
            "search_pattern": {
                "default": "",
            },
        },
        {
            "type": "phabricator",
            "info_url": "https://www.phacility.com/phabricator",
            "info": "public repositories from multiple Phabricator instances",
            "search_pattern": {
                "default": "phabricator",
            },
        },
        {
            "type": "pubdev",
            "info_url": "https://pub.dev",
            "info": "source packages from the official repository for Dart and Flutter apps",
            "search_pattern": {
                "default": "https://pub.dev",
            },
        },
        {
            "type": "puppet",
            "info_url": "https://forge.puppet.com/",
            "info": "source packages from the Puppet Forge",
            "search_pattern": {
                "default": "https://forge.puppet.com/modules/",
            },
        },
        {
            "type": "pypi",
            "info_url": "https://pypi.org",
            "info": "source packages from the Python Package Index",
            "search_pattern": {
                "default": "https://pypi.org",
            },
        },
        {
            "type": "rpm",
            "info_url": "https://www.redhat.com",
            "info": "source packages from Red Hat based distributions",
            "search_pattern": {
                "default": "rpm",
            },
        },
        {
            "type": "rubygems",
            "info_url": "https://rubygems.org",
            "info": "source packages from the Ruby community's gem hosting service",
            "search_pattern": {
                "default": "https://rubygems.org/gems/",
            },
        },
        {
            "type": "sourceforge",
            "info_url": "https://sourceforge.net",
            "info": "public repositories from SourceForge",
            "search_pattern": {
                "default": "code.sf.net",
                "bzr": "bzr.sourceforge.net",
                "cvs": "cvs.sourceforge.net",
            },
        },
        {
            "type": "stagit",
            "info_url": "https://codemadness.org/stagit.html",
            "info": "public repositories from Stagit instances",
            "search_pattern": {
                "default": "stagit",
            },
        },
    ],
}

legacy_origins: Dict[str, Any] = {
    "info": (
        "Discontinued hosting services. Those origins have been archived "
        "by Software Heritage."
    ),
    "origins": [
        {
            "type": "bitbucket-hg",
            "info_url": "https://bitbucket.org",
            "info": "public mercurial repositories from Bitbucket",
            "search_pattern": "https://bitbucket.org/",
            "visit_types": ["hg"],
        },
        {
            "type": "gitorious",
            "info_url": "https://en.wikipedia.org/wiki/Gitorious",
            "info": (
                "public repositories from the former Gitorious code hosting service"
            ),
            "visit_types": ["git"],
            "search_pattern": "https://gitorious.org",
        },
        {
            "type": "googlecode",
            "info_url": "https://code.google.com/archive",
            "info": (
                "public repositories from the former Google Code project "
                "hosting service"
            ),
            "visit_types": ["git", "hg", "svn"],
            "search_pattern": "googlecode.com",
        },
        {
            "type": "osdn",
            "info_url": "https://en.wikipedia.org/wiki/OSDN",
            "info": (
                "public repositories from the former Open Source Development Network "
                "hosting service"
            ),
            "visit_types": ["cvs", "git", "hg", "svn"],
            "search_pattern": "osdn.net",
        },
    ],
}

deposited_origins: Dict[str, Any] = {
    "info": (
        "These origins are directly pushed into the archive by trusted partners "
        f'using the <a href="{_swh_arch_overview_doc}#deposit" target="_blank" '
        'rel="noopener noreferrer">deposit</a> service of Software Heritage.'
    ),
    "origins": [
        {
            "type": "elife",
            "info_url": "https://elifesciences.org",
            "info": (
                "research software source code associated to the articles "
                "eLife publishes"
            ),
            "search_pattern": "elife.stencila.io",
            "visit_types": ["deposit"],
        },
        {
            "type": "hal",
            "info_url": "https://hal.archives-ouvertes.fr",
            "info": "scientific software source code deposited in the open archive HAL",
            "visit_types": ["deposit"],
            "search_pattern": "hal.archives-ouvertes.fr",
        },
        {
            "type": "ipol",
            "info_url": "https://www.ipol.im",
            "info": "software artifacts associated to the articles IPOL publishes",
            "visit_types": ["deposit"],
            "search_pattern": "doi.org/10.5201/ipol",
        },
        {
            "type": "zenodo",
            "info_url": "https://zenodo.org/",
            "info": "software source code deposited in the Open Science platform Zenodo",
            "visit_types": ["deposit"],
            "search_pattern": "doi.org/10.5281/zenodo",
        },
    ],
}

_cache_timeout = 60 * 60  # one hour


def _get_listers_metrics(
    cache_metrics: bool = False,
) -> Dict[str, List[Tuple[str, SchedulerMetrics]]]:
    """Returns scheduler metrics in the following mapping:
    Dict[lister_name, List[Tuple[instance_name, SchedulerMetrics]]]
    as a lister instance has one SchedulerMetrics object per visit type.
    """

    @django_cache(
        timeout=_cache_timeout,
        catch_exception=True,
        exception_return_value={},
        invalidate_cache_pred=lambda m: not cache_metrics,
        extra_encoders=[(SchedulerMetrics, "scheduler_metrics", attr.asdict)],
        extra_decoders={"scheduler_metrics": lambda d: SchedulerMetrics(**d)},
    )
    def _get_listers_metrics_internal():
        listers_metrics = defaultdict(list)
        listers = scheduler().get_listers()
        scheduler_metrics = scheduler().get_metrics()
        for lister in listers:
            for metrics in filter(
                lambda m: m.lister_id == lister.id, scheduler_metrics
            ):
                listers_metrics[lister.name].append((lister.instance_name, metrics))

        return listers_metrics

    return _get_listers_metrics_internal()


def _get_origins_count(
    url_pattern: str, visit_type: str, cache_counts: bool = False
) -> int:
    """Return origin counts per origin url pattern and visit type."""

    @django_cache(
        timeout=_cache_timeout,
        catch_exception=True,
        exception_return_value=0,
        invalidate_cache_pred=lambda m: not cache_counts,
    )
    def _get_origins_count_internal(url_pattern: str, visit_type: str) -> int:
        return count_origins(url_pattern, with_visit=True, visit_types=[visit_type])

    return _get_origins_count_internal(url_pattern, visit_type)


def _search_url(query: str, visit_type: str) -> str:
    return reverse(
        "browse-search",
        query_params={
            "q": query,
            "visit_type": visit_type,
            "with_visit": "true",
            "with_content": "true",
        },
    )


@xframe_options_exempt
@never_cache
def swh_coverage(request: HttpRequest) -> HttpResponse:
    listers_metrics = _get_listers_metrics(cache_metrics=True)

    for origins in listed_origins["origins"]:
        origins["count"] = "0"
        origins["instances"] = {}
        origins_type = origins["type"]

        # special processing for nixos/guix origins
        if origins_type in ("nixos", "guix"):
            manifest_url = origins["search_pattern"]["nixguix"]
            lister_instance = urlparse(manifest_url).netloc
            visit_data = listers_metrics.get("nixguix", [])
            visit_type_counts = {}
            # visit types from new nixguix lister
            for instance, metrics in visit_data:
                if instance != lister_instance:
                    continue
                visit_type_counts[metrics.visit_type] = (
                    metrics.origins_enabled - metrics.origins_never_visited
                )

            count = sum(visit_type_counts.values())
            origins["count"] = f"{count:,}"
            origins["instances"][lister_instance] = {
                key: {"count": f"{value:,}"}
                for key, value in visit_type_counts.items()
                if value > 0
            }

        if origins_type not in listers_metrics:
            continue

        count_total = sum(
            [metrics.origins_enabled for _, metrics in listers_metrics[origins_type]]
        )
        count_never_visited = sum(
            [
                metrics.origins_never_visited
                for _, metrics in listers_metrics[origins_type]
            ]
        )
        count_visited = count_total - count_never_visited

        origins["count"] = f"{count_visited:,}"
        origins["instances"] = defaultdict(dict)
        for instance, metrics in listers_metrics[origins_type]:
            instance_count = metrics.origins_enabled - metrics.origins_never_visited
            # no archived origins for that visit type, skip it
            if instance_count == 0:
                continue

            origins["instances"][instance].update(
                {metrics.visit_type: {"count": f"{instance_count:,}"}}
            )
            origins["visit_types"] = list(
                set(origins["instances"][instance].keys())
                | set(origins.get("visit_types", []))
            )

        # defaultdict cannot be iterated in django template
        origins["instances"] = dict(sorted(origins["instances"].items()))

    for origins in listed_origins["origins"]:
        instances = origins["instances"]
        nb_instances = len(instances)
        for instance_name, visit_types in instances.items():
            for visit_type in visit_types:
                search_url = ""
                if visit_type in origins["search_pattern"]:
                    search_pattern = origins["search_pattern"][visit_type]
                elif nb_instances > 1:
                    search_pattern = instance_name
                else:
                    search_pattern = origins["search_pattern"]["default"]
                if search_pattern:
                    search_url = _search_url(search_pattern, visit_type)
                visit_types[visit_type]["search_url"] = search_url

    # use a light copy to avoid side effects when running tests
    listed_origins_filtered = copy.copy(listed_origins)
    # filter out origin types without archived origins
    listed_origins_filtered["origins"] = list(
        filter(lambda o: o["count"] != "0", listed_origins_filtered["origins"])
    )

    for origins in legacy_origins["origins"]:
        origins["instances"] = {origins["type"]: {}}
        total_count = 0
        for visit_type in origins["visit_types"]:
            count = _get_origins_count(
                origins["search_pattern"], visit_type=visit_type, cache_counts=True
            )
            total_count += count
            origins["instances"][origins["type"]][visit_type] = {
                "count": f"{count:,}",
                "search_url": _search_url(origins["search_pattern"], visit_type),
            }
        origins["count"] = f"{total_count:,}"

    for origins in deposited_origins["origins"]:
        origins["count"] = (
            f"{_get_origins_count(origins['search_pattern'], 'deposit', cache_counts=True):,}"
        )
        origins["search_urls"] = {
            "deposit": _search_url(origins["search_pattern"], "deposit")
        }

    focus = []
    focus_param = request.GET.get("focus")
    if focus_param:
        focus = focus_param.split(",")

    return render(
        request,
        "archive-coverage.html",
        {
            "origins": {
                "Regular crawling": listed_origins_filtered,
                "Discontinued hosting": legacy_origins,
                "On demand archival": deposited_origins,
            },
            "focus": focus,
        },
    )
