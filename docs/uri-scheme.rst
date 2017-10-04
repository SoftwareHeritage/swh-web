URI scheme for SWH Web applications
===================================

SWH Browse Urls
---------------

This web application aims to provide HTML views to easily navigate in the SWH archive,
thus it needs to be reached from a web browser.
If you intend to query the SWH archive programmatically through any HTTP client,
please refer to the `SWH Web API URLs`_ instead.

Content
^^^^^^^

.. _browse_content:

.. http:get:: /browse/content/[(algo_hash):](hash)/

    HTML view that displays a SWH content identified by its hash value.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content filename
           (provided as query parameter when navigating from a directory view).

        2) If no language has been found from the filename,
           try to find one from the content mime type.
           The mime type is retrieved from the content metadata stored
           in the SWH archive or is computed server-side using Python
           magic module.

    When that view is called in the context of a navigation coming from
    a directory view, a breadcrumb will be displayed on top of the rendered
    content in order to easily navigate up to the associated root directory.
    In that case, the path query parameter will be used and filled with the path
    of the file relative to the root directory.

    :param algo_hash: optionnal parameter to indicate the algorithm used 
        to compute the content checksum (default to *sha1*)
    :type algo_hash: a string identifying the hashing algorithm (either *sha1*, 
        *sha1_git*, *sha256* or *blake2s256*)
    :param hash: the checksum from which to retrieve the associated content in
        the SWH archive
    :type hash: hexadecimal representation of the hash value
    :query path: optionnal parameter used to describe the path of the content
        relative to a root directory (used to add context aware navigation links
        when navigating from a directory view)
    :type path: string
    :statuscode 200: no error
    :statuscode 400: an invalid query string has been provided
    :statuscode 404: requested content can not be found in the SWH archive

.. _browse_content_raw:

.. http:get:: /browse/content/[(algo_hash):](hash)/raw/

    HTML view that produces a raw display of a SWH content identified by its hash value.

    The behaviour of that view depends on the mime type of the requested content.
    If the mime type is from the text family, the view will return a response whose
    content type is 'text/plain' that will be rendered by the browser. Otherwise,
    the view will return a response whose content type is 'application/octet-stream'
    and the browser will then offer to download the file.

    In the context of a navigation coming from a directory view, the filename query
    parameter will be used in order to provide the real name of the file when
    one wants to save it locally.

    :param algo_hash: optionnal parameter to indicate the algorithm used 
        to compute the content checksum (default to *sha1*)
    :type algo_hash: a string identifying the hashing algorithm (either *sha1*, 
        *sha1_git*, *sha256* or *blake2s256*)
    :param hash: the checksum from which to retrieve the associated content in
        the SWH archive
    :type hash: hexadecimal representation of the hash value
    :query filename: optionnal parameter used to indicate the name of the file
        holding the requested content (used when one wants to save the content
        to a local file)
    :type path: string
    :statuscode 200: no error
    :statuscode 400: an invalid query string has been provided
    :statuscode 404: requested content can not be found in the SWH archive

Directory
^^^^^^^^^

.. _browse_directory:

.. http:get:: /browse/directory/(sha1_git)/

    HTML view for browsing the content of a SWH directory identified
    by its `sha1_git` value.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the provided root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    :param sha1_git: the `sha1_git` identifier of the directory to browse
    :type sha1_git: hexadecimal representation of that hash value
    :statuscode 200: no error
    :statuscode 400: an invalid `sha1_git` value has been provided
    :statuscode 404: requested directory can not be found in the SWH archive


.. http:get:: /browse/directory/(sha1_git)/(path)

    HTML view for browsing the content of a SWH directory reachable from
    the provided root one identified by its `sha1_git` value.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    :param sha1_git: the `sha1_git` identifier of the directory to browse
    :type sha1_git: hexadecimal representation of that hash value
    :param path: path of a directory reachable from the provided root one
    :type path: string
    :statuscode 200: no error
    :statuscode 400: an invalid `sha1_git` value has been provided
    :statuscode 404: requested directory can not be found in the SWH archive

Origin
^^^^^^

Origin metadata
"""""""""""""""

.. _browse_origin:

.. http:get:: /browse/origin/(origin_id)/

    HTML view that displays a SWH origin identified by its id.

    The view displays the origin metadata and contains links
    for browsing its directories and contents for each SWH visit.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

.. http:get:: /browse/origin/(origin_type)/url/(origin_url)/
    
    HTML view that displays a SWH origin identified by its type and url.

    The view displays the origin metadata and contains links
    for browsing its directories and contents for each SWH visit.

    :param origin_type: the type of the SWH origin (*git*, *svn*, ...)
    :type origin_type: string
    :param origin_url: the url of the origin (e.g. https://github.com/<user>/<repo>/)
    :type origin_url: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

Origin directory
""""""""""""""""

