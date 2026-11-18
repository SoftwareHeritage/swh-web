# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict
import copy
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from django.core.management.base import BaseCommand

from swh.scheduler.model import SchedulerMetrics
from swh.web.archive_coverage import (
    COVERAGE_DATA_CACHE_KEY,
    deposited_origins,
    legacy_origins,
    listed_origins,
)
from swh.web.config import scheduler
from swh.web.utils import cache_set, reverse
from swh.web.utils.archive import count_origins


def get_listers_metrics() -> Dict[str, List[Tuple[str, SchedulerMetrics]]]:
    """Returns scheduler metrics in the following mapping:
    Dict[lister_name, List[Tuple[instance_name, SchedulerMetrics]]]
    as a lister instance has one SchedulerMetrics object per visit type.
    """
    listers_metrics = defaultdict(list)
    listers = scheduler().get_listers()
    scheduler_metrics = scheduler().get_metrics()
    for lister in listers:
        for metrics in filter(lambda m: m.lister_id == lister.id, scheduler_metrics):
            listers_metrics[lister.name].append((lister.instance_name, metrics))

    return listers_metrics


def get_instance_urls() -> Dict[str, str]:
    urls = {}
    for task_type in scheduler().get_task_types():
        if not task_type.type.startswith("list-") or task_type.type == "list-save-bulk":
            continue
        for task in scheduler().search_tasks(task_type=task_type.type):
            kwargs = task.arguments.kwargs
            if url := kwargs.get("url"):
                instance = kwargs.get("instance") or urlparse(url).netloc
                urls[instance] = url
    return urls


# FIXME: remove this once the scheduler database is updated
def adjust_url(origins_type, url):
    API_BASES = {
        "api/v4": {"gitlab", "heptapod"},
        "api/v1": {"gogs", "gitea", "forgejo"},
        "api/diffusion.repository.search": {"phabricator", "phorge"},
    }
    for API_BASE, lister_types in API_BASES.items():
        if origins_type in lister_types:
            if url.endswith(f"/{API_BASE}"):
                return url.removesuffix(API_BASE)
            elif url.endswith(f"/{API_BASE}/"):
                return url.removesuffix(f"{API_BASE}/")
    return url


def update_origins_with_url(origins, urls, origins_type, instance):
    origins["instances"][instance].update(
        {
            "url": origins.get("instances_url_override", {}).get(instance)
            or adjust_url(
                origins_type,
                urls.get(
                    instance,
                    origins.get("instances_url", {}).get(
                        instance, f"https://{instance}"
                    )
                    or origins["info_url"],
                ),
            ),
        }
    )


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


class Command(BaseCommand):
    help = "Generate SWH archive coverage data and store them in django cache"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache-timeout",
            type=int,
            default=None,
            help="optional cache timeout, does not expire by default",
        )

    def handle(self, *args, **options):

        listers_metrics = get_listers_metrics()
        urls = get_instance_urls()

        for origins in listed_origins["origins"]:
            origins["count"] = "0"
            origins["instances"] = {}
            origins_type = origins["type"]

            # special processing for nixos/guix origins
            if origins_type in ("nixos", "guix"):
                main_instance = origins["main_instance"]
                visit_data = listers_metrics.get("nixguix", [])
                visit_type_counts: Dict[str, Dict[str, str]] = defaultdict(dict)
                # visit types from new nixguix lister
                count = 0
                for instance, metrics in visit_data:
                    if instance != main_instance:
                        continue
                    instance_type_count = (
                        metrics.origins_enabled - metrics.origins_never_visited
                    )
                    if instance_type_count > 0:
                        visit_type_counts[metrics.visit_type] = {
                            "count": f"{instance_type_count:,}"
                        }

                    count += instance_type_count

                origins["count"] = f"{count:,}"
                origins["instances"] = {
                    main_instance: {
                        "url": f"https://{main_instance}",
                        "visit_types": dict(visit_type_counts),
                    }
                }

            if origins_type not in listers_metrics:
                continue

            count_total = sum(
                [
                    metrics.origins_enabled
                    for _, metrics in listers_metrics[origins_type]
                ]
            )
            count_never_visited = sum(
                [
                    metrics.origins_never_visited
                    for _, metrics in listers_metrics[origins_type]
                ]
            )
            count_visited = count_total - count_never_visited

            origins["count"] = f"{count_visited:,}"
            origins["instances"] = defaultdict(lambda: defaultdict(dict))
            for instance, metrics in listers_metrics[origins_type]:
                instance_count = metrics.origins_enabled - metrics.origins_never_visited
                # no archived origins for that visit type, skip it
                if instance_count == 0:
                    continue

                update_origins_with_url(origins, urls, origins_type, instance)
                origins["instances"][instance]["visit_types"].update(
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
            for instance_name, instance_data in instances.items():
                visit_types = instance_data["visit_types"]
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
            update_origins_with_url(origins, urls, origins["type"], origins["type"])
            total_count = 0
            for visit_type in origins["visit_types"]:
                count = count_origins(
                    origins["search_pattern"], with_visit=True, visit_types=[visit_type]
                )
                total_count += count
                origins["instances"][origins["type"]]["visit_types"] = {}
                origins["instances"][origins["type"]]["visit_types"][visit_type] = {
                    "count": f"{count:,}",
                    "search_url": _search_url(origins["search_pattern"], visit_type),
                }
            origins["count"] = f"{total_count:,}"

        for origins in deposited_origins["origins"]:
            origins_count = count_origins(
                origins["search_pattern"], with_visit=True, visit_types=["deposit"]
            )
            origins["count"] = f"{origins_count:,}"
            origins["search_urls"] = {
                "deposit": _search_url(origins["search_pattern"], "deposit")
            }

        cache_set(
            COVERAGE_DATA_CACHE_KEY,
            {
                "Regular crawling": listed_origins_filtered,
                "Discontinued hosting": legacy_origins,
                "On demand archival": deposited_origins,
            },
            timeout=options["cache_timeout"],
        )
