# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormMixin, ProcessFormView

from ..config import get_config
from .handle_message import MessageHandler


class InboundEmailForm(forms.Form):
    shared_key = forms.CharField()
    email = forms.FileField()

    def clean_shared_key(self):
        shared_key = self.cleaned_data["shared_key"]
        if not constant_time_compare(
            shared_key, get_config()["inbound_email"]["shared_key"]
        ):
            raise ValidationError("Invalid shared key!")

        return shared_key


class InboundEmailView(FormMixin, ProcessFormView):
    form_class = InboundEmailForm
    success_url = "/"
    http_method_names = ["post", "put"]  # no blank (get) InboundEmailForm view

    def form_invalid(self, form):
        return HttpResponseBadRequest(
            form.errors.as_json(), content_type="application/json"
        )

    def form_valid(self, form):
        message_handled = MessageHandler(
            raw_message=form.files["email"].read(), sender=self.__class__
        ).handle()
        if message_handled:
            response_data = {"content": "Message successfully handled\n", "status": 200}
        else:
            response_data = {"content": "Message could not be handled\n", "status": 400}
        return HttpResponse(**response_data, content_type="text/plain")

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
