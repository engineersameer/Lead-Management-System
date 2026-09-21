from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

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


def is_super_admin(user):
    """
    Keep queryset visibility consistent with the IsSuperAdmin
    permission. A user may be a Super Admin through the
    application's Role system without Django is_superuser=True.
    """
    return user.is_superuser or user.has_role("Super Admin")


class CommissionRateListCreateView(generics.ListCreateAPIView):
    """
    Admin-only CRUD endpoint for CommissionRate configuration.
    """

    queryset = CommissionRate.objects.select_related(
        "role",
        "created_by",
    )
    serializer_class = CommissionRateSerializer
    permission_classes = [IsSuperAdmin]

    def perform_create(self, serializer):
        try:
            serializer.save(
                created_by=self.request.user,
            )
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "A commission rate with these values "
                        "already exists or conflicts with another "
                        "rate period for this role."
                    )
                }
            )


class CommissionRateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only endpoint for viewing, updating, and deleting
    CommissionRate records.
    """

    queryset = CommissionRate.objects.select_related(
        "role",
        "created_by",
    )
    serializer_class = CommissionRateSerializer
    permission_classes = [IsSuperAdmin]

    def update(self, request, *args, **kwargs):
        rate = self.get_object()

        # A rate becomes historical configuration once it has
        # been used by a Commission. It must never be changed.
        if rate.commissions.exists():
            return Response(
                {
                    "detail": (
                        "This commission rate has already been "
                        "used and cannot be modified. Create a "
                        "new commission rate for future payments."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(
            request,
            *args,
            **kwargs,
        )

    def partial_update(self, request, *args, **kwargs):
        rate = self.get_object()

        if rate.commissions.exists():
            return Response(
                {
                    "detail": (
                        "This commission rate has already been "
                        "used and cannot be modified. Create a "
                        "new commission rate for future payments."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().partial_update(
            request,
            *args,
            **kwargs,
        )

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
    """
    Commission endpoint.

    GET:
        Super Admin → all commissions
        BD/Manager → own commissions

    POST:
        Super Admin only
    """

    serializer_class = CommissionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [
            IsSuperAdmin(),
        ]

    def get_queryset(self):
        user = self.request.user

        queryset = Commission.objects.select_related(
            "payment",
            "payment__project",
            "payment__project__lead",
            "recipient",
            "commission_rate",
            "commission_rate__role",
        )

        if is_super_admin(user):
            return queryset

        return queryset.filter(
            recipient=user,
        )

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "A commission already exists for this "
                        "payment and recipient/rate combination."
                    )
                }
            )


class CommissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Commission records are historical financial records.

    GET:
        Super Admin → any commission
        BD/Manager → own commission

    PUT/PATCH:
        not allowed

    DELETE:
        not allowed
    """

    serializer_class = CommissionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [
            IsSuperAdmin(),
        ]

    def get_queryset(self):
        user = self.request.user

        queryset = Commission.objects.select_related(
            "payment",
            "payment__project",
            "payment__project__lead",
            "recipient",
            "commission_rate",
            "commission_rate__role",
        )

        if is_super_admin(user):
            return queryset

        return queryset.filter(
            recipient=user,
        )

    def update(self, request, *args, **kwargs):
        self.get_object()

        return Response(
            {
                "detail": (
                    "Commission records are historical "
                    "financial records and cannot be modified."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        self.get_object()

        return Response(
            {
                "detail": (
                    "Commission records are historical "
                    "financial records and cannot be modified."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        self.get_object()

        return Response(
            {"detail": ("Commission records cannot be deleted " "through the API.")},
            status=status.HTTP_400_BAD_REQUEST,
        )
