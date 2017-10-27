URI scheme for SWH Web Browse application
=========================================

This web application aims to provide HTML views to easily navigate in the SWH archive,
thus it needs to be reached from a web browser.
If you intend to query the SWH archive programmatically through any HTTP client,
please refer to the :ref:`swh-web-api-urls` section instead.

Context-independent browsing
----------------------------

Context-independent URLs provide information about SWH objects (e.g.,
revisions, directories, contents, person, ...), independently of the
contexts where they have been found (e.g., specific repositories,
branches, commits, ...).

The following endpoints are the same of the API case (see below), and
just render the corresponding information for user consumption. Where
hyperlinks are created, they always point to other context-independent
user URLs:

    * :http:get:`/browse/content/[(algo_hash):](hash)/`: Display a content
    * :http:get:`/browse/content/[(algo_hash):](hash)/raw/`: Get / Download content data
    * :http:get:`/browse/directory/(sha1_git)/[(path)/]`: Browse the content of a directory
    * :http:get:`/browse/origin/(origin_id)/`: Information on origin
    * :http:get:`/browse/person/(person_id)/`: Information on person
    * :http:get:`/browse/revision/(sha1_git)/`: Browse revision
    * :http:get:`/browse/revision/(sha1_git)/log/`: Browse history log heading to revision

Context-dependent browsing
--------------------------

Context-dependent URLs provide information about SWH objects, limited to
specific contexts where the objects have been found. 

For instance, instead of having to specify a (root) revision by *sha1_git*, users might want to
specify a place and a time. In SWH a "place" is an origin, with an optional
branch name; a "time" is a timestamp at which some place has been observed by
SWH crawlers.

Wherever a revision context is expected in a path (i.e., a
**/browse/revision/(sha1_git)/** path fragment) we can put in its stead a path fragment
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


SWH Browse Urls
---------------

.. include:: uri-scheme-browse-content.rst

.. include:: uri-scheme-browse-directory.rst

.. include:: uri-scheme-browse-origin.rst

.. include:: uri-scheme-browse-person.rst

.. include:: uri-scheme-browse-revision.rst
