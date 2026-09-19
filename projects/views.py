"""
Before creating a Project, the API validates that:

* The user has permission to create a Project (Super Admin or BD).
* The selected Lead exists.
* The Lead does not already have a Project.
* The Lead has at least one Phase.
* All Phases of the Lead are marked as Completed.
* The selected Manager has the Technical Manager role.
* The Project title is not empty.
* `created_by` is automatically assigned to the authenticated user.
"""

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from users.permissions import (
    IsBusinessDeveloper,
    IsSuperAdmin,
    IsTechnicalManager,
)

from .models import Project
from .serializers import ProjectSerializer


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [(IsSuperAdmin | IsBusinessDeveloper)()]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Project.objects.all()

        if user.has_role("Technical Manager"):
            return Project.objects.filter(manager=user)

        return Project.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [(IsSuperAdmin | IsBusinessDeveloper | IsTechnicalManager)()]

        return [(IsSuperAdmin | IsBusinessDeveloper)()]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Project.objects.all()

        if user.has_role("Technical Manager"):
            return Project.objects.filter(manager=user)

        return Project.objects.all()

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()

        self.perform_destroy(project)

        return Response(
            {"message": "Project deleted successfully."},
            status=status.HTTP_200_OK,
        )


class ProjectCompleteView(generics.GenericAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    permission_classes = [IsSuperAdmin | IsTechnicalManager]

    def post(self, request, pk):
        project = get_object_or_404(
            Project,
            pk=pk,
        )

        # Only the manager assigned to this project
        # can complete it.
        if not request.user.is_superuser and project.manager_id != request.user.id:
            raise PermissionDenied(
                "Only the project manager can complete this project."
            )

        try:
            project.complete()
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ProjectSerializer(
                project,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )
