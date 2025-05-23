from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from conftest import USER_PHONE
from core.utils import error_response
from verifications.models import Verification


@pytest.mark.django_db
class TestSendVerificationCodeView:
    url = reverse("send_code")
    data = {
        "phone": USER_PHONE,
        "mode": Verification.Mode.LOGIN,
    }
    verification = {
        "verification_token": "token",
        "code": "123456",
        "created_at": now(),
    }

    @pytest.fixture(autouse=True)
    def _setup_default_mocks(self, mocker):
        """Autouse fixture to apply default mocks for every test unless overridden."""

        mocker.patch("verifications.views.VerificationService.clean")
        mocker.patch("users.models.UserManager.check_phone_blocked", return_value=None)
        mocker.patch("verifications.views.VerificationService.check_fail_limits", return_value=None)
        mocker.patch("verifications.views.VerificationService.check_unverified_limits", return_value=None)
        mocker.patch("verifications.views.Verification.get_recent_verification", return_value=None)

        mock_create = mocker.patch("verifications.views.VerificationService.create_new_verification")
        mock_create.return_value = mocker.MagicMock(**self.verification)

    @patch("message_management.services.SMSService.send_verification")
    def test_successful_code_send(self, mock_send_verification, api_client):
        response = api_client.post(self.url, self.data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["verification_token"] == self.verification["verification_token"]
        assert response.data["code"] == "123456"
        mock_send_verification.assert_called_once()

    @patch("message_management.services.SMSService.send_verification")
    def test_clean_called(self, mock_send_verification, api_client, mocker):
        mock_clean = mocker.patch("verifications.views.VerificationService.clean")

        response = api_client.post(self.url, self.data)

        mock_clean.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED
        mock_send_verification.assert_called_once()

    def test_blocked_phone(self, api_client, mocker):
        mocker.patch(
            "users.models.UserManager.check_phone_blocked",
            return_value=error_response("Blocked", status.HTTP_403_FORBIDDEN),
        )

        response = api_client.post(self.url, self.data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "Blocked"

    def test_fail_limit_exceeded(self, api_client, mocker):
        mocker.patch(
            "verifications.views.VerificationService.check_fail_limits",
            return_value=error_response("Too many failed", status.HTTP_429_TOO_MANY_REQUESTS),
        )

        response = api_client.post(self.url, self.data)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data["detail"] == "Too many failed"

    def test_unverified_limit_exceeded(self, api_client, mocker):
        mocker.patch(
            "verifications.views.VerificationService.check_unverified_limits",
            return_value=error_response("Too many unverified", status.HTTP_429_TOO_MANY_REQUESTS),
        )

        response = api_client.post(self.url, self.data)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data["detail"] == "Too many unverified"

    class TestVerificationModeChecks:
        url = reverse("send_code")

        def test_phone_already_exists(self, api_client, user):
            data = {"phone": user.phone, "mode": Verification.Mode.CHANGE_PHONE_NEW}

            response = api_client.post(self.url, data)

            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.data["detail"] == "This new phone number already exists."

        @pytest.mark.parametrize("mode", [Verification.Mode.RESET_PASSWORD, Verification.Mode.CHANGE_PASSWORD])
        def test_cannot_change_password_for_regular_user(self, mode, api_client, user):
            data = {"phone": user.phone, "mode": mode}

            response = api_client.post(self.url, data)

            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.data["detail"] == "You do not have permission to perform this action."

        @pytest.mark.parametrize(
            "mode",
            [
                Verification.Mode.RESET_PASSWORD,
                Verification.Mode.CHANGE_PASSWORD,
                Verification.Mode.DELETE_ACCOUNT,
                Verification.Mode.CHANGE_PHONE_OLD,
            ],
        )
        def test_user_not_found_for_modes_that_require_user(self, mode, api_client):
            data = {"phone": USER_PHONE, "mode": mode}

            response = api_client.post(self.url, data)

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.data["detail"] == "User not found."

        @pytest.mark.parametrize("mode", [Verification.Mode.LOGIN, Verification.Mode.CHANGE_PHONE_NEW])
        @patch("message_management.services.SMSService.send_verification")
        def test_passes_for_modes_that_allow_missing_user(self, mock_send_verification, mode, api_client):
            data = {"phone": USER_PHONE, "mode": mode}

            response = api_client.post(self.url, data)

            assert response.status_code == status.HTTP_201_CREATED
            mock_send_verification.assert_called_once()

    def test_recent_code_already_sent(self, api_client, mocker):
        recent = Verification(
            phone=USER_PHONE,
            verification_token="recent_token",
            created_at=now(),
        )
        mocker.patch("verifications.views.Verification.get_recent_verification", return_value=recent)

        response = api_client.post(self.url, self.data)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data["detail"] == "Verification code was already sent. Try again later."
        assert "Retry-After" in response.headers


@pytest.mark.django_db
class TestVerifyCodeView:
    url = reverse("verify_code")

    @pytest.fixture
    def verification_data(self, verification):
        return {
            "phone": verification.phone,
            "code": verification.code,
            "verification_token": verification.verification_token,
        }

    @pytest.fixture(autouse=True)
    def _setup_default_mocks(self, mocker):
        """Autouse fixture to apply default mocks for every test unless overridden."""

        mocker.patch("verifications.views.VerificationService.clean")
        mocker.patch("users.models.UserManager.check_phone_blocked", return_value=None)
        mocker.patch("verifications.views.VerificationService.check_fail_limits", return_value=None)
        mocker.patch("verifications.views.VerificationService.validate_verification_is_usable", return_value=None)

    def test_verify_code(self, api_client, verification, verification_data):
        """Test verifying a correct code"""

        response = api_client.patch(self.url, verification_data)

        assert response.status_code == status.HTTP_200_OK
        verification.refresh_from_db()
        assert verification.status == Verification.Status.VERIFIED

    def test_clean_called(self, api_client, verification_data, mocker):
        mock_clean = mocker.patch("verifications.views.VerificationService.clean")

        response = api_client.patch(self.url, verification_data)

        mock_clean.assert_called_once()
        assert response.status_code == status.HTTP_200_OK

    def test_blocked_phone(self, api_client, verification_data, mocker):
        mocker.patch(
            "users.models.UserManager.check_phone_blocked",
            return_value=error_response("Blocked", status.HTTP_403_FORBIDDEN),
        )

        response = api_client.patch(self.url, verification_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "Blocked"

    def test_fail_limit_exceeded(self, api_client, verification_data, mocker):
        mocker.patch(
            "verifications.views.VerificationService.check_fail_limits",
            return_value=error_response("Too many failed", status.HTTP_429_TOO_MANY_REQUESTS),
        )

        response = api_client.patch(self.url, verification_data)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data["detail"] == "Too many failed"

    def test_verification_fails_due_to_validation(self, api_client, verification_data, mocker):
        mocker.patch(
            "verifications.views.VerificationService.validate_verification_is_usable",
            return_value=error_response("Some validation error", status.HTTP_400_BAD_REQUEST),
        )

        response = api_client.patch(self.url, verification_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Some validation error"

    def test_verification_code_mismatch(self, api_client, verification):

        response = api_client.patch(
            self.url,
            {
                "phone": verification.phone,
                "code": "123456",
                "verification_token": verification.verification_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Invalid code."
        verification.refresh_from_db()
        assert verification.failed_attempts == 1
