Origin
------

Information
^^^^^^^^^^^

.. http:get:: /api/1/origin/(origin_id)/

    Get information about a software origin from its unique (but otherwise meaningless)
    identifier.

    :param int origin_id: a SWH origin identifier

    :>json number id: the origin unique identifier
    :>json string origin_visits_url: link to in order to get information about the SWH 
        visits for that origin
    :>json string type: the type of software origin (*git*, *svn*, *hg*, *deb*, *ftp*, ...)
    :>json string url: the origin canonical url

    :reqheader Accept: the response content type depends on :mailheader:`Accept` header:
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :mailheader:`Accept` header of request

    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`origin/1/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 1,
            "origin_visits_url": "/api/1/origin/1/visits/",
            "type": "git",
            "url": "https://github.com/hylang/hy"
        }

.. http:get:: /api/1/origin/(origin_type)/url/(origin_url)/

    Get information about a software origin from its type and canonical url.

    :param string origin_type: the origin type (*git*, *svn*, *hg*, *deb*, *ftp*, ...)
    :param string origin_url: the origin url

    :>json number id: the origin unique identifier
    :>json string origin_visits_url: link to in order to get information about the SWH 
        visits for that origin
    :>json string type: the type of software origin (*git*, *svn*, *hg*, *deb*, *ftp*, ...)
    :>json string url: the origin canonical url

    :reqheader Accept: the response content type depends on :mailheader:`Accept` header:
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :mailheader:`Accept` header of request

    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`origin/git/url/https://github.com/python/cpython/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 13706355,
            "origin_visits_url": "/api/1/origin/13706355/visits/",
            "type": "git",
            "url": "https://github.com/python/cpython"
        }

Visits
^^^^^^

.. http:get:: /api/1/origin/(origin_id)/visits/

    Get information about all visits of a software origin.

    :param int origin_id: a SWH origin identifier
    :query int per_page: specify the number of visits to list, for pagination purposes
    :query int last_visit: visit to start listing from, for pagination purposes

    :reqheader Accept: the response content type depends on :mailheader:`Accept` header:
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :mailheader:`Accept` header of request
    :resheader Link: indicates that a subsequent result page is available and contains
        the url pointing to it

    :>json string date: ISO representation of the visit date (in UTC)
    :>json number id: the unique identifier of the origin
    :>json string origin_visit_url: link to :http:get:`/api/1/origin/(origin_id)/visit/(visit_id)/`
        in order to get information about the visit
    :>json string status: status of the visit (either *full*, *partial* or *ongoing*)
    :>json number visit: the unique identifier of the visit

    :statuscode 200: no error
    :statuscode 404: requested origin can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`origin/1/visits/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Link: </api/1/origin/1/visits/?last_visit=10>; rel="next"
        Content-Type: application/json

        [
            {
                "date": "2015-08-04T22:26:14.804009+00:00",
                "origin": 1,
                "origin_visit_url": "/api/1/origin/1/visit/1/",
                "status": "full",
                "visit": 1
            },
            {
                "date": "2016-02-22T16:56:16.725068+00:00",
                "metadata": {},
                "origin": 1,
                "origin_visit_url": "/api/1/origin/1/visit/2/",
                "status": "full",
                "visit": 2
            },
        ]

.. http:get:: /api/1/origin/(origin_id)/visit/(visit_id)/

    Get information about a specific visit of a software origin.

    :param int origin_id: a SWH origin identifier
    :param int visit_id: a visit identifier
    
    :reqheader Accept: the response content type depends on :mailheader:`Accept` header:
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :mailheader:`Accept` header of request
    
    :>json string date: ISO representation of the visit date (in UTC)
    :>json object occurrences: object containing all branches associated to the origin found 
        during the visit, for each of them the associated SWH revision id is given but also
        a link to in order to get information about it
    :>json number origin: the origin unique identifier
    :>json string origin_url: link to get information about the origin
    :>json string status: status of the visit (either *full*, *partial* or *ongoing*)
    :>json number visit: the unique identifier of the visit

    :statuscode 200: no error
    :statuscode 404: requested origin or visit can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`origin/1500/visit/1/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "date": "2015-08-23T17:48:46.800813+00:00",
            "occurrences": {
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
            "origin": 1500,
            "origin_url": "/api/1/origin/1500/",
            "status": "full",
            "visit": 1
        }
