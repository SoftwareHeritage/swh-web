# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
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

stub_content_text_data = {
    'checksums': {
        'sha1': '5ecd9f37b7a2d2e9980d201acd6286116f2ba1f1',
        'sha1_git': '537b47f68469c1c916c1bfbc072599133bfcbb21',
        'sha256': 'b3057544f04e5821ab0e2a007e2ceabd7de2dfb1d42a764f1de8d0d2eff80006',
        'blake2s256': '25117fa9f124d5b771a0a7dfca9c7a57247d81f8343334b4b41c782c7f7ed64d'
    },
    'length': 1317,
    'raw_data': str.encode(stub_content_text_file),
    'mimetype': 'text/x-c++',
    'encoding': 'us-ascii',
    'language': 'c++',
    'licenses': 'GPL',
    'error_code': 200,
    'error_message': '',
    'error_description': ''
}

stub_content_text_no_highlight_data = {
    'checksums': {
        'sha1': '8624bcdae55baeef00cd11d5dfcfa60f68710a02',
        'sha1_git': '94a9ed024d3859793618152ea559a168bbcbb5e2',
        'sha256': '8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903',
        'blake2s256': '38702b7168c7785bfe748b51b45d9856070ba90f9dc6d90f2ea75d4356411ffe'
    },
    'length': 35147,
    'raw_data': str.encode(stub_content_text_file_no_highlight),
    'mimetype': 'text/plain',
    'encoding': 'us-ascii',
    'language': 'not detected',
    'licenses': 'GPL',
    'error_code': 200,
    'error_message': '',
    'error_description': ''
}

stub_content_text_path = 'kate/autotests/session_test.h'

stub_content_text_path_with_root_dir = stub_content_root_dir + '/' + stub_content_text_path

stub_content_bin_filename = 'swh-logo.png'

png_file_path = os.path.dirname(__file__) + '/' + stub_content_bin_filename

with open(png_file_path, 'rb') as png_file:
    stub_content_bin_data = {
        'checksums': {
            'sha1': 'd0cec0fc2d795f0077c18d51578cdb228eaf6a99',
            'sha1_git': '02328b91cfad800e1d2808cfb379511b79679ebc',
            'sha256': 'e290592e2cfa9767497011bda4b7e273b4cf29e7695d72ecacbd723008a29144',
            'blake2s256': '7177cad95407952e362ee326a800a9d215ccd619fdbdb735bb51039be81ab9ce'
        },
        'length': 18063,
        'raw_data': png_file.read(),
        'mimetype': 'image/png',
        'encoding': 'binary',
        'language': 'not detected',
        'licenses': 'not detected',
        'error_code': 200,
        'error_message': '',
        'error_description': ''
    }

_non_utf8_encoding_file_path = os.path.dirname(__file__) + '/iso-8859-1_encoded_content'

non_utf8_encoded_content_data = {
    'checksums': {
        'sha1': '62cb71aa3534a03c12572157d20fa893753b03b6',
        'sha1_git': '2f7470d0b26108130e71087e42a53c032473499c',
        'sha256': 'aaf364ccd3acb546829ccc0e8e5e293e924c8a2e55a67cb739d249016e0034ed',
        'blake2s256': 'b7564932460a7c2697c53bd55bd855272490da511d64b20c5a04f636dc9ac467'
    },
    'length': 111000,
    'error_code': 200,
    'error_message': '',
    'error_description': ''
}

non_utf8_encoding = 'iso-8859-1'

with open(_non_utf8_encoding_file_path, 'rb') as iso88591_file:
    non_utf8_encoded_content = iso88591_file.read()

stub_content_too_large_data = {
    'checksums': {
        'sha1': '8624bcdae55baeef00cd11d5dfcfa60f68710a02',
        'sha1_git': '94a9ed024d3859793618152ea559a168bbcbb5e2',
        'sha256': '8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903',
        'blake2s256': '38702b7168c7785bfe748b51b45d9856070ba90f9dc6d90f2ea75d4356411ffe'
    },
    'length': 3000000,
    'raw_data': None,
    'mimetype': 'text/plain',
    'encoding': 'us-ascii',
    'language': 'not detected',
    'licenses': 'GPL',
    'error_code': 200,
    'error_message': '',
    'error_description': ''
}