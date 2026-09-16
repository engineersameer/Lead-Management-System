from django.urls import path

from .views import (
    CommentDetailView,
    CommentImageDetailView,
    CommentImageListCreateView,
    CommentListCreateView,
    MultipleCommentImageUploadView,
)

urlpatterns = [
    path(
        "",
        CommentListCreateView.as_view(),
        name="comment-list-create",
    ),
    path(
        "<int:pk>/",
        CommentDetailView.as_view(),
        name="comment-detail",
    ),
    path(
        "images/",
        CommentImageListCreateView.as_view(),
        name="comment-image-list-create",
    ),
    path(
        "images/<int:pk>/",
        CommentImageDetailView.as_view(),
        name="comment-image-detail",
    ),
    path(
        "<int:comment_id>/images/bulk/",
        MultipleCommentImageUploadView.as_view(),
        name="comment-multiple-images",
    ),
]
