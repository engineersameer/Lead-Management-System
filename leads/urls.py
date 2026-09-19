from django.urls import path

from .views import (
    LeadDetailView,
    LeadListCreateView,
    PhaseAssignmentAcceptView,
    PhaseAssignmentDetailView,
    PhaseAssignmentListCreateView,
    PhaseAssignmentRejectView,
    PhaseCompleteView,
    PhaseDetailView,
    PhaseEngineerDetailView,
    PhaseEngineerListCreateView,
    PhaseListCreateView,
)

urlpatterns = [
    path("", LeadListCreateView.as_view(), name="lead-list-create"),
    path("<int:pk>/", LeadDetailView.as_view(), name="lead-detail"),
    path(
        "phases/",
        PhaseListCreateView.as_view(),
        name="phase-list-create",
    ),
    path(
        "phases/<int:pk>/",
        PhaseDetailView.as_view(),
        name="phase-detail",
    ),
    path(
        "phase-assignments/",
        PhaseAssignmentListCreateView.as_view(),
        name="phase-assignment-list-create",
    ),
    path(
        "phase-assignments/<int:pk>/",
        PhaseAssignmentDetailView.as_view(),
        name="phase-assignment-detail",
    ),
    path(
        "phase-assignments/<int:pk>/accept/",
        PhaseAssignmentAcceptView.as_view(),
        name="phase-assignment-accept",
    ),
    path(
        "phase-assignments/<int:pk>/reject/",
        PhaseAssignmentRejectView.as_view(),
        name="phase-assignment-reject",
    ),
    path(
        "phase-engineers/",
        PhaseEngineerListCreateView.as_view(),
        name="phase-engineer-list-create",
    ),
    path(
        "phase-engineers/<int:pk>/",
        PhaseEngineerDetailView.as_view(),
        name="phase-engineer-detail",
    ),
    path(
        "phases/<int:pk>/complete/",
        PhaseCompleteView.as_view(),
        name="phase-complete",
    ),
]
