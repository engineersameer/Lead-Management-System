from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


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

    def complete(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def assign_engineer(self, engineer, manager):
        assignment = self.assignments.filter(manager=manager).first()

        if not assignment:
            raise ValueError("This manager is not assigned to this phase.")

        if not assignment.is_accepted():
            raise ValueError(
                "The manager must accept the phase before assigning engineers."
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

    # NEW: Allows assignment history, but only one PENDING or ACCEPTED
    # manager assignment can exist for a phase at a time.
    # If one manager assignment is REJECTED, another manager can be assigned to the same phase
    # Can't request another manager assignment if one is already PENDING or ACCEPTED for the same phase.
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

    def accept(self):
        self.status = self.Status.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self, comment):
        if not comment:
            raise ValueError("Rejection comment is required.")

        self.status = self.Status.REJECTED
        self.rejection_comment = comment
        self.responded_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "rejection_comment",
                "responded_at",
            ]
        )

    # If Manager has accepted the assignment, this method will return True, otherwise False.
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
