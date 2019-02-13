# Copyright (C) 2017-2019  The Software Heritage developers
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

stub_content_text_path = 'kate/autotests/session_test.h'