.. _browse_origin_directory:

.. http:get:: /browse/origin/(origin_id)/directory/

    HTML view for browsing the content of the root directory associated
    to the latest visit of a SWH origin.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the origin root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the directory
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

.. http:get:: /browse/origin/(origin_id)/directory/(path)/

    HTML view for browsing the content of a directory reachable from the root directory
    associated to the latest visit of a SWH origin.

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

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param path: path of a directory reachable from the origin root one
    :type path: string
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the directory
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive
        or the provided path does not exist from the origin root directory

.. http:get:: /browse/origin/(origin_id)/visit/(visit_id)/directory/

    HTML view for browsing the content of the root directory
    associated to a specific visit (identified by its id) of a SWH origin. 

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the origin root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param visit_id: the id of the origin visit
    :type visit_id: int
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the directory
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive
        or requested visit id does not exist

.. http:get:: /browse/origin/(origin_id)/visit/(visit_id)/directory/(path)/

    HTML view for browsing the content of a directory reachable from the root directory
    associated to a specific visit (identified by its id) of a SWH origin. 

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

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param visit_id: the id of the origin visit
    :type visit_id: int
    :param path: path of a directory reachable from the origin root one
    :type path: string
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the directory
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit id does not exist or the provided path does 
        not exist from the origin root directory

.. http:get:: /browse/origin/(origin_id)/ts/(ts)/directory/

    HTML view for browsing the content of the root directory
    associated to a specific visit (identified by its timestamp) of a SWH origin. 

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the origin root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param ts: the timestamp of the origin visit
    :type ts: Unix timestamp
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the directory
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive
        or requested visit timestamp does not exist

.. http:get:: /browse/origin/(origin_id)/ts/(ts)/directory/(path)/

    HTML view for browsing the content of a directory reachable from the root directory
    associated to a specific visit (identified by its timestamp) of a SWH origin. 

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

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param ts: the timestamp of the origin visit
    :type ts: Unix timestamp
    :param path: path of a directory reachable from the origin root one
    :type path: string
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the directory
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit timestamp does not exist or the provided path does 
        not exist from the origin root directory

Origin content
""""""""""""""

.. _browse_origin_content:

.. http:get:: /browse/origin/(origin_id)/content/(path)/

    HTML view that produces an HTML display of a SWH content
    associated to the latest visit of a SWH origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content filename

        2) If no language has been found from the filename,
           try to find one from the content mime type.
           The mime type is retrieved from the content metadata stored
           in the SWH archive or is computed server-side using Python
           magic module.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param path: path of a content reachable from the origin root directory
    :type path: string
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the content
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        or the provided content path does not exist from the origin root directory

.. http:get:: /browse/origin/(origin_id)/visit/(visit_id)/content/(path)/

    HTML view that produces an HTML display of a SWH content
    associated to a specific visit (identified by its id) of a SWH origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content filename

        2) If no language has been found from the filename,
           try to find one from the content mime type.
           The mime type is retrieved from the content metadata stored
           in the SWH archive or is computed server-side using Python
           magic module.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param visit_id: the id of the origin visit
    :type visit_id: int
    :param path: path of a content reachable from the origin root directory
    :type path: string
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the content
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit id does not exist or the provided content path does 
        not exist from the origin root directory

.. http:get:: /browse/origin/(origin_id)/ts/(ts)/content/(path)/

    HTML view that produces an HTML display of a SWH content
    associated to a specific visit (identified by its timestamp) of a SWH origin.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content filename

        2) If no language has been found from the filename,
           try to find one from the content mime type.
           The mime type is retrieved from the content metadata stored
           in the SWH archive or is computed server-side using Python
           magic module.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

    :param origin_id: the id of a SWH origin
    :type origin_id: int
    :param ts: the timestamp of the origin visit
    :type ts: Unix timestamp
    :param path: path of a content reachable from the origin root directory
    :type path: string
    :query branch: optional query parameter to specify the origin branch
        from which to retrieve the content
    :type branch: string
    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive,
        requested visit timestamp does not exist or the provided content path does 
        not exist from the origin root directory

SWH Web API URLs
----------------

.. _highlightjs: https://highlightjs.org/