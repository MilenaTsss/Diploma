import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestLoginView:
    """Tests for LoginView"""

    def test_login(self, api_client, verified_verification, user):
        """Test successful login"""
        response = api_client.post(
            "/api/auth/login/",
            {"phone": user.phone, "verification_token": verified_verification.verification_token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_login_unverified_code(self, api_client, verification):
        """Test login with unverified code"""
        response = api_client.post(
            "/api/auth/login/",
            {"phone": verification.phone, "verification_token": verification.verification_token},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_blocked_user(self, api_client, verified_verification, blocked_user):
        """Test login with blocked user"""
        response = api_client.post(
            "/api/auth/login/",
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
            "/api/auth/admin/password_verification/",
            {"phone": admin_user.phone, "password": "adminpassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_password_verification_invalid(self, api_client, admin_user):
        """Test verifying an incorrect admin password"""
        response = api_client.post(
            "/api/auth/admin/password_verification/",
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
        response = api_client.post("/api/auth/token/refresh/", {"refresh": str(refresh)}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
