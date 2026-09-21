from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from users.models import Role

from .models import Commission, CommissionRate


class CommissionRateSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        source="role",
        queryset=Role.objects.all(),
    )

    created_by = serializers.ReadOnlyField(
        source="created_by.username",
    )

    class Meta:
        model = CommissionRate
        fields = [
            "id",
            "role_id",
            "percentage",
            "effective_from",
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
        role = attrs.get("role")
        effective_from = attrs.get("effective_from")

        if role is None:
            raise serializers.ValidationError(
                {"role_id": "A valid role ID is required."}
            )

        if effective_from is None:
            raise serializers.ValidationError(
                {"effective_from": ("An effective start date is required.")}
            )

        # Prevent duplicate rate versions for the same
        # role and effective date.
        existing_rate = CommissionRate.objects.filter(
            role=role,
            effective_from=effective_from,
        )

        if self.instance is not None:
            existing_rate = existing_rate.exclude(
                pk=self.instance.pk,
            )

        if existing_rate.exists():
            raise serializers.ValidationError(
                {
                    "effective_from": (
                        "A commission rate already exists for "
                        "this role with the same effective date."
                    )
                }
            )

        # A CommissionRate that has already been used by a
        # Commission becomes historically immutable.
        if self.instance is not None:
            is_used = Commission.objects.filter(
                commission_rate=self.instance,
            ).exists()

            if is_used:
                protected_fields = [
                    "role",
                    "percentage",
                    "effective_from",
                ]

                for field in protected_fields:
                    if field in attrs:
                        current_value = getattr(
                            self.instance,
                            field,
                        )

                        if attrs[field] != current_value:
                            raise serializers.ValidationError(
                                {
                                    field: (
                                        "This commission rate has "
                                        "already been used and cannot "
                                        "be modified."
                                    )
                                }
                            )

        return attrs


class CommissionSerializer(serializers.ModelSerializer):
    commission_rate_id = serializers.PrimaryKeyRelatedField(
        source="commission_rate",
        queryset=CommissionRate.objects.select_related("role"),
        write_only=True,
    )

    commission_rate = CommissionRateSerializer(
        read_only=True,
    )

    recipient = serializers.ReadOnlyField(
        source="recipient.username",
    )

    class Meta:
        model = Commission
        fields = [
            "id",
            "payment",
            "commission_rate_id",
            "commission_rate",
            "recipient",
            "amount",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "commission_rate",
            "recipient",
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

    def validate(self, attrs):
        payment = attrs.get(
            "payment",
            self.instance.payment if self.instance is not None else None,
        )

        commission_rate = attrs.get(
            "commission_rate",
            self.instance.commission_rate if self.instance is not None else None,
        )

        if payment is None:
            raise serializers.ValidationError({"payment": "Payment is required."})

        if commission_rate is None:
            raise serializers.ValidationError(
                {"commission_rate_id": ("Commission rate is required.")}
            )

        if payment.status != payment.Status.PAID:
            raise serializers.ValidationError(
                {"payment": ("Commission can only be created " "for a paid payment.")}
            )

        if payment.payment_date is None:
            raise serializers.ValidationError(
                {"payment": ("A paid payment must have a " "payment date.")}
            )

        payment_date = payment.payment_date

        # The selected rate must already be effective
        # when the payment was paid.
        if commission_rate.effective_from > payment_date:
            raise serializers.ValidationError(
                {
                    "commission_rate_id": (
                        "The selected commission rate was not "
                        "effective on the payment date."
                    )
                }
            )

        project = payment.project

        candidates = []

        if project.lead_id:
            lead_recipient = project.lead.created_by

            if lead_recipient.user_roles.filter(
                role_id=commission_rate.role_id,
            ).exists():
                candidates.append(lead_recipient)

        if project.manager_id:
            manager_recipient = project.manager

            if manager_recipient.user_roles.filter(
                role_id=commission_rate.role_id,
            ).exists():
                if manager_recipient not in candidates:
                    candidates.append(manager_recipient)

        if not candidates:
            raise serializers.ValidationError(
                {
                    "commission_rate_id": (
                        "The selected commission rate role does "
                        "not match a valid commission recipient "
                        "for this project."
                    )
                }
            )

        if len(candidates) > 1:
            raise serializers.ValidationError(
                {
                    "commission_rate_id": (
                        "The selected commission role matches "
                        "multiple project recipients. "
                        "The commission recipient must be unambiguous."
                    )
                }
            )

        expected_recipient = candidates[0]

        # Prevent duplicate Commission records.
        existing_commission = Commission.objects.filter(
            payment=payment,
            commission_rate=commission_rate,
            recipient=expected_recipient,
        )

        if self.instance is not None:
            existing_commission = existing_commission.exclude(
                pk=self.instance.pk,
            )

        if existing_commission.exists():
            raise serializers.ValidationError(
                {
                    "commission_rate_id": (
                        "A commission already exists for this "
                        "payment, rate, and recipient."
                    )
                }
            )

        # Existing Commission identity is immutable.
        if self.instance is not None:
            if "payment" in attrs and attrs["payment"].pk != self.instance.payment_id:
                raise serializers.ValidationError(
                    {
                        "payment": (
                            "The payment of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

            if (
                "commission_rate" in attrs
                and attrs["commission_rate"].pk != self.instance.commission_rate_id
            ):
                raise serializers.ValidationError(
                    {
                        "commission_rate_id": (
                            "The commission rate of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

        attrs["_expected_recipient"] = expected_recipient

        return attrs

    def create(self, validated_data):
        recipient = validated_data.pop("_expected_recipient")

        payment = validated_data["payment"]
        commission_rate = validated_data["commission_rate"]

        amount = (
            payment.amount * commission_rate.percentage / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        commission = Commission(
            payment=payment,
            commission_rate=commission_rate,
            recipient=recipient,
            amount=amount,
        )

        commission.save()

        return commission
