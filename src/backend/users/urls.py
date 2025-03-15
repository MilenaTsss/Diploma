from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import (
    AdminPasswordVerificationView,
    AdminUserDetailView,
    BlockUserView,
    ChangePasswordView,
    ChangePhoneView,
    CheckAdminView,
    LoginView,
    ResetPasswordView,
    SearchUserView,
    UnblockUserView,
    UserAccountView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "auth/admin/password_verification/", AdminPasswordVerificationView.as_view(), name="admin_password_verification"
    ),
    path("users/check-admin/", CheckAdminView.as_view(), name="check_admin"),
    path("users/me/", UserAccountView.as_view(), name="user_account"),
    path("users/me/phone/", ChangePhoneView.as_view(), name="change_phone"),
    path("users/me/password/", ChangePasswordView.as_view(), name="admin_change_password"),
    path("users/me/password/reset/", ResetPasswordView.as_view(), name="admin_reset_password"),
    path("users/<int:id>/", AdminUserDetailView.as_view(), name="admin_get_user"),
    path("users/<int:id>/block/", BlockUserView.as_view(), name="admin_block_user"),
    path("users/<int:id>/unblock/", UnblockUserView.as_view(), name="admin_unblock_user"),
    path("users/search/", SearchUserView.as_view(), name="admin_search_user"),
]
