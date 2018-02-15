Snapshot
--------

.. http:get:: /api/1/snapshot/(snapshot_id)/

    Get information about a snapshot in the SWH archive.

    A snapshot is a set of named branches, which are pointers to objects at any
    level of the Software Heritage DAG. It represents a full picture of an
    origin at a given time.

    As well as pointing to other objects in the Software Heritage DAG, branches
    can also be aliases, in which case their target is the name of another
    branch in the same snapshot, or dangling, in which case the target is
    unknown.

    A snapshot identifier is a salted sha1. See :func:`swh.model.identifiers.snapshot_identifier`
    in our data model module for details about how they are computed.

    :param sha1 snapshot_id: a SWH snapshot identifier

    :reqheader Accept: the requested response content type,
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :>json object branches: object containing all branches associated to the snapshot,
        for each of them the associated SWH target type and id are given but also
        a link to get information about that target
    :>json string id: the unique identifier of the snapshot

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 400: an invalid snapshot identifier has been provided
    :statuscode 404: requested snapshot can not be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`snapshot/6a3a2cf0b2b90ce7ae1cf0a221ed68035b686f5a/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "branches": {
                "refs/heads/master": {
                    "target": "83c20a6a63a7ebc1a549d367bc07a61b926cecf3",
                    "target_type": "revision",
                    "target_url": "/api/1/revision/83c20a6a63a7ebc1a549d367bc07a61b926cecf3/"
                },
                "refs/heads/wiki": {
                    "target": "71f667aeb5d02562f2fa0941ad91df69c474ff3b",
                    "target_type": "revision",
                    "target_url": "/api/1/revision/71f667aeb5d02562f2fa0941ad91df69c474ff3b/"
                },
                "refs/tags/dpkt-1.6": {
                    "target": "7fc0fd582812af36064d1c85fe51e33227920479",
                    "target_type": "revision",
                    "target_url": "/api/1/revision/7fc0fd582812af36064d1c85fe51e33227920479/"
                },
                "refs/tags/dpkt-1.7": {
                    "target": "0c9dbfbc0974ec8ac1d8253aa1092366a03633a8",
                    "target_type": "revision",
                    "target_url": "/api/1/revision/0c9dbfbc0974ec8ac1d8253aa1092366a03633a8/"
                }
            },
            "id": "6a3a2cf0b2b90ce7ae1cf0a221ed68035b686f5a"
        }


