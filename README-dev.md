README-dev
==========

# modules' description

## Main

swh.web.ui.main: Start the server or the dev server

## Layers

Folder swh/web/ui/:

- api            main api endpoints definition (api)
- views          main ui endpoints (web app)
- service        Orchestration layer used by api/view module.
                 In charge of communication with `backend` to retrieve
                 information and conversion for the upper layer.
- backend        Lower layer in charge of communication with swh storage.
                 Used by `service` module.

In short:
1. views -depends-> api -depends-> service -depends-> backend     ----asks----> swh-storage
2. views <- api <- service <- backend                             <----rets---- swh-storage

## Utilities

Folder swh/web/ui/:

- apidoc         Browsable api functions.
- exc            Exception definitions.
- errorhandler   Exception (defined in `exc`) handlers.
                 Use at route definition time (`api`, `views`).
- renderers      Rendering utilities (html, json, yaml, data...).
                 Use at route definition time (`api`, `views`).
- converters     conversion layer to transform swh data to serializable data.
                 Used by `service` to convert data before transmitting to `api` or `views`.
- query          Utilities to parse data from http endpoints.
                 Used by `service`
- upload         Utility module to deal with upload of data to webapp or api.
                 Used by `api`
- utils          Utilities used throughout swh-web-ui.

### About apidoc

This is a 'decorator tower' that stores the data associated with the
documentation upon loading the apidoc module. The top decorator of any
tower should be @apidoc.route(). Apidoc raises an exception if this
decorator is missing, and flask raises an exception if it is present
but not at the top of the tower.

## Graphics summary

    ![Summary dependencies](./docs/dependencies.png)
