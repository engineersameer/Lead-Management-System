from rest_framework import serializers
from .models import Comment, CommentImage


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Comment
        fields = [
            "id",
            "lead",
            "phase",
            "author",
            "content",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
        ]

    def validate(self, attrs):
        lead = attrs.get("lead")
        phase = attrs.get("phase")
        content = attrs.get("content")

        if lead is None and phase is None:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "A comment must belong to either a lead or a phase."
                    ]
                }
            )

        if lead is not None and phase is not None:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "A comment cannot belong to both a lead and a phase."
                    ]
                }
            )

        if content is None or not content.strip():
            raise serializers.ValidationError(
                {"content": "Comment content cannot be empty."}
            )

        request = self.context.get("request")
        user = request.user if request else None

        # Validate user involvement before creating the Comment.
        if user and not user.is_superuser:
            if lead is not None:
                if lead.created_by_id != user.id:
                    manager_involved = lead.phases.filter(
                        assignments__manager_id=user.id
                    ).exists()

                    engineer_involved = lead.phases.filter(
                        engineers__engineer_id=user.id
                    ).exists()

                    if not manager_involved and not engineer_involved:
                        raise serializers.ValidationError(
                            {
                                "detail": (
                                    "You are not involved with this lead "
                                    "and cannot comment on it."
                                )
                            }
                        )

            elif phase is not None:
                bd_involved = phase.lead.created_by_id == user.id

                manager_involved = phase.assignments.filter(manager_id=user.id).exists()

                engineer_involved = phase.engineers.filter(engineer_id=user.id).exists()

                if not (bd_involved or manager_involved or engineer_involved):
                    raise serializers.ValidationError(
                        {
                            "detail": (
                                "You are not involved with this phase "
                                "and cannot comment on it."
                            )
                        }
                    )

        return attrs


class CommentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentImage
        fields = [
            "id",
            "comment",
            "image",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "uploaded_at",
        ]

    def validate_image(self, image):
        max_size = 5 * 1024 * 1024  # 5 MB

        if image.size > max_size:
            raise serializers.ValidationError("Image size cannot exceed 5 MB.")

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        extension = ""
        if image.name and "." in image.name:
            extension = "." + image.name.rsplit(".", 1)[1].lower()

        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                "Only JPG, JPEG, PNG, and WebP images are allowed."
            )

        return image



class MultipleCommentImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False,
    )

    def validate_images(self, images):
        max_images = 10
        max_size = 5 * 1024 * 1024  # 5 MB per image

        if len(images) > max_images:
            raise serializers.ValidationError(
                f"You can upload a maximum of {max_images} images at once."
            )

        for image in images:
            if image.size > max_size:
                raise serializers.ValidationError(
                    f"{image.name} exceeds the 5 MB size limit."
                )

            allowed_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            }

            extension = ""
            if image.name and "." in image.name:
                extension = "." + image.name.rsplit(".", 1)[1].lower()

            if extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"{image.name} is not a supported image format. "
                    "Allowed formats are JPG, JPEG, PNG, and WebP."
                )

        return images