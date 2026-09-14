from django.urls import path

from .views import LeadDetailView, LeadListCreateView, PhaseDetailView, PhaseListCreateView

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
]

"""
Lead list create view:
GET  /api/leads/   → list all leads
POST /api/leads/   → create a lead



RetrieveUpdateDestroyAPIView
GET    /api/leads/1/   → retrieve lead
PUT    /api/leads/1/   → full update
PATCH  /api/leads/1/   → partial update
DELETE /api/leads/1/   → delete

"""
