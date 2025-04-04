import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from barriers.models import Barrier, UserBarrier

User = get_user_model()


@pytest.mark.django_db
class TestUserHasAccessToBarrier:
    def test_returns_true(self):
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

    def test_returns_false_if_no_link(self):
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

    def test_returns_false_if_inactive(self):
        user = User.objects.create(phone="+71112223344", full_name="Inactive User", role=User.Role.ADMIN, is_staff=True)
        barrier = Barrier.objects.create(
            address="Inactive Test",
            owner=user,
            device_phone="+71110002233",
            device_model=Barrier.Model.ELFOC,
            device_phones_amount=2,
            device_password="5678",
            additional_info="Test",
            is_public=False,
        )

        UserBarrier.objects.create(user=user, barrier=barrier, is_active=False)

        result = UserBarrier.user_has_access_to_barrier(user, barrier)

        assert result is False


@pytest.mark.django_db
class TestUserBarrierCreate:
    def test_creates_new_active_link(self):
        user = User.objects.create(phone="+71110000000", full_name="New User", role=User.Role.ADMIN, is_staff=True)
        barrier = Barrier.objects.create(
            address="Create New",
            owner=user,
            device_phone="+71110001111",
            device_model=Barrier.Model.RTU5025,
            device_phones_amount=1,
            device_password="1234",
            additional_info="Info",
            is_public=True,
        )

        user_barrier = UserBarrier.create(user=user, barrier=barrier)

        assert user_barrier.user == user
        assert user_barrier.barrier == barrier
        assert user_barrier.is_active is True

    def test_reactivates_existing_inactive_link(self):
        user = User.objects.create(phone="+71110000001", full_name="Old User", role=User.Role.ADMIN, is_staff=True)
        barrier = Barrier.objects.create(
            address="Reactivate",
            owner=user,
            device_phone="+71110002222",
            device_model=Barrier.Model.ELFOC,
            device_phones_amount=1,
            device_password="4321",
            additional_info="Info",
            is_public=False,
        )
        user_barrier = UserBarrier.objects.create(user=user, barrier=barrier, is_active=False)

        result = UserBarrier.create(user=user, barrier=barrier)

        user_barrier.refresh_from_db()
        assert result == user_barrier
        assert user_barrier.is_active is True

    def test_raises_error_if_active_link_exists(self):
        user = User.objects.create(phone="+71110000002", full_name="Active User", role=User.Role.ADMIN, is_staff=True)
        barrier = Barrier.objects.create(
            address="Already Active",
            owner=user,
            device_phone="+71110003333",
            device_model=Barrier.Model.TELEMETRICA,
            device_phones_amount=2,
            device_password="0000",
            additional_info="Info",
            is_public=True,
        )
        UserBarrier.objects.create(user=user, barrier=barrier, is_active=True)

        with pytest.raises(ValidationError, match="An active access already exists for this user and barrier."):
            UserBarrier.create(user=user, barrier=barrier)
