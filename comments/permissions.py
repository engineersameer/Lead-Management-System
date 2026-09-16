from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCommentParticipant(BasePermission):
    """
    A user must be involved with the Lead/Phase associated
    with the comment.

    Super Admin can always access the comment.
    """

    def has_object_permission(self, request, view, obj):
        return obj.is_user_involved(request.user)


class IsCommentParticipantOrAuthor(BasePermission):
    """
    Involved users can read a comment.

    Only the author or Super Admin can modify/delete it.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return obj.is_user_involved(request.user)

        return obj.author_id == request.user.id
