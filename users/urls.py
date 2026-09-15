from django.urls import path

from .views import (
    ChangePasswordView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshTokenView,
    RegisterView,
    ResetPasswordView,
    RoleListCreateView,
    RoleDetailView,
    UserRoleListCreateView,
    UserRoleDetailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
    path(
        "forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "roles/",
        RoleListCreateView.as_view(),
        name="role-list-create",
    ),
    path(
        "roles/<int:pk>/",
        RoleDetailView.as_view(),
        name="role-detail",
    ),
    path(
        "user-roles/",
        UserRoleListCreateView.as_view(),
        name="user-role-list-create",
    ),
    path(
        "user-roles/<int:pk>/",
        UserRoleDetailView.as_view(),
        name="user-role-detail",
    ),
]
