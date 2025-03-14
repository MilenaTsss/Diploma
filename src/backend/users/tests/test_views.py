import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


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

    def test_delete_user_account_invalid_verification(self, api_client, user):
        """Test deleting user account with invalid verification token"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.delete("/users/me/", {"verification_token": "invalid"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
