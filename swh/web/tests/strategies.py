# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime

from hypothesis.extra.dateutil import timezones
from hypothesis.strategies import composite, datetimes, lists, text

from swh.model.hypothesis_strategies import origins as new_origin_strategy
from swh.model.hypothesis_strategies import persons as new_person_strategy
from swh.model.hypothesis_strategies import sha1_git
from swh.model.hypothesis_strategies import snapshots as new_snapshot
from swh.model.model import Revision, RevisionType, TimestampWithTimezone

# Module dedicated to the generation of input data for tests through
# the use of hypothesis.


def new_origin():
    """Hypothesis strategy returning a random origin not ingested
    into the test archive.
    """
    return new_origin_strategy()


def visit_dates(nb_dates=None):
    """Hypothesis strategy returning a list of visit dates."""
    min_size = nb_dates if nb_dates else 2
    max_size = nb_dates if nb_dates else 8
    return lists(
        datetimes(
            min_value=datetime(2015, 1, 1, 0, 0),
            max_value=datetime.now(),
            timezones=timezones(),
        ),
        min_size=min_size,
        max_size=max_size,
        unique=True,
    ).map(sorted)


def new_person():
    """Hypothesis strategy returning random raw swh person data."""
    return new_person_strategy()


@composite
def new_swh_date(draw):
    """Hypothesis strategy returning random raw swh date data."""
    timestamp = draw(
        datetimes(min_value=datetime(2015, 1, 1, 0, 0), max_value=datetime.now()).map(
            lambda d: int(d.timestamp())
        )
    )
    return {
        "timestamp": timestamp,
        "offset": 0,
        "negative_utc": False,
    }


@composite
def new_revision(draw):
    """Hypothesis strategy returning random raw swh revision data
    not ingested into the test archive.
    """
    return Revision(
        directory=draw(sha1_git()),
        author=draw(new_person()),
        committer=draw(new_person()),
        message=draw(text(min_size=20, max_size=100).map(lambda t: t.encode())),
        date=TimestampWithTimezone.from_datetime(draw(new_swh_date())),
        committer_date=TimestampWithTimezone.from_datetime(draw(new_swh_date())),
        synthetic=False,
        type=RevisionType.GIT,
    )


def new_snapshots(nb_snapshots=None):
    min_size = nb_snapshots if nb_snapshots else 2
    max_size = nb_snapshots if nb_snapshots else 8
    return lists(
        new_snapshot(min_size=2, max_size=10, only_objects=True),
        min_size=min_size,
        max_size=max_size,
    )
