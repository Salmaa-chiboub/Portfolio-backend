from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    ProfileView,
    ChangePasswordView,
    ForgotPasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Auth & JWT
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # User profile
    path("me/", ProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # Password reset flow
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),  # Public
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),  # Admin
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),  # Confirmation
]
