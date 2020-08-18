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

.. http:get:: /browse/origin/visits/

    HTML view that displays visits reporting for a software origin identified by
    its type and url.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/visits/?origin_url=https://github.com/torvalds/linux`
        :swh_web_browse:`origin/visits/?origin_url=https://github.com/python/cpython`
        :swh_web_browse:`origin/visits/?origin_url=deb://Debian-Security/packages/mediawiki`
        :swh_web_browse:`origin/visits/?origin_url=https://gitorious.org/qt/qtbase.git`


.. http:get:: /browse/origin/(origin_url)/visits/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/visits/` instead.

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

.. http:get:: /browse/origin/directory/

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

    The origin branch (default to HEAD) from which to retrieve the directory
    content can also be specified by using the branch query parameter.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
    :query string path: optional parameter used to specify the path of a directory
        reachable from the origin root one
    :query string branch: specify the origin branch name from which
        to retrieve the root directory
    :query string release: specify the origin release name from which
        to retrieve the root directory
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the root directory
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :query int visit_id: specify a visit id to retrieve the directory from instead
        of using the latest full visit by default
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive
        or the provided path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/directory/?origin_url=https://github.com/torvalds/linux`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/torvalds/linux&path=net/ethernet`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/python/cpython`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/python/cpython&path=Python`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/python/cpython&branch=refs/heads/2.7`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/torvalds/linux&path=net/ethernet&timestamp=2016-09-14T10:36:21Z`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/python/cpython&path=Python&timestamp=2017-05-05`
        :swh_web_browse:`origin/directory/?origin_url=https://github.com/python/cpython&branch=refs/heads/2.7&timestamp=2015-08`


.. http:get:: /browse/origin/(origin_url)/directory/[(path)/]
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/directory/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the directory
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
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/directory/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the directory
    content can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
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
        :swh_web_browse:`origin/https://github.com/torvalds/linux/visit/2016-09-14T10:36:21Z/directory/net/ethernet/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visit/1474620651/directory/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visit/2017-05-05/directory/Python/`
        :swh_web_browse:`origin/https://github.com/python/cpython/visit/2015-08/directory/?branch=refs/heads/2.7`


Origin content
""""""""""""""

.. http:get:: /browse/origin/content/

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

    The origin branch (default to HEAD) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
    :query string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch name from which
        to retrieve the content
    :query string release: specify the origin release name from which
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the content
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :query int visit_id: specify a visit id to retrieve the content from instead
        of using the latest full visit by default
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive,
        or the provided content path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/content/?origin_url=https://github.com/git/git?path=git.c`
        :swh_web_browse:`origin/content/?origin_url=https://github.com/mozilla/gecko-dev&path=js/src/json.cpp`
        :swh_web_browse:`origin/content/?origin_url=https://github.com/git/git?path=git.c&branch=refs/heads/next`
        :swh_web_browse:`origin/content/?origin_url=https://github.com/git/git&path=git.c&timestamp=2016-05-05T00:0:00+00:00Z`
        :swh_web_browse:`origin/content/?origin_url=https://github.com/mozilla/gecko-dev&path=js/src/json.cpp&timestamp=2017-03-21#L904-L931`
        :swh_web_browse:`origin/content/?origin_url=https://github.com/git/git&path=git.c&branch=refs/heads/next&timestamp=2017-09-15`


.. http:get:: /browse/origin/(origin_url)/content/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/content/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :query string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch name from which
        to retrieve the content
    :query string release: specify the origin release name from which
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the content
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :query int visit_id: specify a visit id to retrieve the content from instead
        of using the latest full visit by default
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive,
        or the provided content path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/git/git/content/?path=git.c`
        :swh_web_browse:`origin/https://github.com/mozilla/gecko-dev/content/?path=js/src/json.cpp`
        :swh_web_browse:`origin/https://github.com/git/git/content/?path=git.c&branch=refs/heads/next`
        :swh_web_browse:`origin/https://github.com/git/git/content/?path=git.c&timestamp=2016-05-05T00:0:00+00:00Z`
        :swh_web_browse:`origin/https://github.com/mozilla/gecko-dev/content?path=js/src/json.cpp&timestamp=2017-03-21#L904-L931`
        :swh_web_browse:`origin/https://github.com/git/git/content/git.c/?branch=refs/heads/next&timestamp=2017-09-15`


.. http:get:: /browse/origin/(origin_url)/content/(path)/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/content/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the content
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
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/content/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
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

        :swh_web_browse:`origin/https://github.com/git/git/visit/2016-05-05T00:0:00+00:00Z/content/git.c/`
        :swh_web_browse:`origin/https://github.com/mozilla/gecko-dev/visit/2017-03-21/content/js/src/json.cpp/#L904-L931`
        :swh_web_browse:`origin/https://github.com/git/git/visit/2017-09-15/content/git.c/?branch=refs/heads/next`


Origin history
""""""""""""""

