Revision
^^^^^^^^

.. http:get:: /browse/revision/(sha1_git)/

    HTML view to browse a revision. It notably shows the revision date
    and message but also offers links to get more details on:

        * its author
        * its parent revisions
        * the history log reachable from it

    The view also enables to navigate in the source tree associated to the
    revision and browse its content.

    Last but not least, the view displays the list of file changes introduced
    in the revision but also the diffs of each changed files.

    :param string sha1_git: hexadecimal representation for the **sha1_git**
         identifier of a revision
    :query string origin_url: used internally to associate an origin url
        (e.g. https://github.com/user/repo) to the revision
    :query string timestamp: an ISO 8601 datetime string to parse in order to find the
        closest visit.
    :query int visit_id: specify a visit id instead of
        using the provided timestamp
    :query string path: optional relative path from the revision root directory
    :statuscode 200: no error
    :statuscode 404: requested revision can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/`
        :swh_web_browse:`revision/d1aa2b3f607b35dc5dbf613b2334b6d243ec2bda/`

.. http:get:: /browse/revision/(sha1_git)/log/

    HTML view that displays the list of revisions heading to
    a given one. In other words, it shows a commit log.
    The following data are displayed for each log entry:

        * link to browse the revision
        * author of the revision
        * date of the revision
        * message associated to the revision
        * commit date of the revision

    By default, the revisions are ordered in reverse chronological order of
    their commit date.

    N log entries are displayed per page (default is 100). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * **Newer**: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * **Older**: fetch and display if available the N older log entries
          than the ones currently displayed

    :param string sha1_git: hexadecimal representation for the **sha1_git**
        identifier of a revision
    :query int per_page: the number of log entries to display per page
    :query int offset: the number of revisions to skip before returning those to display
    :query str revs_ordering: specify the revisions ordering, possible values are ``committer_date``,
        ``dfs``, ``dfs_post`` and ``bfs``
    :statuscode 200: no error
    :statuscode 404: requested revision can not be found in the archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/log/`
        :swh_web_browse:`revision/d1aa2b3f607b35dc5dbf613b2334b6d243ec2bda/log/`
