import pytest

from barriers.models import Barrier
from barriers_management.serializers import (
    AdminBarrierSerializer,
    CreateBarrierSerializer,
    UpdateBarrierSerializer,
)


@pytest.mark.django_db
def test_admin_barrier_serializer_excludes_password(admin_barrier):
    serializer = AdminBarrierSerializer(admin_barrier)
    data = serializer.data

    assert "device_password" not in data
    assert data["address"] == admin_barrier.address


@pytest.mark.django_db
def test_create_barrier_serializer_valid_data(admin_user, api_client):
    payload = {
        "address": "ул. Тестовая, 5",
        "device_phone": "+79991112233",
        "device_model": Barrier.Model.RTU5025,
        "device_phones_amount": 2,
        "device_password": "pass1234",
        "additional_info": "Тестовое описание",
        "is_public": True,
    }

    serializer = CreateBarrierSerializer(data=payload, context={"request": api_client.request().wsgi_request})
    serializer.context["request"].user = admin_user

    assert serializer.is_valid(), serializer.errors
    barrier = serializer.save()

    assert barrier.owner == admin_user
    assert barrier.device_phone == "+79991112233"


@pytest.mark.django_db
def test_create_barrier_serializer_invalid_phone(admin_user, api_client, admin_barrier):
    # Тот же номер, что уже есть
    payload = {
        "address": "улица Дублирующая",
        "device_phone": admin_barrier.device_phone,
        "device_model": Barrier.Model.ELFOC,
        "device_phones_amount": 1,
        "device_password": "pass4321",
        "additional_info": "",
        "is_public": False,
    }

    serializer = CreateBarrierSerializer(data=payload, context={"request": api_client.request().wsgi_request})
    serializer.context["request"].user = admin_user

    assert not serializer.is_valid()
    assert "device_phone" in serializer.errors


@pytest.mark.django_db
def test_create_barrier_serializer_invalid_amount(admin_user, api_client):
    payload = {
        "address": "Новый адрес",
        "device_phone": "+79991112244",
        "device_model": Barrier.Model.TELEMETRICA,
        "device_phones_amount": 0,
        "device_password": "secret",
        "additional_info": "Описание",
        "is_public": True,
    }

    serializer = CreateBarrierSerializer(data=payload, context={"request": api_client.request().wsgi_request})
    serializer.context["request"].user = admin_user

    assert not serializer.is_valid()
    assert "device_phones_amount" in serializer.errors


@pytest.mark.django_db
def test_update_barrier_serializer_partial_update(admin_barrier):
    payload = {
        "device_password": "newpassword",
        "additional_info": "Updated info",
    }

    serializer = UpdateBarrierSerializer(instance=admin_barrier, data=payload, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()

    assert updated.device_password == "newpassword"
    assert updated.additional_info == "Updated info"
