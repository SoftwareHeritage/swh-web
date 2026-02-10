# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django_bootstrap5.renderers import FieldRenderer


class CustomValidationClassFieldRenderer(FieldRenderer):
    def get_server_side_validation_classes(self) -> str:
        """Return CSS classes for server-side validation.

        This overrides the default field renderer to properly use ``error_css_class``
        and ``success_css_class`` parameters which are otherwise ignored.

        @see: https://github.com/zostera/django-bootstrap5/issues/302

        Returns:
            A class name to apply to a field.
        """
        if self.field_errors:
            return self.error_css_class
        elif self.field.form.is_bound:
            return self.success_css_class
        return ""
