import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from verifications.models import Verification


@pytest.mark.django_db
class TestAdminPasswordVerificationView:
    """Tests for AdminPasswordVerificationView"""

    def test_admin_password_verification(self, api_client, admin_user):
        """Test verifying admin password"""
        response = api_client.post(
            "/auth/admin/password_verification/",
            {"phone": admin_user.phone, "password": "adminpassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_password_verification_invalid(self, api_client, admin_user):
        """Test verifying an incorrect admin password"""

        response = api_client.post(
            "/auth/admin/password_verification/",
            {"phone": admin_user.phone, "password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestLoginView:
    """Tests for LoginView"""

    def test_login(self, api_client, verified_verification, user):
        """Test successful login"""

        response = api_client.post(
            "/auth/login/",
            {"phone": user.phone, "verification_token": verified_verification.verification_token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        verified_verification.refresh_from_db()
        assert verified_verification.status == Verification.Status.USED
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_login_unverified_code(self, api_client, login_verification):
        """Test login with unverified code"""

        response = api_client.post(
            "/auth/login/",
            {"phone": login_verification.phone, "verification_token": login_verification.verification_token},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_blocked_user(self, api_client, verified_verification, blocked_user):
        """Test login with blocked user"""

        response = api_client.post(
            "/auth/login/",
            {"phone": blocked_user.phone, "verification_token": verified_verification.verification_token},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCheckAdminView:
    """Tests for CheckAdminView"""

    def test_check_admin_success(self, api_client, admin_user):
        """Test checking if an admin user is recognized correctly"""

        response = api_client.post(
            "/users/check-admin/",
            {"phone": admin_user.phone},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_admin"] is True

    def test_check_non_admin_success(self, api_client, user):
        """Test checking if a regular user is not an admin"""

        response = api_client.post(
            "/users/check-admin/",
            {"phone": user.phone},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_admin"] is False

    def test_check_non_existing_user(self, api_client):
        """Test checking a non-existing user returns is_admin: false"""

        response = api_client.post(
            "/users/check-admin/",
            {"phone": "+79990000000"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_admin"] is False

    def test_check_admin_missing_phone(self, api_client):
        """Test checking admin status without providing a phone number"""

        response = api_client.post(
            "/users/check-admin/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"phone": ["This field is required."]}


@pytest.mark.django_db
class TestTokenRefreshView:
    """Tests for TokenRefreshView"""

    def test_token_refresh(self, api_client, user):
        """Test refreshing JWT token"""

        refresh = RefreshToken.for_user(user)
        response = api_client.post("/auth/token/refresh/", {"refresh": str(refresh)}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data


@pytest.mark.django_db
class TestUserAccountView:
    """Tests for UserAccountView"""

    def test_get_user_profile(self, api_client, user):
        """Test retrieving user profile"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.get("/users/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone
        assert response.data["full_name"] == user.full_name

    def test_edit_user_profile(self, api_client, user):
        """Test editing user profile"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        new_data = {"full_name": "New Name", "phone_privacy": "private"}
        response = api_client.patch("/users/me/", new_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "New Name"
        assert response.data["phone_privacy"] == "private"

    def test_delete_user_account(self, api_client, user, delete_verification):
        """Test deleting user account"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.delete(
            "/users/me/", {"verification_token": delete_verification.verification_token}, format="json"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert not user.is_active
        delete_verification.refresh_from_db()
        assert delete_verification.status == Verification.Status.USED

    def test_delete_user_account_invalid_verification(self, api_client, user):
        """Test deleting user account with invalid verification token"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.delete("/users/me/", {"verification_token": "invalid"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChangePhoneView:
    """Tests for ChangePhoneView"""

    def test_change_phone_success(self, api_client, user, old_verification, new_verification):
        """Test changing phone number successfully"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        new_phone = "+79991112233"
        response = api_client.patch(
            "/users/me/phone/",
            {
                "new_phone": new_phone,
                "old_verification_token": old_verification.verification_token,
                "new_verification_token": new_verification.verification_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.phone == new_phone

        old_verification.refresh_from_db()
        new_verification.refresh_from_db()
        assert old_verification.status == Verification.Status.USED
        assert new_verification.status == Verification.Status.USED


@pytest.mark.django_db
class TestChangePasswordView:
    """Tests for ChangePasswordView"""

    def test_change_password_success(self, api_client, admin_user, password_verification):
        """Test changing password successfully"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(
            "/users/me/password/",
            {
                "old_password": "adminpassword",
                "new_password": "NewPass456!",
                "verification_token": password_verification.verification_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewPass456!") is True

        password_verification.refresh_from_db()
        assert password_verification.status == Verification.Status.USED


@pytest.mark.django_db
class TestResetPasswordView:
    """Tests for ResetPasswordView"""

    def test_reset_password_success(self, api_client, admin_user, reset_verification):
        """Test resetting password successfully"""

        response = api_client.patch(
            "/users/me/password/reset/",
            {
                "phone": admin_user.phone,
                "new_password": "NewSecurePass!",
                "verification_token": reset_verification.verification_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewSecurePass!") is True

        reset_verification.refresh_from_db()
        assert reset_verification.status == Verification.Status.USED


@pytest.mark.django_db
class TestAdminUserAccountView:
    """Tests for AdminUserAccountView"""

    def test_get_user_account_success(self, api_client, admin_user, user):
        """Test retrieving user details as an admin"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.get(f"/admin/users/{user.id}/", format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone

    def test_get_user_not_found(self, api_client, admin_user):
        """Test retrieving details of a non-existent user"""
        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.get("/admin/users/999999/", format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAdminBlockUserView:
    """Tests for AdminBlockUserView"""

    def test_admin_block_user_success(self, api_client, admin_user, user):
        """Test blocking a user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(f"/admin/users/{user.id}/block/", {"reason": "Spamming"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is False
        assert user.block_reason == "Spamming"

    def test_admin_block_user_missing_reason(self, api_client, admin_user, user):
        """Test blocking a user without providing a reason"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(f"/admin/users/{user.id}/block/", {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_block_already_blocked_user(self, api_client, admin_user, blocked_user):
        """Test blocking a user who is already blocked"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(
            f"/admin/users/{blocked_user.id}/block/", {"reason": "Multiple violations"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAdminUnblockUserView:
    """Tests for AdminUnblockUserView"""

    def test_admin_unblock_user_success(self, api_client, admin_user, blocked_user):
        """Test unblocking a user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(f"/admin/users/{blocked_user.id}/unblock/", format="json")

        assert response.status_code == status.HTTP_200_OK
        blocked_user.refresh_from_db()
        assert blocked_user.is_active is True

    def test_admin_unblock_already_active_user(self, api_client, admin_user, user):
        """Test trying to unblock a user who is already active"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(f"/admin/users/{user.id}/unblock/", format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_unblock_admin_user(self, api_client, admin_user, superuser):
        """Test trying to unblock an admin user"""

        superuser.is_active = False
        superuser.save()

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(f"/admin/users/{superuser.id}/unblock/", format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminSearchUserView:
    """Tests for AdminSearchUserView"""

    def test_admin_search_user_success(self, api_client, admin_user, user):
        """Test searching for an existing user by phone"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.post("/admin/users/search/", {"phone": user.phone}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone

    def test_admin_search_user_not_found(self, api_client, admin_user):
        """Test searching for a non-existent user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.post("/admin/users/search/", {"phone": "+79990000000"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_search_user_invalid_phone(self, api_client, admin_user):
        """Test searching with an invalid phone format"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.post("/admin/users/search/", {"phone": "invalid_phone"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
