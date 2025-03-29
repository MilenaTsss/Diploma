import pytest
from django.urls import reverse
from rest_framework import status

from barriers.models import Barrier


@pytest.mark.django_db
class TestCreateBarrierView:
    def test_create_barrier_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)

        payload = {
            "address": "ул. Тестовая 5",
            "device_phone": "+79991112233",
            "device_model": Barrier.Model.RTU5025,
            "device_phones_amount": 1,
            "device_password": "1234",
            "additional_info": "Test barrier",
            "is_public": True,
        }

        response = api_client.post(reverse("create_barrier"), payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["address"] == "ул. тестовая 5"
        assert response.data["device_phone"] == "+79991112233"
        assert "device_password" not in response.data


@pytest.mark.django_db
class TestMyAdminBarrierView:
    def test_admin_list_own_barriers(self, api_client, admin_user, admin_barrier):
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(reverse("admin_my_barriers"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] == 1
        assert response.data["barriers"][0]["address"] == admin_barrier.address


@pytest.mark.django_db
class TestAdminBarrierView:
    def test_admin_get_own_barrier(self, api_client, admin_user, admin_barrier):
        api_client.force_authenticate(user=admin_user)

        url = reverse("admin_barrier_view", args=[admin_barrier.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["address"] == admin_barrier.address

    def test_admin_cannot_get_foreign_barrier(self, api_client, admin_user, other_barrier):
        api_client.force_authenticate(user=admin_user)

        url = reverse("admin_barrier_view", args=[other_barrier.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "You do not have permission to access this barrier."

    def test_admin_update_barrier(self, api_client, admin_user, admin_barrier):
        api_client.force_authenticate(user=admin_user)

        url = reverse("admin_barrier_view", args=[admin_barrier.id])
        payload = {
            "device_password": "updatedpass",
            "additional_info": "Updated description",
        }

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["additional_info"] == "Updated description"

    def test_admin_delete_barrier(self, api_client, admin_user, admin_barrier):
        api_client.force_authenticate(user=admin_user)

        url = reverse("admin_barrier_view", args=[admin_barrier.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        admin_barrier.refresh_from_db()
        assert not admin_barrier.is_active
