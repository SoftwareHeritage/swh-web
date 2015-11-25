URI scheme
==========

Browsing namespace
------------------

### Global

The api /api/1 is partially browsable on defined endpoints.

Also, you can specify specify 'Accept' header using your favorite
client side to see the answer being transformed accordingly.

Support of the following 'Accept' header:
- application/json
- application/yaml
- text/html

To be anchored where browsing starts (e.g., at /api/1)

* /revision/<SHA1_GIT>: show commit information

    $ curl -H 'Accept: application/json' http://localhost:6543/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5
    {
        "author_email": "robot@softwareheritage.org",
        "author_name": "Software Heritage",
        "committer_date": "Mon, 17 Jan 2000 10:23:54 GMT",
        "committer_date_offset": 0,
        "committer_email": "robot@softwareheritage.org",
        "committer_name": "Software Heritage",
        "date": "Mon, 17 Jan 2000 10:23:54 GMT",
        "date_offset": 0,
        "directory": "7834ef7e7c357ce2af928115c6c6a42b7e2a44e6",
        "id": "18d8be353ed3480476f032475e7c233eff7371d5",
        "message": "synthetic revision message",
        "metadata": {
          "original_artifact": [
            {
              "archive_type": "tar",
              "name": "webbase-5.7.0.tar.gz",
              "sha1": "147f73f369733d088b7a6fa9c4e0273dcd3c7ccd",
              "sha1_git": "6a15ea8b881069adedf11feceec35588f2cfe8f1",
              "sha256": "401d0df797110bea805d358b85bcc1ced29549d3d73f309d36484e7edf7bb912"
            }
          ]
        },
        "parents": [
          null
        ],
        "synthetic": true,
        "type": "tar"
    }

* /directory/<SHA1_GIT>: show directory information (including ls)

    curl -X GET http://localhost:6543/api/1/directory/3126f46e2f7dc752227131a2a658265e58f53e38?recursive=True
    [
        {
          "dir_id": "3126f46e2f7dc752227131a2a658265e58f53e38",
          "name": "Makefile.am",
          "perms": 100644,
          "sha1": "b0283d8126f975e7b4a4348d13b07ddebe2cf8bf",
          "sha1_git": "e0522786777256d57c5210219bcbe8dacdad273d",
          "sha256": "897f3189dcfba96281b2190325c54afc74a42e2419c053baadfadc14386935ee",
          "status": "visible",
          "target": "e0522786777256d57c5210219bcbe8dacdad273d",
          "type": "file"
        },
        {
          "dir_id": "3126f46e2f7dc752227131a2a658265e58f53e38",
          "name": "Makefile.in",
          "perms": 100644,
          "sha1": "81f5757b9451811cfb3ef84612e45a973c70b4e6",
          "sha1_git": "3b948d966fd8e99f93670025f63a550168d57d71",
          "sha256": "f5acd84a40f05d997a36b8846c4872a92ee57083abb77c82e05e9763c8edb59a",
          "status": "visible",
          "target": "3b948d966fd8e99f93670025f63a550168d57d71",
              "type": "file"
        },

        ... snip ...

        {
          "dir_id": "3126f46e2f7dc752227131a2a658265e58f53e38",
          "name": "webtools.h",
          "perms": 100644,
          "sha1": "4b4c942ddd490ec1e312074ddfac352097886c02",
          "sha1_git": "e6fb8969d00e23dd152df5e7fb167118eab67342",
          "sha256": "95ffe6c0108f6ec48ccb0c93e966b54f1494f5cc353b066644c11fa47766620f",
          "status": "visible",
          "target": "e6fb8969d00e23dd152df5e7fb167118eab67342",
          "type": "file"
        },
        {
          "dir_id": "3126f46e2f7dc752227131a2a658265e58f53e38",
          "name": "ylwrap",
          "perms": 100644,
          "sha1": "9073938df9ae47d585bfdf176bfff45d06f3e13e",
          "sha1_git": "13fc38d75f2a47bc55e90ad5bf8d8a0184b14878",
          "sha256": "184eb644e51154c79b42df70c22955b818d057491f84ca0e579e4f9e48a60d7b",
          "status": "visible",
          "target": "13fc38d75f2a47bc55e90ad5bf8d8a0184b14878",
          "type": "file"
        }
    ]

* /directory/<SHA1_GIT>/path/to/file-or-dir: ditto, but for dir pointed by path

  - note: this is the same as /dir/<SHA1_GIT'>, where <SHA1_GIT'> is the
  sha1_git ID of the dir pointed by path

