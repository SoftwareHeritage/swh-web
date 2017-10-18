Archive statistics
------------------

.. http:get:: /api/1/stat/counters

    Get statistics about the content of the archive.

    :>json number content: current number of content objects (aka files) in the SWH archive
    :>json number directory: current number of directory objects in the SWH archive
    :>json number directory_entry_dir: current number of SWH directory entries 
        pointing to others SWH directories in the SWH archive
    :>json number directory_entry_file: current number of SWH directory entries
        pointing to SWH content objects in the SWH archive
    :>json number directory_entry_rev: current number of SWH directory entries
        pointing to SWH revision objects (e.g. git submodules) in the SWH archive
    :>json number entity: current number of SWH entities (a SWH entity is either
        a *group_of_entities*, a *group_of_persons*, a *project*, a *person*, an *organization*,
        or a *hosting* service) in the SWH archive
    :>json number occurrence: current number of SWH occurences (an occurrence may be assimilated
        to a branch found during a SWH crawl of a repository) in the SWH archive
    :>json number origin: current number of SWH origins (an origin is a "place" where code
        source can be found, e.g. a git repository, a tarball, ...) in the SWH archive
    :>json number person: current number of SWH persons (code source authors or commiters)
        in the SWH archive
    :>json number release: current number of SWH releases objects in the SWH archive
    :>json number revision: current number of SWH revision objects (aka commits) in the SWH archive
    :>json number skipped_content: current number of content objects (aka files) which where
        not inserted in the SWH archive

    :reqheader Accept: the response content type depends on :mailheader:`Accept` header:
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :mailheader:`Accept` header of request

    :statuscode 200: no error

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`stat/counters/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "content": 3837301367,
            "directory": 3385342732,
            "directory_entry_dir": 2696063206,
            "directory_entry_file": 3969668591,
            "directory_entry_rev": 8201450,
            "entity": 7101551,
            "entity_history": 7148571,
            "occurrence": 538691292,
            "occurrence_history": 554791126,
            "origin": 65642044,
            "person": 17211993,
            "release": 6666960,
            "revision": 879725958,
            "revision_history": 908684112,
            "skipped_content": 19383
        }
