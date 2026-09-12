from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Commission(models.Model):
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    recipient_role = models.CharField(
        max_length=100,
    )
    # Making Sure all Percenatage commision lies between 1 - 100
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.recipient.username} - {self.amount}"
