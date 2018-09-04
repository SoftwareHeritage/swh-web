# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import render

import swh.web.browse.views.directory # noqa
import swh.web.browse.views.content # noqa
import swh.web.browse.views.origin_save # noqa
import swh.web.browse.views.origin # noqa
import swh.web.browse.views.person # noqa
import swh.web.browse.views.release # noqa
import swh.web.browse.views.revision # noqa
import swh.web.browse.views.snapshot # noqa

from swh.web.browse.browseurls import BrowseUrls
from swh.web.browse.identifiers import swh_id_browse
from swh.web.config import get_config


def _browse_help_view(request):
    return render(request, 'browse/help.html',
                  {'heading': 'How to browse the archive ?'})


def _browse_search_view(request):
    return render(request, 'browse/search.html',
                  {'heading': 'Search software origins to browse'})


def _browse_vault_view(request):
    return render(request, 'browse/vault-ui.html',
                  {'heading': 'Download archive content from the Vault'})


def _browse_origin_save_view(request):
    return render(request, 'browse/origin-save.html',
                  {'heading': 'Request the saving of a software origin into the archive', # noqa
                   'grecaptcha_site_key': get_config()['grecaptcha']['site_key']}) # noqa


urlpatterns = [
    url(r'^$', _browse_search_view),
    url(r'^help/$', _browse_help_view, name='browse-help'),
    url(r'^search/$', _browse_search_view, name='browse-search'),
    url(r'^vault/$', _browse_vault_view, name='browse-vault'),
    url(r'^origin/save/$', _browse_origin_save_view,
        name='browse-origin-save'),
    # for backward compatibility
    url(r'^(?P<swh_id>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)/$', swh_id_browse)
]

urlpatterns += BrowseUrls.get_url_patterns()
