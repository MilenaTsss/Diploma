import pytest
from django.urls import reverse
from rest_framework import status

from barriers.models import BarrierLimit


@pytest.mark.django_db
class TestListBarriersView:
    def test_list_public_barriers(self, authenticated_client, barrier, private_barrier):
        response = authenticated_client.get(reverse("list_barriers"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] == 1
        assert response.data["barriers"][0]["id"] == barrier.id


@pytest.mark.django_db
class TestMyBarriersListView:
    def test_list_my_barriers(self, authenticated_client, user, private_barrier_with_access):
        response = authenticated_client.get(reverse("my_barriers"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] == 1
        assert response.data["barriers"][0]["id"] == private_barrier_with_access.id


@pytest.mark.django_db
class TestBarrierView:
    def test_get_public_barrier(self, authenticated_client, barrier):
        url = reverse("get_barrier", kwargs={"id": barrier.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == barrier.id

    def test_get_private_barrier_with_access(self, authenticated_client, user, private_barrier_with_access):
        url = reverse("get_barrier", kwargs={"id": private_barrier_with_access.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == private_barrier_with_access.id

    def test_get_private_barrier_without_access(self, authenticated_client, user, private_barrier):
        url = reverse("get_barrier", kwargs={"id": private_barrier.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "You do not have access to this barrier."


@pytest.mark.django_db
class TestBarrierLimitView:
    def test_public_barrier_with_no_limits_creates_one(self, authenticated_client, barrier):
        url = reverse("get_barrier_limits", kwargs={"id": barrier.id})
        assert not hasattr(barrier, "limits")  # Ensure no limit initially

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert BarrierLimit.objects.filter(barrier=barrier).exists()

    def test_public_barrier_with_limits(self, authenticated_client, barrier):
        BarrierLimit.objects.create(
            barrier=barrier,
            user_phone_limit=3,
            user_temp_phone_limit=1,
            global_temp_phone_limit=10,
            sms_weekly_limit=50,
        )

        url = reverse("get_barrier_limits", kwargs={"id": barrier.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_phone_limit"] == 3
        assert response.data["sms_weekly_limit"] == 50

    def test_private_barrier_with_access_and_no_limit_creates_one(
        self, authenticated_client, private_barrier_with_access
    ):
        url = reverse("get_barrier_limits", kwargs={"id": private_barrier_with_access.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert BarrierLimit.objects.filter(barrier=private_barrier_with_access).exists()

    def test_owner_can_view_limits(self, authenticated_admin_client, private_barrier):
        url = reverse("get_barrier_limits", kwargs={"id": private_barrier.id})
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None

    def test_private_barrier_without_access(self, authenticated_client, private_barrier):
        url = reverse("get_barrier_limits", kwargs={"id": private_barrier.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "You do not have access to this barrier."
