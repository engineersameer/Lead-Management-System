from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Lead(models.Model):

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SOLD = "SOLD", "Sold"
        NO_SALE = "NO_SALE", "No Sale"

    project_name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    client_address = models.TextField(blank=True)
    client_email = models.EmailField(blank=True)
    client_contact = models.CharField(max_length=50, blank=True)

    platform = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_leads",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    outcome_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    outcome_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_outcomes",
    )

    def __str__(self):
        return self.project_name

    def change_status(self, status):
        if status not in self.Status.values:
            raise ValidationError("Invalid lead status.")

        self.status = status
        self.save(update_fields=["status"])


class Phase(models.Model):

    class Type(models.TextChoices):
        INTERVIEW = "INTERVIEW", "Interview"
        TEST = "TEST", "Test"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="phases",
    )

    sequence = models.PositiveIntegerField()

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    start_date = models.DateTimeField()
    due_date = models.DateTimeField()

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.project_name} - Phase {self.sequence}"

    def complete(self, user):
        # A completed phase cannot be completed again.
        if self.status == self.Status.COMPLETED:
            raise ValidationError(
                "This phase has already been completed."
            )

        # A phase must be in progress before it can be completed.
        if self.status != self.Status.IN_PROGRESS:
            raise ValidationError(
                "A phase must be in progress before it can be completed."
            )

        # There must be an accepted manager assignment.
        accepted_assignment = self.assignments.filter(
            status=PhaseAssignment.Status.ACCEPTED,
        ).first()

        if not accepted_assignment:
            raise ValidationError(
                "The phase must have an accepted manager assignment "
                "before it can be completed."
            )

        # Only the manager who accepted the phase can complete it.
        if (
            not user.is_superuser
            and accepted_assignment.manager_id != user.id
        ):
            raise ValidationError(
                "Only the manager who accepted the phase can complete it."
            )

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

    def assign_engineer(self, engineer, manager):
        # A completed phase cannot receive a new engineer.
        if self.status == self.Status.COMPLETED:
            raise ValidationError(
                "A completed phase cannot be assigned to an engineer."
            )

        # The selected user must have the Engineer role.
        if not engineer.has_role("Engineer"):
            raise ValidationError(
                "The selected user must have the Engineer role."
            )

        # Engineer assignment is only possible after manager acceptance.
        accepted_assignment = self.assignments.filter(
            status=PhaseAssignment.Status.ACCEPTED,
        ).first()

        if not accepted_assignment:
            raise ValidationError(
                "The phase must be accepted by a manager "
                "before assigning an engineer."
            )

        # A Technical Manager can assign engineers only to a phase
        # that they personally accepted.
        if (
            not manager.is_superuser
            and accepted_assignment.manager_id != manager.id
        ):
            raise ValidationError(
                "Only the manager who accepted the phase "
                "can assign an engineer."
            )

        # Prevent duplicate phase-engineer assignments.
        if self.engineers.filter(
            engineer=engineer,
        ).exists():
            raise ValidationError(
                "This engineer is already assigned to this phase."
            )

        return PhaseEngineer.objects.create(
            phase=self,
            engineer=engineer,
            assigned_by=manager,
        )


class PhaseAssignment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_assignments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    rejection_comment = models.TextField(blank=True)

    assigned_at = models.DateTimeField(auto_now_add=True)

    responded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["phase"],
                condition=models.Q(
                    status__in=[
                        "PENDING",
                        "ACCEPTED",
                    ]
                ),
                name="unique_active_phase_manager",
            ),
        ]

    def __str__(self):
        return f"{self.phase} - {self.manager.username}"

    def accept(self, user):
        # The assignment can only be accepted while pending.
        if self.status != self.Status.PENDING:
            raise ValidationError(
                "You cannot change the decision after the assignment "
                "has been accepted or rejected."
            )

        # Only the assigned manager can accept the assignment.
        if (
            not user.is_superuser
            and self.manager_id != user.id
        ):
            raise ValidationError(
                "Only the manager assigned to this phase can accept it."
            )

        with transaction.atomic():
            self.status = self.Status.ACCEPTED
            self.responded_at = timezone.now()

            self.save(
                update_fields=[
                    "status",
                    "responded_at",
                ]
            )

            # Accepting the phase automatically starts it.
            if self.phase.status == Phase.Status.PENDING:
                self.phase.status = Phase.Status.IN_PROGRESS
                self.phase.save(
                    update_fields=["status"]
                )

    def reject(self, comment, user):
        # The assignment can only be rejected while pending.
        if self.status != self.Status.PENDING:
            raise ValidationError(
                "You cannot change the decision after the assignment "
                "has been accepted or rejected."
            )

        # Only the assigned manager can reject the assignment.
        if (
            not user.is_superuser
            and self.manager_id != user.id
        ):
            raise ValidationError(
                "Only the manager assigned to this phase can reject it."
            )

        if not comment or not comment.strip():
            raise ValidationError(
                "Rejection comment is required."
            )

        self.status = self.Status.REJECTED
        self.rejection_comment = comment.strip()
        self.responded_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "rejection_comment",
                "responded_at",
            ]
        )

    def is_accepted(self):
        return self.status == self.Status.ACCEPTED


class PhaseEngineer(models.Model):

    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name="engineers",
    )

    engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_engineer_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="engineers_assigned",
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["phase", "engineer"],
                name="unique_phase_engineer",
            )
        ]

    def __str__(self):
        return f"{self.phase} - {self.engineer.username}"

