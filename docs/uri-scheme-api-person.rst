Person
------

.. http:get:: /api/1/person/(person_id)/

    Get information about a person in the SWH archive.

    :param int person_id: a SWH person identifier
    
    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request
    
    :>json string email: the email of the person
    :>json string fullname: the full name of the person: combination of its name and email
    :>json number id: the unique identifier of the person
    :>json string name: the name of the person

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 404: requested person can not be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`person/8275/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "email": "torvalds@linux-foundation.org",
            "fullname": "Linus Torvalds <torvalds@linux-foundation.org>",
            "id": 8275,
            "name": "Linus Torvalds"
        }
