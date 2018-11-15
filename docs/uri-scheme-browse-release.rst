Release
^^^^^^^

.. http:get:: /browse/release/(sha1_git)/

    HTML view that displays metadata associated to a release:

        * the author
        * the release date
        * the release name
        * the associated message
        * the type of target the release points to (revision, directory, content or release)
        * the link to browse the release target

    :param string sha1_git: hexadecimal representation for the **sha1_git**
         identifier of a release
    :statuscode 200: no error
    :statuscode 404: requested release can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`release/208f61cc7a5dbc9879ae6e5c2f95891e270f09ef/`
        :swh_web_browse:`release/f883596e997fe5bcbc5e89bee01b869721326109/`
