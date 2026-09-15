from rest_framework import serializers

from .models import Lead, Phase, PhaseAssignment, PhaseEngineer


class LeadSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Lead
        fields = [
            "id",
            "project_name",
            "client_name",
            "client_address",
            "client_email",
            "client_contact",
            "platform",
            "status",
            "created_by",
            "created_at",
            "outcome_at",
            "outcome_by",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "outcome_at",
            "outcome_by",
        ]


class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = [
            "id",
            "lead",
            "sequence",
            "type",
            "start_date",
            "due_date",
            "status",
            "completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "completed_at",
            "created_at",
        ]


class PhaseAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhaseAssignment
        fields = [
            "id",
            "phase",
            "manager",
            "status",
            "rejection_comment",
            "assigned_at",
            "responded_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "rejection_comment",
            "assigned_at",
            "responded_at",
        ]


class PhaseEngineerSerializer(serializers.ModelSerializer):
    assigned_by = serializers.ReadOnlyField(source="assigned_by.username")

    class Meta:
        model = PhaseEngineer
        fields = [
            "id",
            "phase",
            "engineer",
            "assigned_by",
            "assigned_at",
        ]
        read_only_fields = [
            "id",
            "assigned_by",
            "assigned_at",
        ]
