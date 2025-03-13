from datetime import timedelta

import pytest
from django.utils.timezone import now

from users.constants import VERIFICATION_CODE_MAX_LENGTH, VERIFICATION_TOKEN_MAX_LENGTH
from users.models import User, Verification


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(phone="+79991234567")
        assert user.phone == "+79991234567"
        assert user.is_active is True
        assert user.role == User.Role.USER
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_admin(self):
        """Test creating an admin user."""
        user = User.objects.create_admin(phone="+79991234568", password="AdminPass123")
        assert user.phone == "+79991234568"
        assert user.is_staff is True
        assert user.role == User.Role.ADMIN
        assert user.is_superuser is False

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(phone="+79991234569", password="SuperPass123")
        assert user.phone == "+79991234569"
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.role == User.Role.SUPERUSER

    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(phone="+79991234567", full_name="John Doe")
        assert user.get_full_name() == "John Doe"

    def test_get_phone(self):
        """Test get_phone method."""
        user = User.objects.create_user(phone="+79991234567")
        assert user.get_phone() == "+79991234567"


@pytest.mark.django_db
class TestVerificationModel:
    def test_create_new_verification(self):
        """Test creation of a new verification entry."""
        verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        assert verification.phone == "+79991234567"
        assert verification.mode == Verification.Mode.LOGIN
        assert verification.status == Verification.Status.SENT
        assert len(verification.code) == VERIFICATION_CODE_MAX_LENGTH
        assert len(verification.verification_token) == VERIFICATION_TOKEN_MAX_LENGTH

    def test_get_verification_by_token(self):
        """Test retrieving a verification entry by token."""
        verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        retrieved = Verification.get_verification_by_token(verification.verification_token)
        assert retrieved is not None
        assert retrieved.verification_token == verification.verification_token

    def test_get_recent_verification(self):
        """Test retrieving the most recent verification code within a delay window."""
        verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        recent_verification = Verification.get_recent_verification("+79991234567", 60)
        assert recent_verification is not None
        assert recent_verification.verification_token == verification.verification_token

    def test_clean_old_verifications(self):
        """Test that old verifications are cleaned up correctly."""
        old_verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        old_verification.created_at = now() - timedelta(days=2)
        old_verification.save()

        Verification.clean()
        assert Verification.objects.filter(pk=old_verification.pk).count() == 0

    def test_mark_expired_codes(self):
        """Test marking expired codes as expired."""
        verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        verification.created_at = now() - timedelta(minutes=20)
        verification.save()

        Verification.clean()
        verification.refresh_from_db()
        assert verification.status == Verification.Status.EXPIRED

    def test_count_failed_attempts(self):
        """Test counting failed verification attempts."""
        verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        verification.failed_attempts = 3
        verification.save()

        count = Verification.count_failed_attempts("+79991234567")
        assert count == 3

    def test_count_unverified_codes(self):
        """Test counting unverified codes."""

        sent_verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)  # SENT

        expired_verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        expired_verification.status = Verification.Status.EXPIRED
        expired_verification.save()

        verified_verification = Verification.create_new_verification("+79991234567", Verification.Mode.LOGIN)
        verified_verification.status = Verification.Status.VERIFIED
        verified_verification.save()

        count = Verification.count_unverified_codes("+79991234567")

        assert count == 2
