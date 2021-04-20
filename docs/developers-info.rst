Developers Information
======================

Sample configuration
--------------------

The configuration will be taken from the default configuration file: ``~/.config/swh/web/web.yml``.
The following introduces a default configuration file:

.. sourcecode:: yaml

    storage:
        cls: remote
        args:
            url: http://localhost:5002
    debug: false
    throttling:
        cache_uri: None
        scopes:
            swh_api:
                limiter_rate:
                    default: 120/h
                exempted_networks:
                    - 127.0.0.0/8

Run server
----------

Either use the django manage script directly (useful in development mode as it offers various commands):

.. sourcecode:: shell

    $ python3 -m swh.web.manage runserver

or use the following shortcut:

.. sourcecode:: shell

    $ make run

Modules description
-------------------

Common to all web applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configuration and settings
""""""""""""""""""""""""""

    * :mod:`swh.web.config`: holds the configuration for the web applications.
      when building the documentation.
    * :mod:`swh.web.manage`: Django management module for developers.
    * :mod:`swh.web.urls`: module that holds the whole URI scheme of all
      the web applications.
    * :mod:`swh.web.settings.common`: Common Django settings
    * :mod:`swh.web.settings.development`: Django settings for development
    * :mod:`swh.web.settings.production`: Django settings for production
    * :mod:`swh.web.settings.tests`: Django settings for tests

Common utilities
""""""""""""""""

    * :mod:`swh.web.common.converters`: conversion module used to transform raw data
      to serializable ones. It is used by :mod:`swh.web.common.archive`: to convert data
      before transmitting then to Django views.
    * :mod:`swh.web.common.exc`: module defining exceptions used in the web applications.
    * :mod:`swh.web.common.highlightjs`: utility module to ease the use of the highlightjs_
      library in produced Django views.
    * :mod:`swh.web.common.query`: Utilities to parse data from HTTP endpoints. It is used
      by :mod:`swh.web.common.archive`.
    * :mod:`swh.web.common.archive`: Orchestration layer used by views module
      in charge of communication with :mod:`swh.storage` to retrieve information and
      perform conversion for the upper layer.
    * :mod:`swh.web.common.swh_templatetags`: Custom Django template tags library for swh.
    * :mod:`swh.web.common.urlsindex`: Utilities to help the registering of endpoints
      for the web applications
    * :mod:`swh.web.common.utils`: Utility functions used in the web applications implementation


swh-web API application
^^^^^^^^^^^^^^^^^^^^^^^

    * :mod:`swh.web.api.apidoc`: Utilities to document the web api for its html
      browsable rendering.
    * :mod:`swh.web.api.apiresponse`: Utility module to ease the generation of
      web api responses.
    * :mod:`swh.web.api.apiurls`: Utilities to facilitate the registration of web api endpoints.
    * :mod:`swh.web.api.throttling`: Custom request rate limiter to use with the `Django REST Framework
      <http://www.django-rest-framework.org/>`_
    * :mod:`swh.web.api.urls`: Module that defines the whole URI scheme for the api endpoints
    * :mod:`swh.web.api.utils`: Utility functions used in the web api implementation.
    * :mod:`swh.web.api.views.content`: Implementation of API endpoints for getting information
      about contents.
    * :mod:`swh.web.api.views.directory`: Implementation of API endpoints for getting information
      about directories.
    * :mod:`swh.web.api.views.origin`: Implementation of API endpoints for getting information
      about origins.
    * :mod:`swh.web.api.views.person`: Implementation of API endpoints for getting information
      about persons.
    * :mod:`swh.web.api.views.release`: Implementation of API endpoints for getting information
      about releases.
    * :mod:`swh.web.api.views.revision`: Implementation of API endpoints for getting information
      about revisions.
    * :mod:`swh.web.api.views.snapshot`: Implementation of API endpoints for getting information
      about snapshots.
    * :mod:`swh.web.api.views.stat`: Implementation of API endpoints for getting information
      about archive statistics.
    * :mod:`swh.web.api.views.utils`: Utilities used in the web api endpoints implementation.

swh-web browse application
^^^^^^^^^^^^^^^^^^^^^^^^^^

    * :mod:`swh.web.browse.browseurls`: Utilities to facilitate the registration of browse endpoints.
    * :mod:`swh.web.browse.urls`: Module that defines the whole URI scheme for the browse endpoints.
    * :mod:`swh.web.browse.utils`: Utilities functions used throughout the browse endpoints implementation.
    * :mod:`swh.web.browse.views.content`: Implementation of endpoints for browsing contents.
    * :mod:`swh.web.browse.views.directory`: Implementation of endpoints for browsing directories.
    * :mod:`swh.web.browse.views.identifiers`: Implementation of endpoints for browsing objects
      through :ref:`persistent-identifiers`.
    * :mod:`swh.web.browse.views.origin`: Implementation of endpoints for browsing origins.
    * :mod:`swh.web.browse.views.person`: Implementation of endpoints for browsing persons.
    * :mod:`swh.web.browse.views.release`: Implementation of endpoints for browsing releases.
    * :mod:`swh.web.browse.views.revision`: Implementation of endpoints for browsing revisions.
    * :mod:`swh.web.browse.views.snapshot`: Implementation of endpoints for browsing snapshots.

.. _highlightjs: https://highlightjs.org/
