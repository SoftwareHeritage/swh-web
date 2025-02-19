# Copyright (C) 2018-2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
from typing import Any

from rest_framework import serializers
from rest_framework.request import Request

from swh.model.model import TargetType
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.utils import enrich_snapshot
from swh.web.api.views.utils import api_lookup
from swh.web.config import get_config
from swh.web.utils import archive, reverse

snapshot_content_max_size = get_config()["snapshot_content_max_size"]


class TargetTypesField(serializers.Field):
    """A DRF field to handle snapshot target types."""

    def to_representation(self, value: list[str]) -> str:
        """Serialize value.

        Args:
            value: a list of target types

        Returns:
            A comma separated list of target types
        """

        return ",".join(value)

    def to_internal_value(self, data: str) -> list[str]:
        """From a comma separated string to a list.

        Handles serialization and validation of the target types requested.

        Args:
            data: a comma separated string of target types

        Raises:
            serializers.ValidationError: one or more target types are not valid.

        Returns:
            A list of target types
        """
        choices = [e.value for e in TargetType]
        target_types = [t.strip() for t in data.split(",")]
        if not all(e in choices for e in target_types):
            raise serializers.ValidationError(
                f"Valid target type values are: {', '.join(choices)}"
            )
        return target_types


class SnapshotQuerySerializer(serializers.Serializer):
    """Snapshot query parameters serializer."""

    branches_from = serializers.CharField(default="", required=False)
    branches_count = serializers.IntegerField(
        default=snapshot_content_max_size,
        required=False,
        min_value=0,
        max_value=snapshot_content_max_size,
    )
    target_types = TargetTypesField(default=None, required=False)


@api_route(
    r"/snapshot/(?P<snapshot_id>[0-9a-f]+)/",
    "api-1-snapshot",
    checksum_args=["snapshot_id"],
    query_params_serializer=SnapshotQuerySerializer,
)
@api_doc("/snapshot/", category="Archive")
@format_docstring()
def api_snapshot(
    request: Request,
    snapshot_id: str,
    validated_query_params: dict[str, Any],
):
    """
    .. http:get:: /api/1/snapshot/(snapshot_id)/

        Get information about a snapshot in the archive.

        A snapshot is a set of named branches, which are pointers to objects
        at any level of the Software Heritage DAG. It represents a full picture
        of an origin at a given time.

        As well as pointing to other objects in the Software Heritage DAG,
        branches can also be aliases, in which case their target is the name of
        another branch in the same snapshot, or dangling, in which case the
        target is unknown.

        A snapshot identifier is a salted sha1. See
        :func:`swh.model.git_objects.snapshot_git_object` in our data model
        module for details about how they are computed.

        :param sha1 snapshot_id: a snapshot identifier
        :query str branches_from: optional parameter used to skip branches
            whose name is lesser than it before returning them
        :query int branches_count: optional parameter used to restrain
            the amount of returned branches (default to 1000)
        :query str target_types: optional comma separated list parameter
            used to filter the target types of branch to return (possible
            values that can be contained in that list are ``content``,
            ``directory``, ``revision``, ``release``, ``snapshot`` or
            ``alias``)

        {common_headers}
        {resheader_link}

        :>json object branches: object containing all branches associated to
            the snapshot,for each of them the associated target type and id are
            given but also a link to get information about that target
        :>json string id: the unique identifier of the snapshot

        :statuscode 200: no error
        :statuscode 400: an invalid snapshot identifier or invalid query parameters has
            been provided
        :statuscode 404: requested snapshot cannot be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`snapshot/6a3a2cf0b2b90ce7ae1cf0a221ed68035b686f5a/`
    """
    branches_from = validated_query_params["branches_from"]
    branches_count = validated_query_params["branches_count"]
    target_types = validated_query_params["target_types"]

    results = api_lookup(
        archive.lookup_snapshot,
        snapshot_id,
        branches_from,
        branches_count,
        target_types,
        branch_name_exclude_prefix=None,
        notfound_msg="Snapshot with id {} not found.".format(snapshot_id),
        enrich_fn=enrich_snapshot,
        request=request,
    )

    response = {"results": results, "headers": {}}

    if results["next_branch"] is not None:
        response["headers"]["link-next"] = reverse(
            "api-1-snapshot",
            url_args={"snapshot_id": snapshot_id},
            query_params={
                "branches_from": results["next_branch"],
                "branches_count": str(branches_count),
                "target_types": ",".join(target_types) if target_types else None,
            },
            request=request,
        )

    return response
