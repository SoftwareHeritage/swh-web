Miscellaneous URLs
^^^^^^^^^^^^^^^^^^

Iframe view for contents and directories
----------------------------------------

A subset of Software Heritage objects (contents and directories) can be embedded
in external websites through the use of iframes. A dedicated endpoint serving
a minimalist Web UI is available for that use case.

.. http:get:: /embed/(swhid)/

    Endpoint to embed Software Heritage objects in external websites using
    an iframe.

    :param string swhid: a SoftWare Heritage persistent IDentifier
        object, or SWHID (see :ref:`swhids` to learn more about its syntax)

    :statuscode 200: no error
    :statuscode 400: the provided identifier is malformed or
      the object type is not supported by the view
    :statuscode 404: requested object cannot be found in the archive

    **Example:**

    By adding HTML code similar to the one below in a web page,

    .. code-block:: html

      <iframe style="width: 100%; height: 500px; border: 1px solid rgba(0, 0, 0, 0.125);"
              src="https://archive.softwareheritage.org/embed/swh:1:cnt:edc043a59197bcebc1d44fb70bf1b84cde3db791;origin=https://github.com/rdicosmo/parmap;visit=swh:1:snp:2d869aa00591d2ac8ec8e7abacdda563d413189d;anchor=swh:1:rev:f140dbc8b05aa3d341c70436a1920a06df9a0ed4;path=/src/parmap.ml">
      </iframe>

    you will obtain the following rendering.

    .. raw:: html

      <iframe style="width: 100%; height: 500px; border: 1px solid rgba(0, 0, 0, 0.125);"
              src="https://archive.softwareheritage.org/embed/swh:1:cnt:edc043a59197bcebc1d44fb70bf1b84cde3db791;origin=https://github.com/rdicosmo/parmap;visit=swh:1:snp:2d869aa00591d2ac8ec8e7abacdda563d413189d;anchor=swh:1:rev:f140dbc8b05aa3d341c70436a1920a06df9a0ed4;path=/src/parmap.ml">
      </iframe>

