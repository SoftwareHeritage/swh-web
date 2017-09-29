# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

import os

stub_content_root_dir = '08e8329257dad3a3ef7adea48aa6e576cd82de5b'

stub_content_text_file = \
"""
/* This file is part of the KDE project
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Library General Public
 *  License as published by the Free Software Foundation; either
 *  version 2 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Library General Public License for more details.
 *
 *  You should have received a copy of the GNU Library General Public License
 *  along with this library; see the file COPYING.LIB.  If not, write to
 *  the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 *  Boston, MA 02110-1301, USA.
 */

#ifndef KATE_SESSION_TEST_H
#define KATE_SESSION_TEST_H

#include <QObject>

class KateSessionTest : public QObject
{
    Q_OBJECT

private Q_SLOTS:
    void init();
    void cleanup();
    void initTestCase();
    void cleanupTestCase();

    void create();
    void createAnonymous();
    void createAnonymousFrom();
    void createFrom();
    void documents();
    void setFile();
    void setName();
    void timestamp();

private:
    class QTemporaryFile *m_tmpfile;
};

#endif
"""

stub_content_text_file_no_highlight = \
"""
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received.  You must make sure that they, too, receive
or can get the source code.  And you must show them these terms so they
know their rights.

  Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

  For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software.  For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

  Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so.  This is fundamentally incompatible with the aim of
protecting users' freedom to change the software.  The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

  Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary.  To prevent this, the GPL assures that
patents cannot be used to render the program non-free.
"""

stub_content_text_sha1 = '5ecd9f37b7a2d2e9980d201acd6286116f2ba1f1'

stub_content_text_no_highlight_sha1 = '94a9ed024d3859793618152ea559a168bbcbb5e2'

stub_content_text_path = 'kate/autotests/session_test.h'

stub_content_text_path_with_root_dir = stub_content_root_dir + '/' + stub_content_text_path

stub_content_text_data = {'data': str.encode(stub_content_text_file),
                          'sha1': stub_content_text_sha1}

stub_content_text_no_highlight_data = {'data': str.encode(stub_content_text_file_no_highlight),
                                       'sha1': stub_content_text_no_highlight_sha1}

stub_content_bin_filename = 'swh-logo.png'

png_file_path = os.path.dirname(__file__) + '/' + stub_content_bin_filename

stub_content_bin_sha1 = '02328b91cfad800e1d2808cfb379511b79679ebc'

with open(png_file_path, 'rb') as png_file:
    stub_content_bin_data = {'data': png_file.read(),
                             'sha1': stub_content_bin_sha1}

stub_content_origin_id = 10357753

stub_content_origin_visit_id = 10

stub_content_origin_visit_ts = 1494032350

stub_content_origin_branch = 'refs/heads/master'