* /content/[<HASH_ALGO>:]<HASH>: show content information

  - content is specified by HASH, according to HASH_ALGO, where HASH_ALGO is
  one of: sha1, sha1_git, sha256. This means that several different URLs (at
  least one per HASH_ALGO) will point to the same content
  - HASH_ALGO defaults to "sha1" (?)

    curl -X GET http://localhost:6543/api/1/content/sha1:486b486d2a4998929c68265fa85ab2326db5528a
    {
        "data": "The GNU cfs-el web homepage is at\n@uref{http://www.gnu.org/software/cfs-el/cfs-el.html}.\n\nYou can find the latest distribution of GNU cfs-el at\n@uref{ftp://ftp.gnu.org/gnu/} or at any of its mirrors.\n",
         "sha1": "486b486d2a4998929c68265fa85ab2326db5528a"
    }

    curl -X GET http://localhost:6543/api/1/content/sha1:4a1b6d7dd0a923ed90156c4e2f5db030095d8e08/
    {"error": "Content with sha1:4a1b6d7dd0a923ed90156c4e2f5db030095d8e08 not found."}

* /content/[<hash_algo:]<HASH>/raw

    curl -H 'Accept: text/plain' http://localhost:6543/api/1/content/sha1:486b486d2a4998929c68265fa85ab2326db5528a/raw

    The GNU cfs-el web homepage is at
    @uref{http://www.gnu.org/software/cfs-el/cfs-el.html}.

    You can find the latest distribution of GNU cfs-el at
    @uref{ftp://ftp.gnu.org/gnu/} or at any of its mirrors.


* /release/<SHA1_GIT>: show release information

Sample:

    $ curl -X GET http://localhost:6543/api/1/release/4a1b6d7dd0a923ed90156c4e2f5db030095d8e08
    {
        "author_name": "Software Heritage",
        "author_email": "robot@softwareheritage.org",
        "comment": "synthetic release message",
        "date": "Sat, 04 Mar 2000 07:50:35 GMT",
        "date_offset": 0,
        "id": "4a1b6d7dd0a923ed90156c4e2f5db030095d8e08",
        "name": "4.0.6",
        "revision": "5c7814ce9978d4e16f3858925b5cea611e500eec",
        "synthetic": true
    }%

* /person/<PERSON_ID>: show person information

    curl http://localhost:6543/api/1/person/1
    {
      "email": "robot@softwareheritage.org",
      "id": 1,
      "name": "Software Heritage"
    }

    curl http://localhost:6543/api/1/person/2
    {"error": "Person with id 2 not found."}

* /origin/<ORIGIN_ID>: show origin information

Sample:

    $ curl -X GET http://localhost:6543/api/1/origin/1
    {
        "id": 1,
        "lister": null,
        "project": null,
        "type": "ftp",
        "url": "rsync://ftp.gnu.org/old-gnu/solfege"
    }%

* /project/<PROJECT_ID>: show project information

* /organization/<ORGANIZATION_ID>: show organization information

* /browse/<SHA:HASH>

Return content information up to one of its origin if the content is
found.

    curl http://localhost:6543/api/1/browse/sha1:2e98ab73456aad8dfc6cc50d562ee1b80d201753
    {
        "path": "republique.py",
        "origin_url": "file:///dev/null",
        "origin_type": "git",
        "revision": "8f8640a1c024c2ef85fa8e8d9297ea289134472d",
        "branch": "refs/remotes/origin/master"
    }

### Occurrence

Origin/Branch do not contain `|` so it is used as a terminator.
Origin is <TYPE+URL>.
Timestamp is one of: latest or an ISO8601 date (TODO: decide the time matching
policy).

* /directory/<TIMESTAMP>/<ORIGIN>|/<BRANCH>|/path/to/file-or-dir

  - Same as /directory/<SHA1_GIT> but looking up sha1 git using origin and
    branch at a given timestamp

* /revision/<TIMESTAMP>/<ORIGIN>|/<BRANCH>

  - Same as /revision/<SHA1_GIT> but looking up sha1 git using origin and
    branch at a given timestamp

* /revision/<TIMESTAMP>/<ORIGIN>|

  - Show all branches of origin at a given timestamp

* /revision/<TIMESTAMP>/<ORIGIN>|/<BRANCH>|

  - Show all revisions (~git log) of origin and branch at a given timestamp


### Upload and search

* /1/api/uploadnsearch/

Post a file's content to api.
Api computes the sha1 hash and checks in the storage if such sha1 exists.
Json answer:

    {'sha1': hexadecimal sha1,
     'found': true or false}

Sample:

    $ curl -X POST -F filename=@/path/to/file http://localhost:6543/api/1/uploadnsearch
    {
        "found": false,
        "sha1": "e95097ad2d607b4c89c1ce7ca1fef2a1e4450558"
    }%


Search namespace
----------------
