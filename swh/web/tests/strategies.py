# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from collections import defaultdict
from datetime import datetime

from hypothesis import settings
from hypothesis.strategies import (
    just, sampled_from, lists, composite, datetimes
)
from string import ascii_letters, hexdigits

from swh.model.hashutil import hash_to_hex
from swh.storage.algos.revisions_walker import get_revisions_walker
from swh.storage.tests.algos.test_snapshot import origins
from swh.web.tests.data import get_tests_data

# Module dedicated to the generation of input data for tests through
# the use of hypothesis.
# Some of these data are sampled from a test archive created and populated
# in the swh.web.tests.data module.

# Set some hypothesis settings
settings.register_profile("swh-web", settings(deadline=None, max_examples=1))
settings.load_profile("swh-web")

# The following strategies exploit the hypothesis capabilities


def _known_swh_object(object_type):
    tests_data = get_tests_data()
    return sampled_from(tests_data[object_type])


def _unknown_swh_object(draw, object_type):
    tests_data = get_tests_data()
    while True:
        sha1_git = draw(sha1())
        if sha1_git not in tests_data[object_type]:
            return sha1_git


def sha1():
    """
    Hypothesis strategy returning a valid hexadecimal sha1 value.
    """
    sha1 = ''.join(random.choice(hexdigits) for x in range(40))
    return just(sha1.lower())


def invalid_sha1():
    """
    Hypothesis strategy returning an invalid sha1 representation.
    """
    invalid_sha1 = ''.join(random.choice(ascii_letters) for x in range(50))
    return just(invalid_sha1.lower())


def sha256():
    """
    Hypothesis strategy returning a valid hexadecimal sha256 value.
    """
    sha256 = ''.join(random.choice(hexdigits) for x in range(64))
    return just(sha256.lower())


def content():
    """
    Hypothesis strategy returning a random content ingested
    into the test archive.
    """
    return _known_swh_object('contents')


def contents():
    """
    Hypothesis strategy returning random contents ingested
    into the test archive.
    """
    return lists(content(), min_size=2, max_size=8)


@composite
def unknown_content(draw):
    """
    Hypothesis strategy returning a random content not ingested
    into the test archive.
    """
    tests_data = get_tests_data()
    while True:
        unknown_content = {
            'blake2s256': draw(sha256()),
            'sha1': draw(sha1()),
            'sha1_git': draw(sha1()),
            'sha256': draw(sha256())
        }
        if unknown_content not in tests_data['contents']:
            return unknown_content


def unknown_contents():
    """
    Hypothesis strategy returning random contents not ingested
    into the test archive.
    """
    return lists(unknown_content(), min_size=2, max_size=8)


def directory():
    """
    Hypothesis strategy returning a random directory ingested
    into the test archive.
    """
    return _known_swh_object('directories')


@composite
def unknown_directory(draw):
    """
    Hypothesis strategy returning a random directory not ingested
    into the test archive.
    """
    return _unknown_swh_object(draw, 'directories')


def origin():
    """
    Hypothesis strategy returning a random origin not ingested
    into the test archive.
    """
    return origins()


def visit_dates():
    """
    Hypothesis strategy returning a list of visit dates.
    """
    return lists(datetimes(min_value=datetime(2015, 1, 1, 0, 0),
                           max_value=datetime(2018, 12, 31, 0, 0)),
                 min_size=2, max_size=8, unique=True)


def release():
    """
    Hypothesis strategy returning a random release ingested
    into the test archive.
    """
    return _known_swh_object('releases')


@composite
def unknown_release(draw):
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return _unknown_swh_object(draw, 'releases')


def revision():
    """
    Hypothesis strategy returning a random revision ingested
    into the test archive.
    """
    return _known_swh_object('revisions')


@composite
def unknown_revision(draw):
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return _unknown_swh_object(draw, 'revisions')


def snapshot():
    """
    Hypothesis strategy returning a random snapshot ingested
    into the test archive.
    """
    return _known_swh_object('snapshots')


@composite
def unknown_snapshot(draw):
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return _unknown_swh_object(draw, 'snapshots')


