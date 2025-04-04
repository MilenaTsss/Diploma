import pytest
from rest_framework.test import APIClient

from barriers.models import Barrier, UserBarrier
from users.models import User


@pytest.fixture
def api_client():
    """Fixture for API client"""

    return APIClient()


@pytest.fixture
def user():
    """Create a test user"""

    return User.objects.create_user(phone="+79991234567")


@pytest.fixture
def authenticated_client(api_client, user):

    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_user():
    """Create an admin user"""

    return User.objects.create_admin(phone="+79995554433", password="adminpassword")


@pytest.fixture
def public_barrier(admin_user):
    """A public barrier owned by admin"""

    return Barrier.objects.create(
        address="Public Barrier",
        owner=admin_user,
        device_phone="+70000000001",
        device_model=Barrier.Model.RTU5025,
        device_phones_amount=1,
        is_public=True,
    )


@pytest.fixture
def private_barrier(admin_user):
    """A private barrier not accessible to regular user"""

    return Barrier.objects.create(
        address="Private Barrier",
        owner=admin_user,
        device_phone="+70000000002",
        device_model=Barrier.Model.RTU5035,
        device_phones_amount=1,
        is_public=False,
    )


@pytest.fixture
def private_barrier_with_access(user, admin_user):
    """Private barrier to which the user has access"""

    barrier = Barrier.objects.create(
        address="Accessible Barrier",
        owner=admin_user,
        device_phone="+70000000003",
        device_model=Barrier.Model.TELEMETRICA,
        device_phones_amount=1,
        is_public=False,
    )
    UserBarrier.objects.create(user=user, barrier=barrier)
    return barrier
