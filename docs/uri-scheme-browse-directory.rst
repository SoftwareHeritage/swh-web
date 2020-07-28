Directory
^^^^^^^^^

.. http:get:: /browse/directory/(sha1_git)/

    HTML view for browsing the content of a directory reachable from
    the provided root one (including itself) identified by its **sha1_git** value.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    :param string sha1_git: hexadecimal representation for the **sha1_git** identifier
        of the directory to browse
    :query string path: optional parameter used to specify the path of a directory
        reachable from the provided root one
    :statuscode 200: no error
    :statuscode 400: an invalid **sha1_git** value has been provided
    :statuscode 404: requested directory can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`directory/977fc4b98c0e85816348cebd3b12026407c368b6/`
        :swh_web_browse:`directory/9650ed370c0330d2cd2b6fd1e9febf649ffe538d/?path=kernel/sched`


.. http:get:: /browse/directory/(sha1_git)/(path)/
   :deprecated:

    .. warning::
       That endpoint is deprecated, use :http:get:`/browse/directory/(sha1_git)/` instead.

    HTML view for browsing the content of a directory reachable from
    the provided root one (including itself) identified by its **sha1_git** value.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the requested directory to
    directories reachable from it in a recursive way but also
    up to the root directory.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    :param string sha1_git: hexadecimal representation for the **sha1_git** identifier
        of the directory to browse
    :param string path: optional parameter used to specify the path of a directory
        reachable from the provided root one
    :statuscode 200: no error
    :statuscode 400: an invalid **sha1_git** value has been provided
    :statuscode 404: requested directory can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`directory/977fc4b98c0e85816348cebd3b12026407c368b6/`
        :swh_web_browse:`directory/9650ed370c0330d2cd2b6fd1e9febf649ffe538d/kernel/sched/`
