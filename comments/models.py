from django.conf import settings
from django.db import models

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


from django.conf import settings
from django.db import models


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
        # Data Integrity Constraint: Ensure that a comment is associated with either a lead or a phase, but not both.
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(lead__isnull=False)
                        & models.Q(phase__isnull=True)
                    )
                    |
                    (
                        models.Q(lead__isnull=True)
                        & models.Q(phase__isnull=False)
                    )
                ),
                name="comment_belongs_to_one_parent",
            )
        ]

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