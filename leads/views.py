from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Lead, Phase
from .serializers import LeadSerializer, PhaseSerializer
from django.utils import timezone

class LeadListCreateView(generics.ListCreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class LeadDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]


class PhaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = [IsAuthenticated]
