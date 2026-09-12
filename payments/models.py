from django.db import models


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
    # Make sure one Payment per project per month is unique. This is to avoid duplicate payments for the same project in the same month.
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "payment_month"],
                name="unique_project_payment_month",
            ),
        ]

    def __str__(self):
        return f"{self.project.title} - {self.amount}"
