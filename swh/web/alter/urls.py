# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import path

from .views import (
    admin_alteration,
    admin_dashboard,
    admin_event,
    admin_message,
    admin_origin,
    alteration_access,
    alteration_details,
    alteration_link,
    alteration_message,
    assistant_category,
    assistant_email,
    assistant_email_verification,
    assistant_origins,
    assistant_reasons,
    assistant_summary,
    content_policies,
)

urlpatterns = [
    path("content-policies/", content_policies, name="content-policies"),
    path("alteration/email/", assistant_email, name="alteration-email"),
    path(
        "alteration/email/verification/<str:value>/",
        assistant_email_verification,
        name="alteration-email-verification",
    ),
    path("alteration/category/", assistant_category, name="alteration-category"),
    path("alteration/origins/", assistant_origins, name="alteration-origins"),
    path("alteration/reasons/", assistant_reasons, name="alteration-reasons"),
    path("alteration/summary/", assistant_summary, name="alteration-summary"),
    path("alteration/<uuid:pk>/", alteration_details, name="alteration-details"),
    path(
        "alteration/<uuid:pk>/message/", alteration_message, name="alteration-message"
    ),
    path("alteration/<uuid:pk>/access/", alteration_access, name="alteration-access"),
    path("alteration/link/<str:value>/", alteration_link, name="alteration-link"),
    path("admin/alteration/", admin_dashboard, name="alteration-dashboard"),
    path("admin/alteration/<uuid:pk>/", admin_alteration, name="alteration-admin"),
    path(
        "admin/alteration/<uuid:alteration_pk>/origin/<uuid:pk>/",
        admin_origin,
        name="alteration-origin-admin",
    ),
    path(
        "admin/alteration/<uuid:alteration_pk>/origin/",
        admin_origin,
        name="alteration-origin-admin-create",
    ),
    path(
        "admin/alteration/<uuid:pk>/message/",
        admin_message,
        name="alteration-message-admin",
    ),
    path(
        "admin/alteration/<uuid:alteration_pk>/event/<uuid:pk>/",
        admin_event,
        name="alteration-event-admin",
    ),
]
