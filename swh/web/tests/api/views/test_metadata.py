# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import attr
from hypothesis import given, settings
from hypothesis.strategies import composite, sampled_from, sets
import pytest

from swh.model.hypothesis_strategies import (
    raw_extrinsic_metadata as raw_extrinsic_metadata_orig,
)
from swh.model.hypothesis_strategies import sha1_git
from swh.model.swhids import ExtendedObjectType, ExtendedSWHID, ObjectType
from swh.web.common.utils import reverse
from swh.web.tests.api.views.utils import scroll_results
from swh.web.tests.utils import check_api_get_responses, check_http_get_response


# public Web API endpoint for raw extrinsic metadata does not support
# extended SWHIDs so we ensure only core ones will be used in test inputs.
@composite
def raw_extrinsic_metadata(draw):
    remd = draw(raw_extrinsic_metadata_orig())
    remd = attr.evolve(
        remd,
        target=ExtendedSWHID(
            object_type=ExtendedObjectType(draw(sampled_from(ObjectType)).value),
            object_id=draw(sha1_git()),
        ),
    )
    return attr.evolve(remd, id=remd.compute_hash())


@given(raw_extrinsic_metadata())
def test_api_raw_extrinsic_metadata(api_client, subtest, metadata):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.metadata_authority_add([metadata.authority])
        archive_data.metadata_fetcher_add([metadata.fetcher])
        archive_data.raw_extrinsic_metadata_add([metadata])

        authority = metadata.authority
        url = reverse(
            "api-1-raw-extrinsic-metadata-swhid",
            url_args={"target": str(metadata.target)},
            query_params={"authority": f"{authority.type.value} {authority.url}"},
        )
        rv = check_api_get_responses(api_client, url, status_code=200)

        assert len(rv.data) == 1

        expected_result = metadata.to_dict()
        del expected_result["id"]
        del expected_result["metadata"]
        metadata_url = rv.data[0]["metadata_url"]
        expected_result["metadata_url"] = metadata_url
        expected_result["discovery_date"] = expected_result[
            "discovery_date"
        ].isoformat()
        assert rv.data == [expected_result]

        rv = check_http_get_response(api_client, metadata_url, status_code=200)
        assert rv["Content-Type"] == "application/octet-stream"
        assert (
            rv["Content-Disposition"]
            == f'attachment; filename="{metadata.target}_metadata"'
        )
        assert rv.content == metadata.metadata


@pytest.mark.parametrize("limit", [1, 2, 10, 100])
@settings(max_examples=2)
@given(sets(raw_extrinsic_metadata(), min_size=1))
def test_api_raw_extrinsic_metadata_scroll(api_client, subtest, limit, meta):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        # Make all metadata objects use the same authority and target
        metadata0 = next(iter(meta))
        metadata = {
            attr.evolve(m, authority=metadata0.authority, target=metadata0.target)
            for m in meta
        }
        # Metadata ids must also be updated as they depend on authority and target
        metadata = {attr.evolve(m, id=m.compute_hash()) for m in metadata}
        authority = metadata0.authority

        archive_data.metadata_authority_add([authority])
        archive_data.metadata_fetcher_add(list({m.fetcher for m in metadata}))
        archive_data.raw_extrinsic_metadata_add(metadata)

        url = reverse(
            "api-1-raw-extrinsic-metadata-swhid",
            url_args={"target": str(metadata0.target)},
            query_params={
                "authority": f"{authority.type.value} {authority.url}",
                "limit": limit,
            },
        )

        results = scroll_results(api_client, url)

        expected_results = [m.to_dict() for m in metadata]

        for expected_result in expected_results:
            del expected_result["id"]
            del expected_result["metadata"]
            expected_result["discovery_date"] = expected_result[
                "discovery_date"
            ].isoformat()

        assert len(results) == len(expected_results)

        for result in results:
            del result["metadata_url"]
            assert result in expected_results


_swhid = "swh:1:dir:a2faa28028657859c16ff506924212b33f0e1307"


@pytest.mark.parametrize(
    "status_code,url_args,query_params",
    [
        pytest.param(
            200,
            {"target": _swhid},
            {"authority": "forge http://example.org"},
            id="minimal working",
        ),
        pytest.param(
            200,
            {"target": _swhid},
            {
                "authority": "forge http://example.org",
                "after": "2021-06-18T09:31:09",
                "limit": 100,
            },
            id="maximal working",
        ),
        pytest.param(
            400,
            {"target": _swhid},
            {"authority": "foo http://example.org"},
            id="invalid authority type",
        ),
        pytest.param(
            400,
            {"target": _swhid},
            {
                "authority": "forge http://example.org",
                "after": "yesterday",
            },
            id="invalid 'after' format",
        ),
        pytest.param(
            400,
            {"target": _swhid},
            {
                "authority": "forge http://example.org",
                "limit": "abc",
            },
            id="invalid 'limit'",
        ),
    ],
)
def test_api_raw_extrinsic_metadata_check_params(
    api_client, archive_data, status_code, url_args, query_params
):
    url = reverse(
        "api-1-raw-extrinsic-metadata-swhid",
        url_args=url_args,
        query_params=query_params,
    )
    check_api_get_responses(api_client, url, status_code=status_code)


@given(raw_extrinsic_metadata())
def test_api_raw_extrinsic_metadata_list_authorities(api_client, subtest, metadata):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.metadata_authority_add([metadata.authority])
        archive_data.metadata_fetcher_add([metadata.fetcher])
        archive_data.raw_extrinsic_metadata_add([metadata])

        authority = metadata.authority
        url = reverse(
            "api-1-raw-extrinsic-metadata-swhid-authorities",
            url_args={"target": str(metadata.target)},
        )
        rv = check_api_get_responses(api_client, url, status_code=200)

        expected_results = [
            {
                "type": authority.type.value,
                "url": authority.url,
                "metadata_list_url": "http://testserver"
                + reverse(
                    "api-1-raw-extrinsic-metadata-swhid",
                    url_args={"target": str(metadata.target)},
                    query_params={
                        "authority": f"{authority.type.value} {authority.url}"
                    },
                ),
            }
        ]

        assert rv.data == expected_results
