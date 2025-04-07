import pytest

from barriers.models import Barrier
from users.models import User


@pytest.fixture
def admin_barrier(admin_user):
    return Barrier.objects.create(
        address="St. Example",
        owner=admin_user,
        device_phone="+79995551122",
        device_model=Barrier.Model.RTU5035,
        device_phones_amount=1,
        device_password="adminpass",
        additional_info="Test barrier",
        is_public=True,
        is_active=True,
    )


@pytest.fixture
def another_admin(db):
    return User.objects.create_user(phone="+79992223333", password="otherpass", role=User.Role.ADMIN, is_staff=True)


@pytest.fixture
def other_barrier(another_admin):
    return Barrier.objects.create(
        address="St. Another, 9",
        owner=another_admin,
        device_phone="+79995554433",
        device_model=Barrier.Model.ELFOC,
        device_phones_amount=1,
        device_password="4321",
        additional_info="Private",
        is_public=False,
    )
