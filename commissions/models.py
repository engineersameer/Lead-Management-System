from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models, transaction
from django.db.models import Q

from users.models import Role


class CommissionRate(models.Model):
    """
    Stores one version of a commission rate for a specific Role.

    A new rate is created when the percentage changes.
    Existing rates that have already been used by a Commission
    cannot be modified.
    """

    # These are business-role names from the existing Role table.
    # The CommissionRate itself stores the Role through role_id.
    BD_ROLE_NAME = "BD"
    MANAGER_ROLE_NAME = "Technical Manager"

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="commission_rates",
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
            models.UniqueConstraint(
                fields=[
                    "role",
                    "effective_from",
                ],
                name="unique_commission_rate_start",
            ),
            models.CheckConstraint(
                condition=Q(percentage__gt=0),
                name="commission_rate_percentage_positive",
            ),
        ]

        ordering = [
            "role_id",
            "-effective_from",
        ]

    def clean(self):
        if self.percentage <= 0:
            raise ValidationError(
                {
                    "percentage": (
                        "Commission percentage must be "
                        "greater than zero."
                    )
                }
            )

        if self.percentage > 100:
            raise ValidationError(
                {
                    "percentage": (
                        "Commission percentage cannot "
                        "exceed 100."
                    )
                }
            )

        if self.role_id is None:
            raise ValidationError(
                {
                    "role": "A valid role is required."
                }
            )

        if self.created_by_id is None:
            raise ValidationError(
                {
                    "created_by": (
                        "The user creating the commission "
                        "rate is required."
                    )
                }
            )

        # A used rate is historical and immutable.
        if self.pk:
            existing = CommissionRate.objects.get(
                pk=self.pk,
            )

            is_used = Commission.objects.filter(
                commission_rate_id=self.pk,
            ).exists()

            if is_used:
                if existing.role_id != self.role_id:
                    raise ValidationError(
                        {
                            "role": (
                                "The role of a used commission "
                                "rate cannot be changed."
                            )
                        }
                    )

                if existing.percentage != self.percentage:
                    raise ValidationError(
                        {
                            "percentage": (
                                "The percentage of a used "
                                "commission rate cannot be changed."
                            )
                        }
                    )

                if (
                    existing.effective_from
                    != self.effective_from
                ):
                    raise ValidationError(
                        {
                            "effective_from": (
                                "The effective date of a used "
                                "commission rate cannot be changed."
                            )
                        }
                    )

                if (
                    existing.created_by_id
                    != self.created_by_id
                ):
                    raise ValidationError(
                        {
                            "created_by": (
                                "The creator of a used commission "
                                "rate cannot be changed."
                            )
                        }
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_required_role(cls, role_name):
        try:
            return Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise ValidationError(
                f"The required role '{role_name}' does not exist."
            )

    @classmethod
    def get_rate_for_role(
        cls,
        role_id,
        effective_date,
    ):
        """
        Find the latest rate version for a Role that was
        effective on the supplied date.
        """

        rate = (
            cls.objects.filter(
                role_id=role_id,
                effective_from__lte=effective_date,
            )
            .select_related("role")
            .order_by("-effective_from")
            .first()
        )

        if rate is None:
            raise ValidationError(
                f"No commission rate is configured for "
                f"role {role_id} on {effective_date}."
            )

        return rate

    def __str__(self):
        return (
            f"{self.role.name} - "
            f"{self.percentage}% "
            f"from {self.effective_from}"
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

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "payment",
                    "commission_rate",
                    "recipient",
                ],
                name="unique_payment_rate_recipient",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="commission_amount_positive",
            ),
        ]

    def get_expected_recipient(self):
        project = self.payment.project
        rate_role = self.commission_rate.role

        bd_role = CommissionRate.get_required_role(
            CommissionRate.BD_ROLE_NAME
        )

        manager_role = CommissionRate.get_required_role(
            CommissionRate.MANAGER_ROLE_NAME
        )

        if rate_role.id == bd_role.id:
            return project.lead.created_by

        if rate_role.id == manager_role.id:
            return project.manager

        raise ValidationError(
            {
                "commission_rate": (
                    "This role is not configured as a "
                    "supported commission role."
                )
            }
        )

    def calculate_amount(self):
        return (
            self.payment.amount
            * self.commission_rate.percentage
            / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def clean(self):
        if not self.payment_id:
            raise ValidationError(
                {
                    "payment": "Payment is required."
                }
            )

        if self.payment.status != self.payment.Status.PAID:
            raise ValidationError(
                {
                    "payment": (
                        "Commission can only be created "
                        "for a paid payment."
                    )
                }
            )

        if self.payment.payment_date is None:
            raise ValidationError(
                {
                    "payment": (
                        "A paid payment must have a "
                        "payment date."
                    )
                }
            )

        if not self.commission_rate_id:
            raise ValidationError(
                {
                    "commission_rate": (
                        "Commission rate is required."
                    )
                }
            )

        if not self.recipient_id:
            raise ValidationError(
                {
                    "recipient": (
                        "Commission recipient is required."
                    )
                }
            )

        expected_recipient = self.get_expected_recipient()

        # Recipient must match the business relationship
        # represented by the selected Role.
        if self.recipient_id != expected_recipient.id:
            raise ValidationError(
                {
                    "recipient": (
                        "The recipient does not match the "
                        "selected commission role for this project."
                    )
                }
            )

        # The recipient must actually have the selected Role.
        if not self.recipient.user_roles.filter(
            role_id=self.commission_rate.role_id,
        ).exists():
            raise ValidationError(
                {
                    "commission_rate": (
                        "The recipient does not have the "
                        "role associated with this rate."
                    )
                }
            )

        payment_date = self.payment.payment_date

        # The rate must have started before the payment
        # became eligible for commission.
        if (
            self.commission_rate.effective_from
            > payment_date
        ):
            raise ValidationError(
                {
                    "commission_rate": (
                        "The selected commission rate was not "
                        "effective on the payment date."
                    )
                }
            )

        expected_amount = self.calculate_amount()

        if self.amount != expected_amount:
            raise ValidationError(
                {
                    "amount": (
                        "The commission amount must match "
                        "the system calculation."
                    )
                }
            )

        # Commission becomes a historical financial record.
        if self.pk:
            existing = Commission.objects.get(
                pk=self.pk,
            )

            if existing.payment_id != self.payment_id:
                raise ValidationError(
                    {
                        "payment": (
                            "The payment of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

            if (
                existing.commission_rate_id
                != self.commission_rate_id
            ):
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

            if existing.amount != self.amount:
                raise ValidationError(
                    {
                        "amount": (
                            "The amount of an existing "
                            "commission cannot be changed."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic
    def generate_for_payment(cls, payment):
        """
        Generate the two business commissions for a PAID payment:

        1. Business Developer → Lead.created_by
        2. Technical Manager → Project.manager

        The applicable CommissionRate is selected using
        the Role ID and payment_date.
        """

        if payment.status != payment.Status.PAID:
            raise ValidationError(
                "Commission can only be generated "
                "for a paid payment."
            )

        if payment.payment_date is None:
            raise ValidationError(
                "A paid payment must have a payment date."
            )

        project = (
            payment.__class__.objects
            .select_related(
                "project",
                "project__lead",
                "project__lead__created_by",
                "project__manager",
            )
            .get(
                pk=payment.pk,
            )
        ).project

        # Resolve the exact Role records from the central
        # Role table. CommissionRate stores their IDs.
        bd_role = CommissionRate.get_required_role(
            CommissionRate.BD_ROLE_NAME
        )

        manager_role = CommissionRate.get_required_role(
            CommissionRate.MANAGER_ROLE_NAME
        )

        bd_recipient = project.lead.created_by
        manager_recipient = project.manager

        # Verify the Lead creator is actually a BD.
        if not bd_recipient.user_roles.filter(
            role_id=bd_role.id,
        ).exists():
            raise ValidationError(
                (
                    f"{bd_recipient.username} must have the "
                    "Business Developer role before commission "
                    "can be generated."
                )
            )

        # Verify the Project Manager has the expected role.
        if not manager_recipient.user_roles.filter(
            role_id=manager_role.id,
        ).exists():
            raise ValidationError(
                (
                    f"{manager_recipient.username} must have the "
                    "Technical Manager role before commission "
                    "can be generated."
                )
            )

        commission_data = [
            (
                bd_recipient,
                bd_role.id,
            ),
            (
                manager_recipient,
                manager_role.id,
            ),
        ]

        commissions = []

        for recipient, role_id in commission_data:
            rate = CommissionRate.get_rate_for_role(
                role_id=role_id,
                effective_date=payment.payment_date,
            )

            amount = (
                payment.amount
                * rate.percentage
                / Decimal("100")
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            if amount <= 0:
                raise ValidationError(
                    (
                        f"The calculated commission for "
                        f"{recipient.username} must be greater "
                        "than zero."
                    )
                )

            commission, created = cls.objects.get_or_create(
                payment=payment,
                commission_rate=rate,
                recipient=recipient,
                defaults={
                    "amount": amount,
                },
            )

            commissions.append(commission)

        return commissions

    def __str__(self):
        return (
            f"{self.recipient.username} - "
            f"{self.commission_rate.role.name} - "
            f"{self.amount}"
        )