from django.conf.urls import url

from swh.web.add_forge_now import views

urlpatterns = [
    url(r"^add/$", views.submit_request, name="forge-add"),
]
