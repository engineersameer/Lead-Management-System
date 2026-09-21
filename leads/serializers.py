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

    def validate(self, attrs):
        phase = attrs["phase"]
        manager = attrs["manager"]

        # The selected user must have the Technical Manager role.
        if not manager.has_role("Technical Manager"):
            raise serializers.ValidationError(
                {
                    "manager": (
                        "The selected user must have the " "Technical Manager role."
                    )
                }
            )

        # A phase can have only one active assignment.
        active_assignment_exists = PhaseAssignment.objects.filter(
            phase=phase,
            status__in=[
                PhaseAssignment.Status.PENDING,
                PhaseAssignment.Status.ACCEPTED,
            ],
        ).exists()

        if active_assignment_exists:
            raise serializers.ValidationError(
                {
                    "phase": (
                        "This phase already has a pending or accepted "
                        "manager assignment."
                    )
                }
            )

        return attrs


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

    def validate(self, attrs):
        phase = attrs["phase"]
        engineer = attrs["engineer"]

        if not engineer.has_role("Engineer"):
            raise serializers.ValidationError(
                {"engineer": ("The selected user must have the Engineer role.")}
            )

        if PhaseEngineer.objects.filter(
            phase=phase,
            engineer=engineer,
        ).exists():
            raise serializers.ValidationError(
                {"engineer": ("This engineer is already assigned to this phase.")}
            )

        return attrs
