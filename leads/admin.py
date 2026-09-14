from django.contrib import admin

from .models import Lead, Phase, PhaseAssignment, PhaseEngineer


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "project_name",
        "client_name",
        "platform",
        "status",
        "created_by",
        "created_at",
        "outcome_at",
        "outcome_by",
    )

    list_filter = (
        "status",
        "platform",
    )

    search_fields = (
        "project_name",
        "client_name",
        "client_email",
    )


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = (
        "lead",
        "sequence",
        "type",
        "status",
        "start_date",
        "due_date",
        "completed_at",
    )

    list_filter = (
        "type",
        "status",
    )

    search_fields = (
        "lead__project_name",
    )


@admin.register(PhaseAssignment)
class PhaseAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "phase",
        "manager",
        "status",
        "assigned_at",
        "responded_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "manager__username",
        "phase__lead__project_name",
    )


@admin.register(PhaseEngineer)
class PhaseEngineerAdmin(admin.ModelAdmin):
    list_display = (
        "phase",
        "engineer",
        "assigned_by",
        "assigned_at",
    )

    search_fields = (
        "engineer__username",
        "assigned_by__username",
        "phase__lead__project_name",
    )