from django.contrib import admin
from django.db.models.deletion import ProtectedError

from .models import Commission, CommissionRate


@admin.register(CommissionRate)
class CommissionRateAdmin(admin.ModelAdmin):
    list_display = (
        "role",
        "percentage",
        "effective_from",
        "created_by",
        "created_at",
    )

    list_filter = (
        "role",
        "effective_from",
    )

    search_fields = (
        "role__name",
        "created_by__username",
        "created_by__email",
    )

    readonly_fields = (
        "created_by",
        "created_at",
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        try:
            super().delete_model(request, obj)
        except ProtectedError:
            self.message_user(
                request,
                "This commission rate cannot be deleted because it is being used by a commission.",
                level="error",
            )


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "recipient",
        "commission_rate",
        "amount",
        "created_at",
    )

    list_filter = (
        "commission_rate__role",
        "created_at",
    )

    search_fields = (
        "recipient__username",
        "recipient__email",
        "commission_rate__role__name",
    )

    readonly_fields = (
        "payment",
        "recipient",
        "commission_rate",
        "amount",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
