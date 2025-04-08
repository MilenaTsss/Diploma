import json

import pytest
from django.urls import reverse
from rest_framework import status

from access_requests.models import AccessRequest
from barriers.models import UserBarrier


@pytest.mark.django_db
class TestCreateAccessRequestView:
    url = reverse("create_access_request")
    admin_url = reverse("admin_create_access_request")

    def test_user_creates_access_request(self, authenticated_client, barrier, user):
        response = authenticated_client.post(self.url, data={"user": user.id, "barrier": barrier.id})

        assert response.status_code == status.HTTP_201_CREATED
        assert AccessRequest.objects.filter(user=user, barrier=barrier).exists()

    def test_user_cannot_create_for_another_user(self, authenticated_client, barrier, admin_user):
        response = authenticated_client.post(self.url, data={"user": admin_user.id, "barrier": barrier.id})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_creates_access_request(self, authenticated_admin_client, admin_user, user, barrier):
        response = authenticated_admin_client.post(self.admin_url, data={"user": user.id, "barrier": barrier.id})

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestAccessRequestListViews:
    url = reverse("my_access_requests")
    admin_url = reverse("admin_access_requests")

    def test_user_sees_own_requests(self, authenticated_client, user, barrier):
        AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access_requests"]

    def test_admin_sees_requests_for_their_barriers(self, authenticated_admin_client, admin_user, user, barrier):
        AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        response = authenticated_admin_client.get(self.admin_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access_requests"]


@pytest.mark.django_db
class TestAccessRequestDetailView:
    def test_user_can_cancel_own_request(self, authenticated_client, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user, barrier=barrier, request_type=AccessRequest.RequestType.FROM_USER
        )
        response = authenticated_client.patch(
            reverse("access_request_view", args=[access_request.id]),
            data=json.dumps({"status": AccessRequest.Status.CANCELLED}),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        access_request.refresh_from_db()
        assert access_request.status == AccessRequest.Status.CANCELLED

    def test_admin_can_accept_user_request(self, authenticated_admin_client, admin_user, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user, barrier=barrier, request_type=AccessRequest.RequestType.FROM_USER
        )
        response = authenticated_admin_client.patch(
            reverse("admin_access_request_view", args=[access_request.id]),
            data=json.dumps({"status": AccessRequest.Status.ACCEPTED}),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        access_request.refresh_from_db()
        assert access_request.status == AccessRequest.Status.ACCEPTED
        assert UserBarrier.objects.filter(user=user, barrier=barrier, is_active=True).exists()

    def test_user_cannot_access_others_request(self, authenticated_client, admin_user, barrier):
        access_request = AccessRequest.objects.create(
            user=admin_user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
        )
        response = authenticated_client.get(reverse("access_request_view", args=[access_request.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_method_not_allowed(self, authenticated_client, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        url = reverse("access_request_view", args=[access_request.id])
        response = authenticated_client.put(url, data={})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data["detail"].lower() == 'method "put" not allowed.'
