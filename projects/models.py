from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Project(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    lead = models.OneToOneField(
        "leads.Lead",
        on_delete=models.PROTECT,
        related_name="project",
    )

    title = models.CharField(
        max_length=255,
    )

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="managed_projects",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self):
        if self.manager_id and not self.manager.has_role(
            "Technical Manager"
        ):
            raise ValidationError(
                {
                    "manager": (
                        "The selected user must have the "
                        "Technical Manager role."
                    )
                }
            )

    def complete(self):
        if self.status == self.Status.COMPLETED:
            raise ValidationError(
                "This project has already been completed."
            )

        if self.status != self.Status.ACTIVE:
            raise ValidationError(
                "Only an active project can be completed."
            )

        self.status = self.Status.COMPLETED
        self.save(update_fields=["status"])

    def __str__(self):
        return self.title

