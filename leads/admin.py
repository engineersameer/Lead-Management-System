from django.contrib import admin
from .models import Lead


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