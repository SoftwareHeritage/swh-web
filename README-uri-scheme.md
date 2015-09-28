URI scheme
==========

Browsing namespace
------------------

### Global

To be anchored where browsing starts (e.g., at /browse)

* /revision/<SHA1_GIT>: show commit information

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

* /person/<PERSON_ID>: show person information

* /origin/<ORIGIN_ID>: show origin information

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


Search namespace
----------------
