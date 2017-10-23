Revision
--------

.. http:get:: /api/1/revision/(sha1_git)/

    Get information about a revision in the SWH archive.
    Releases are identified by *sha1* checksums, compatible with Git commit identifiers.
    See :func:`swh.model.identifiers.revision_identifier` in our data model module for details 
    about how they are computed.

    :param string sha1_git: hexadecimal representation of the revision *sha1_git* identifier
    
    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request
    
    :>json object author: information about the author of the revision
    :>json string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
        information about the author of the revision
    :>json object committer: information about the committer of the revision
    :>json string committer_url: link to :http:get:`/api/1/person/(person_id)/` to get
        information about the committer of the revision    
    :>json string committer_date: ISO representation of the commit date (in UTC)
    :>json string date: ISO representation of the revision date (in UTC)
    :>json string directory: the unique identifier that revision points to
    :>json string directory_url: link to :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
        to get information about the directory associated to the revision
    :>json string id: the revision unique identifier
    :>json boolean merge: whether or not the revision corresponds to a merge commit
    :>json string message: the message associated to the revision
    :>json array parents: the parents of the revision, i.e. the previous revisions
        that head directly to it, each entry of that array contains an unique parent 
        revision identifier but also a link to :http:get:`/api/1/revision/(sha1_git)/`
        to get more informations about it
    :>json string type: the type of the revision
    
    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 400: an invalid *sha1_git* value has been provided
    :statuscode 404: requested revision can not be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "author": {
                "email": "nicolas.dandrimont@crans.org",
                "fullname": "Nicolas Dandrimont <nicolas.dandrimont@crans.org>",
                "id": 42,
                "name": "Nicolas Dandrimont"
            },
            "author_url": "/api/1/person/42/",
            "committer": {
                "email": "nicolas.dandrimont@crans.org",
                "fullname": "Nicolas Dandrimont <nicolas.dandrimont@crans.org>",
                "id": 42,
                "name": "Nicolas Dandrimont"
            },
            "committer_date": "2014-08-18T18:18:25+02:00",
            "committer_url": "/api/1/person/42/",
            "date": "2014-08-18T18:18:25+02:00",
            "directory": "9f2e5898e00a66e6ac11033959d7e05b1593353b",
            "directory_url": "/api/1/directory/9f2e5898e00a66e6ac11033959d7e05b1593353b/",
            "history_url": "/api/1/revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/log/",
            "id": "aafb16d69fd30ff58afdd69036a26047f3aebdc6",
            "merge": true,
            "message": "Merge branch 'master' into pr/584\n",
            "metadata": {},
            "parents": [
                {
                    "id": "26307d261279861c2d9c9eca3bb38519f951bea4",
                    "url": "/api/1/revision/26307d261279861c2d9c9eca3bb38519f951bea4/"
                },
                {
                    "id": "37fc9e08d0c4b71807a4f1ecb06112e78d91c283",
                    "url": "/api/1/revision/37fc9e08d0c4b71807a4f1ecb06112e78d91c283/"
                }
            ],
            "synthetic": false,
            "type": "git",
            "url": "/api/1/revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/"
        }

.. http:get:: /api/1/revision/(sha1_git)/directory/[(path)/]

    Get information about directory (entry) objects associated to revisions.
    Each revision is associated to a single "root" directory. 
    This endpoint behaves like :http:get:`/api/1/directory/(sha1_git)/[(path)/]`, 
    but operates on the root directory associated to a given revision.

    :param string sha1_git: hexadecimal representation of the revision *sha1_git* identifier
    :param string path: optional parameter to get information about the directory entry
        pointed by that relative path
    
    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :>json array content: directory entries as returned by :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
    :>json string path: path of directory from the revision root one
    :>json string revision: the unique revision identifier
    :>json string type: the type of the directory

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 400: an invalid *sha1_git* value has been provided
    :statuscode 404: requested revision can not be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/directory/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "content": [
                {
                    "checksums": {
                        "sha1": "8de896f1d96b05c0cc3ea5233fdc232e90978c52",
                        "sha1_git": "f3a32d36d443cbb63ffb1bff743a890c181f482a",
                        "sha256": "a2ea552b2ed62b7f77cf47dae805d491fdb684ed3bbe297fcc68cbee755a5d10"
                    },
                    "dir_id": "778d9438465328f7c2ffe1c9d791f5b83a194c39",
                    "file_url": "/api/1/revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/directory/.gitattributes/",
                    "length": 73,
                    "name": ".gitattributes",
                    "perms": 33188,
                    "status": "visible",
                    "target": "f3a32d36d443cbb63ffb1bff743a890c181f482a",
                    "target_url": "/api/1/content/sha1_git:f3a32d36d443cbb63ffb1bff743a890c181f482a/",
                    "type": "file"
                },
                {
                    "checksums": {
                        "sha1": "d493cd8f6de7611b9f0ef2b5cdf80d85adcc7917",
                        "sha1_git": "0b0ee9cc20323d3e4206eb3172f111bb211274e3",
                        "sha256": "4d6aaab1da470f61b92134d8b78a80376ae1ab74ec6a23a045e039065eafafd9"
                    },
                    "dir_id": "778d9438465328f7c2ffe1c9d791f5b83a194c39",
                    "file_url": "/api/1/revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/directory/.gitignore/",
                    "length": 452,
                    "name": ".gitignore",
                    "perms": 33188,
                    "status": "visible",
                    "target": "0b0ee9cc20323d3e4206eb3172f111bb211274e3",
                    "target_url": "/api/1/content/sha1_git:0b0ee9cc20323d3e4206eb3172f111bb211274e3/",
                    "type": "file"
                },
            ],
            "path": ".",
            "revision": "ec72c666fb345ea5f21359b7bc063710ce558e39",
            "type": "dir"
        }

