import pytest
from rest_framework.test import APIRequestFactory

from barriers.models import Barrier, UserBarrier
from barriers.serializers import BarrierSerializer
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
