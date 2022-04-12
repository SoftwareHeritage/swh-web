# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.config import get_config, is_feature_enabled


@pytest.mark.parametrize(
    "feature_name",
    ["inexistant-feature", "awesome-stuff"],
)
def test_is_feature_enabled(feature_name):
    config = get_config()
    # by default, feature non configured are considered disabled
    assert is_feature_enabled(feature_name) is False

    for enabled in [True, False]:
        # Let's configure the feature
        config["features"] = {feature_name: enabled}
        # and check its configuration is properly read
        assert is_feature_enabled(feature_name) is enabled