def _get_origin_dfs_revisions_walker():
    storage = get_tests_data()['storage']
    origin = random.choice(get_tests_data()['origins'])
    snapshot = storage.snapshot_get_latest(origin['id'])
    head = snapshot['branches'][b'HEAD']['target']
    return get_revisions_walker('dfs', storage, head)


def ancestor_revisions():
    """
    Hypothesis strategy returning a pair of revisions ingested into the
    test archive with an ancestor relation.
    """
    # get a dfs revisions walker for one of the origins
    # loaded into the test archive
    revisions_walker = _get_origin_dfs_revisions_walker()
    master_revisions = []
    children = defaultdict(list)
    init_rev_found = False
    # get revisions only authored in the master branch
    for rev in revisions_walker:
        for rev_p in rev['parents']:
            children[rev_p].append(rev['id'])
        if not init_rev_found:
            master_revisions.append(rev)
        if not rev['parents']:
            init_rev_found = True

    # head revision
    root_rev = master_revisions[0]
    # pick a random revision, different from head, only authored
    # in the master branch
    ancestor_rev_idx = random.choice(list(range(1, len(master_revisions)-1)))
    ancestor_rev = master_revisions[ancestor_rev_idx]
    ancestor_child_revs = children[ancestor_rev['id']]

    return just({
        'sha1_git_root': hash_to_hex(root_rev['id']),
        'sha1_git': hash_to_hex(ancestor_rev['id']),
        'children': [hash_to_hex(r) for r in ancestor_child_revs]
    })


def non_ancestor_revisions():
    """
    Hypothesis strategy returning a pair of revisions ingested into the
    test archive with no ancestor relation.
    """
    # get a dfs revisions walker for one of the origins
    # loaded into the test archive
    revisions_walker = _get_origin_dfs_revisions_walker()
    merge_revs = []
    children = defaultdict(list)
    # get all merge revisions
    for rev in revisions_walker:
        if len(rev['parents']) > 1:
            merge_revs.append(rev)
        for rev_p in rev['parents']:
            children[rev_p].append(rev['id'])
    # find a merge revisions whose parents have a unique child revision
    random.shuffle(merge_revs)
    selected_revs = None
    for merge_rev in merge_revs:
        if all(len(children[rev_p]) == 1
               for rev_p in merge_rev['parents']):
            selected_revs = merge_rev['parents']

    return just({
        'sha1_git_root': hash_to_hex(selected_revs[0]),
        'sha1_git': hash_to_hex(selected_revs[1])
    })

# The following strategies returns data specific to some tests
# that can not be generated and thus are hardcoded.


def contents_with_ctags():
    """
    Hypothesis strategy returning contents ingested into the test
    archive. Those contents are ctags compatible, that is running
    ctags on those lay results.
    """
    return just({
        'sha1s': ['0ab37c02043ebff946c1937523f60aadd0844351',
                  '15554cf7608dde6bfefac7e3d525596343a85b6f',
                  '2ce837f1489bdfb8faf3ebcc7e72421b5bea83bd',
                  '30acd0b47fc25e159e27a980102ddb1c4bea0b95',
                  '4f81f05aaea3efb981f9d90144f746d6b682285b',
                  '5153aa4b6e4455a62525bc4de38ed0ff6e7dd682',
                  '59d08bafa6a749110dfb65ba43a61963d5a5bf9f',
                  '7568285b2d7f31ae483ae71617bd3db873deaa2c',
                  '7ed3ee8e94ac52ba983dd7690bdc9ab7618247b4',
                  '8ed7ef2e7ff9ed845e10259d08e4145f1b3b5b03',
                  '9b3557f1ab4111c8607a4f2ea3c1e53c6992916c',
                  '9c20da07ed14dc4fcd3ca2b055af99b2598d8bdd',
                  'c20ceebd6ec6f7a19b5c3aebc512a12fbdc9234b',
                  'e89e55a12def4cd54d5bff58378a3b5119878eb7',
                  'e8c0654fe2d75ecd7e0b01bee8a8fc60a130097e',
                  'eb6595e559a1d34a2b41e8d4835e0e4f98a5d2b5'],
        'symbol_name': 'ABS'
    })
