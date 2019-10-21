Origin
^^^^^^

This describes the URI scheme when one wants to browse the Software Heritage
archive in the context of an origin (for instance, a repository crawled from
GitHub or a Debian source package). All the views pointed by that scheme
offer quick links to browse objects as found during the associated crawls
performed by Software Heritage:

    * the root directory of the origin
    * the list of branches of the origin
    * the list of releases of the origin

Origin visits
"""""""""""""

.. http:get:: /browse/origin/(origin_url)/visits/

    HTML view that displays a visits reporting for a software origin identified by
    its type and url.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/torvalds/linux/visits/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visits/`
        :swh_web_browse:`origin/deb://Debian-Security/packages/mediawiki/visits/`
        :swh_web_browse:`origin/https://gitorious.org/qt/qtbase.git/visits/`


Origin directory
""""""""""""""""

.. http:get:: /browse/origin/(origin_url)/directory/[(path)/]

    HTML view for browsing the content of a directory reachable from the root directory
    (including itself) associated to the latest full visit of a software origin.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the origin root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    and releases through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory
    content can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string path: optional parameter used to specify the path of a directory
        reachable from the origin root one
    :query string branch: specify the origin branch name from which
        to retrieve the root directory
    :query string release: specify the origin release name from which
        to retrieve the root directory
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the root directory
    :query int visit_id: specify a visit id to retrieve the directory from instead
        of using the latest full visit by default
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive
        or the provided path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/torvalds/linux/directory/`
        :swh_web_browse:`origin/https://github.com/torvalds/linux/directory/net/ethernet/`
        :swh_web_browse:`origin/https://github.com/python/cpython/directory/`
        :swh_web_browse:`origin/https://github.com/python/cpython/directory/Python/`
        :swh_web_browse:`origin/https://github.com/python/cpython/directory/?branch=refs/heads/2.7`


.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/directory/[(path)/]

    HTML view for browsing the content of a directory reachable from
    the root directory (including itself) associated to a visit of a software
    origin closest to a provided timestamp.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the origin root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    and releases through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory
    content can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: a date string (any format parsable by `dateutil.parser.parse`_)
        or Unix timestamp to parse in order to find the closest visit.
    :param path: optional parameter used to specify the path of a directory
        reachable from the origin root one
    :type path: string
    :query string branch: specify the origin branch name from which
        to retrieve the root directory
    :query string release: specify the origin release name from which
        to retrieve the root directory
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the directory
    :query int visit_id: specify a visit id to retrieve the directory from instead
        of using the provided timestamp
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive,
        requested visit timestamp does not exist or the provided path does
        not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/torvalds/linux/visit/1493926809/directory/`
        :swh_web_browse:`origin/https://github.com/torvalds/linux/visit/2016-09-14T10:36:21/directory/net/ethernet/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visit/1474620651/directory/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visit/2017-05-05/directory/Python/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visit/2015-08/directory/?branch=refs/heads/2.7`


Origin content
""""""""""""""

.. http:get:: /browse/origin/(origin_url)/content/(path)/

    HTML view that produces a display of a content
    associated to the latest full visit of a software origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. The procedure to perform that task is described
    in :http:get:`/browse/content/[(algo_hash):](hash)/`.

    It is also possible to highlight specific lines of a textual
    content (not in terms of syntax highlighting but to emphasize
    some relevant content part) by either:

        * clicking on line numbers (holding shift to highlight a lines range)

        * using an url fragment in the form '#Ln' or '#Lm-Ln'

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    and releases through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch name from which
        to retrieve the content
    :query string release: specify the origin release name from which
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the content
    :query int visit_id: specify a visit id to retrieve the content from instead
        of using the latest full visit by default
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive,
        or the provided content path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/git/git/content/git.c/`
        :swh_web_browse:`origin/https://github.com/git/git/content/git.c/`
        :swh_web_browse:`origin/https://github.com/mozilla/gecko-dev/content/js/src/json.cpp/`
        :swh_web_browse:`origin/https://github.com/git/git/content/git.c/?branch=refs/heads/next`

.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/content/(path)/

    HTML view that produces a display of a content associated to a
    visit of a software origin closest to a provided timestamp.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. The procedure to perform that task is described
    in :http:get:`/browse/content/[(algo_hash):](hash)/`.

    It is also possible to highlight specific lines of a textual
    content (not in terms of syntax highlighting but to emphasize
    some relevant content part) by either:

        * clicking on line numbers (holding shift to highlight a lines range)

        * using an url fragment in the form '#Ln' or '#Lm-Ln'


    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    and releases through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: a date string (any format parsable by `dateutil.parser.parse`_)
        or Unix timestamp to parse in order to find the closest visit.
    :param string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch name from which
        to retrieve the content
    :query string release: specify the origin release name from which
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the content
    :query int visit_id: specify a visit id to retrieve the content from instead
        of using the provided timestamp
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive,
        requested visit timestamp does not exist or the provided content path does
        not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/git/git/visit/1473933564/content/git.c/`
        :swh_web_browse:`origin/https://github.com/git/git/visit/2016-05-05T00:0:00+00:00/content/git.c/`
        :swh_web_browse:`origin/https://github.com/mozilla/gecko-dev/visit/1490126182/content/js/src/json.cpp/`
        :swh_web_browse:`origin/https://github.com/mozilla/gecko-dev/visit/2017-03-21/content/js/src/json.cpp/#L904-L931`
        :swh_web_browse:`origin/https://github.com/git/git/visit/2017-09-15/content/git.c/?branch=refs/heads/next`


Origin history
""""""""""""""

.. http:get:: /browse/origin/(origin_url)/log/

    HTML view that produces a display of revisions history heading
    to the last revision found during the latest visit of a software origin.
    In other words, it shows the commit log associated to the latest
    full visit of a software origin.

    The following data are displayed for each log entry:

        * link to browse the associated revision in the origin context
        * author of the revision
        * date of the revision
        * message associated the revision
        * commit date of the revision

    By default, the revisions are ordered in reverse chronological order of
    their commit date.

    N log entries are displayed per page (default is 100). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * **Newer**: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * **Older**: fetch and display if available the N older log entries
          than the ones currently displayed

    The view also enables to easily switch between the origin branches
    and releases through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :query int per_page: the number of log entries to display per page
    :query int offset: the number of revisions to skip before returning those to display
    :query str revs_ordering: specify the revisions ordering, possible values are ``committer_date``,
        ``dfs``, ``dfs_post`` and ``bfs``
    :query string branch: specify the origin branch name from which
        to retrieve the commit log
    :query string release: specify the origin release name from which
        to retrieve the commit log
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the commit log
    :query int visit_id: specify a visit id to retrieve the history log from instead
        of using the latest visit by default
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/videolan/vlc/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/log/?branch=refs/heads/release`


.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/log/

    HTML view that produces a display of revisions history heading
    to the last revision found during a visit of a software origin closest
    to the provided timestamp.
    In other words, it shows the commit log associated to a visit of
    a software origin closest to a provided timestamp.

    The following data are displayed for each log entry:

        * author of the revision
        * link to the revision metadata
        * message associated the revision
        * date of the revision
        * link to browse the associated source tree in the origin context

    N log entries are displayed per page (default is 20). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * **Newer**: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * **Older**: fetch and display if available the N older log entries
          than the ones currently displayed

    The view also enables to easily switch between the origin branches
    and releases through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: a date string (any format parsable by `dateutil.parser.parse`_)
        or Unix timestamp to parse in order to find the closest visit.
    :query string revs_breadcrumb: used internally to store
        the navigation breadcrumbs (i.e. the list of descendant revisions
        visited so far). It must be a string in the form
        "(rev_1)[/(rev_2)/.../(rev_n)]" where rev_i corresponds to a
        revision **sha1_git**.
    :query int per_page: the number of log entries to display per page
        (default is 20, max is 50)
    :query string branch: specify the origin branch name from which
        to retrieve the commit log
    :query string release: specify the origin release name from which
        to retrieve the commit log
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the commit log
    :query int visit_id: specify a visit id to retrieve the history log from instead
        of using the provided timestamp
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/videolan/vlc/visit/1459651262/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/2016-04-01/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/1438116814/log/?branch=refs/heads/release`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/2017-05-05T03:14:23/log/?branch=refs/heads/release`

Origin branches
"""""""""""""""

