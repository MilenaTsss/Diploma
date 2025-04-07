import pytest

from barriers.models import Barrier, UserBarrier


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
