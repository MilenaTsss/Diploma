from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import (
    AdminPasswordVerificationView,
    ChangePasswordView,
    ChangePhoneView,
    LoginView,
    ResetPasswordView,
    UserAccountView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "auth/admin/password_verification/", AdminPasswordVerificationView.as_view(), name="admin_password_verification"
    ),
    path("users/me/", UserAccountView.as_view(), name="user_account"),
    path("users/me/phone/", ChangePhoneView.as_view(), name="change_phone"),
    path("users/me/password/", ChangePasswordView.as_view(), name="change_password"),
    path("users/me/password/reset/", ResetPasswordView.as_view(), name="reset_password"),
]
