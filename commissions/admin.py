from django.contrib import admin

from .models import Commission, CommissionRate


@admin.register(CommissionRate)
class CommissionRateAdmin(admin.ModelAdmin):
    list_display = [
        "role",
        "percentage",
        "effective_from",
        "effective_to",
        "created_by",
        "created_at",
    ]

    list_filter = [
        "role",
        "effective_from",
        "effective_to",
    ]

    search_fields = [
        "created_by__username",
    ]

    readonly_fields = [
        "created_by",
        "created_at",
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = [
        "payment",
        "recipient",
        "recipient_role",
        "commission_rate",
        "amount",
        "created_at",
    ]

    list_filter = [
        "recipient_role",
        "commission_rate__role",
        "payment__status",
    ]

    search_fields = [
        "recipient__username",
        "payment__project__title",
    ]

    readonly_fields = [
        "payment",
        "commission_rate",
        "recipient",
        "recipient_role",
        "amount",
        "created_at",
    ]