.. http:get:: /api/1/revision/(sha1_git)[/prev/(prev_sha1s)]/log/

    Get a list of all SWH revisions heading to a given one, i.e., show the commit log.

    :param string sha1_git: hexadecimal representation of the revision *sha1_git* identifier
    :param string prev_sha1s: optional parameter representing the navigation breadcrumbs 
        (descendant revisions previously visited). If multiple values, use / as delimiter.
        If provided, revisions information will be added at the beginning of the returned list.
    :query int per_page: number of elements in the returned list, for pagination purpose

    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request
    :resheader Link: indicates that a subsequent result page is available and contains
        the url pointing to it

    **Response JSON Array of Objects:**
    
        array of revisions information as returned by :http:get:`/api/1/revision/(sha1_git)/`

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 400: an invalid *sha1_git* value has been provided
    :statuscode 404: requested revision can not be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`revision/e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad/log/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "author": {
                    "email": "uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6",
                    "fullname": "uwog <uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6>",
                    "id": 1234212,
                    "name": "uwog"
                },
                "author_url": "/api/1/person/1234212/",
                "committer": {
                    "email": "uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6",
                    "fullname": "uwog <uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6>",
                    "id": 1234212,
                    "name": "uwog"
                },
                "committer_date": "2010-10-09T21:28:27+00:00",
                "committer_url": "/api/1/person/1234212/",
                "date": "2010-10-09T21:28:27+00:00",
                "directory": "d8f68b3628ac6f32b6532688bea3574c378ba403",
                "directory_url": "/api/1/directory/d8f68b3628ac6f32b6532688bea3574c378ba403/",
                "history_url": "/api/1/revision/e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad/log/",
                "id": "e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad",
                "merge": false,
                "message": "Restore binary compatibility again, 1.2.8 broke it (Fridrich Strba)\n\n\n\ngit-svn-id: http://svn.abisource.com/wv/trunk@29360 bcba8976-2d24-0410-9c9c-aab3bd5fdfd6\n",
                "metadata": {},
                "parents": [
                    {
                        "id": "e9a1e0e2805d01095bccea37ddabae5b3853bf74",
                        "url": "/api/1/revision/e9a1e0e2805d01095bccea37ddabae5b3853bf74/"
                    }
                ],
                "synthetic": false,
                "type": "git",
                "url": "/api/1/revision/e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad/"
            },
            {
                "author": {
                    "email": "uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6",
                    "fullname": "uwog <uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6>",
                    "id": 1234212,
                    "name": "uwog"
                },
                "author_url": "/api/1/person/1234212/",
                "committer": {
                    "email": "uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6",
                    "fullname": "uwog <uwog@bcba8976-2d24-0410-9c9c-aab3bd5fdfd6>",
                    "id": 1234212,
                    "name": "uwog"
                },
                "committer_date": "2010-10-09T10:42:20+00:00",
                "committer_url": "/api/1/person/1234212/",
                "date": "2010-10-09T10:42:20+00:00",
                "directory": "00d3b261bb4e9253a84409cb7f69ed866fdbff5c",
                "directory_url": "/api/1/directory/00d3b261bb4e9253a84409cb7f69ed866fdbff5c/",
                "history_url": "/api/1/revision/e9a1e0e2805d01095bccea37ddabae5b3853bf74/log/",
                "id": "e9a1e0e2805d01095bccea37ddabae5b3853bf74",
                "merge": false,
                "message": "Bump version\n\n\n\ngit-svn-id: http://svn.abisource.com/wv/trunk@29356 bcba8976-2d24-0410-9c9c-aab3bd5fdfd6\n",
                "metadata": {},
                "parents": [
                    {
                        "id": "73c589f19c060eb8af7c3fd3b4f50d44dd5218c8",
                        "url": "/api/1/revision/73c589f19c060eb8af7c3fd3b4f50d44dd5218c8/"
                    }
                ],
                "synthetic": false,
                "type": "git",
                "url": "/api/1/revision/e9a1e0e2805d01095bccea37ddabae5b3853bf74/"
            },
        ]


.. http:get:: /api/1/revision/origin/(origin_id)/[branch/(branch_name)/][ts/(timestamp)/]

    Get information about a revision, searching for it based on software origin, 
    branch name, and/or visit timestamp.

    This endpoint behaves like :http:get:`/api/1/revision/(sha1_git)/`, 
    but operates on the revision that has been found at a given software origin, 
    close to a given point in time, pointed by a given branch.

    :param int origin_id: a SWH origin identifier
    :param string branch_name: optional parameter specifying a fully-qualified branch name
        associated to the software origin, e.g., "refs/heads/master". Defaults to the master branch.
    :param string timestamp: optional parameter specifying a timestamp close to which the revision 
        pointed by the given branch should be looked up. The timestamp can be expressed either
        as an ISO date or as a Unix one (in UTC). Defaults to now.

    :reqheader Accept: the requested response content type,
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    **Response JSON Object:**
        same object as returned by :http:get:`/api/1/revision/(sha1_git)/`

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 404: no revision matching the given criteria could be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`revision/origin/13706355/branch/refs/heads/2.7/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "author": {
                "email": "victor.stinner@gmail.com",
                "fullname": "Victor Stinner <victor.stinner@gmail.com>",
                "id": 56592,
                "name": "Victor Stinner"
            },
            "author_url": "/api/1/person/56592/",
            "committer": {
                "email": "noreply@github.com",
                "fullname": "GitHub <noreply@github.com>",
                "id": 10932771,
                "name": "GitHub"
            },
            "committer_date": "2017-05-05T03:14:23+02:00",
            "committer_url": "/api/1/person/10932771/",
            "date": "2017-05-05T03:14:23+02:00",
            "directory": "8657d73ae7c4018e24874f952d9b525bb6299027",
            "directory_url": "/api/1/directory/8657d73ae7c4018e24874f952d9b525bb6299027/",
            "history_url": "/api/1/revision/8a19eb24c97ef43e9fc7d45af180334ac8093545/log/",
            "id": "8a19eb24c97ef43e9fc7d45af180334ac8093545",
            "merge": false,
            "message": "bpo-23404: make touch becomes make regen-all (#1466)\n\nDon't rebuild generated files based on file modification time\r\nanymore, the action is now explicit. Replace \"make touch\"\r\nwith \"make regen-all\".\r\n\r\nChanges:\r\n\r\n* Remove \"make touch\", Tools/hg/hgtouch.py and .hgtouch\r\n* Add a new \"make regen-all\" command to rebuild all generated files\r\n* Add subcommands to only generate specific files:\r\n\r\n  - regen-ast: Include/Python-ast.h and Python/Python-ast.c\r\n  - regen-grammar: Include/graminit.h and Python/graminit.c\r\n  - regen-opcode-targets: Python/opcode_targets.h\r\n\r\n* Add PYTHON_FOR_REGEN variable\r\n* pgen is now only built by by \"make regen-grammar\"\r\n* Add $(srcdir)/ prefix to paths to source files to handle correctly\r\n  compilation outside the source directory",
            "metadata": {},
            "parents": [
                {
                    "id": "e81e355a8e43956802211115e3f99859a1a29ecb",
                    "url": "/api/1/revision/e81e355a8e43956802211115e3f99859a1a29ecb/"
                }
            ],
            "synthetic": false,
            "type": "git",
            "url": "/api/1/revision/8a19eb24c97ef43e9fc7d45af180334ac8093545/"
        }

