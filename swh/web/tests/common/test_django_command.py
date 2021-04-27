# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from io import StringIO

import pytest

from django.core.management import call_command


@pytest.mark.parametrize("nb_results", [0, 10, 20])
def test_command_refresh__with_statuses_refreshed(mocker, nb_results):
    """Refresh status command reported updated non-terminal statuses.

    """
    command_name = "refresh_savecodenow_statuses"
    module_fqdn = "swh.web.common.management.commands"
    mock_refresh = mocker.patch(
        f"{module_fqdn}.{command_name}.refresh_save_origin_request_statuses"
    )
    # fake returned refreshed status
    mock_refresh.return_value = [{"": ""}] * nb_results

    out = StringIO()
    call_command(command_name, stdout=out)

    assert mock_refresh.called

    actual_output = out.getvalue()
    if nb_results > 0:
        assert f"updated {nb_results}" in actual_output
    else:
        assert "Nothing" in actual_output