.. http:get:: /browse/origin/log/

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

    The origin branch (default to HEAD) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
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
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :query int visit_id: specify a visit id to retrieve the history log from instead
        of using the latest visit by default
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/log/?origin_url=https://github.com/videolan/vlc`
        :swh_web_browse:`origin/log/?origin_url=https://github.com/Kitware/CMake`
        :swh_web_browse:`origin/log/?origin_url=https://github.com/Kitware/CMake&branch=refs/heads/release`
        :swh_web_browse:`origin/log/?origin_url=https://github.com/videolan/vlc&visit=1459651262`
        :swh_web_browse:`origin/log/?origin_url=https://github.com/Kitware/CMake&timestamp=2016-04-01`
        :swh_web_browse:`origin/log/?origin_url=https://github.com/Kitware/CMake&branch=refs/heads/release&timestamp=1438116814`
        :swh_web_browse:`origin/log/?origin_url=https://github.com/Kitware/CMake&branch=refs/heads/release&timestamp=2017-05-05T03:14:23Z`


.. http:get:: /browse/origin/(origin_url)/log/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/log/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
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
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :query int visit_id: specify a visit id to retrieve the history log from instead
        of using the latest visit by default
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/videolan/vlc/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/log/?branch=refs/heads/release`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/log/?timestamp=2016-04-01`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/log/?branch=refs/heads/release&timestamp=2017-05-05T03:14:23Z`


.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/log/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/log/` instead.

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

    The origin branch (default to HEAD) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param string origin_url: the url of the origin (e.g. https://github.com/(user)/(repo)/)
    :param string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
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

        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/2016-04-01/log/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/2017-05-05T03:14:23Z/log/?branch=refs/heads/release`

Origin branches
"""""""""""""""

.. http:get:: /browse/origin/branches/

    HTML view that produces a display of the list of branches
    found during the latest full visit of a software origin.

    The following data are displayed for each branch:

        * its name
        * a link to browse the associated directory
        * a link to browse the associated revision
        * last commit message
        * last commit date

    That list of branches is paginated, each page displaying a maximum of 100 branches.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/branches/?origin_url=deb://Debian/packages/linux`
        :swh_web_browse:`origin/branches/?origin_url=https://github.com/webpack/webpack`
        :swh_web_browse:`origin/branches/?origin_url=https://github.com/kripken/emscripten&timestamp=2017-05-05T12:02:03Z`
        :swh_web_browse:`origin/branches/?origin_url=deb://Debian/packages/apache2-mod-xforward&timestamp=2017-11-15T05:15:09Z`


.. http:get:: /browse/origin/(origin_url)/branches/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/branches/` instead.

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
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/deb://Debian/packages/linux/branches/`
        :swh_web_browse:`origin/https://github.com/webpack/webpack/branches/`
        :swh_web_browse:`origin/https://github.com/kripken/emscripten/branches/?timestamp=2017-05-05T12:02:03Z`
        :swh_web_browse:`origin/deb://Debian/packages/apache2-mod-xforward/branches/?timestamp=2017-11-15T05:15:09`


.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/branches/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/branches/` instead.

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
    :param string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/kripken/emscripten/visit/2017-05-05T12:02:03Z/branches/`
        :swh_web_browse:`origin/deb://Debian/packages/apache2-mod-xforward/visit/2017-11-15T05:15:09Z/branches/`

Origin releases
"""""""""""""""

.. http:get:: /browse/origin/releases/

    HTML view that produces a display of the list of releases
    found during the latest full visit of a software origin.

    The following data are displayed for each release:

        * its name
        * a link to browse the release details
        * its target type (revision, directory, content or release)
        * its associated message
        * its date

    That list of releases is paginated, each page displaying a maximum of 100 releases.

    :query string origin_url: mandatory parameter providing the url of the origin
        (e.g. https://github.com/(user)/(repo))
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :statuscode 200: no error
    :statuscode 400: no origin url has been provided as parameter
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/releases/?origin_url=https://github.com/git/git`
        :swh_web_browse:`origin/releases/?origin_url=https://github.com/webpack/webpack`
        :swh_web_browse:`origin/releases/?origin_url=https://github.com/torvalds/linux&timestamp=2017-11-21T19:37:42Z`
        :swh_web_browse:`origin/releases/?origin_url=https://github.com/Kitware/CMake&timestamp=2016-09-23T14:06:35Z`


.. http:get:: /browse/origin/(origin_url)/releases/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/releases/` instead.

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
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/git/git/releases/`
        :swh_web_browse:`origin/https://github.com/webpack/webpack/releases/`
        :swh_web_browse:`origin/https://github.com/torvalds/linux/releases/?timestamp=2017-11-21T19:37:42Z`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/releases/?timestamp=2016-09-23T14:06:35Z`


.. http:get:: /browse/origin/(origin_url)/visit/(timestamp)/releases/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/origin/releases/` instead.

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
    :param string timestamp: an ISO 8601 datetime string to parse in order to find the
      closest visit.
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/https://github.com/torvalds/linux/visit/2017-11-21T19:37:42Z/releases/`
        :swh_web_browse:`origin/https://github.com/Kitware/CMake/visit/2016-09-23T14:06:35Z/releases/`


.. _highlightjs: https://highlightjs.org/
