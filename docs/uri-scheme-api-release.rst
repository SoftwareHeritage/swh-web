Release
-------

.. http:get:: /api/1/release/(sha1_git)/

    Get information about a release in the SWH archive.
    Releases are identified by *sha1* checksums, compatible with Git tag identifiers.
    See :func:`swh.model.identifiers.release_identifier` in our data model module for details 
    about how they are computed.

    :param string sha1_git: hexadecimal representation of the release *sha1_git* identifier
    
    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request
    
    :>json object author: information about the author of the release
    :>json string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
        information about the author of the release
    :>json string date: ISO representation of the release date (in UTC)
    :>json string id: the release unique identifier
    :>json string message: the message associated to the release
    :>json string name: the name of the release
    :>json string target: the target identifier of the release
    :>json string target_type: the type of the target, can be either *release*,
        *revision*, *content*, *directory*
    :>json string target_url: a link to the adequate api url based on the target type
    
    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 400: an invalid *sha1_git* value has been provided
    :statuscode 404: requested release can not be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`release/208f61cc7a5dbc9879ae6e5c2f95891e270f09ef/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "author": {
                "email": "nad@python.org",
                "fullname": "Ned Deily <nad@python.org>",
                "id": 8318464,
                "name": "Ned Deily"
            },
            "author_url": "/api/1/person/8318464/",
            "date": "2017-03-21T02:46:28-04:00",
            "id": "208f61cc7a5dbc9879ae6e5c2f95891e270f09ef",
            "message": "Tag v3.6.1\n-----BEGIN PGP SIGNATURE-----\n\niQIcBAABCgAGBQJY0MxgAAoJEC00fqaqZUIdkZ0QAJw9PR++cbpS3Pt8QrmgS+xG\nPxrZ1yPPNPNSfbmRLWOlHJ0nBzFPVXUWdrqnevmZVRghyrc78sjuBL8QczYsum22\n1B6X/63vX3dI9yj8FR5nldEYPBMOOD6ryObWoKMeqyQT3LhAqxIU/9oqAsbx+ZYw\nrXmRTuypenmZabq3yIv2hORMFgcS7JZFuVb181b0Cihji/7l+WRI9hkGO8POBeFq\ntfJ16beH8hbbDw/+MLpwJifsALWsQOqnWt2/C8tJeHtMX+FLuJflwcIwotv73E22\nulmpXNwTNxnK5l5/C9JC6kr5nN9VJatVpSpe6dftAmTy16O5OrADtePZYxOZ7S3X\n6ipOaiKl3s/2oykkmasxPeaVXllbWgd2UGqIBlAUxM6rVD/4DyVDUHqbDotQD8Kz\nZ8nSFxou1ZdRTSlC26ToGCNc+B6bqv9GTC1hph/ijJkhvXfIC9X1fc/uO1wrV+wB\ni2dxXKh1mQCXuogNAx6rv7gPaXbPgDHob7Tlvo5Ddhr7rQoAaMjceGfUMOTORSqO\nR4ssE6yyNASQtMjW+Y5WeVEgtX7ttGKBsgD0PsrZTCjnZfJkFtZGUyfkdwNzLK8v\nRBqi1r+tEuR5tpin4h+erdlVjeMhVMQZOhBYmxY2Ge70PMVrOz4KaFY1GD+aaxt7\n+PfOKUxMYGKvogv7gD/3\n=Peec\n-----END PGP SIGNATURE-----\n",
            "name": "v3.6.1",
            "synthetic": false,
            "target": "69c0db5050f623e8895b72dfe970392b1f9a0e2e",
            "target_type": "revision",
            "target_url": "/api/1/revision/69c0db5050f623e8895b72dfe970392b1f9a0e2e/"
        }
