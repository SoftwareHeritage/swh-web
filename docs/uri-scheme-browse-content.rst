Content
^^^^^^^

.. http:get:: /browse/content/[(algo_hash):](hash)/

    HTML view that displays a content identified by its hash value.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlightjs_. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content filename
           (provided as query parameter when navigating from a directory view).

        2) If no language has been found from the filename,
           try to find one from the content mime type.
           The mime type is retrieved from the content metadata stored
           in the archive or is computed server-side using Python
           magic module.

    It is also possible to highlight specific lines of a textual
    content (not in terms of syntax highlighting but to emphasize
    some relevant content part) by either:

        * clicking on line numbers (holding shift to highlight a lines range)

        * using an url fragment in the form '#Ln' or '#Lm-Ln'

    When that view is called in the context of a navigation coming from
    a directory view, a breadcrumb will be displayed on top of the rendered
    content in order to easily navigate up to the associated root directory.
    In that case, the path query parameter will be used and filled with the path
    of the file relative to the root directory.

    :param string algo_hash: optional parameter to indicate the algorithm used
        to compute the content checksum (can be either ``sha1``,
        ``sha1_git``, ``sha256`` or ``blake2s256``, default to ``sha1``)
    :param string hash: hexadecimal representation for the checksum from which
        to retrieve the associated content in the archive
    :query string path: describe the path of the content relative to a root
        directory (used to add context aware navigation links when navigating
        from a directory view)
    :statuscode 200: no error
    :statuscode 400: an invalid query string has been provided
    :statuscode 404: requested content can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`content/sha1_git:f5d0b39a0cdddb91a31a537052b7d8d31a4aa79f/`
        :swh_web_browse:`content/sha1_git:f5d0b39a0cdddb91a31a537052b7d8d31a4aa79f/#L23-L41`
        :swh_web_browse:`content/blake2s256:1cc1e3124957c9be8a454c58e92eb925cf4aa9823984bd01451c5b7e0fee99d1/`
        :swh_web_browse:`content/sha1:1cb1447c1c7ddc1b03eac88398e40bd914d46b62/`
        :swh_web_browse:`content/sha256:8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903/`

.. http:get:: /browse/content/[(algo_hash):](hash)/raw/

    HTML view that produces a raw display of a content identified by its hash value.

    The behaviour of that view depends on the mime type of the requested content.
    If the mime type is from the text family, the view will return a response whose
    content type is 'text/plain' that will be rendered by the browser. Otherwise,
    the view will return a response whose content type is 'application/octet-stream'
    and the browser will then offer to download the file.

    In the context of a navigation coming from a directory view, the filename query
    parameter will be used in order to provide the real name of the file when
    one wants to save it locally.

    :param string algo_hash: optional parameter to indicate the algorithm used
        to compute the content checksum (can be either ``sha1``,
        ``sha1_git``, ``sha256`` or ``blake2s256``, default to ``sha1``)
    :param string hash: hexadecimal representation for the checksum from which
        to retrieve the associated content in the archive
    :query string filename: indicate the name of the file holding the requested
        content (used when one wants to save the content to a local file)
    :statuscode 200: no error
    :statuscode 400: an invalid query string has been provided
    :statuscode 404: requested content can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`content/sha1_git:f5d0b39a0cdddb91a31a537052b7d8d31a4aa79f/raw/?filename=LICENSE`
        :swh_web_browse:`content/blake2s256:1cc1e3124957c9be8a454c58e92eb925cf4aa9823984bd01451c5b7e0fee99d1/raw/?filename=MAINTAINERS`
        :swh_web_browse:`content/sha1:1cb1447c1c7ddc1b03eac88398e40bd914d46b62/raw/`
        :swh_web_browse:`content/sha256:8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903/raw/?filename=COPYING`

.. _highlightjs: https://highlightjs.org/