# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest
from unittest.mock import patch, MagicMock

from swh.web.ui import upload
from swh.web.ui.tests import test_app


class UploadTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.config, cls.storage, _ = test_app.create_app()

    @istest
    def allowed_file_ok(self):
        # when
        actual_perm = upload.allowed_file('README')
        self.assertTrue(actual_perm)

        # when
        actual_perm2 = upload.allowed_file('README', [])
        self.assertTrue(actual_perm2)

        # when
        actual_perm3 = upload.allowed_file('README', ['README',
                                                      'LICENCE',
                                                      'BUGS'])
        self.assertTrue(actual_perm3)

        # when
        actual_perm4 = upload.allowed_file('some-filename.txt', ['txt',
                                                                 'blah',
                                                                 'gz'])
        self.assertTrue(actual_perm4)

        # when
        actual_perm5 = upload.allowed_file('something.tar.gz', ['gz',
                                                                'txt',
                                                                'tar.gz'])
        # then
        self.assertTrue(actual_perm5)

    @istest
    def allowed_file_denied(self):
        # when
        actual_perm = upload.allowed_file('some-filename', ['blah'])
        self.assertFalse(actual_perm)

        # when
        actual_perm = upload.allowed_file('something.tgz', ['gz',
                                                            'txt',
                                                            'tar.gz'])
        # then
        self.assertFalse(actual_perm)

    @patch('swh.web.ui.upload.os.path')
    @patch('swh.web.ui.upload.shutil')
    @istest
    def cleanup_ok(self, mock_shutil, mock_os_path):
        # given
        mock_os_path.commonprefix.return_value = '/some/upload-dir'
        mock_shutil.rmtree.return_value = True

        # when
        upload.cleanup('/some/upload-dir/some-dummy-path')

        # then
        mock_os_path.commonprefix.assert_called_with(
            ['/some/upload-dir', '/some/upload-dir/some-dummy-path'])
        mock_shutil.rmtree.assert_called_with(
            '/some/upload-dir/some-dummy-path')

    @patch('swh.web.ui.upload.os.path')
    @patch('swh.web.ui.upload.shutil')
    @istest
    def cleanup_should_fail(self, mock_shutil, mock_os_path):
        # given
        mock_os_path.commonprefix.return_value = '/somewhere/forbidden'
        mock_shutil.rmtree.return_value = True

        # when
        with self.assertRaises(AssertionError):
            upload.cleanup('/some/upload-dir/some-dummy-path')

        # then
        mock_os_path.commonprefix.assert_called_with(
            ['/some/upload-dir', '/some/upload-dir/some-dummy-path'])
        self.assertTrue(mock_shutil.rmtree.not_called)

    @istest
    def save_in_upload_folder_no_file(self):
        # when
        act_tmpdir, act_name, act_path = upload.save_in_upload_folder(None)

        # then
        self.assertIsNone(act_tmpdir)
        self.assertIsNone(act_name)
        self.assertIsNone(act_path)

    @istest
    def save_in_upload_folder_file_not_allowed(self):
        # given
        file = MagicMock()
        file.filename = 'some-non-file-allowed.ext'

        # when
        with self.assertRaises(ValueError) as exc:
            act_tmpdir, act_name, act_path = upload.save_in_upload_folder(file)

        # then
        self.assertIn('Only', exc.exception.args[0])
        self.assertIn('extensions are valid for upload', exc.exception.args[0])

    @patch('swh.web.ui.upload.werkzeug')
    @patch('swh.web.ui.upload.tempfile')
    @istest
    def save_in_upload_folder_OK(self, mock_tempfile, mock_werkzeug):
        # given
        upload_folder = self.config['conf']['upload_folder']

        # mock the dependencies
        mock_werkzeug.secure_filename.return_value = 'some-allowed-file.txt'
        tmpdir = upload_folder + '/foobar/'
        mock_tempfile.mkdtemp.return_value = tmpdir

        # mock the input
        file = MagicMock()
        file.filename = 'some-allowed-file.txt'

        # when
        act_tmpdir, act_name, act_path = upload.save_in_upload_folder(file)

        # then
        expected_tmpdir = tmpdir
        expected_filename = 'some-allowed-file.txt'
        expected_filepath = tmpdir + 'some-allowed-file.txt'

        self.assertEqual(act_tmpdir, expected_tmpdir)
        self.assertEqual(act_name, expected_filename)
        self.assertEqual(act_path, expected_filepath)

        mock_werkzeug.secure_filename.assert_called_with(expected_filename)
        file.save.assert_called_once_with(expected_filepath)

        mock_tempfile.mkdtemp.assert_called_with(
            suffix='tmp',
            prefix='swh.web.ui-',
            dir=upload_folder)