.. http:get:: /browse/origin/(origin_url)/branches/

    HTML view that produces a display of the list of branches
    found during the latest full visit of a software origin.

    The following data are displayed for each branch:

        * its name
        * a link to browse the associated directory
        * a link to browse the associated revision
        * last commit message
        * last commit date

    That list of branches is paginated, each page displaying a maximum of 100 branches.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/deb://Debian/packages/linux/branches/`
        :swh_web_browse:`origin/https://github.com/webpack/webpack/branches/`

.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/branches/

    HTML view that produces a display of the list of branches
    found during a visit of a software origin closest to the provided timestamp.

    The following data are displayed for each branch:

        * its name
        * a link to browse the associated directory
        * a link to browse the associated revision
        * last commit message
        * last commit date

    That list of branches is paginated, each page displaying a maximum of 100 branches.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: a date string (any format parsable by `dateutil.parser.parse`_)
        or Unix timestamp to parse in order to find the closest visit.
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/kripken/emscripten/visit/2017-05-05T12:02:03/branches/`
        :swh_web_browse:`origin/deb://Debian/packages/apache2-mod-xforward/visit/2017-11-15T05:15:09/branches/`

Origin releases
"""""""""""""""

.. http:get:: /browse/origin/(origin_url)/releases/

    HTML view that produces a display of the list of releases
    found during the latest full visit of a software origin.

    The following data are displayed for each release:

        * its name
        * a link to browse the release details
        * its target type (revision, directory, content or release)
        * its associated message
        * its date

    That list of releases is paginated, each page displaying a maximum of 100 releases.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/git/git/releases/`
        :swh_web_browse:`origin/https://github.com/webpack/webpack/releases/`

.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/releases/

    HTML view that produces a display of the list of releases
    found during a visit of a software origin closest to the provided timestamp.

    The following data are displayed for each release:

        * its name
        * a link to browse the release details
        * its target type (revision, directory, content or release)
        * its associated message
        * its date

    That list of releases is paginated, each page displaying a maximum of 100 releases.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: a date string (any format parsable by `dateutil.parser.parse`_)
        or Unix timestamp to parse in order to find the closest visit.
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/torvalds/linux/visit/2017-11-21T19:37:42/releases/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/2016-09-23T14:06:35/releases/`

.. _highlightjs: https://highlightjs.org/
.. _dateutil.parser.parse: http://dateutil.readthedocs.io/en/stable/parser.html
