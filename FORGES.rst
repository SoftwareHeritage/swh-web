To add support for a new forge type, edit these files:

    swh/web/add_forge_now/views.py

        Modify the forge list in FORGE_TYPES to add the forge type name.

    swh/web/add_forge_now/templates/add-forge-help.html

        Modify the forge list in swh-add-forge-requests-help to add the
        forge type name and a link to the forge type website or repo.

    swh/web/add_forge_now/assets/create-request.js

	Modify validateForgeContents to add a check that the forge is valid,
	usually by checking that the forge API works and returns repos.

        Modify getUrlExtra to add a check for common URL suffixes that
        should be removed before submission of the URL to the AFN interface.

    swh/web/archive_coverage/views.py

        Modify the origins item of the listed_origins dict to add the
        forge type name, info URL, description and search pattern

    swh/web/static/img/logos/$type.png

        Add the logo for the forge type.

    swh/web/save_origin_webhooks/$type.py

        If the forge has webhooks support then add that here.

    swh/web/save_origin_webhooks/urls.py

        If the forge has webhooks support then add that here.

    docs/uri-scheme-api-request-archival.rst

        If the forge has webhooks support then add that here.
