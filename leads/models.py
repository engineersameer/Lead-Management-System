from django.conf import settings
from django.db import models


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
    