from rest_framework import serializers

from leads.models import Phase
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(
        source="created_by.username"
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "lead",
            "title",
            "manager",
            "status",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "created_at",
        ]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Project title cannot be empty."
            )

        return value.strip()

    def validate(self, attrs):
        lead = attrs.get("lead")
        manager = attrs.get("manager")

        # A lead can have only one project.
        if lead is not None:
            existing_project = Project.objects.filter(
                lead=lead
            )

            # Allow the current project to retain its own lead
            # during update.
            if self.instance is not None:
                existing_project = existing_project.exclude(
                    pk=self.instance.pk
                )

            if existing_project.exists():
                raise serializers.ValidationError(
                    {
                        "lead": (
                            "This lead already has a project."
                        )
                    }
                )

            # A project requires at least one phase.
            phases = lead.phases.all()

            if not phases.exists():
                raise serializers.ValidationError(
                    {
                        "lead": (
                            "A project cannot be created because "
                            "this lead has no phases."
                        )
                    }
                )

            # All phases of the lead must be completed.
            incomplete_phases = phases.exclude(
                status=Phase.Status.COMPLETED
            )

            if incomplete_phases.exists():
                raise serializers.ValidationError(
                    {
                        "lead": (
                            "A project cannot be created until "
                            "all phases of the lead are completed."
                        )
                    }
                )

        # The selected manager must be a Technical Manager.
        if manager is not None and not manager.has_role(
            "Technical Manager"
        ):
            raise serializers.ValidationError(
                {
                    "manager": (
                        "The selected user must have the "
                        "Technical Manager role."
                    )
                }
            )

        return attrs

