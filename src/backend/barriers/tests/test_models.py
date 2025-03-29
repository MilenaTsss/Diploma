import pytest
from django.contrib.auth import get_user_model

from barriers.models import Barrier, UserBarrier

User = get_user_model()


@pytest.mark.django_db
def test_user_has_access_to_barrier_returns_true():
    user = User.objects.create(phone="+71234567890", full_name="Test User", role=User.Role.ADMIN, is_staff=True)
    barrier = Barrier.objects.create(
        address="Test Address",
        owner=user,
        device_phone="+70001112233",
        device_model=Barrier.Model.RTU5025,
        device_phones_amount=1,
        device_password="1234",
        additional_info="Test",
        is_public=False,
    )
    UserBarrier.objects.create(user=user, barrier=barrier)

    result = UserBarrier.user_has_access_to_barrier(user, barrier)

    assert result is True


@pytest.mark.django_db
def test_user_has_access_to_barrier_returns_false():
    user1 = User.objects.create(phone="+71234567890", full_name="User1", role=User.Role.ADMIN, is_staff=True)
    user2 = User.objects.create(phone="+79876543210", full_name="User2", role=User.Role.ADMIN, is_staff=True)

    barrier = Barrier.objects.create(
        address="Another Address",
        owner=user1,
        device_phone="+79998887766",
        device_model=Barrier.Model.RTU5035,
        device_phones_amount=1,
        device_password="4321",
        additional_info="Test",
        is_public=False,
    )

    result = UserBarrier.user_has_access_to_barrier(user2, barrier)

    assert result is False
