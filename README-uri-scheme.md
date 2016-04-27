URI scheme
==========


User URLs
---------

### Context-independent browsing

Context-independent URLs provide information about SWH objects (e.g.,
revisions, directories, contents, person, ...), independently of the
contexts where they have been found (e.g., specific repositories,
branches, commits, ...).

The following endpoints are the same of the API case (see below), and
just render the corresponding information for user consumption. Where
hyperlinks are created, they always point to other context-independent
user URLs:

* /content/[<HASH_ALGO>:]<HASH>/        Information on content
* /content/[<HASH_ALGO>:]<HASH>/raw/    Display the content data
* /content/[<HASH_ALGO>:]<HASH>/origin/ Display information on content with its origin information (Deactivated)
* /directory/<SHA1_GIT>/                Browse directory's files
* /origin/<ORIGIN_ID>/                  Information on origin
* /person/<PERSON_ID>/                  Information on person
* /release/<SHA1_GIT>/                  Information on release
* /entity/<entity_uuid>/                Information on Entity with hierarchy
* /revision/<SHA1_GIT>/                 Browse revision
* /revision/<SHA1_GIT>/log/             Revision log from <SHA1_GIT>

Currently, the above endpoints are mounted below the top-level /browse/
namespace.


### Context-dependent browsing

Context-dependent URLs provide information about SWH objects, limited to
specific contexts where the objects have been found. For example, users might
want to see:

- the commits that descend (i.e., are based on and hence more recent) from a
  given commit but only in a given repository, ignoring "forks" elsewhere

- the parent directory of a given one, limited to a specific revision
  and starting root directory (note indeed that in the general case a
  given directory might be mounted in multiple places, which might
  vary across revisions)


### Context: a specific revision (AKA commit)

* /revision/<SHA1_GIT>/

  Show information about a given revision, pointing to parent
  revisions only (i.e., no links/info about child revisions as they
  cannot be limited a priori).  Links to parent revisions maintains a
  reference to <SHA1_GIT>, using the /history/ URL scheme (see below).

* /revision/<SHA1_GIT_CUR>/root/<SHA1_GIT_ROOT>/

  Show information about revision <SHA1_GIT_CUR>, limited to the sub-graph
  rooted at <SHA1_GIT_ROOT>. The obtained page show both parent and child
  revisions of <SHA1_GIT_CUR>, but exclude all revisions that are *not*
  transitively reachable (going back in time) from <SHA1_GIT_ROOT>.

  Links to all revisions SHA1_GIT' reachable from <SHA1_GIT_CUR> are of the
  form /revision/<SHA1_GIT'>/root/<SHA1_GIT_ROOT>, where <SHA1_GIT_ROOT>
  remains unchanged. In the degenerate case of browsing back to the root
  revision, we might end up on the URL
  /revision/<SHA1_GIT_1>/root/<SHA1_GIT_2>/ where SHA1_GIT_1 == SHA1_GIT_2.
  That URL is equivalent to /revision/<SHA1_GIT_1>/ and might be simplified
  redirecting to it.

  **Workaround**. Currently, we cannot quickly check whether SHA1_GIT_CUR is
  reachable from SHA1_GIT_ROOT. Therefore we adopt the following (sub-optimal
  and incomplete) endpoint instead.

  * /revision/<SHA1_GIT_CUR>/prev/<SHA1_GIT_N>,[...],<SHA1_GIT_1>

    where <SHA1_GIT_1>,[...],<SHA1_GIT_N> is a path in the revision graph
    leading to <SHA1_GIT_CUR>, i.e., SHA1_GIT_N is a revision pointing directly
    to SHA1_GIT_CUR, SHA1_GIT_(N-1) points directly to SHA1_GIT_N, etc.

    They path might be empty, complete w.r.t. the user navigation history up to
    SHA1_GIT_CUR, or incomplete. The UI will show (some of) the most near
    revisions in the path as previous commits and will allow users to jump to
    them. When following parent revisions of <SHA1_GIT_CUR> (going back in
    time), the path is extended, possibly trimming it to a maximum size; when
    following descendant revisions of <SHA1_GIT_CUR>, choosing from path
    elements, the path is trimmed to the selected revision.

    Note: it is possible for users to "cheat" and create URLs where the given
    revision path does not match the reality of our revision graph. Well, too
    bad for them. They will get pages whose navigation breadcrumbs do not
    reflect reality.

