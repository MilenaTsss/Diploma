import pytest
from django.utils.timezone import now
from rest_framework.test import APIClient

from users.models import User
from verifications.models import Verification, VerificationService

USER_PHONE = "+79991234567"
ADMIN_PHONE = "+79995554433"
SUPERUSER_PHONE = "+79994443322"
OTHER_PHONE = "+79999999999"
BLOCKED_USER_PHONE = "+79993332211"
ADMIN_PASSWORD = "adminpassword"
SUPERUSER_PASSWORD = "SuperSecurePass"
USER_NAME = "John User"
ADMIN_NAME = "Admin"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user():
    return User.objects.create_user(phone=USER_PHONE, full_name=USER_NAME)


@pytest.fixture
def admin_user():
    return User.objects.create_admin(phone=ADMIN_PHONE, password=ADMIN_PASSWORD)


@pytest.fixture
def superuser():
    return User.objects.create_superuser(phone=SUPERUSER_PHONE, password=SUPERUSER_PASSWORD)


@pytest.fixture
def blocked_user():
    return User.objects.create_user(phone=BLOCKED_USER_PHONE, is_active=False, block_reason="Spamming")


@pytest.fixture
def client_user(user, client):
    client.force_login(user)
    return client


@pytest.fixture
def client_superuser(superuser, client):
    client.force_login(superuser)
    return client


@pytest.fixture
def client_admin(admin_user, client):
    client.force_login(admin_user)
    return client


@pytest.fixture
def create_verification(db):
    """Factory fixture to create a verification entry"""

    def _create_verification(
        phone=USER_PHONE,
        status=Verification.Status.SENT,
        mode=Verification.Mode.LOGIN,
        code=None,
        verification_token=None,
        created_at=None,
    ):
        return Verification.objects.create(
            phone=phone,
            code=code or VerificationService.generate_verification_code(),
            verification_token=verification_token or VerificationService.generate_verification_token(),
            mode=mode,
            status=status,
            created_at=created_at or now(),
        )

    return _create_verification
