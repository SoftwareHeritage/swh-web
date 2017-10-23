Origin
^^^^^^

Origin metadata
"""""""""""""""

.. http:get:: /browse/origin/(origin_id)/

    HTML view that displays a SWH origin identified by its id.

    The view displays the origin metadata and contains links
    for browsing its directories and contents for each SWH visit.

    :param int origin_id: the id of a SWH origin
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/2/`
        :swh_web_browse:`origin/13706355/`

.. http:get:: /browse/origin/(origin_type)/url/(origin_url)/
    
    HTML view that displays a SWH origin identified by its type and url.

    The view displays the origin metadata and contains links
    for browsing its directories and contents for each SWH visit.

    :param string origin_type: the type of the SWH origin (*git*, *svn*, ...)
    :param string origin_url: the url of the origin (e.g. https://github.com/<user>/<repo>/)
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/git/url/https://github.com/torvalds/linux/`
        :swh_web_browse:`origin/git/url/https://github.com/python/cpython/`

Origin directory
""""""""""""""""

.. http:get:: /browse/origin/(origin_id)/directory/[(path)/]

    HTML view for browsing the content of a directory reachable from the root directory
    (including itself) associated to the latest visit of a SWH origin.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the origin root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param string path: optional parameter used to specify the path of a directory 
        reachable from the origin root one
    :query string branch: specify the origin branch from which 
        to retrieve the directory
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the directory
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive
        or the provided path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/2/directory/`
        :swh_web_browse:`origin/2/directory/net/ethernet/`
        :swh_web_browse:`origin/13706355/directory/`
        :swh_web_browse:`origin/13706355/directory/Python/`
        :swh_web_browse:`origin/13706355/directory/?branch=refs/heads/2.7`

.. http:get:: /browse/origin/(origin_id)/visit/(visit_id)/directory/[(path)/]

    HTML view for browsing the content of a directory reachable from the root directory
    (including itself) associated to a specific visit (identified by its id) of a SWH origin. 

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the origin root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param int visit_id: the id of the origin visit
    :param string path: optional parameter used to specify the path of a directory 
        reachable from the origin root one
    :query string branch: specify the origin branch from which
         to retrieve the directory
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the directory
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit id does not exist or the provided path does 
        not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/2/visit/2/directory/`
        :swh_web_browse:`origin/2/visit/2/directory/net/ethernet/`
        :swh_web_browse:`origin/13706355/visit/1/directory/`
        :swh_web_browse:`origin/13706355/visit/1/directory/Python/`
        :swh_web_browse:`origin/13706355/visit/1/directory/?branch=refs/heads/2.7`

.. http:get:: /browse/origin/(origin_id)/ts/(timestamp)/directory/[(path)/]

    HTML view for browsing the content of a directory reachable from the root directory
    (including itself) associated to a specific visit (identified by its timestamp) of a SWH origin. 

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the origin root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param int timestamp: the Unix timestamp of the origin visit
    :param path: optional parameter used to specify the path of a directory 
        reachable from the origin root one
    :type path: string
    :query string branch: specify the origin branch from which 
        to retrieve the directory
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the directory
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit timestamp does not exist or the provided path does 
        not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/2/ts/1493926809/directory/`
        :swh_web_browse:`origin/2/ts/1493926809/directory/net/ethernet/`
        :swh_web_browse:`origin/13706355/ts/1474620651/directory/`
        :swh_web_browse:`origin/13706355/ts/1474620651/directory/Python/`
        :swh_web_browse:`origin/13706355/ts/1474620651/directory/?branch=refs/heads/2.7`

    

Origin content
""""""""""""""

.. http:get:: /browse/origin/(origin_id)/content/(path)/

    HTML view that produces a display of a SWH content
    associated to the latest visit of a SWH origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. The procedure to perform that task is described
    in :http:get:`/browse/content/[(algo_hash):](hash)/`.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch from which 
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the content
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        or the provided content path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/723566/content/git.c/`
        :swh_web_browse:`origin/16297443/content/js/src/json.cpp/`
        :swh_web_browse:`origin/723566/content/git.c/?branch=refs/heads/next`

