# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import tempfile
import shutil

from werkzeug import secure_filename


UPLOAD_FOLDER = '/tmp/swh-web-ui/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    """Filter on filename extensions.

    The filename to check for permission.

    """
    # return '.' in filename and \
    #        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    return True


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
    if not file:
        return None, None

    filename = file.filename
    if allowed_file(filename):
        filename = secure_filename(filename)

        tmpdir = tempfile.mkdtemp(suffix='tmp',
                                  prefix='swh.web.ui-',
                                  dir=UPLOAD_FOLDER)

        filepath = os.path.join(tmpdir, filename)
        file.save(filepath)  # persist on disk (not found how to avoid this)

        return tmpdir, filename, filepath


def cleanup(tmpdir):
    """Clean up after oneself.

    Args:
        The directory dir to destroy.
    """
    assert (os.path.commonprefix([UPLOAD_FOLDER, tmpdir]) == UPLOAD_FOLDER)
    shutil.rmtree(tmpdir)
