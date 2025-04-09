import pytest
from django.urls import reverse
from rest_framework import status

from barriers.models import Barrier, BarrierLimit
from conftest import BARRIER_ADDRESS, BARRIER_DEVICE_PASSWORD, BARRIER_DEVICE_PHONE


@pytest.mark.django_db
class TestCreateBarrierView:
    def test_create_barrier_success(self, authenticated_admin_client, admin_user):
        url = reverse("create_barrier")
        data = {
            "address": BARRIER_ADDRESS,
            "device_phone": BARRIER_DEVICE_PHONE,
            "device_model": Barrier.Model.RTU5025,
            "device_phones_amount": 1,
            "device_password": BARRIER_DEVICE_PASSWORD,
            "additional_info": "Test barrier",
            "is_public": True,
        }

        response = authenticated_admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["address"] == BARRIER_ADDRESS.lower()
        assert response.data["device_phone"] == BARRIER_DEVICE_PHONE
        assert response.data["owner"] == admin_user.id
        assert "device_password" not in response.data

        # Ensure BarrierLimit is created
        barrier_id = response.data["id"]
        assert BarrierLimit.objects.filter(barrier_id=barrier_id).exists()


@pytest.mark.django_db
class TestMyAdminBarrierView:
    def test_admin_list_own_barriers(self, authenticated_admin_client, barrier):
        url = reverse("admin_my_barriers")
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] == 1
        assert response.data["barriers"][0]["address"] == barrier.address

    def test_no_barriers_returns_empty_list(self, authenticated_admin_client):
        url = reverse("admin_my_barriers")
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] == 0
        assert response.data["barriers"] == []

    def test_sort_by_created_at(self, authenticated_admin_client, admin_user, barrier, other_admin_barrier):
        response = authenticated_admin_client.get(reverse("admin_my_barriers") + "?ordering=created_at")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"][0]["id"] == barrier.id
        assert response.data["barriers"][1]["id"] == other_admin_barrier.id

        assert response.data["barriers"][0]["created_at"] <= response.data["barriers"][1]["created_at"]

    def test_sort_descending_updated_at(self, authenticated_admin_client, admin_user, barrier, other_admin_barrier):
        barrier.device_password = "1235"
        barrier.save()

        response = authenticated_admin_client.get(reverse("admin_my_barriers") + "?ordering=-updated_at")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"][0]["id"] == barrier.id
        assert response.data["barriers"][1]["id"] == other_admin_barrier.id

    def test_invalid_ordering_fallbacks_to_default(
        self, authenticated_admin_client, admin_user, barrier, other_admin_barrier
    ):
        response = authenticated_admin_client.get(reverse("admin_my_barriers") + "?ordering=invalid_field")

        assert response.status_code == status.HTTP_200_OK
        addresses = [b["address"] for b in response.data["barriers"]]
        assert addresses == sorted(addresses)

    def test_admin_sees_only_own_barriers(self, authenticated_admin_client, admin_user, another_admin, other_barrier):
        response = authenticated_admin_client.get(reverse("admin_my_barriers"))

        assert response.status_code == status.HTTP_200_OK
        for barr in response.data["barriers"]:
            assert barr["owner"]["phone"] == admin_user.phone


@pytest.mark.django_db
class TestAdminBarrierView:
    def test_admin_get_own_barrier(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("admin_barrier_view", args=[barrier.id])
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["address"] == barrier.address

    def test_admin_cannot_get_foreign_barrier(self, authenticated_admin_client, admin_user, other_barrier):
        url = reverse("admin_barrier_view", args=[other_barrier.id])
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "You do not have permission to access this barrier."

    def test_admin_update_barrier(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("admin_barrier_view", args=[barrier.id])
        data = {
            "device_password": "0000",
            "additional_info": "Updated description",
        }

        response = authenticated_admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["additional_info"] == "Updated description"

    def test_admin_update_barrier_invalid_password(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("admin_barrier_view", args=[barrier.id])
        data = {"device_password": "updatedpass"}

        response = authenticated_admin_client.patch(url, data)

        print(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Enter a valid device password. Must be exactly 4 digits." in response.data["non_field_errors"]

    def test_admin_delete_barrier(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("admin_barrier_view", args=[barrier.id])
        response = authenticated_admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        barrier.refresh_from_db()
        assert not barrier.is_active

    def test_put_method_not_allowed(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("admin_barrier_view", args=[barrier.id])
        data = {"device_password": "0000"}

        response = authenticated_admin_client.put(url, data)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestBarrierLimitUpdateView:
    def test_update_limit_successfully(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("update_barrier_limit", kwargs={"id": barrier.id})
        data = {"sms_weekly_limit": 5}

        response = authenticated_admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["sms_weekly_limit"] == 5
        assert barrier.limits.sms_weekly_limit == 5

    def test_update_limit_creates_if_missing(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("update_barrier_limit", kwargs={"id": barrier.id})
        data = {"user_phone_limit": 2}

        response = authenticated_admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_phone_limit"] == 2
        assert BarrierLimit.objects.filter(barrier=barrier).exists()

    def test_update_limit_forbidden_for_non_owner(self, api_client, another_admin, barrier):
        api_client.force_authenticate(user=another_admin)
        url = reverse("update_barrier_limit", kwargs={"id": barrier.id})
        data = {"user_temp_phone_limit": 3}

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "You are not the owner of this barrier."

    def test_update_limit_invalid_negative_value(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("update_barrier_limit", kwargs={"id": barrier.id})
        data = {"global_temp_phone_limit": -1}

        response = authenticated_admin_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "global_temp_phone_limit" in response.data

    def test_put_method_not_allowed(self, authenticated_admin_client, admin_user, barrier):
        url = reverse("update_barrier_limit", kwargs={"id": barrier.id})
        data = {"sms_weekly_limit": 7}

        response = authenticated_admin_client.put(url, data)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
