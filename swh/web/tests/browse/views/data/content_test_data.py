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

stub_content_text_sha1 = '5ecd9f37b7a2d2e9980d201acd6286116f2ba1f1'

stub_content_text_path = stub_content_root_dir + '/kate/autotests/session_test.h'

stub_content_text_data = {'data': str.encode(stub_content_text_file),
                          'sha1': stub_content_text_sha1}

stub_content_bin_filename = 'swh-logo.png'

png_file_path = os.path.dirname(__file__) + '/' + stub_content_bin_filename

stub_content_bin_sha1 = '02328b91cfad800e1d2808cfb379511b79679ebc'

with open(png_file_path, 'rb') as png_file:
    stub_content_bin_data = {'data': png_file.read(),
                             'sha1': stub_content_bin_sha1}
