# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

# Current coverage list of the archive
# TODO: Retrieve that list dynamically instead of hardcoding it
_code_providers = [
    {
        'provider_url': 'https://www.debian.org/',
        'provider_logo': 'img/logos/debian.png',
        'provider_info': 'source packages from the Debian distribution '
                         '(continuously archived)',
    },
    {
        'provider_url': 'https://github.com',
        'provider_logo': 'img/logos/github.png',
        'provider_info': 'public repositories from GitHub '
                         '(continuously archived)',
    },
    {
        'provider_url': 'https://gitlab.com',
        'provider_logo': 'img/logos/gitlab.svg',
        'provider_info': 'public repositories from GitLab '
                         '(continuously archived)',
    },
    {
        'provider_url': 'https://gitorious.org/',
        'provider_logo': 'img/logos/gitorious.png',
        'provider_info': 'public repositories from the former Gitorious code '
                         'hosting service',
    },
    {
        'provider_url': 'https://code.google.com/archive/',
        'provider_logo': 'img/logos/googlecode.png',
        'provider_info': 'public repositories from the former Google Code '
                         'project hosting service',
    },
    {
        'provider_url': 'https://www.gnu.org',
        'provider_logo': 'img/logos/gnu.png',
        'provider_info': 'releases from the GNU project (as of August 2015)',
    },
    {
        'provider_url': 'https://hal.archives-ouvertes.fr/',
        'provider_logo': 'img/logos/hal.png',
        'provider_info': 'scientific software source code deposited in the '
                         'open archive HAL'
    },
    {
        'provider_url': 'https://gitlab.inria.fr',
        'provider_logo': 'img/logos/inria.jpg',
        'provider_info': 'public repositories from Inria GitLab '
                         '(continuously archived)',
    },
    {
        'provider_url': 'https://pypi.org',
        'provider_logo': 'img/logos/pypi.svg',
        'provider_info': 'source packages from the Python Packaging Index '
                         '(continuously archived)',
    },
]


@xframe_options_exempt
def swh_coverage(request):
    return render(request, 'coverage.html', {'providers': _code_providers})
