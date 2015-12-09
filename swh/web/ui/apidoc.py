# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui import utils
from swh.web.ui import main
from swh.web.ui.main import app


@app.route('/browse/directory/')
def api_doc_browse_directory_endpoint():
    """List endpoints mounted at /browse/directory/.

    Sample:
        GET /browse/directory/3ece177bd38aaa55dd92ece88cd57a9f083b7660/

    """
    return utils.filter_endpoints(main.rules(), '/browse/directory/')


@app.route('/browse/')
def api_doc_browse_endpoints():
    """List endpoints mounted at /browse/.

    """
    return utils.filter_endpoints(main.rules(), '/browse')


@app.route('/api/')
def api_doc_main_endpoints():
    """List endpoints mounted at /api/.

    """
    return utils.filter_endpoints(main.rules(), '/api')


@app.route('/api/1/')
def api_doc_main_v1_endpoints():
    """List endpoints mounted at /api/1/.

    """
    return utils.filter_endpoints(main.rules(), '/api/1')


@app.route('/api/1/stat/')
def api_doc_stat_main_v1_endpoints():
    """List endpoints mounted at /api/1/stat/.

    """
    return utils.filter_endpoints(main.rules(), '/api/1')
