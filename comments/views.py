from django.db.models import Q
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Comment, CommentImage
from .permissions import (
    IsCommentParticipant,
    IsCommentParticipantOrAuthor,
)
from .serializers import CommentImageSerializer, CommentSerializer, MultipleCommentImageUploadSerializer
from rest_framework import generics, status
from rest_framework.response import Response

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = Comment.objects.select_related(
            "lead",
            "phase",
            "author",
        ).prefetch_related("images")

        if user.is_superuser:
            return queryset

        return queryset.filter(
            Q(author=user)
            | Q(lead__created_by=user)
            | Q(lead__phases__assignments__manager=user)
            | Q(lead__phases__engineers__engineer=user)
            | Q(phase__lead__created_by=user)
            | Q(phase__assignments__manager=user)
            | Q(phase__engineers__engineer=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related(
        "lead",
        "phase",
        "author",
    ).prefetch_related("images")

    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthenticated,
        IsCommentParticipantOrAuthor,
    ]


class CommentImageListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = CommentImage.objects.select_related(
            "comment",
            "comment__lead",
            "comment__phase",
            "comment__author",
        )

        if user.is_superuser:
            return queryset

        return queryset.filter(
            Q(comment__author=user)
            | Q(comment__lead__created_by=user)
            | Q(comment__lead__phases__assignments__manager=user)
            | Q(comment__lead__phases__engineers__engineer=user)
            | Q(comment__phase__lead__created_by=user)
            | Q(comment__phase__assignments__manager=user)
            | Q(comment__phase__engineers__engineer=user)
        ).distinct()

    def perform_create(self, serializer):
        comment = serializer.validated_data["comment"]

        if (
            not self.request.user.is_superuser
            and comment.author_id != self.request.user.id
        ):
            raise PermissionDenied("Only the comment author can upload images.")

        serializer.save()


class CommentImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CommentImage.objects.select_related(
        "comment",
        "comment__lead",
        "comment__phase",
        "comment__author",
    )

    serializer_class = CommentImageSerializer
    permission_classes = [IsAuthenticated]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)

        if request.user.is_superuser:
            return

        if request.method in ["GET", "HEAD", "OPTIONS"]:
            if not obj.comment.is_user_involved(request.user):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You are not involved with this comment.")
            return

        if obj.comment.author_id != request.user.id:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Only the comment author can modify or delete images."
            )


class MultipleCommentImageUploadView(generics.CreateAPIView):
    serializer_class = MultipleCommentImageUploadSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        comment = generics.get_object_or_404(
            Comment,
            pk=kwargs["comment_id"],
        )

        if (
            not request.user.is_superuser
            and comment.author_id != request.user.id
        ):
            raise PermissionDenied(
                "Only the comment author can upload images."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        images = serializer.validated_data["images"]
        created_images = []

        try:
            with transaction.atomic():
                for image in images:
                    comment_image = CommentImage.objects.create(
                        comment=comment,
                        image=image,
                    )
                    created_images.append(comment_image)

        except Exception:
            for comment_image in created_images:
                if comment_image.image.name:
                    comment_image.image.storage.delete(
                        comment_image.image.name
                    )

            raise

        response_serializer = CommentImageSerializer(
            created_images,
            many=True,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )