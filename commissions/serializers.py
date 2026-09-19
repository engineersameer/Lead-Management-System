from django.core.exceptions import ValidationError

from rest_framework import serializers

from .models import Commission, CommissionRate, CommissionRole


class CommissionRateSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = CommissionRate
        fields = [
            "id",
            "role",
            "percentage",
            "effective_from",
            "effective_to",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
        ]

    def validate_percentage(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Commission percentage must be greater than zero."
            )

        if value > 100:
            raise serializers.ValidationError(
                "Commission percentage cannot exceed 100."
            )

        return value

    def validate(self, attrs):
        effective_from = attrs.get("effective_from")
        effective_to = attrs.get("effective_to")

        if (
            effective_from is not None
            and effective_to is not None
            and effective_to < effective_from
        ):
            raise serializers.ValidationError(
                {
                    "effective_to": (
                        "Effective end date cannot be before " "effective start date."
                    )
                }
            )

        return attrs


class CommissionSerializer(serializers.ModelSerializer):
    recipient = serializers.ReadOnlyField(source="recipient.username")

    commission_rate = CommissionRateSerializer(read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id",
            "payment",
            "recipient",
            "recipient_role",
            "commission_rate",
            "amount",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "commission_rate",
            "amount",
            "created_at",
        ]

    def validate_payment(self, payment):
        if payment.status != payment.Status.PAID:
            raise serializers.ValidationError(
                "Commission can only be created for a paid payment."
            )

        if payment.payment_date is None:
            raise serializers.ValidationError(
                "A paid payment must have a payment date."
            )

        return payment

    def validate_recipient_role(self, value):
        if value not in CommissionRole.values:
            raise serializers.ValidationError("Invalid commission recipient role.")

        return value

    def validate(self, attrs):
        payment = attrs.get("payment")
        recipient_role = attrs.get("recipient_role")

        if payment is not None and recipient_role is not None:
            try:
                CommissionRate.get_rate_for_role(
                    role=recipient_role,
                    effective_date=payment.payment_date,
                )
            except ValidationError as exc:
                raise serializers.ValidationError(
                    {
                        "recipient_role": str(exc),
                    }
                )

        return attrs
