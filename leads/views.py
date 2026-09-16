from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import (
    IsBusinessDeveloper,
    IsSuperAdmin,
    IsTechnicalManager,
)

from .models import Lead, Phase, PhaseAssignment, PhaseEngineer
from .serializers import (
    LeadSerializer,
    PhaseAssignmentSerializer,
    PhaseEngineerSerializer,
    PhaseSerializer,
)


class LeadListCreateView(generics.ListCreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsSuperAdmin | IsBusinessDeveloper]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class LeadDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsSuperAdmin | IsBusinessDeveloper]

    def perform_update(self, serializer):
        old_status = self.get_object().status
        lead = serializer.save()

        if old_status != lead.status and lead.status in [
            Lead.Status.SOLD,
            Lead.Status.NO_SALE,
        ]:
            lead.outcome_at = timezone.now()
            lead.outcome_by = self.request.user
            lead.save(update_fields=["outcome_at", "outcome_by"])


class PhaseListCreateView(generics.ListCreateAPIView):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = [IsSuperAdmin | IsBusinessDeveloper]


class PhaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = [IsSuperAdmin | IsBusinessDeveloper]


class PhaseAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = PhaseAssignmentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [(IsSuperAdmin | IsBusinessDeveloper)()]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return PhaseAssignment.objects.all()

        if self.request.user.has_role("Technical Manager"):
            return PhaseAssignment.objects.filter(manager=self.request.user)

        return PhaseAssignment.objects.all()


class PhaseAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PhaseAssignment.objects.all()
    serializer_class = PhaseAssignmentSerializer
    permission_classes = [IsSuperAdmin | IsBusinessDeveloper]


# Accept and Reject are custom business actions, not standard CRUD operations.
class PhaseAssignmentAcceptView(APIView):
    permission_classes = [IsSuperAdmin | IsTechnicalManager]

    def post(self, request, pk):
        assignment = generics.get_object_or_404(
            PhaseAssignment,
            pk=pk,
        )

        try:
            assignment.accept()
        except ValidationError as exc:
            return Response(
                {"detail": exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseAssignmentSerializer(assignment).data,
            status=status.HTTP_200_OK,
        )


class PhaseAssignmentRejectView(APIView):
    permission_classes = [IsSuperAdmin | IsTechnicalManager]

    def post(self, request, pk):
        assignment = generics.get_object_or_404(
            PhaseAssignment,
            pk=pk,
        )

        comment = request.data.get("comment")

        try:
            assignment.reject(comment)
        except ValidationError as exc:
            return Response(
                {"detail": exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseAssignmentSerializer(assignment).data,
            status=status.HTTP_200_OK,
        )


class PhaseEngineerListCreateView(generics.ListCreateAPIView):
    queryset = PhaseEngineer.objects.all()
    serializer_class = PhaseEngineerSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phase = serializer.validated_data["phase"]
        engineer = serializer.validated_data["engineer"]

        try:
            phase_engineer = phase.assign_engineer(
                engineer=engineer,
                manager=request.user,
            )

        except (ValueError, ValidationError) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = self.get_serializer(phase_engineer)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PhaseEngineerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PhaseEngineer.objects.all()
    serializer_class = PhaseEngineerSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]
