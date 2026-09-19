from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F, Q


class CommissionRole(models.TextChoices):
    BD = "BD", "Business Developer"
    MANAGER = "MANAGER", "Manager"


class CommissionRate(models.Model):
    """
    Stores the commission percentage for a role and the period
    during which that percentage is effective.
    """

    role = models.CharField(
        max_length=20,
        choices=CommissionRole.choices,
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_commission_rates",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            # A role cannot have two rate records starting
            # on the same date.
            models.UniqueConstraint(
                fields=[
                    "role",
                    "effective_from",
                ],
                name="unique_commission_rate_start",
            ),
            # effective_to must be the same date or after
            # effective_from when it is provided.
            models.CheckConstraint(
                condition=(
                    Q(effective_to__isnull=True)
                    | Q(effective_to__gte=F("effective_from"))
                ),
                name="valid_commission_rate_period",
            ),
            # Only one open-ended/current rate can exist
            # for each role.
            models.UniqueConstraint(
                fields=["role"],
                condition=Q(effective_to__isnull=True),
                name="one_open_commission_rate_per_role",
            ),
        ]

    def clean(self):
        if self.effective_to is not None:
            if self.effective_to < self.effective_from:
                raise ValidationError(
                    {
                        "effective_to": (
                            "Effective end date cannot be before "
                            "the effective start date."
                        )
                    }
                )

        # Prevent overlapping rate periods for the same role.
        overlapping_rates = CommissionRate.objects.filter(
            role=self.role,
        )

        if self.pk:
            overlapping_rates = overlapping_rates.exclude(
                pk=self.pk,
            )

        overlapping_rates = overlapping_rates.filter(
            effective_from__lte=(
                self.effective_to if self.effective_to is not None else "9999-12-31"
            ),
        )

        if self.effective_to is None:
            overlapping_rates = overlapping_rates.filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=self.effective_from)
            )
        else:
            overlapping_rates = overlapping_rates.filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=self.effective_from)
            )

        if overlapping_rates.exists():
            raise ValidationError(
                {
                    "effective_from": (
                        "The effective period overlaps with "
                        "another commission rate for this role."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_rate_for_role(cls, role, effective_date):
        rate = (
            cls.objects.filter(
                role=role,
                effective_from__lte=effective_date,
            )
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=effective_date))
            .first()
        )

        if rate is None:
            raise ValidationError(
                f"No commission rate is configured for " f"{role} on {effective_date}."
            )

        return rate

    def __str__(self):
        end_date = self.effective_to if self.effective_to is not None else "Open-ended"

        return (
            f"{self.get_role_display()} - "
            f"{self.percentage}% "
            f"({self.effective_from} to {end_date})"
        )


class Commission(models.Model):

    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    commission_rate = models.ForeignKey(
        CommissionRate,
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    recipient_role = models.CharField(
        max_length=20,
        choices=CommissionRole.choices,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            # One commission per payment per recipient role.
            models.UniqueConstraint(
                fields=[
                    "payment",
                    "recipient_role",
                ],
                name="unique_payment_recipient_role",
            ),
            # Commission amount must always be positive.
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="commission_amount_positive",
            ),
        ]

    def get_expected_recipient(self):
        project = self.payment.project

        if self.recipient_role == CommissionRole.BD:
            return project.lead.created_by

        if self.recipient_role == CommissionRole.MANAGER:
            return project.manager

        raise ValidationError("Invalid commission recipient role.")

    def calculate_amount(self):
        return (
            self.payment.amount * self.commission_rate.percentage / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def clean(self):
        if not self.payment_id:
            raise ValidationError({"payment": "Payment is required."})

        # Commission applies only when the payment is PAID.
        if self.payment.status != self.payment.Status.PAID:
            raise ValidationError(
                {"payment": ("Commission can only be created " "for a paid payment.")}
            )

        if not self.commission_rate_id:
            raise ValidationError({"commission_rate": ("Commission rate is required.")})

        if not self.recipient_role:
            raise ValidationError(
                {"recipient_role": ("Commission recipient role is required.")}
            )

        # The selected CommissionRate must belong to
        # the same role as the Commission.
        if self.commission_rate.role != self.recipient_role:
            raise ValidationError(
                {
                    "commission_rate": (
                        "The commission rate role must match "
                        "the commission recipient role."
                    )
                }
            )

        # The selected rate must have been effective on
        # the payment date.
        if self.payment.payment_date is None:
            raise ValidationError(
                {
                    "payment": (
                        "A paid payment must have a payment date "
                        "before commission can be created."
                    )
                }
            )

        payment_date = self.payment.payment_date

        if payment_date < self.commission_rate.effective_from:
            raise ValidationError(
                {
                    "commission_rate": (
                        "The selected commission rate was not "
                        "effective on the payment date."
                    )
                }
            )

        if (
            self.commission_rate.effective_to is not None
            and payment_date > self.commission_rate.effective_to
        ):
            raise ValidationError(
                {
                    "commission_rate": (
                        "The selected commission rate had "
                        "expired before the payment date."
                    )
                }
            )

        expected_recipient = self.get_expected_recipient()

        if self.recipient_id != expected_recipient.id:
            raise ValidationError(
                {
                    "recipient": (
                        "The recipient does not match the "
                        "project's commission recipient."
                    )
                }
            )

        expected_amount = self.calculate_amount()

        if self.amount != expected_amount:
            raise ValidationError(
                {
                    "amount": (
                        "The commission amount must match " "the system calculation."
                    )
                }
            )

        # Financial identity becomes immutable after creation.
        if self.pk:
            existing = Commission.objects.get(
                pk=self.pk,
            )

            if existing.payment_id != self.payment_id:
                raise ValidationError(
                    {"payment": ("The payment of a commission " "cannot be changed.")}
                )

            if existing.commission_rate_id != self.commission_rate_id:
                raise ValidationError(
                    {
                        "commission_rate": (
                            "The commission rate of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

            if existing.recipient_id != self.recipient_id:
                raise ValidationError(
                    {
                        "recipient": (
                            "The recipient of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

            if existing.recipient_role != self.recipient_role:
                raise ValidationError(
                    {
                        "recipient_role": (
                            "The recipient role of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_for_payment(cls, payment):
        """
        Generate the BD and Manager commissions for a PAID payment.
        The applicable CommissionRate is selected using the payment date.
        """

        if payment.status != payment.Status.PAID:
            raise ValidationError(
                "Commission can only be generated for a paid payment."
            )

        if payment.payment_date is None:
            raise ValidationError("A paid payment must have a payment date.")

        project = payment.project
        payment_date = payment.payment_date

        commission_data = [
            (
                CommissionRole.BD,
                project.lead.created_by,
            ),
            (
                CommissionRole.MANAGER,
                project.manager,
            ),
        ]

        commissions = []

        for recipient_role, recipient in commission_data:
            rate = CommissionRate.get_rate_for_role(
                role=recipient_role,
                effective_date=payment_date,
            )

            amount = (payment.amount * rate.percentage / Decimal("100")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            commission, created = cls.objects.get_or_create(
                payment=payment,
                recipient_role=recipient_role,
                defaults={
                    "commission_rate": rate,
                    "recipient": recipient,
                    "amount": amount,
                },
            )

            commissions.append(commission)

        return commissions

    def __str__(self):
        return (
            f"{self.recipient.username} - " f"{self.recipient_role} - " f"{self.amount}"
        )
