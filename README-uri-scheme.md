URI scheme
==========

Browsing namespace
------------------

### Global

To be anchored where browsing starts (e.g., at /api/1)

* /revision/<SHA1_GIT>: show commit information

    $curl http://localhost:6543/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5
    {
      "revision": {
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
    }

* /directory/<SHA1_GIT>: show directory information (including ls)

* /directory/<SHA1_GIT>/path/to/file-or-dir: ditto, but for dir pointed by path

  - note: this is the same as /dir/<SHA1_GIT'>, where <SHA1_GIT'> is the
  sha1_git ID of the dir pointed by path

* /content/[<HASH_ALGO>:]<HASH>: show content information

  - content is specified by HASH, according to HASH_ALGO, where HASH_ALGO is
  one of: sha1, sha1_git, sha256. This means that several different URLs (at
  least one per HASH_ALGO) will point to the same content
  - HASH_ALGO defaults to "sha1" (?)

* /release/<SHA1_GIT>: show release information

Sample:

    $ curl -X GET http://localhost:6543/api/1/release/4a1b6d7dd0a923ed90156c4e2f5db030095d8e08
    {
      "release": {
        "author": 1,
        "comment": "synthetic release message",
        "date": "Sat, 04 Mar 2000 07:50:35 GMT",
        "date_offset": 0,
        "id": "4a1b6d7dd0a923ed90156c4e2f5db030095d8e08",
        "name": "4.0.6",
        "revision": "5c7814ce9978d4e16f3858925b5cea611e500eec",
        "synthetic": true
      }
    }%

* /person/<PERSON_ID>: show person information

* /origin/<ORIGIN_ID>: show origin information

Sample:

    $ curl -X GET http://localhost:6543/api/1/origin/1
    {
      "origin": {
        "id": 1,
        "lister": null,
        "project": null,
        "type": "ftp",
        "url": "rsync://ftp.gnu.org/old-gnu/solfege"
      }
    }%

* /project/<PROJECT_ID>: show project information

* /organization/<ORGANIZATION_ID>: show organization information

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

    $ curl -X POST -F filename=@/path/to/file http://localhost:6543/api/1/uploadnsearch/
    {
        "found": false,
        "sha1": "e95097ad2d607b4c89c1ce7ca1fef2a1e4450558"
    }%


Search namespace
----------------
