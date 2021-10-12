# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime
import random

from hypothesis import assume, settings
from hypothesis.extra.dateutil import timezones
from hypothesis.strategies import (
    binary,
    characters,
    composite,
    datetimes,
    lists,
    sampled_from,
    text,
)

from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.hypothesis_strategies import origins as new_origin_strategy
from swh.model.hypothesis_strategies import snapshots as new_snapshot
from swh.model.model import Person, Revision, RevisionType, TimestampWithTimezone
from swh.model.swhids import ObjectType
from swh.web.tests.data import get_tests_data

# Module dedicated to the generation of input data for tests through
# the use of hypothesis.
# Some of these data are sampled from a test archive created and populated
# in the swh.web.tests.data module.

# Set the swh-web hypothesis profile if none has been explicitly set
hypothesis_default_settings = settings.get_profile("default")
if repr(settings()) == repr(hypothesis_default_settings):
    settings.load_profile("swh-web")


# The following strategies exploit the hypothesis capabilities


def _known_swh_object(object_type):
    return sampled_from(get_tests_data()[object_type])


def sha1():
    """
    Hypothesis strategy returning a valid hexadecimal sha1 value.
    """
    return binary(min_size=20, max_size=20).map(hash_to_hex)


def invalid_sha1():
    """
    Hypothesis strategy returning an invalid sha1 representation.
    """
    return binary(min_size=50, max_size=50).map(hash_to_hex)


def sha256():
    """
    Hypothesis strategy returning a valid hexadecimal sha256 value.
    """
    return binary(min_size=32, max_size=32).map(hash_to_hex)


@composite
def new_content(draw):
    blake2s256_hex = draw(sha256())
    sha1_hex = draw(sha1())
    sha1_git_hex = draw(sha1())
    sha256_hex = draw(sha256())

    assume(sha1_hex != sha1_git_hex)
    assume(blake2s256_hex != sha256_hex)

    return {
        "blake2S256": blake2s256_hex,
        "sha1": sha1_hex,
        "sha1_git": sha1_git_hex,
        "sha256": sha256_hex,
    }


def unknown_content():
    """
    Hypothesis strategy returning a random content not ingested
    into the test archive.
    """
    return new_content().filter(
        lambda c: get_tests_data()["storage"].content_get_data(hash_to_bytes(c["sha1"]))
        is None
    )


def unknown_contents():
    """
    Hypothesis strategy returning random contents not ingested
    into the test archive.
    """
    return lists(unknown_content(), min_size=2, max_size=8)


def unknown_directory():
    """
    Hypothesis strategy returning a random directory not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: len(
            list(get_tests_data()["storage"].directory_missing([hash_to_bytes(s)]))
        )
        > 0
    )


def new_origin():
    """
    Hypothesis strategy returning a random origin not ingested
    into the test archive.
    """
    return new_origin_strategy()


def new_origins(nb_origins=None):
    """
    Hypothesis strategy returning random origins not ingested
    into the test archive.
    """
    min_size = nb_origins if nb_origins is not None else 2
    max_size = nb_origins if nb_origins is not None else 8
    size = random.randint(min_size, max_size)
    return lists(
        new_origin(),
        min_size=size,
        max_size=size,
        unique_by=lambda o: tuple(sorted(o.items())),
    )


def visit_dates(nb_dates=None):
    """
    Hypothesis strategy returning a list of visit dates.
    """
    min_size = nb_dates if nb_dates else 2
    max_size = nb_dates if nb_dates else 8
    return lists(
        datetimes(
            min_value=datetime(2015, 1, 1, 0, 0),
            max_value=datetime(2018, 12, 31, 0, 0),
            timezones=timezones(),
        ),
        min_size=min_size,
        max_size=max_size,
        unique=True,
    ).map(sorted)


def unknown_release():
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: get_tests_data()["storage"].release_get([s])[0] is None
    )


def unknown_revision():
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: get_tests_data()["storage"].revision_get([hash_to_bytes(s)])[0]
        is None
    )


@composite
def new_person(draw):
    """
    Hypothesis strategy returning random raw swh person data.
    """
    name = draw(
        text(
            min_size=5,
            max_size=30,
            alphabet=characters(min_codepoint=0, max_codepoint=255),
        )
    )
    email = "%s@company.org" % name
    return Person(
        name=name.encode(),
        email=email.encode(),
        fullname=("%s <%s>" % (name, email)).encode(),
    )


@composite
def new_swh_date(draw):
    """
    Hypothesis strategy returning random raw swh date data.
    """
    timestamp = draw(
        datetimes(
            min_value=datetime(2015, 1, 1, 0, 0), max_value=datetime(2018, 12, 31, 0, 0)
        ).map(lambda d: int(d.timestamp()))
    )
    return {
        "timestamp": timestamp,
        "offset": 0,
        "negative_utc": False,
    }


@composite
def new_revision(draw):
    """
    Hypothesis strategy returning random raw swh revision data
    not ingested into the test archive.
    """
    return Revision(
        directory=draw(sha1().map(hash_to_bytes)),
        author=draw(new_person()),
        committer=draw(new_person()),
        message=draw(text(min_size=20, max_size=100).map(lambda t: t.encode())),
        date=TimestampWithTimezone.from_datetime(draw(new_swh_date())),
        committer_date=TimestampWithTimezone.from_datetime(draw(new_swh_date())),
        synthetic=False,
        type=RevisionType.GIT,
    )


def unknown_revisions(min_size=2, max_size=8):
    """
    Hypothesis strategy returning random revisions not ingested
    into the test archive.
    """
    return lists(unknown_revision(), min_size=min_size, max_size=max_size)


def snapshot():
    """
    Hypothesis strategy returning a random snapshot ingested
    into the test archive.
    """
    return _known_swh_object("snapshots")


def new_snapshots(nb_snapshots=None):
    min_size = nb_snapshots if nb_snapshots else 2
    max_size = nb_snapshots if nb_snapshots else 8
    return lists(
        new_snapshot(min_size=2, max_size=10, only_objects=True),
        min_size=min_size,
        max_size=max_size,
    )


def unknown_snapshot():
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: get_tests_data()["storage"].snapshot_get_branches(hash_to_bytes(s))
        is None
    )


def swhid():
    """
    Hypothesis strategy returning a qualified SWHID for any object
    ingested into the test archive.
    """
    return _known_swh_object("swhids")


def snapshot_swhid():
    """
    Hypothesis strategy returning a qualified SWHID for a snapshot object
    ingested into the test archive.
    """
    return swhid().filter(lambda swhid: swhid.object_type == ObjectType.SNAPSHOT)
