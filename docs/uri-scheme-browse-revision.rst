Revision
^^^^^^^^

.. http:get:: /browse/revision/(sha1_git)/

    HTML view to browse a SWH revision. It notably shows the revision date
    and message but also offers links to get more details on:

        * its author
        * its parent revisions
        * the history log reachable from it

    The view also enables to navigate in the source tree associated to the
    revision and browse its content.

    Last but not least, the view displays the list of file changes introduced
    in the revision but also the diffs of each changed files.

    :param string sha1_git: hexadecimal representation for the *sha1_git*
         identifier of a SWH revision
    :query string origin_type: used internally to associate a SWH origin type
        (*git*, *svn*, *deb* ...) to the revision
    :query string origin_url: used internally to associate an origin url
        (e.g. https://github.com/user/repo) to the revision
    :query string timestamp: used internally to associate an origin visit to the
        revision, must be a date string (any format parsable by `dateutil.parser.parse`_)
        or Unix timestamp to parse in order to find the closest SWH visit.
    :query int visit_id: used internally to specify a SWH visit id instead of
        using the provided timestamp
    :query string path: used internally when navigating in the source tree
        associated to the revision
    :statuscode 200: no error
    :statuscode 404: requested revision can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/`
        :swh_web_browse:`revision/d1aa2b3f607b35dc5dbf613b2334b6d243ec2bda/`

    .. _dateutil.parser.parse: http://dateutil.readthedocs.io/en/stable/parser.html

.. http:get:: /browse/revision/(sha1_git)/log/

    HTML view that displays the list of revisions heading to
    a given one. In other words, it shows a commit log.
    The following data are displayed for each log entry:

        * author of the revision
        * link to browse the revision
        * message associated to the revision
        * date of the revision
        * link to browse the associated source tree

    N log entries are displayed per page (default is 20). In order to navigate
    in a large history, two buttons are present at the bottom of the view:

        * *Newer*: fetch and display if available the N more recent log entries
          than the ones currently displayed
        * *Older*: fetch and display if available the N older log entries
          than the ones currently displayed

    :param string sha1_git: hexadecimal representation for the *sha1_git*
        identifier of a SWH revision
    :query string revs_breadcrumb: used internally to store
        the navigation breadcrumbs (i.e. the list of descendant revisions
        visited so far). It must be a string in the form
        "<rev_1>[/<rev_2>/.../<rev_n>]" where rev_i corresponds to a
        revision sha1_git.
    :query int per_page: the number of log entries to display per page
        (default is 20, max is 50)
    :statuscode 200: no error
    :statuscode 404: requested revision can not be found in the SWH archive

    **Examples:**

    .. parsed-literal::

        :swh_web_browse:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/log/`
        :swh_web_browse:`revision/d1aa2b3f607b35dc5dbf613b2334b6d243ec2bda/log/`
