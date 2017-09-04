import yaml

from rest_framework import renderers


class YAMLRenderer(renderers.BaseRenderer):
    """
    Renderer which serializes to YAML.
    """

    media_type = 'application/yaml'
    format = 'yaml'
    charset = 'utf-8'
    ensure_ascii = False
    default_flow_style = False

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized YAML.
        """
        assert yaml, 'YAMLRenderer requires pyyaml to be installed'

        if data is None:
            return ''

        return yaml.dump(
            data,
            stream=None,
            encoding=self.charset,
            allow_unicode=not self.ensure_ascii,
            default_flow_style=self.default_flow_style
        )