.. http:get:: /browse/origin/(origin_id)/visit/(visit_id)/content/(path)/

    HTML view that produces a display of a SWH content
    associated to a specific visit (identified by its id) of a SWH origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. The procedure to perform that task is described
    in :http:get:`/browse/content/[(algo_hash):](hash)/`.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param int visit_id: the id of the origin visit
    :param string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch from which 
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the content
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit id does not exist or the provided content path does 
        not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/723566/visit/1/content/git.c/`
        :swh_web_browse:`origin/16297443/visit/3/content/js/src/json.cpp/`
        :swh_web_browse:`origin/723566/visit/1/content/git.c/?branch=refs/heads/next`

.. http:get:: /browse/origin/(origin_id)/ts/(timestamp)/content/(path)/

    HTML view that produces a display of a SWH content
    associated to a specific visit (identified by its timestamp) of a SWH origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. The procedure to perform that task is described
    in :http:get:`/browse/content/[(algo_hash):](hash)/`.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param int timestamp: the Unix timestamp of the origin visit
    :param string path: path of a content reachable from the origin root directory
    :query string branch: specify the origin branch from which 
        to retrieve the content
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the content
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit timestamp does not exist or the provided content path does 
        not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/723566/ts/1473933564/content/git.c/`
        :swh_web_browse:`origin/16297443/ts/1490126182/content/js/src/json.cpp/`
        :swh_web_browse:`origin/723566/ts/1473933564/content/git.c/?branch=refs/heads/next`

Origin history
""""""""""""""

.. http:get:: /browse/origin/(origin_id)/log/

    HTML view that produces a display of revisions history heading
    to the last revision found during the latest visit of a SWH origin.
    In other words, it shows the commit log associated to the latest
    visit of a SWH origin.

    The following data are displayed for each log entry:

        * author of the revision
        * link to the revision metadata
        * message associated the revision
        * date of the revision
        * link to browse the associated source tree in the origin context

    N log entries are displayed per page (default is 20). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * *Newer*: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * *Older*: fetch and display if available the N older log entries
          than the ones currently displayed

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :query string revs_breadcrumb: used internally to store 
        the navigation breadcrumbs (i.e. the list of descendant revisions
        visited so far). It must be a string in the form 
        "<rev_1>[/<rev_2>/.../<rev_n>]" where rev_i corresponds to a
        revision sha1_git.
    :query int per_page: the number of log entries to display per page 
        (default is 20, max is 50)
    :query string branch: specify the origin branch from which 
        to retrieve the commit log
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the commit log
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/12215444/log/`
        :swh_web_browse:`origin/2081083/log/`
        :swh_web_browse:`origin/12081083/log/?branch=refs/heads/release`
        
.. http:get:: /browse/origin/(origin_id)/visit/(visit_id)/log/

    HTML view that produces a display of revisions history heading
    to the last revision found during a specific visit of a SWH origin.
    In other words, it shows the commit log associated to a specific
    visit of a SWH origin.

    The following data are displayed for each log entry:

        * author of the revision
        * link to the revision metadata
        * message associated the revision
        * date of the revision
        * link to browse the associated source tree in the origin context

    N log entries are displayed per page (default is 20). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * *Newer*: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * *Older*: fetch and display if available the N older log entries
          than the ones currently displayed

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param int visit_id: the id of the origin visit
    :query string revs_breadcrumb: used internally to store 
        the navigation breadcrumbs (i.e. the list of descendant revisions
        visited so far). It must be a string in the form 
        "<rev_1>[/<rev_2>/.../<rev_n>]" where rev_i corresponds to a
        revision sha1_git.
    :query int per_page: the number of log entries to display per page 
        (default is 20, max is 50)
    :query string branch: specify the origin branch from which 
        to retrieve the commit log
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the commit log
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/12215444/visit/2/log/`
        :swh_web_browse:`origin/12081083/visit/10/log/`
        :swh_web_browse:`origin/12081083/visit/10/log/?branch=refs/heads/release`

.. http:get:: /browse/origin/(origin_id)/ts/(timestamp)/log/

    HTML view that produces a display of revisions history heading
    to the last revision found during a specific visit (identified by its 
    timestamp) of a SWH origin.
    In other words, it shows the commit log associated to a specific
    visit (identified by its timestamp) of a SWH origin.

    The following data are displayed for each log entry:

        * author of the revision
        * link to the revision metadata
        * message associated the revision
        * date of the revision
        * link to browse the associated source tree in the origin context

    N log entries are displayed per page (default is 20). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * *Newer*: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * *Older*: fetch and display if available the N older log entries
          than the ones currently displayed

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param int origin_id: the id of a SWH origin
    :param int timestamp: the Unix timestamp of the origin visit
    :query string revs_breadcrumb: used internally to store 
        the navigation breadcrumbs (i.e. the list of descendant revisions
        visited so far). It must be a string in the form 
        "<rev_1>[/<rev_2>/.../<rev_n>]" where rev_i corresponds to a
        revision sha1_git.
    :query int per_page: the number of log entries to display per page 
        (default is 20, max is 50)
    :query string branch: specify the origin branch from which 
        to retrieve the commit log
    :query string revision: specify the origin revision, identified by the hexadecimal 
        representation of its *sha1_git* value, from which to retrieve the commit log
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`origin/12215444/ts/1459651262/log/`
        :swh_web_browse:`origin/12081083/ts/1438116814/log/`
        :swh_web_browse:`origin/12081083/ts/1438116814/log/?branch=refs/heads/release`

.. _highlightjs: https://highlightjs.org/
