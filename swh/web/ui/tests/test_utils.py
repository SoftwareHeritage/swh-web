# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui import utils


class Rule(object):
    rule = ""
    endpoint = None
    methods = []

    def __init__(self, rule, methods, endpoint):
        self.rule = rule
        self.endpoint = endpoint
        self.methods = methods


class Map(object):
    _rules = []

    def __init__(self, rules):
        self._rules = rules


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.url_map = Map([Rule('/other/<slug>',
                                 methods=set(['GET', 'POST', 'HEAD']),
                                 endpoint='foo'),
                            Rule('/some/old/url/<slug>',
                                 methods=set(['GET', 'POST']),
                                 endpoint='blablafn'),
                            Rule('/other/old/url/<int:id>',
                                 methods=set(['GET', 'HEAD']),
                                 endpoint='bar'),
                            Rule('/other',
                                 methods=set([]),
                                 endpoint=None),
                            Rule('/other2',
                                 methods=set([]),
                                 endpoint=None)])

    @istest
    def filter_endpoints_1(self):
        # when
        actual_data = utils.filter_endpoints(self.url_map, '/some')

        # then
        self.assertEquals(actual_data, {
            '/some/old/url/<slug>': {
                'methods': ['GET', 'POST'],
                'endpoint': 'blablafn'
            }
        })

    @istest
    def filter_endpoints_2(self):
        # when
        actual_data = utils.filter_endpoints(self.url_map, '/other',
                                             blacklist=['/other2'])

        # then
        # rules /other is skipped because its' exactly the prefix url
        # rules /other2 is skipped because it's blacklisted
        self.assertEquals(actual_data, {
            '/other/<slug>': {
                'methods': ['GET', 'HEAD', 'POST'],
                'endpoint': 'foo'
            },
            '/other/old/url/<int:id>': {
                'methods': ['GET', 'HEAD'],
                'endpoint': 'bar'
            }
        })
