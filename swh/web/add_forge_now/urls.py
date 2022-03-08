from django.conf.urls import url

from swh.web.add_forge_now import views

urlpatterns = [
    url(r"^add/$", views.create_request, name="forge-add"),
]