stub_content_origin_visits = [
 {'date': '2015-09-26T09:30:52.373449+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 1},
 {'date': '2016-03-10T05:36:11.118989+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 2},
 {'date': '2016-03-24T07:39:29.727793+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 3},
 {'date': '2016-03-31T22:55:31.402863+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 4},
 {'date': '2016-05-26T06:25:54.879676+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 5},
 {'date': '2016-06-07T17:16:33.964164+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 6},
 {'date': '2016-07-27T01:38:20.345358+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 7},
 {'date': '2016-08-13T04:46:45.987508+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 8},
 {'date': '2016-08-16T23:24:13.214496+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 9},
 {'date': '2016-08-17T18:10:39.841005+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 10},
 {'date': '2016-08-30T17:28:02.476486+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 11},
 {'date': '2016-09-08T09:32:37.152054+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 12},
 {'date': '2016-09-15T09:47:37.758093+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 13},
 {'date': '2016-12-04T06:14:02.688518+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 14},
 {'date': '2017-02-16T08:45:57.719974+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'partial',
  'visit': 15},
 {'date': '2017-05-06T00:59:10.495727+00:00',
  'metadata': {},
  'origin': 10357753,
  'status': 'full',
  'visit': 16}
]

stub_content_origin_branches = [
 {'directory': '08e8329257dad3a3ef7adea48aa6e576cd82de5b',
  'name': 'HEAD',
  'revision': '11f15b0789344427ddf17b8d75f38577c4395ce0'},
 {'directory': '2371baf0411e3adf12d65daf86c3b135633dd5e4',
  'name': 'refs/heads/Applications/14.12',
  'revision': '5b27ad32f8c8da9b6fc898186d59079488fb74c9'},
 {'directory': '5d024d33a218eeb164936301a2f89231d1f0854a',
  'name': 'refs/heads/Applications/15.04',
  'revision': '4f1e29120795ac643044991e91f24d02c9980202'},
 {'directory': 'f33984df50ec29dbbc86295adb81ebb831e3b86d',
  'name': 'refs/heads/Applications/15.08',
  'revision': '52722e588f46a32b480b5f304ba21480fc8234b1'},
 {'directory': 'e706b836cf32929a48b6f92c07766f237f9d068f',
  'name': 'refs/heads/Applications/15.12',
  'revision': '38c4e42c4a653453fc668c704bb8995ae31b5baf'},
 {'directory': 'ebf8ae783b44df5c827bfa46227e5dbe98f25eb4',
  'name': 'refs/heads/Applications/16.04',
  'revision': 'd0fce3b880ab37a551d75ec940137e0f46bf2143'},
 {'directory': '68ea0543fa80cc512d969fc2294d391a904e04fa',
  'name': 'refs/heads/Applications/16.08',
  'revision': '0b05000bfdde06aec2dc6528411ec24c9e20e672'},
 {'directory': 'b9481c652d57b2e0e36c63f2bf795bc6ffa0b6a1',
  'name': 'refs/heads/Applications/16.12',
  'revision': '2a52ca09fce28e29f5afd0ba4622635679036837'},
 {'directory': '415ea4716870c59feabde3210da6f60bcf897479',
  'name': 'refs/heads/Applications/17.04',
  'revision': 'c7ba6cef1ebfdb743e4f3f53f51f44917981524a'},
 {'directory': 'a9d27a5cd354f2f1e50304ef72818141231f7876',
  'name': 'refs/heads/KDE/4.10',
  'revision': 'e0bc3d8ab537d06c817c459f0be7c7f21d670b6e'},
 {'directory': 'a273331f42e6998099ac98934f33431eb244b222',
  'name': 'refs/heads/KDE/4.11',
  'revision': 'e9db108b584aabe88eff1969f408146b0b9eac32'},
 {'directory': '00be5902593157c55a9888b9e5c17c3b416d1f89',
  'name': 'refs/heads/KDE/4.12',
  'revision': 'c2a1c24f28613342985aa40573fb922370900a3a'},
 {'directory': 'f25aa509cc4ad99478a71407850575d267ae4106',
  'name': 'refs/heads/KDE/4.13',
  'revision': 'b739b7a67882408b4378d901c38b2c88108f1312'},
 {'directory': 'e39f1a6967c33635c9e0c3ee627fbd987612417b',
  'name': 'refs/heads/KDE/4.14',
  'revision': 'dd6530d110b165dfeed8dc1b20b8cfab0e4bd25b'},
 {'directory': '5ac8842a402fe3136be5e2ddd31cb24232152994',
  'name': 'refs/heads/KDE/4.7',
  'revision': '776b581f5f724b1179f2fe013c2da835bb0d5cfc'},
 {'directory': '1e6d88a64ecfa70a6883efd977bfd6248344b108',
  'name': 'refs/heads/KDE/4.8',
  'revision': 'fe3723f6ab789ecf21864e198c91092d10a5289b'},
 {'directory': 'aa03927b4d5738c67646509b4b5d55faef03f024',
  'name': 'refs/heads/KDE/4.9',
  'revision': '69121e434e25f8f4c8ee92a1771a8e87913b3559'},
 {'directory': '57844f10b9ade482ece88ae07a406570e5c0b35d',
  'name': 'refs/heads/goinnn-kate-plugins',
  'revision': 'f51e7810338fe5648319a88712d0ce560cc5f847'},
 {'directory': 'eed636cada058599df292eb59180896cd8aeceac',
  'name': 'refs/heads/kfunk/fix-katecompletionmodel',
  'revision': 'dbf7cae67c5db0737fcf37235000b867cd839f3e'},
 {'directory': '08e8329257dad3a3ef7adea48aa6e576cd82de5b',
  'name': 'refs/heads/master',
  'revision': '11f15b0789344427ddf17b8d75f38577c4395ce0'},
 {'directory': '7b5bdcb46cfaa25229af6b038190b004a26397ff',
  'name': 'refs/heads/plasma/sreich/declarative-kate-applet',
  'revision': '51ab3ea145abd3219c3fae06ff99fa911a6a8993'},
 {'directory': 'e39f1a6967c33635c9e0c3ee627fbd987612417b',
  'name': 'refs/pull/1/head',
  'revision': 'dd6530d110b165dfeed8dc1b20b8cfab0e4bd25b'}
]
