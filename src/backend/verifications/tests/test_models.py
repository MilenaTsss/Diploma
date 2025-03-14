from datetime import timedelta

import pytest
from django.utils.timezone import now

from verifications.constants import VERIFICATION_CODE_MAX_LENGTH, VERIFICATION_TOKEN_MAX_LENGTH
from verifications.models import Verification, VerificationService


@pytest.mark.django_db
class TestVerificationService:
    def test_generate_verification_code(self):
        """Test that verification code has the correct format and length."""
        code = VerificationService.generate_verification_code()
        assert isinstance(code, str)
        assert len(code) == VERIFICATION_CODE_MAX_LENGTH
        assert code.isdigit()

    def test_generate_verification_token(self):
        """Test that verification token has the correct format and length."""
        token = VerificationService.generate_verification_token()
        assert isinstance(token, str)
        assert len(token) == VERIFICATION_TOKEN_MAX_LENGTH
        assert token.isalnum()

    def test_create_new_verification(self, verification):
        """Test creation of a new verification entry."""
        verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        assert verification.phone == "+79991234567"
        assert verification.mode == Verification.Mode.LOGIN
        assert verification.status == Verification.Status.SENT
        assert len(verification.code) == VERIFICATION_CODE_MAX_LENGTH
        assert len(verification.verification_token) == VERIFICATION_TOKEN_MAX_LENGTH

    def test_clean_old_verifications(self):
        """Test that old verifications are cleaned up correctly."""
        old_verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        old_verification.created_at = now() - timedelta(days=2)
        old_verification.save()

        VerificationService.clean()
        assert Verification.objects.filter(pk=old_verification.pk).count() == 0

    def test_mark_expired_codes(self, verification):
        """Test marking expired codes as expired."""
        verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        verification.created_at = now() - timedelta(minutes=20)
        verification.save()

        VerificationService.clean()
        verification.refresh_from_db()
        assert verification.status == Verification.Status.EXPIRED

    def test_count_failed_attempts(self, verification):
        """Test counting failed verification attempts."""
        verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        verification.failed_attempts = 3
        verification.save()

        count = VerificationService.count_failed_attempts("+79991234567")
        assert count == 3

    def test_count_unverified_codes(self, verified_verification):
        """Test counting unverified codes."""

        sent_verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)

        expired_verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        expired_verification.status = Verification.Status.EXPIRED
        expired_verification.save()

        verified_verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        verified_verification.status = Verification.Status.VERIFIED
        verified_verification.save()

        count = VerificationService.count_unverified_codes("+79991234567")

        assert count == 2

    @pytest.mark.parametrize(
        "phone, token, mode, expected_status, expected_message",
        [
            ("+79991234567", "valid_token", Verification.Mode.LOGIN, None, None),
            ("+79991234567", "invalid_token", Verification.Mode.LOGIN, 404, "Invalid verification token."),
            ("+79991112233", "valid_token", Verification.Mode.LOGIN, 404, "Invalid phone number."),
            ("+79991234567", "valid_token", Verification.Mode.RESET_PASSWORD, 404, "Invalid verification mode."),
            ("+79991234567", "expired_token", Verification.Mode.LOGIN, 400, "Phone number has not been verified."),
        ],
    )
    def test_confirm_verification(self, db, phone, token, mode, expected_status, expected_message, verification):
        """Test confirming verification based on token, phone, and mode."""

        verification_verified = Verification.objects.create(
            phone="+79991234567",
            verification_token="valid_token",
            mode=Verification.Mode.LOGIN,
            status=Verification.Status.VERIFIED,
        )

        verification_expired = Verification.objects.create(
            phone="+79991234567",
            verification_token="expired_token",
            mode=Verification.Mode.LOGIN,
            status=Verification.Status.EXPIRED,
        )

        verification, message, status_code = VerificationService.confirm_verification(phone, token, mode)

        if expected_status is None:
            assert verification is not None
            assert message is None
        else:
            assert verification is None
            assert message == expected_message
            assert status_code == expected_status

    def test_confirm_verification_wrong_status(db):
        """Test confirming verification with non-verified status."""
        verification = Verification.objects.create(
            phone="+79991234567",
            verification_token="wrong_status_token",
            mode=Verification.Mode.LOGIN,
            status=Verification.Status.SENT,
        )

        verification, message, status_code = VerificationService.confirm_verification(
            "+79991234567", "wrong_status_token", Verification.Mode.LOGIN
        )

        assert verification is None
        assert message == "Phone number has not been verified."
        assert status_code == 400


@pytest.mark.django_db
class TestVerificationModel:

    def test_get_verification_by_token(self, verification):
        """Test retrieving a verification entry by token."""

        verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        retrieved = Verification.get_verification_by_token(verification.verification_token)
        assert retrieved is not None
        assert retrieved.verification_token == verification.verification_token

    def test_get_recent_verification(self, verification):
        """Test retrieving the most recent verification code within a delay window."""

        verification = VerificationService.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        recent_verification = Verification.get_recent_verification("+79991234567", 60)
        assert recent_verification is not None
        assert recent_verification.verification_token == verification.verification_token

    def test_get_recent_verification_with_delay(self):
        """Test retrieving the most recent verification code within a resend delay window."""
        Verification.objects.create(
            phone="+79991234567", verification_token="old_token", created_at=now() - timedelta(seconds=100)
        )
        new_verification = Verification.objects.create(
            phone="+79991234567", verification_token="new_token", created_at=now() - timedelta(seconds=20)
        )

        recent_verification = Verification.get_recent_verification("+79991234567", resend_delay=90)
        assert recent_verification.verification_token == "new_token"

        old_verification = Verification.get_recent_verification("+79991234567", resend_delay=10)
        assert old_verification is None