.. http:get:: /api/1/revision/origin/(origin_id)[/branch/(branch_name)][/ts/(timestamp)]/log

    Show the commit log for a revision, searching for it based on software origin, 
    branch name, and/or visit timestamp.

    This endpoint behaves like :http:get:`/api/1/revision/(sha1_git)[/prev/(prev_sha1s)]/log/`, 
    but operates on the revision that has been found at a given software origin, 
    close to a given point in time, pointed by a given branch.

    :param int origin_id: a SWH origin identifier
    :param string branch_name: optional parameter specifying a fully-qualified branch name
        associated to the software origin, e.g., "refs/heads/master". Defaults to the master branch.
    :param string timestamp: optional parameter specifying a timestamp close to which the revision 
        pointed by the given branch should be looked up. The timestamp can be expressed either
        as an ISO date or as a Unix one (in UTC). Defaults to now.

    :reqheader Accept: the requested response content type,
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    **Response JSON Array of Objects:**
    
        array of revisions information as returned by :http:get:`/api/1/revision/(sha1_git)/`

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 404: no revision matching the given criteria could be found in the SWH archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`revision/origin/723566/ts/2016-01-17T00:00:00+00:00/log/`

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "author": {
                    "email": "gitster@pobox.com",
                    "fullname": "Junio C Hamano <gitster@pobox.com>",
                    "id": 4974,
                    "name": "Junio C Hamano"
                },
                "author_url": "/api/1/person/4974/",
                "committer": {
                    "email": "gitster@pobox.com",
                    "fullname": "Junio C Hamano <gitster@pobox.com>",
                    "id": 4974,
                    "name": "Junio C Hamano"
                },
                "committer_date": "2016-02-24T13:31:57-08:00",
                "committer_url": "/api/1/person/4974/",
                "date": "2016-02-24T13:31:57-08:00",
                "directory": "6985b8ccee00205572e706add0359e8f2b4c83b4",
                "directory_url": "/api/1/directory/6985b8ccee00205572e706add0359e8f2b4c83b4/",
                "history_url": "/api/1/revision/56f37fda511e1615dc6df86c68f3b841711a7828/log/",
                "id": "56f37fda511e1615dc6df86c68f3b841711a7828",
                "merge": false,
                "message": "Eighth batch for 2.8\n\nSigned-off-by: Junio C Hamano <gitster@pobox.com>\n",
                "metadata": {},
                "parents": [
                    {
                        "id": "c3b1e8d85133e2a19d372b7c166d5b49fcbbfef2",
                        "url": "/api/1/revision/c3b1e8d85133e2a19d372b7c166d5b49fcbbfef2/"
                    }
                ],
                "synthetic": false,
                "type": "git",
                "url": "/api/1/revision/56f37fda511e1615dc6df86c68f3b841711a7828/"
            },
            {
                "author": {
                    "email": "gitster@pobox.com",
                    "fullname": "Junio C Hamano <gitster@pobox.com>",
                    "id": 4974,
                    "name": "Junio C Hamano"
                },
                "author_url": "/api/1/person/4974/",
                "committer": {
                    "email": "gitster@pobox.com",
                    "fullname": "Junio C Hamano <gitster@pobox.com>",
                    "id": 4974,
                    "name": "Junio C Hamano"
                },
                "committer_date": "2016-02-24T13:26:01-08:00",
                "committer_url": "/api/1/person/4974/",
                "date": "2016-02-24T13:26:01-08:00",
                "directory": "0db4cfbd62218fbf54be4160420b6e9c67cd60a0",
                "directory_url": "/api/1/directory/0db4cfbd62218fbf54be4160420b6e9c67cd60a0/",
                "history_url": "/api/1/revision/c3b1e8d85133e2a19d372b7c166d5b49fcbbfef2/log/",
                "id": "c3b1e8d85133e2a19d372b7c166d5b49fcbbfef2",
                "merge": true,
                "message": "Merge branch 'jc/am-i-v-fix'\n\nThe \"v(iew)\" subcommand of the interactive \"git am -i\" command was\nbroken in 2.6.0 timeframe when the command was rewritten in C.\n\n* jc/am-i-v-fix:\n  am -i: fix \"v\"iew\n  pager: factor out a helper to prepare a child process to run the pager\n  pager: lose a separate argv[]\n",
                "metadata": {},
                "parents": [
                    {
                        "id": "595bfefa6c31fa6d76b686ed79b024838db5933e",
                        "url": "/api/1/revision/595bfefa6c31fa6d76b686ed79b024838db5933e/"
                    },
                    {
                        "id": "708b8cc9a114ea1e5b90f5f52fd24ecade4e8b40",
                        "url": "/api/1/revision/708b8cc9a114ea1e5b90f5f52fd24ecade4e8b40/"
                    }
                ],
                "synthetic": false,
                "type": "git",
                "url": "/api/1/revision/c3b1e8d85133e2a19d372b7c166d5b49fcbbfef2/"
            },
        ]

