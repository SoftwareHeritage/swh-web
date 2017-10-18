Directory
---------

.. http:get:: /api/1/directory/(sha1_git)/[(path)/]

    Get information about directory objects.
    Directories are identified by *sha1* checksums, compatible with Git directory identifiers. 
    See :func:`swh.model.identifiers.directory_identifier` in our data model module for details 
    about how they are computed.

    When given only a directory identifier, this endpoint returns information about the directory itself, 
    returning its content (usually a list of directory entries). When given a directory identifier and a 
    path, this endpoint returns information about the directory entry pointed by the relative path, 
    starting path resolution from the given directory.

    :param string sha1_git: hexadecimal representation of the directory *sha1_git* identifier
    :param string path: optional parameter to get information about the directory entry
        pointed by that relative path

    :reqheader Accept: the response content type depends on :mailheader:`Accept` header:
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :mailheader:`Accept` header of request

    :>json object checksums: object holding the computed checksum values for a directory entry
        (only for file entries)
    :>json string dir_id: *sha1_git* identifier of the requested directory
    :>json number length: length of a directory entry in bytes (only for file entries)
        for getting information about the content MIME type
    :>json string name: the directory entry name
    :>json number perms: permissions for the directory entry
    :>json string target: *sha1_git* identifier of the directory entry
    :>json string target_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/`
        or :http:get:`/api/1/directory/(sha1_git)/[(path)/]` depending on the directory entry type
    :>json string type: the type of the directory entry, can be either *dir*, *file* or *rev*

    :statuscode 200: no error
    :statuscode 400: an invalid *hash_type* or *hash* has been provided
    :statuscode 404: requested directory can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`directory/977fc4b98c0e85816348cebd3b12026407c368b6/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "checksums": {
                    "sha1": "e2d79ae437210941840f49966497cc348c7e817f",
                    "sha1_git": "58471109208922c9ee8c4b06135725f03ed16814",
                    "sha256": "2b7001f4819e898776b45b2fa3411018b7bc24e38afbb351691c32508eb2ae5d"
                },
                "dir_id": "977fc4b98c0e85816348cebd3b12026407c368b6",
                "length": 582,
                "name": ".bzrignore",
                "perms": 33188,
                "status": "visible",
                "target": "58471109208922c9ee8c4b06135725f03ed16814",
                "target_url": "/api/1/content/sha1_git:58471109208922c9ee8c4b06135725f03ed16814/",
                "type": "file"
            },
            {
                "checksums": {
                    "sha1": "f47aabb47381119cf72add7633bc095ca2cd030d",
                    "sha1_git": "2106da61725973b81a63a817ec6f245706af4353",
                    "sha256": "4f0475fac23bcd3ebceceecffb0d4facc5a413f6d9a0287185fb75638b8e9c69"
                },
                "dir_id": "977fc4b98c0e85816348cebd3b12026407c368b6",
                "length": 453,
                "name": ".codecov.yml",
                "perms": 33188,
                "status": "visible",
                "target": "2106da61725973b81a63a817ec6f245706af4353",
                "target_url": "/api/1/content/sha1_git:2106da61725973b81a63a817ec6f245706af4353/",
                "type": "file"
            },
            
        ]
