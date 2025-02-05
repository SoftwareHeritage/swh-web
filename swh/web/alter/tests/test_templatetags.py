# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from bs4 import BeautifulSoup

from swh.web.alter.forms import OriginSearchForm
from swh.web.alter.models import AlterationStatus, OriginOutcome
from swh.web.alter.templatetags.alter_extras import (
    absolute_url,
    bootstrap_field_submit,
    outcome_badge,
    status_badge,
)


def test_absolute_url_outside_request():
    assert absolute_url({}, "abc/def") == "abc/def"


def test_absolute_url_path(rf):
    request = rf.get("/")  # RequestFactory sets `testserver` as the default host
    assert absolute_url({"request": request}, "abc/def") == "http://testserver/abc/def"


def test_absolute_url_route(rf, alteration):
    request = rf.get("/")
    url = absolute_url(
        {"request": request},
        "alteration-admin",
        pk=alteration.pk,
    )
    assert alteration.get_admin_url() in url


def test_outcome_badge():
    for value in OriginOutcome:
        assert "my label" in outcome_badge(value, "my label")
    assert "text-bg-secondary" in outcome_badge("test fallback", "my label")


def test_status_badge():
    for value in AlterationStatus:
        assert "my label" in status_badge(value, "my label")
    assert "text-bg-secondary" in status_badge("test fallback", "my label")


def test_bootstrap_field_submit():
    form = OriginSearchForm()
    html = bootstrap_field_submit(form["query"], "Software Heritage")
    soup = BeautifulSoup(html, "lxml")
    assert soup.find("label", class_="visually-hidden")
    button = soup.find("button", type="submit")
    assert button.text == "Software Heritage"
    assert soup.find("input", class_="form-control")
