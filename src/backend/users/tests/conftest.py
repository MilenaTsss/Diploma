import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from verifications.models import Verification, VerificationService

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
def superuser():
    """Creates a superuser"""

    return User.objects.create_superuser(phone="+79991234567", password="SuperSecurePass")


@pytest.fixture
def admin_user():
    """Create an admin user"""
    return User.objects.create_admin(phone="+79995554433", password="adminpassword")


@pytest.fixture
def blocked_user():
    """Create a blocked user"""

    return User.objects.create_user(phone="+79991234567", is_active=False)


@pytest.fixture
def client_superuser(superuser, client):
    """Logs in client as a superuser"""

    client.force_login(superuser)
    return client


@pytest.fixture
def client_admin(admin_user, client):
    """Logs in client as a regular admin"""

    client.force_login(admin_user)
    return client


@pytest.fixture
def create_verification(db):
    """Factory fixture to create a verification entry"""

    def _create_verification(phone="+79991234567", status=Verification.Status.SENT, mode=Verification.Mode.LOGIN):
        return Verification.objects.create(
            phone=phone,
            code="123456",
            verification_token=VerificationService.generate_verification_token(),  # Generate unique token
            mode=mode,
            status=status,
        )

    return _create_verification


@pytest.fixture
def login_verification(create_verification):
    """Creates a test verification entry with login mode"""

    return create_verification()


@pytest.fixture
def delete_verification(create_verification):
    """Creates a test verification entry with delete mode"""

    return create_verification(mode=Verification.Mode.DELETE_ACCOUNT, status=Verification.Status.VERIFIED)


@pytest.fixture
def verified_verification(create_verification):
    """Creates a verified verification entry"""

    return create_verification(status=Verification.Status.VERIFIED)


@pytest.fixture
def old_verification(create_verification):
    """Creates a verified verification entry for old phone number"""

    return create_verification(mode=Verification.Mode.CHANGE_PHONE_OLD, status=Verification.Status.VERIFIED)


@pytest.fixture
def new_verification(create_verification):
    """Creates a verified verification entry for new phone number"""

    return create_verification(
        phone="+79991112233", mode=Verification.Mode.CHANGE_PHONE_NEW, status=Verification.Status.VERIFIED
    )


@pytest.fixture
def password_verification(create_verification):
    """Creates a verified verification entry for new phone number"""

    return create_verification(
        phone="+79995554433", mode=Verification.Mode.CHANGE_PASSWORD, status=Verification.Status.VERIFIED
    )


@pytest.fixture
def reset_verification(create_verification):
    """Creates a verified verification entry for new phone number"""

    return create_verification(
        phone="+79995554433", mode=Verification.Mode.RESET_PASSWORD, status=Verification.Status.VERIFIED
    )
