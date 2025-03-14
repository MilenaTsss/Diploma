from datetime import timedelta

import pytest
from django.utils.timezone import now
from rest_framework import status

from verifications.models import Verification


@pytest.mark.django_db
class TestSendVerificationCodeView:
    """Tests for SendVerificationCodeView"""

    def test_send_verification_code(self, api_client):
        """Test sending a verification code"""
        response = api_client.post("/auth/codes/", {"phone": "+79991234567", "mode": "login"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "verification_token" in response.data

    def test_send_verification_code_blocked_user(self, api_client, blocked_user):
        """Test sending a verification code for a blocked user"""
        response = api_client.post("/auth/codes/", {"phone": blocked_user.phone, "mode": "login"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_verification_code_too_many_attempts(self, api_client, user, mocker):
        """Test sending a verification code when too many attempts have been made."""
        mocker.patch("verifications.models.VerificationService.count_failed_attempts", return_value=5)
        response = api_client.post("/auth/codes/", {"phone": user.phone, "mode": "login"}, format="json")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_send_verification_code_recently_sent(self, api_client, user, mocker):
        """Test sending a verification code when a recent code was already sent."""

        mock_verification = Verification(
            phone=user.phone,
            verification_token="mock_token",
            created_at=now() - timedelta(seconds=10),  # Recent verification
        )
        mocker.patch("verifications.models.Verification.get_recent_verification", return_value=mock_verification)
        response = api_client.post("/auth/codes/", {"phone": user.phone, "mode": "login"}, format="json")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
class TestVerifyCodeView:
    """Tests for VerifyCodeView"""

    def test_verify_code(self, api_client, verification):
        """Test verifying a correct code"""
        response = api_client.patch(
            "/auth/codes/verify/",
            {
                "phone": verification.phone,
                "code": verification.code,
                "verification_token": verification.verification_token,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        verification.refresh_from_db()
        assert verification.status == Verification.Status.VERIFIED

    def test_verify_invalid_code(self, api_client, verification):
        """Test verifying an incorrect code"""
        response = api_client.patch(
            "/auth/codes/verify/",
            {"phone": verification.phone, "code": "654321", "verification_token": verification.verification_token},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_expired_code(self, api_client, verified_verification):
        """Test verifying an expired code"""
        response = api_client.patch(
            "/auth/codes/verify/",
            {
                "phone": verified_verification.phone,
                "code": verified_verification.code,
                "verification_token": verified_verification.verification_token,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_verify_code_too_many_attempts(self, api_client, verification, mocker):
        """Test verifying a code when too many failed attempts have been made."""
        mocker.patch("verifications.models.VerificationService.count_failed_attempts", return_value=5)
        response = api_client.patch(
            "/auth/codes/verify/",
            {
                "phone": verification.phone,
                "code": verification.code,
                "verification_token": verification.verification_token,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_verify_code_invalid_token(self, api_client):
        """Test verifying a code when the verification token is invalid."""
        response = api_client.patch(
            "/auth/codes/verify/",
            {"phone": "+79991234567", "code": "123456", "verification_token": "invalid_token"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
