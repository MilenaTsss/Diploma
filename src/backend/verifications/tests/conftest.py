import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from verifications.models import Verification

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for API client"""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user"""
    return User.objects.create_user(phone="+79991234567")


@pytest.fixture
def blocked_user():
    """Create a blocked user"""

    return User.objects.create_user(phone="+79991234567", is_active=False)


@pytest.fixture
def create_verification(db):
    """Factory fixture to create a verification entry"""

    def _create_verification(phone="+79991234567", status=Verification.Status.SENT, mode=Verification.Mode.LOGIN):
        return Verification.objects.create(
            phone=phone,
            code="123456",
            verification_token="a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",  # Generate unique token
            mode=mode,
            status=status,
        )

    return _create_verification


@pytest.fixture
def verification(create_verification):
    """Creates a test verification entry"""

    return create_verification()


@pytest.fixture
def verified_verification(create_verification):
    """Creates a verified verification entry"""

    return create_verification(status=Verification.Status.VERIFIED)
