import pytest

from barriers.models import Barrier
from barriers_management.serializers import (
    AdminBarrierSerializer,
    CreateBarrierSerializer,
    UpdateBarrierSerializer,
)


@pytest.mark.django_db
class TestAdminBarrierSerializer:
    def test_excludes_password(self, admin_barrier):
        serializer = AdminBarrierSerializer(admin_barrier)
        data = serializer.data

        assert "device_password" not in data
        assert data["address"] == admin_barrier.address


@pytest.mark.django_db
class TestCreateBarrierSerializer:
    def test_valid_data(self, admin_user, api_client):
        payload = {
            "address": "St. Test, 5",
            "device_phone": "+79991112233",
            "device_model": Barrier.Model.RTU5025,
            "device_phones_amount": 2,
            "device_password": "1234",
            "additional_info": "Testing description",
            "is_public": True,
        }

        serializer = CreateBarrierSerializer(data=payload, context={"request": api_client.request().wsgi_request})
        serializer.context["request"].user = admin_user

        assert serializer.is_valid(), serializer.errors
        barrier = serializer.save()

        assert barrier.owner == admin_user
        assert barrier.device_phone == "+79991112233"

    def test_invalid_phone(self, admin_user, api_client, admin_barrier):
        payload = {
            "address": "St. Double",
            "device_phone": admin_barrier.device_phone,
            "device_model": Barrier.Model.ELFOC,
            "device_phones_amount": 1,
            "device_password": "4321",
            "additional_info": "",
            "is_public": False,
        }

        serializer = CreateBarrierSerializer(data=payload, context={"request": api_client.request().wsgi_request})
        serializer.context["request"].user = admin_user

        assert not serializer.is_valid()
        assert "device_phone" in serializer.errors

    def test_invalid_amount(self, admin_user, api_client):
        payload = {
            "address": "New address",
            "device_phone": "+79991112244",
            "device_model": Barrier.Model.TELEMETRICA,
            "device_phones_amount": 0,
            "device_password": "secret",
            "additional_info": "Description",
            "is_public": True,
        }

        serializer = CreateBarrierSerializer(data=payload, context={"request": api_client.request().wsgi_request})
        serializer.context["request"].user = admin_user

        assert not serializer.is_valid()
        assert "device_phones_amount" in serializer.errors

    def test_missing_password_for_non_telemetrica(self, admin_user, api_client):
        payload = {
            "address": "No password",
            "device_phone": "+79991112299",
            "device_model": Barrier.Model.RTU5035,
            "device_phones_amount": 1,
            "device_password": "",
            "additional_info": "",
            "is_public": True,
        }

        request = api_client.request().wsgi_request
        request.user = admin_user
        serializer = CreateBarrierSerializer(data=payload, context={"request": request})

        assert not serializer.is_valid()
        assert "device_password" in serializer.errors

    def test_invalid_password_format(self, admin_user, api_client):
        payload = {
            "address": "Wrong password",
            "device_phone": "+79991112298",
            "device_model": Barrier.Model.RTU5035,
            "device_phones_amount": 1,
            "device_password": "abcd",
            "additional_info": "",
            "is_public": True,
        }

        request = api_client.request().wsgi_request
        request.user = admin_user
        serializer = CreateBarrierSerializer(data=payload, context={"request": request})

        assert not serializer.is_valid()
        assert "Enter a valid device password. Must be exactly 4 digits." in serializer.errors["non_field_errors"]


@pytest.mark.django_db
class TestUpdateBarrierSerializer:
    def test_partial_update(self, admin_barrier):
        payload = {
            "device_password": "newpassword",
            "additional_info": "Updated info",
        }

        serializer = UpdateBarrierSerializer(instance=admin_barrier, data=payload, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert updated.device_password == "newpassword"
        assert updated.additional_info == "Updated info"
