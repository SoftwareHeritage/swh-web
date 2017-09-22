Developers Information
======================

Run server
----------

Either use the django manage script directly (useful in development mode as it offers various commands).
The configuration will be taken from the default configuration file: '~/.config/swh/webapp/webapp.yml'.

```
python3 -m swh.web.manage runserver
```

or use the following shortcut:

```
make run
```

Sample configuration
--------------------

The following introduces a default configuration file:
```
storage:
  cls: remote
  args:
    url: http://localhost:5002
debug: false
throttling:
  cache_uri: None
  scopes:
    swh_api:
      limiter_rate: 120/h
      exempted_networks:
        - 127.0.0.0/8
```

modules' description
--------------------

### Layers

Folder swh/web/api/:

- views          main api endpoints definitions (html browsable + json + yaml)
- service        Orchestration layer used by views module.
                 In charge of communication with swh storage to retrieve
                 information and conversion for the upper layer.

In short:
1. views -depends-> service ----asks----> swh-storage
2. views <- service <----rets---- swh-storage

### Utilities

Folder swh/web/api/:

- apidoc         Browsable api functions.
- apiresponse    Api response utility functions
- apiurls        Api routes registration functions
- exc            Exception definitions
- converters     conversion layer to transform swh data to serializable data.
                 Used by `service` to convert data before transmitting to `api` or `views`.
- query          Utilities to parse data from http endpoints.
                 Used by `service`
- utils          Utilities used throughout swh-web-api.

### About apidoc

This is a 'decorator tower' that stores the data associated with the
documentation upon loading the apidoc module. The top decorator of any
tower should be @apidoc.route(). Apidoc raises an exception if this
decorator is missing, and flask raises an exception if it is present
but not at the top of the tower.

