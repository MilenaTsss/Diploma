from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import AdminPasswordVerificationView, LoginView, SendVerificationCodeView, VerifyCodeView

urlpatterns = [
    path("auth/codes/", SendVerificationCodeView.as_view(), name="send_code"),
    path("auth/codes/verify/", VerifyCodeView.as_view(), name="verify_code"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "auth/admin/password_verification/", AdminPasswordVerificationView.as_view(), name="admin_password_verification"
    ),
]
