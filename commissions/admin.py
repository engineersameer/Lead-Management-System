from django.contrib import admin

from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "recipient",
        "recipient_role",
        "percentage",
        "amount",
        "created_at",
    )

    list_filter = (
        "recipient_role",
    )

    search_fields = (
        "recipient__username",
        "payment__project__title",
    )