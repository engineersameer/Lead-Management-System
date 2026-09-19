from django.urls import path

from .views import (
    CommissionDetailView,
    CommissionListCreateView,
    CommissionRateDetailView,
    CommissionRateListCreateView,
)

urlpatterns = [
    # Commission Rate APIs
    path(
        "rates/",
        CommissionRateListCreateView.as_view(),
        name="commission-rate-list-create",
    ),
    path(
        "rates/<int:pk>/",
        CommissionRateDetailView.as_view(),
        name="commission-rate-detail",
    ),
    # Commission APIs
    path(
        "",
        CommissionListCreateView.as_view(),
        name="commission-list-create",
    ),
    path(
        "<int:pk>/",
        CommissionDetailView.as_view(),
        name="commission-detail",
    ),
]
