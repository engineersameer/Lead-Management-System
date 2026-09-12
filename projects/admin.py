from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lead",
        "manager",
        "created_by",
        "created_at",
    )

    search_fields = (
        "title",
        "lead__project_name",
        "manager__username",
        "created_by__username",
    )

    list_filter = (
        "manager",
        "created_by",
    )