import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_list_public_barriers(authenticated_client, public_barrier):
    url = reverse("list_barriers")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_count"] == 1
    assert response.data["barriers"][0]["id"] == public_barrier.id


@pytest.mark.django_db
def test_list_my_barriers(api_client, user, private_barrier_with_access):
    api_client.force_authenticate(user=user)

    url = reverse("my_barriers")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_count"] == 1
    assert response.data["barriers"][0]["id"] == private_barrier_with_access.id


@pytest.mark.django_db
def test_get_public_barrier(authenticated_client, public_barrier):
    url = reverse("get_barrier", kwargs={"id": public_barrier.id})
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == public_barrier.id


@pytest.mark.django_db
def test_get_private_barrier_with_access(api_client, user, private_barrier_with_access):
    api_client.force_authenticate(user=user)

    url = reverse("get_barrier", kwargs={"id": private_barrier_with_access.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == private_barrier_with_access.id


@pytest.mark.django_db
def test_get_private_barrier_without_access(api_client, user, private_barrier):
    api_client.force_authenticate(user=user)

    url = reverse("get_barrier", kwargs={"id": private_barrier.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["detail"] == "You do not have access to this barrier."
