Snapshot
^^^^^^^^

.. http:get:: /browse/snapshot/(snapshot_id)/

    HTML view that displays the content of a snapshot from its identifier
    (see :func:`swh.model.identifiers.snapshot_identifier`
    in our data model module for details about how they are computed).

    A snapshot is a set of named branches, which are pointers to objects at any
    level of the Software Heritage DAG. It represents a full picture of an
    origin at a given time. Thus, multiple visits of different origins can
    point to the same snapshot (for instance, when several projects are forks
    of a common one).

    Currently, that endpoint simply performs a redirection to
    :http:get:`/browse/snapshot/(snapshot_id)/directory/`
    in order to display the root directory associated to the default
    snapshot branch (usually master).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/baebc2109e4a2ec22a1129a3859647e191d04df4/`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/`


Snapshot directory
""""""""""""""""""

.. http:get:: /browse/snapshot/(snapshot_id)/directory/

    HTML view that displays the content of a directory reachable from
    a snapshot.

    The features offered by the view are similar to the one for browsing
    a directory in an origin context
    (see :http:get:`/browse/origin/(origin_url)/directory/[(path)/]`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :query string path: optional parameter used to specify the path of a directory
        reachable from the snapshot root one
    :query string branch: specify the snapshot branch name from which
        to retrieve the root directory
    :query string release: specify the snapshot release name from which
        to retrieve the root directory
    :query string revision: specify the snapshot revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the root directory

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/baebc2109e4a2ec22a1129a3859647e191d04df4/directory/?path=drivers/gpu`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/directory/?path=src/opengl`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/directory/?release=v5.7.0`


.. http:get:: /browse/snapshot/(snapshot_id)/directory/(path)/
   :deprecated:

    .. warning::
      That endpoint is deprecated, use :http:get:`/browse/snapshot/(snapshot_id)/directory/` instead.

    HTML view that displays the content of a directory reachable from
    a snapshot.

    The features offered by the view are similar to the one for browsing
    a directory in an origin context
    (see :http:get:`/browse/origin/(origin_url)/directory/[(path)/]`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :param string path: optional parameter used to specify the path of a directory
        reachable from the snapshot root one
    :query string branch: specify the snapshot branch name from which
        to retrieve the root directory
    :query string release: specify the snapshot release name from which
        to retrieve the root directory
    :query string revision: specify the snapshot revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the root directory

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/baebc2109e4a2ec22a1129a3859647e191d04df4/directory/drivers/gpu/`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/directory/src/opengl/`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/directory/?release=v5.7.0`


Snapshot content
""""""""""""""""

.. http:get:: /browse/snapshot/(snapshot_id)/content/

    HTML view that produces a display of a content reachable from
    a snapshot.

    The features offered by the view are similar to the one for browsing
    a content in an origin context
    (see :http:get:`/browse/origin/(origin_url)/content/`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :query string path: path of a content reachable from the snapshot root directory
    :query string branch: specify the snapshot branch name from which
        to retrieve the content
    :query string release: specify the snapshot release name from which
        to retrieve the content
    :query string revision: specify the snapshot revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the content

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive,
        or the provided content path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/baebc2109e4a2ec22a1129a3859647e191d04df4/content/?path=init/initramfs.c`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/content/?path=src/opengl/qglbuffer.h`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/content/?path=src/opengl/qglbuffer.h&?release=v5.0.0`


.. http:get:: /browse/snapshot/(snapshot_id)/content/(path)/
   :deprecated:

    .. warning::
      That endpoint is deprecated, use :http:get:`/browse/snapshot/(snapshot_id)/content/` instead.

    HTML view that produces a display of a content reachable from
    a snapshot.

    The features offered by the view are similar to the one for browsing
    a content in an origin context
    (see :http:get:`/browse/origin/(origin_url)/content/(path)/`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :param string path: path of a content reachable from the snapshot root directory
    :query string branch: specify the snapshot branch name from which
        to retrieve the content
    :query string release: specify the snapshot release name from which
        to retrieve the content
    :query string revision: specify the snapshot revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the content

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive,
        or the provided content path does not exist from the origin root directory

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/baebc2109e4a2ec22a1129a3859647e191d04df4/content/init/initramfs.c`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/content/src/opengl/qglbuffer.h/`
        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/content/src/opengl/qglbuffer.h/?release=v5.0.0`


Snapshot history
""""""""""""""""

.. http:get:: /browse/snapshot/(snapshot_id)/log/

    HTML view that produces a display of revisions history (aka the commit log)
    heading to the last revision collected in a snapshot.

    The features offered by the view are similar to the one for browsing
    the history in an origin context
    (see :http:get:`/browse/origin/(origin_url)/log/`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :query int per_page: the number of log entries to display per page
        (default is 20, max is 50)
    :query string branch: specify the snapshot branch name from which
        to retrieve the commit log
    :query string release: specify the snapshot release name from which
        to retrieve the commit log
    :query string revision: specify the snapshot revision, identified by the hexadecimal
        representation of its **sha1_git** value, from which to retrieve the commit log

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/a274b44111f777209556e94920b7e71cf5c305cd/log/`
        :swh_web_browse:`snapshot/9ca9e75279df5f4e3fee19bf5190ed672dcdfb33/log/?branch=refs/heads/emacs-unicode`


Snapshot branches
"""""""""""""""""

.. http:get:: /browse/snapshot/(snapshot_id)/branches/

    HTML view that produces a display of the list of branches
    collected in a snapshot.

    The features offered by the view are similar to the one for browsing
    the list of branches in an origin context
    (see :http:get:`/browse/origin/(origin_url)/branches/`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/03d7897352541e78ee7b13a580dc836778e8126a/branches/`
        :swh_web_browse:`snapshot/f37563b953327f8fd83e39af6ebb929ef85103d5/branches/`


Snapshot releases
"""""""""""""""""

.. http:get:: /browse/snapshot/(snapshot_id)/releases/

    HTML view that produces a display of the list of releases
    collected in a snapshot.

    The features offered by the view are similar to the one for browsing
    the list of releases in an origin context
    (see :http:get:`/browse/origin/(origin_url)/releases/`).

    :param string snapshot_id: hexadecimal representation of the snapshot **sha1** identifier
    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`snapshot/673156c31a876c5b99b2fe3e89615529de9a3c44/releases/`
        :swh_web_browse:`snapshot/23e6fb084a60cc909b9e222d80d89fdb98756dee/releases/`
