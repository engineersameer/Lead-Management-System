from django.urls import path

from .views import (
    ProjectCompleteView,
    ProjectDetailView,
    ProjectListCreateView,
)

urlpatterns = [
    path(
        "",
        ProjectListCreateView.as_view(),
        name="project-list-create",
    ),
    path(
        "<int:pk>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "<int:pk>/complete/",
        ProjectCompleteView.as_view(),
        name="project-complete",
    ),
]
