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

    * :http:get:`/browse/content/[(algo_hash):](hash)/`: Display a SWH content
    * :http:get:`/browse/content/[(algo_hash):](hash)/raw/`: Get / Download SWH content raw data
    * :http:get:`/browse/directory/(sha1_git)/[(path)/]`: Browse the content of a SWH directory
    * :http:get:`/browse/origin/(origin_id)/`: Information on a SWH origin
    * :http:get:`/browse/person/(person_id)/`: Information on a SWH person
    * :http:get:`/browse/revision/(sha1_git)/`: Browse a SWH revision
    * :http:get:`/browse/revision/(sha1_git)/log/`: Browse history log heading to a SWH revision

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
of the form **/origin/(origin_id)[/visit/(visit_id)/][?branch=(branch)]** or
**/origin/(origin_id)[/ts/(timestamp/][?branch=(branch)]**. Such a
fragment is resolved, internally by the SWH archive, to a *sha1_git* as follows:

- if *timestamp* or *visit_id* is absent: look for the most recent crawl of origin *origin_id*
- if *visit_id* is given: look for crawl with id *visit_id* of origin *origin_id*
- if *timestamp* is given: look for the closest crawl of origin *origin_id*
  from timestamp *timestamp*
- if *branch* is given as a query parameter: look for the branch *branch*
- if *branch* is absent: look for branch "HEAD" or "master"
- return the *sha1_git* pointed by the chosen branch

The already mentioned URLs for revision contexts can therefore be alternatively
specified by users as:

* :http:get:`/browse/origin/(origin_id)/directory/[(path)/]`
* :http:get:`/browse/origin/(origin_id)/visit/(visit_id)/directory/[(path)/]`
* :http:get:`/browse/origin/(origin_id)/ts/(timestamp)/directory/[(path)/]`
* :http:get:`/browse/origin/(origin_id)/content/(path)/`
* :http:get:`/browse/origin/(origin_id)/visit/(visit_id)/content/(path)/`
* :http:get:`/browse/origin/(origin_id)/ts/(timestamp)/content/(path)/`
* :http:get:`/browse/origin/(origin_id)/log/`
* :http:get:`/browse/origin/(origin_id)/visit/(visit_id)/log/`
* :http:get:`/browse/origin/(origin_id)/ts/(timestamp)/log/`

Typing:

- *origin_id* is given as an integer identifier, pointing into the origin table.
  There will be separate mechanisms for finding origins by other means (e.g.,
  URLs, metadata, etc).

- *branch* name is given as per the corresponding VCS (e.g., Git) as
  a query parameter to the requestes URL.

- *timestamp* is given in a format as liberal as possible, to uphold the
  principle of least surprise. At the very minimum it is possible to
  enter timestamps as:

  - Unix epoch timestamp (see for instance the output of `date +%s`)
  - ISO 8601 timestamps (see for instance the output of `date -I`, `date -Is`)
  - YYYY[MM[DD[HH[MM[SS]]]]] ad-hoc format
  - YYYY[-MM[-DD[ HH:[MM:[SS:]]]]] ad-hoc format


SWH Browse Urls
---------------

.. include:: uri-scheme-browse-content.rst

.. include:: uri-scheme-browse-directory.rst

.. include:: uri-scheme-browse-origin.rst

.. include:: uri-scheme-browse-person.rst

.. include:: uri-scheme-browse-revision.rst
