import json

import pytest
from django.urls import reverse
from rest_framework import status

from access_requests.models import AccessRequest
from barriers.models import UserBarrier


@pytest.mark.django_db
class TestCreateAccessRequestView:
    def test_user_creates_access_request(self, authenticated_client, barrier, user):
        response = authenticated_client.post(
            reverse("create_access_request"),
            data={"user": user.id, "barrier": barrier.id},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert AccessRequest.objects.filter(user=user, barrier=barrier).exists()

    def test_user_cannot_create_for_another_user(self, authenticated_client, barrier, admin_user):
        response = authenticated_client.post(
            reverse("create_access_request"),
            data={"user": admin_user.id, "barrier": barrier.id},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_creates_access_request(self, api_client, admin_user, user, barrier):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            reverse("admin_create_access_request"),
            data={"user": user.id, "barrier": barrier.id},
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestAccessRequestListViews:
    def test_user_sees_own_requests(self, authenticated_client, user, barrier):
        AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        response = authenticated_client.get(reverse("my_access_requests"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["access_requests"]

    def test_admin_sees_requests_for_their_barriers(self, api_client, admin_user, user, barrier):
        api_client.force_authenticate(user=admin_user)
        AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        response = api_client.get(reverse("admin_access_requests"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["access_requests"]


@pytest.mark.django_db
class TestAccessRequestDetailView:
    def test_user_can_cancel_own_request(self, authenticated_client, user, barrier):
        ar = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        response = authenticated_client.patch(
            reverse("access_request_view", args=[ar.id]),
            data=json.dumps({"status": AccessRequest.Status.CANCELLED}),
            content_type="application/json",
        )
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        ar.refresh_from_db()
        assert ar.status == AccessRequest.Status.CANCELLED

    def test_admin_can_accept_user_request(self, api_client, admin_user, user, barrier):
        api_client.force_authenticate(user=admin_user)
        ar = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        response = api_client.patch(
            reverse("admin_access_request_view", args=[ar.id]),
            data=json.dumps({"status": AccessRequest.Status.ACCEPTED}),
            content_type="application/json",
        )
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        ar.refresh_from_db()
        assert ar.status == AccessRequest.Status.ACCEPTED
        assert UserBarrier.objects.filter(user=user, barrier=barrier, is_active=True).exists()

    def test_user_cannot_access_others_request(self, authenticated_client, admin_user, barrier):
        ar = AccessRequest.objects.create(
            user=admin_user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
        )
        response = authenticated_client.get(reverse("access_request_view", args=[ar.id]))
        assert response.status_code == status.HTTP_403_FORBIDDEN
