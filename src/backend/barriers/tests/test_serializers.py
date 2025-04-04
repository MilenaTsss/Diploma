import pytest
from rest_framework.test import APIRequestFactory

from barriers.models import Barrier, BarrierLimit, UserBarrier
from barriers.serializers import BarrierLimitSerializer, BarrierSerializer
from users.models import User


@pytest.mark.django_db
class TestBarrierSerializer:

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def admin(self):
        return User.objects.create(phone="+70000000001", full_name="Admin", role=User.Role.ADMIN)

    @pytest.fixture
    def user(self):
        return User.objects.create(phone="+70000000002", full_name="User", role=User.Role.USER)

    @pytest.fixture
    def barrier(self, admin):
        return Barrier.objects.create(
            address="test address",
            owner=admin,
            device_phone="+79000000000",
            device_model=Barrier.Model.RTU5025,
            device_phones_amount=1,
            device_password="1234",
            is_public=True,
        )

    def test_owner_phone_hidden_for_private(self, factory, user, barrier):
        barrier.owner.phone_privacy = User.PhonePrivacy.PRIVATE
        barrier.owner.save()

        request = factory.get("/")
        request.user = user
        serializer = BarrierSerializer(barrier, context={"request": request})

        assert serializer.data["owner"]["phone"] is None

    def test_owner_phone_visible_for_public(self, factory, user, barrier):
        barrier.owner.phone_privacy = User.PhonePrivacy.PUBLIC
        barrier.owner.save()

        request = factory.get("/")
        request.user = user
        serializer = BarrierSerializer(barrier, context={"request": request})

        assert serializer.data["owner"]["phone"] == barrier.owner.phone

    def test_owner_phone_visible_for_protected_with_access(self, factory, user, barrier):
        barrier.owner.phone_privacy = User.PhonePrivacy.PROTECTED
        barrier.owner.save()

        UserBarrier.objects.create(user=user, barrier=barrier)

        request = factory.get("/")
        request.user = user
        serializer = BarrierSerializer(barrier, context={"request": request})

        assert serializer.data["owner"]["phone"] == barrier.owner.phone

    def test_device_phone_hidden_without_access(self, factory, user, barrier):
        request = factory.get("/")
        request.user = user
        serializer = BarrierSerializer(barrier, context={"request": request})

        assert serializer.data["device_phone"] is None

    def test_device_phone_visible_with_access(self, factory, user, barrier):
        UserBarrier.objects.create(user=user, barrier=barrier)

        request = factory.get("/")
        request.user = user
        serializer = BarrierSerializer(barrier, context={"request": request})

        assert serializer.data["device_phone"] == barrier.device_phone


@pytest.mark.django_db
class TestBarrierLimitSerializer:
    def test_serializes_all_fields_except_timestamps(self):
        user = User.objects.create_admin(phone="+79991230000", password="1234")
        barrier = Barrier.objects.create(
            address="Limit Address",
            owner=user,
            device_phone="+79991230001",
            device_model=Barrier.Model.RTU5035,
            device_phones_amount=1,
            device_password="0000",
            additional_info="For test",
            is_public=True,
        )

        limits = BarrierLimit.objects.create(
            barrier=barrier,
            user_phone_limit=3,
            user_temp_phone_limit=1,
            global_temp_phone_limit=5,
            sms_weekly_limit=50,
        )

        serialized = BarrierLimitSerializer(limits).data

        assert serialized["user_phone_limit"] == 3
        assert serialized["user_temp_phone_limit"] == 1
        assert serialized["global_temp_phone_limit"] == 5
        assert serialized["sms_weekly_limit"] == 50
        assert "created_at" not in serialized
        assert "updated_at" not in serialized

    def test_serializes_null_values(self):
        user = User.objects.create_admin(phone="+79991231111", password="pass")
        barrier = Barrier.objects.create(
            address="Null Limits",
            owner=user,
            device_phone="+79991231112",
            device_model=Barrier.Model.ELFOC,
            device_phones_amount=1,
            device_password="4321",
            additional_info="Test nulls",
            is_public=True,
        )

        limits = BarrierLimit.objects.create(barrier=barrier)

        serialized = BarrierLimitSerializer(limits).data

        assert serialized["user_phone_limit"] is None
        assert serialized["user_temp_phone_limit"] is None
        assert serialized["global_temp_phone_limit"] is None
        assert serialized["sms_weekly_limit"] is None
