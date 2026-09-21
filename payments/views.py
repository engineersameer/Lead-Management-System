"""
Payment validations and business rules:

- Only Super Admin can manage Payment records.
- The selected Project must exist.
- Payments can only be created for an Active Project.
- Payment amount must be greater than zero.
- payment_month must use the first day of the month.
- Only one Payment can exist for the same Project and payment month.
- A newly created Payment starts with PENDING status.
- Payment status cannot be directly changed through normal PUT/PATCH.
- A PENDING Payment can be changed to PAID or FAILED.
- A FAILED Payment can be changed to PAID.
- A FAILED Payment cannot be changed to FAILED again.
- A PAID Payment cannot be changed to PAID again.
- A PAID Payment cannot be changed to FAILED.
- A PAID Payment cannot be modified through normal PUT/PATCH.
- A PAID Payment cannot be deleted.
- A PAID Payment requires a payment date.
- A PENDING Payment cannot have a payment date.
- Payments cannot be added to a Completed Project.
- Payment deletion returns a custom success message.
"""

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

from rest_framework import generics, status
from rest_framework.response import Response

from users.permissions import IsSuperAdmin

from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentStatusChangeSerializer,
)


class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.select_related("project")
    serializer_class = PaymentSerializer
    permission_classes = [IsSuperAdmin]

    def perform_create(self, serializer):
        serializer.save()


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.select_related("project")
    serializer_class = PaymentSerializer
    permission_classes = [IsSuperAdmin]

    def update(self, request, *args, **kwargs):
        payment = self.get_object()

        if payment.status == Payment.Status.PAID:
            return Response(
                {"detail": ("A paid payment cannot be modified.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(
            request,
            *args,
            **kwargs,
        )

    def destroy(self, request, *args, **kwargs):
        payment = self.get_object()

        if payment.status == Payment.Status.PAID:
            return Response(
                {"detail": ("A paid payment cannot be deleted.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self.perform_destroy(payment)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "This payment cannot be deleted because "
                        "it is referenced by another record."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": ("Payment deleted successfully.")},
            status=status.HTTP_200_OK,
        )


class PaymentChangeStatusView(generics.GenericAPIView):
    queryset = Payment.objects.select_related("project")
    serializer_class = PaymentStatusChangeSerializer
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        payment = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            payment.change_status(
                new_status=serializer.validated_data["status"],
                payment_date=serializer.validated_data.get("payment_date"),
            )
        except ValidationError as exc:
            return Response(
                {
                    "detail": (
                        exc.message_dict
                        if hasattr(exc, "message_dict")
                        else exc.messages
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )
