from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_month = models.DateField()

    payment_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "payment_month"],
                name="unique_project_payment_month",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_amount_positive",
            ),
        ]

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError(
                {"amount": ("Payment amount must be greater than zero.")}
            )

        if self.payment_month is not None and self.payment_month.day != 1:
            raise ValidationError(
                {
                    "payment_month": (
                        "Payment month must use the first day " "of the month."
                    )
                }
            )

        if (
            self.project_id
            and self.project.status == self.project.Status.COMPLETED
            and self._state.adding
        ):
            raise ValidationError(
                {"project": ("Payments cannot be added to a " "completed project.")}
            )

        if self.status == self.Status.PAID and self.payment_date is None:
            raise ValidationError(
                {"payment_date": ("Payment date is required for a paid payment.")}
            )

        if self.status == self.Status.PENDING and self.payment_date is not None:
            raise ValidationError(
                {"payment_date": ("Pending payments cannot have a payment date.")}
            )

    @transaction.atomic
    def change_status(self, new_status, payment_date=None):
        if new_status not in [
            self.Status.PAID,
            self.Status.FAILED,
        ]:
            raise ValidationError("Payment can only be changed to PAID or FAILED.")

        if self.status == self.Status.PAID:
            raise ValidationError("A paid payment cannot have its status changed.")

        if self.status == self.Status.FAILED and new_status == self.Status.FAILED:
            raise ValidationError("This payment has already been marked as failed.")

        if new_status == self.Status.PAID and payment_date is None:
            raise ValidationError(
                "Payment date is required when marking a payment as paid."
            )

        self.status = new_status
        self.payment_date = payment_date

        self.save(
            update_fields=[
                "status",
                "payment_date",
            ]
        )

        # Commission is generated only when the payment
        # successfully reaches the PAID status.
        if new_status == self.Status.PAID:
            from commissions.models import Commission

            Commission.generate_for_payment(self)

    def __str__(self):
        return (
            f"{self.project.title} - " f"{self.amount} - " f"{self.payment_month:%Y-%m}"
        )
