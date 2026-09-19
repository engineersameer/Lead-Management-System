from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "project",
            "amount",
            "payment_month",
            "payment_date",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "payment_date",
            "status",
            "created_at",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        return value

    def validate_payment_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError(
                "Payment month must use the first day of the month."
            )

        return value

    def validate(self, attrs):
        project = attrs.get("project")
        payment_month = attrs.get("payment_month")

        if project is not None:
            if project.status != project.Status.ACTIVE:
                raise serializers.ValidationError(
                    {
                        "project": (
                            "Payments cannot be added to a "
                            "completed project."
                        )
                    }
                )

            if payment_month is not None:
                existing_payment = Payment.objects.filter(
                    project=project,
                    payment_month=payment_month,
                )

                if self.instance is not None:
                    existing_payment = existing_payment.exclude(
                        pk=self.instance.pk
                    )

                if existing_payment.exists():
                    raise serializers.ValidationError(
                        {
                            "payment_month": (
                                "A payment already exists for "
                                "this project and month."
                            )
                        }
                    )

        return attrs


class PaymentStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            Payment.Status.PAID,
            Payment.Status.FAILED,
        ]
    )

    payment_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        new_status = attrs["status"]
        payment_date = attrs.get("payment_date")

        if (
            new_status == Payment.Status.PAID
            and payment_date is None
        ):
            raise serializers.ValidationError(
                {
                    "payment_date": (
                        "Payment date is required when "
                        "status is PAID."
                    )
                }
            )

        return attrs

