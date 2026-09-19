from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/leads/", include("leads.urls")),
    path("api/comments/", include("comments.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/payments/", include("payments.urls")),
    path(
        "api/commissions/",
        include("commissions.urls"),
    ),
]