* /revision/<SHA1_GIT>/directory/[<PATH>]
* /revision/<SHA1_GIT_CUR>/root/<SHA1_GIT_ROOT>/directory/[<PATH>]

  Starting from the revision identified as in the previous URLs, navigate the
  directory associated to that revision.

  When <PATH> is absent, show the content of the root directory for the given
  revision. When <PATH> is present, treat it as a local path starting at that
  root directory, resolve it, and show the content of the obtained directory.

  Links to *sub*-directory/files append new parts to <PATH>. Links to parent
  directories remove trailing parts of <PATH>. Note that this latter operation
  is well-defined, given that we are looking at a specific revision and
  navigation starts at the root directory.


### Context: a specific point in spacetime

Instead of having to specify a (root) revision by SHA1_GIT, users might want to
specify a place and a time. In SWH a "place" is an origin, with an optional
branch name; a "time" is a timestamp at which some place has been observed by
SWH crawlers.

Wherever a revision context is expected in a path (i.e., a
"/revision/<SHA1_GIT>/" path fragment) we can put in its stead a path fragment
of the form /origin/<ORIG_ID>[/branch/<BRANCH>][/ts/<TIMESTAMP>/]. Such a
fragment is resolved, internally by the SWH archive, to a SHA1_GIT as follows:

- [if <TIMESTAMP> is absent] look for the most recent crawl of origin <ORIG_ID>
- [if <TIMESTAMP> is given] look for the most recent crawl of origin <ORIG_ID>
  whose timestamp is <= <TS>
- [if <BRANCH> is given] look for the branch <BRANCH>
- [if <BRANCH> is absent] look for branch "master"
- return the <SHA1_GIT> pointed by the chosen branch

The already mentioned URLs for revision contexts can therefore be alternatively
specified by users as:

* /revision/origin/<ORIG_ID>[/branch/<BRANCH>][/ts/<TIMESTAMP>]/
* /revision/origin/<ORIG_ID>[/branch/<BRANCH>][/ts/<TIMESTAMP>]/history/<SHA1>/
* /revision/origin/<ORIG_ID>[/branch/<BRANCH>][/ts/<TIMESTAMP>]/directory/[<PATH>]
* /revision/origin/<ORIG_ID>[/branch/<BRANCH>][/ts/<TIMESTAMP>]/history/<SHA1>/directory/[<PATH>]

Typing:

- <ORIG_ID>s are given as integer identifiers, pointing into the origin table.
  There will be separate mechanisms for finding origins by other means (e.g.,
  URLs, metadata, etc). Once an origin is found, it can be used by ID into the
  above URL schemes

- <BRANCH> names are given as per the corresponding VCS (e.g., Git) and might
  therefore contains characters that are either invalid in URLs, or that might
  make the above URL schemes ambiguous (e.g., '/'). All those characters will
  need to be URL-escaped. (e.g., '/' will become '%2F')

- <TIMESTAMP>s are given in a format as liberal as possible, to uphold the
  principle of least surprise. At the very minimum it should be possible to
  enter timestamps as:

  - ISO 8601 timestamps (see for instance the output of `date -I`, `date -Is`)
  - YYYY[MM[DD[HH[MM[SS]]]]] ad-hoc format

  Implementation proposal: use Python dateutil's parser and be done with it
  https://dateutil.readthedocs.org/en/latest/parser.html . Note: that dateutil
  does *not* allow to use classical UNIX timestamps expressed as seconds since
  the epoch (i.e., `date +%s` output). We will need to single case them.

  The same escaping considerations given for <BRANCH> apply.

Notes:

- Differently from <SHA1_GIT_ROOT>, <SHA1_GIT>s are still specified as SHA1 and
  cannot be specified a origin/branch/ts triples. This is to preserve some URL
  sanity.


API URLs
--------

### Endpoints

The api /api/1 is partially browsable on defined endpoints (/api, /api/1).

* /api/ and /api/1/

List endpoint methods as per the client's 'Accept' header request.

The following routes are to be anchored at at /api/1

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

    curl -X GET http://localhost:6543/api/1/directory/3126f46e2f7dc752227131a2a658265e58f53e38
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

