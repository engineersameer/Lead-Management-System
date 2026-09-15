from django.utils import timezone

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
    permission_classes = [IsSuperAdmin | IsTechnicalManager]


class PhaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]


class PhaseAssignmentListCreateView(generics.ListCreateAPIView):
    queryset = PhaseAssignment.objects.all()
    serializer_class = PhaseAssignmentSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]


class PhaseAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PhaseAssignment.objects.all()
    serializer_class = PhaseAssignmentSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]


# Accept and Reject are custom business actions, not standard CRUD operations.
class PhaseAssignmentAcceptView(APIView):
    permission_classes = [IsSuperAdmin | IsTechnicalManager]

    def post(self, request, pk):
        assignment = generics.get_object_or_404(
            PhaseAssignment,
            pk=pk,
        )

        assignment.accept()

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

        if not comment:
            return Response(
                {"comment": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assignment.reject(comment)

        return Response(
            PhaseAssignmentSerializer(assignment).data,
            status=status.HTTP_200_OK,
        )


class PhaseEngineerListCreateView(generics.ListCreateAPIView):
    queryset = PhaseEngineer.objects.all()
    serializer_class = PhaseEngineerSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class PhaseEngineerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PhaseEngineer.objects.all()
    serializer_class = PhaseEngineerSerializer
    permission_classes = [IsSuperAdmin | IsTechnicalManager]
