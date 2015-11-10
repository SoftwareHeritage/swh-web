# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import tempfile
import shutil
import werkzeug

from swh.web.ui import main


def allowed_file(filename, allowed_extensions=[]):
    """Filter on filename extension.
    The filename to check for permission.

    Args:
        filename. If no extension on the filename, the filename itself is
        checked against allowed extensions (example of current extensionless
        filenames: README, LICENCE, BUGS, etc...)

    Returns:
        True if allowed, False otherwise.

    """
    if allowed_extensions == []:
        return True
    if '.' in filename:
        return filename.rsplit('.', 1)[1] in allowed_extensions
    return filename in allowed_extensions


def save_in_upload_folder(file):
    """Persist uploaded file on server.

    Args:
        File object (as per Flask's submission form)

    Returns:
        a triplet:
        - the temporary directory holding the persisted file
        - the filename without any path from the file entry
        - the complete path filepath

    """
    main_conf = main.app.config['conf']
    upload_folder = main_conf['upload_folder']
    allowed_extensions = main_conf['upload_allowed_extensions']

    if not file:
        return None, None, None

    filename = file.filename
    if allowed_file(filename, allowed_extensions):
        filename = werkzeug.secure_filename(filename)

        tmpdir = tempfile.mkdtemp(suffix='tmp',
                                  prefix='swh.web.ui-',
                                  dir=upload_folder)

        filepath = os.path.join(tmpdir, filename)
        file.save(filepath)  # persist on disk (not found how to avoid this)

        return tmpdir, filename, filepath
    else:
        raise ValueError(
            'Only %s extensions are valid for upload.' % allowed_extensions)


def cleanup(tmpdir):
    """Clean up after oneself.

    Args:
        The directory dir to destroy.
    """
    upload_folder = main.app.config['conf']['upload_folder']
    assert (os.path.commonprefix([upload_folder, tmpdir]) == upload_folder)
    shutil.rmtree(tmpdir)