* /content/[<HASH_ALGO>:]<HASH>: show content information

  - content is specified by HASH, according to HASH_ALGO, where HASH_ALGO is
  one of: sha1, sha1_git, sha256. This means that several different URLs (at
  least one per HASH_ALGO) will point to the same content
  - HASH_ALGO defaults to "sha1" (?)

    curl -X GET http://localhost:6543/api/1/content/sha1:486b486d2a4998929c68265fa85ab2326db5528a

    {
        "data": "/api/1/content/486b486d2a4998929c68265fa85ab2326db5528a/raw",
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

* /browse/<SHA:HASH>

  TODO: rename this to something more explicit about the fact we want more
  information about some content

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

* /uploadnsearch/

  TODO: remove this?

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

* /revision/<SHA1_GIT>/log

Show all revisions (~git log) starting from <sha1_git>.
The first element is the given sha1_git.

Sample:

    curl http://localhost:6543/api/1/revision/7026b7c1a2af56521e951c01ed20f255fa054238/log/

    [
        {
            "id": "7026b7c1a2af56521e951c01ed20f255fa054238",
            "parents": [],
            "type": "git",
            "committer_date": "Mon, 12 Oct 2015 11:05:53 GMT",
            "synthetic": false,
            "committer": {
                "email": "a3nm@a3nm.net",
                "name": "Antoine Amarilli"
            },
            "message": "+1 limitation\n",
            "author": {
                "email": "a3nm@a3nm.net",
                "name": "Antoine Amarilli"
            },
            "date": "Mon, 12 Oct 2015 11:05:53 GMT",
            "metadata": null,
            "directory": "a33a9acf2419b9a291e8a02302e6347dcffde5a6"
        },
        {
            "id": "368a48fe15b7db2383775f97c6b247011b3f14f4",
            "parents": [],
            "type": "git",
            "committer_date": "Mon, 12 Oct 2015 10:57:11 GMT",
            "synthetic": false,
            "committer": {
                "email": "a3nm@a3nm.net",
                "name": "Antoine Amarilli"
            },
            "message": "actually fix bug\n",
            "author": {
                "email": "a3nm@a3nm.net",
                "name": "Antoine Amarilli"
            },
            "date": "Mon, 12 Oct 2015 10:57:11 GMT",
            "metadata": null,
            "directory": "1d5188e4991510c74d62272f0301352c5c1b850b"
            },
            ...
    ]

* /project/<PROJECT_ID>: show project information

* /organization/<ORGANIZATION_ID>: show organization information

* /directory/<SHA1_GIT>/path/to/file-or-dir: ditto, but for file or directory pointed by path

  - note: This is the same as /directory/<SHA1_GIT>, where <SHA1_GIT>
  is the sha1_git ID of the directory pointed by path or
  /content/sha1_git:<SHA1_GIT> (for content)


### Global behavior

The api routes outputs 'application/json' as default.

#### Accept header

Also, you can specify the following 'Accept' header in your client query:
- application/json
- application/yaml
- text/html

The client can use specific filters and compose them as (s)he sees fit.

#### Fields

The client can filter the result output by field names when requesting
`application/json` or `application/yaml` output.

Ex:

    curl http://localhost:6543/api/1/stat/counters?fields=revision,release,content
    {
        "content": 133616,
        "revision": 1042,
        "release": 660
    }

#### JSONP

When using the accept header 'application/json', the route can be
enhanced by adding a `callback` parameter.  This will output the
result in a json function whose name is the callback parameter

Ex:

    curl http://localhost:6543/api/1/stat/counters?callback=jsonp&fields=directory_entry_dir,revision,entity

    jsonp({
        "directory_entry_dir": 12478,
        "revision": 1042,
        "entity": 0
    })

#### Error

When an error is raised, the error code response is used:
- 400: user's input is not correct regarding the API
- 404: user's input is ok but we did not found what (s)he was looking for
- 503: temporary internal server error (backend is down for example)

And the body of the response should be a dictionary with some more information on the error.

Bad request sample:

    curl http://localhost:6543/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d
    {"error": "Invalid checksum query string 18d8be353ed3480476f032475e7c233eff7371d"}

    curl http://localhost:6543/api/1/revision/sha1:18d8be353ed3480476f032475e7c233eff7371d
    {"error": "Invalid hash 18d8be353ed3480476f032475e7c233eff7371d for algorithm sha1"}

Not found sample:

    curl http://localhost:6543/api/1/revision/sha1:18d8be353ed3480476f032475e7c233eff7371df
    {"error": "Revision with sha1_git sha1:18d8be353ed3480476f032475e7c233eff7371df not found."}
