from django.urls import path

from .views import (
    PaymentChangeStatusView,
    PaymentDetailView,
    PaymentListCreateView,
)


urlpatterns = [
    path(
        "",
        PaymentListCreateView.as_view(),
        name="payment-list-create",
    ),
    path(
        "<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "<int:pk>/change-status/",
        PaymentChangeStatusView.as_view(),
        name="payment-change-status",
    ),
]
