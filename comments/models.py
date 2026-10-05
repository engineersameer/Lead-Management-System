from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

'''Models for the comments app.'''
class Comment(models.Model):
    lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    phase = models.ForeignKey(
        "leads.Phase",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comments",
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(lead__isnull=False) & models.Q(phase__isnull=True))
                    | (models.Q(lead__isnull=True) & models.Q(phase__isnull=False))
                ),
                name="comment_belongs_to_one_parent",
            )
        ]

    def clean(self):
        if self.lead_id is None and self.phase_id is None:
            raise ValidationError("A comment must belong to either a lead or a phase.")

        if self.lead_id is not None and self.phase_id is not None:
            raise ValidationError("A comment cannot belong to both a lead and a phase.")

    def is_user_involved(self, user):
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if self.lead_id:
            lead = self.lead

            # BD who created the lead.
            if lead.created_by_id == user.id:
                return True

            # Manager assigned to any phase of this lead.
            if lead.phases.filter(assignments__manager_id=user.id).exists():
                return True

            # Engineer assigned to any phase of this lead.
            if lead.phases.filter(engineers__engineer_id=user.id).exists():
                return True

            return False

        if self.phase_id:
            # Manager assigned to this phase.
            if self.phase.assignments.filter(manager_id=user.id).exists():
                return True

            # Engineer assigned to this phase.
            if self.phase.engineers.filter(engineer_id=user.id).exists():
                return True

            # BD who created the lead associated with this phase.
            if self.phase.lead.created_by_id == user.id:
                return True

            return False

        return False

    def __str__(self):
        return f"Comment by {self.author.username}"


class CommentImage(models.Model):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="comment_images/",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Image for comment {self.comment_id}"



