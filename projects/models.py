from django.conf import settings
from django.db import models


class Project(models.Model):
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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.title