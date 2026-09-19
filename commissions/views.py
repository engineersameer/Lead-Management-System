from decimal import Decimal, ROUND_HALF_UP
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError

from rest_framework import generics, serializers, status
from rest_framework.response import Response

from users.permissions import (
    IsBusinessDeveloper,
    IsSuperAdmin,
    IsTechnicalManager,
)

from .models import Commission, CommissionRate
from .serializers import (
    CommissionRateSerializer,
    CommissionSerializer,
)


class CommissionRateListCreateView(generics.ListCreateAPIView):
    queryset = CommissionRate.objects.select_related("created_by")
    serializer_class = CommissionRateSerializer
    permission_classes = [IsSuperAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CommissionRateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CommissionRate.objects.select_related("created_by")
    serializer_class = CommissionRateSerializer
    permission_classes = [IsSuperAdmin]

    def destroy(self, request, *args, **kwargs):
        rate = self.get_object()

        try:
            self.perform_destroy(rate)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "This commission rate cannot be deleted "
                        "because it is already used by a commission."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": ("Commission rate deleted successfully.")},
            status=status.HTTP_200_OK,
        )


class CommissionListCreateView(generics.ListCreateAPIView):
    serializer_class = CommissionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [IsSuperAdmin()]

    def get_queryset(self):
        user = self.request.user

        queryset = Commission.objects.select_related(
            "payment",
            "payment__project",
            "recipient",
            "commission_rate",
        )

        if user.is_superuser:
            return queryset

        return queryset.filter(recipient=user)

    def perform_create(self, serializer):
        payment = serializer.validated_data["payment"]
        recipient_role = serializer.validated_data["recipient_role"]

        if payment.status != payment.Status.PAID:
            raise serializers.ValidationError(
                {"payment": ("Commission can only be created " "for a paid payment.")}
            )

        if payment.payment_date is None:
            raise serializers.ValidationError(
                {
                    "payment": (
                        "A paid payment must have a payment "
                        "date before commission can be created."
                    )
                }
            )

        try:
            commission_rate = CommissionRate.get_rate_for_role(
                role=recipient_role,
                effective_date=payment.payment_date,
            )
        except ValidationError as exc:
            raise serializers.ValidationError(
                {
                    "recipient_role": str(exc),
                }
            )

        project = payment.project

        if recipient_role == Commission.RecipientRole.BD:
            recipient = project.lead.created_by

        elif recipient_role == Commission.RecipientRole.MANAGER:
            recipient = project.manager

        else:
            raise serializers.ValidationError(
                {"recipient_role": ("Invalid commission recipient role.")}
            )

        amount = (
            payment.amount * commission_rate.percentage / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        serializer.save(
            recipient=recipient,
            commission_rate=commission_rate,
            amount=amount,
        )


class CommissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommissionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [IsSuperAdmin()]

    def get_queryset(self):
        user = self.request.user

        queryset = Commission.objects.select_related(
            "payment",
            "payment__project",
            "recipient",
            "commission_rate",
        )

        if user.is_superuser:
            return queryset

        return queryset.filter(recipient=user)

    def update(self, request, *args, **kwargs):
        commission = self.get_object()

        return Response(
            {
                "detail": (
                    "Commission financial values cannot " "be modified after creation."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        commission = self.get_object()

        return Response(
            {
                "detail": (
                    "Commission financial values cannot " "be modified after creation."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        commission = self.get_object()

        return Response(
            {"detail": ("Commission records cannot be deleted " "through the API.")},
            status=status.HTTP_400_BAD_REQUEST,
        )
