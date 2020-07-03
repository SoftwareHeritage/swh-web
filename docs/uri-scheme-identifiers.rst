URI scheme for Software Heritage identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A subset of Software Heritage objects (contents, directories, releases and
revisions) can be browsed using :ref:`persistent-identifiers`.  Those
identifiers are guaranteed to remain stable (persistent) over time.


.. http:get:: /(swhid)/

    Endpoint to browse Software Heritage objects using their SWHIDs.
    A redirection to the adequate HTML view will be performed when
    reaching it.

    :param string swhid: a SoftWare Heritage persistent IDentifier
        object, or SWHID (see :ref:`persistent-identifiers` to learn more about its syntax)
    :resheader Location: the redirection URL for browsing the Software Heritage object
        associated to the provided identifier
    :statuscode 302: no error
    :statuscode 400: the provided identifier is malformed

    **Examples:**

    .. parsed-literal::

        :swh_web:`swh:1:cnt:0ffd12d85cdec70c88e852fc3f5ea9fd342213cd`
        :swh_web:`swh:1:dir:db990da9af15427455ce7836ce2b8a34b9bf67f5`
        :swh_web:`swh:1:rel:a9b7e3f1eada90250a6b2ab2ef3e0a846cb16831`
        :swh_web:`swh:1:rev:f1b94134a4b879bc55c3dacdb496690c8ebdc03f`
        :swh_web:`swh:1:snp:673156c31a876c5b99b2fe3e89615529de9a3c44`
