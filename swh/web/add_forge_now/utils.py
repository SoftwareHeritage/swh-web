from urllib.parse import urlparse

from requests import post

from swh.web.config import get_config


def trigger_request_processing_pipeline(id, forge_type, forge_url):
    request_id = id
    lister_type = forge_type
    instance_name = urlparse(forge_url).netloc
    gitlab_pipeline_config = (
        get_config().get("add_forge_now", {}).get("gitlab_pipeline", {})
    )
    pipeline_token = gitlab_pipeline_config.get("token")
    pipeline_trigger_url = gitlab_pipeline_config.get("trigger_url")

    if pipeline_token and pipeline_trigger_url:
        data = {
            "token": pipeline_token,
            "ref": "main",
            "variables[LISTER_TYPE]": lister_type,
            "variables[INSTANCE_NAME]": instance_name,
            "variables[REQUEST_ID]": request_id,
        }

        response = post(
            pipeline_trigger_url,
            data=data,
        )
        # ensure /add-forge/request/update endpoint will return a 500 error
        # if something went wrong with the GitLab request
        response.raise_for_status()
