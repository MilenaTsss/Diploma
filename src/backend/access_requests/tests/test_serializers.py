import pytest

from access_requests.models import AccessRequest
from access_requests.serializers import CreateAccessRequestSerializer, UpdateAccessRequestSerializer
from users.models import User


@pytest.mark.django_db
class TestCreateAccessRequestSerializer:
    def test_user_creates_valid_request(self, user, barrier):
        context = {"request": type("Request", (), {"user": user})(), "as_admin": False}
        serializer = CreateAccessRequestSerializer(
            data={"user": user.id, "barrier": barrier.id},
            context=context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_user_cannot_request_private_barrier(self, user, private_barrier):
        context = {"request": type("Request", (), {"user": user})(), "as_admin": False}
        serializer = CreateAccessRequestSerializer(
            data={"user": user.id, "barrier": private_barrier.id},
            context=context,
        )

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "barrier" in serializer.errors

    def test_user_cannot_create_for_another_user(self, user, admin_user, barrier):
        context = {"request": type("Request", (), {"user": user})(), "as_admin": False}
        serializer = CreateAccessRequestSerializer(
            data={"user": admin_user.id, "barrier": barrier.id},
            context=context,
        )

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "user" in serializer.errors

    def test_admin_creates_valid_request(self, admin_user, user, barrier):
        context = {"request": type("Request", (), {"user": admin_user})(), "as_admin": True}
        serializer = CreateAccessRequestSerializer(
            data={"user": user.id, "barrier": barrier.id},
            context=context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_admin_cannot_create_for_barrier_they_do_not_own(self, user, barrier):
        another_admin = User.objects.create_admin(phone="+79998887777", password="pass")
        context = {"request": type("Request", (), {"user": another_admin})(), "as_admin": True}
        serializer = CreateAccessRequestSerializer(
            data={"user": user.id, "barrier": barrier.id},
            context=context,
        )

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "barrier" in serializer.errors

    def test_cannot_create_if_user_already_has_access(self, user, private_barrier_with_access):
        context = {"request": type("Request", (), {"user": user})(), "as_admin": False}
        serializer = CreateAccessRequestSerializer(
            data={"user": user.id, "barrier": private_barrier_with_access.id},
            context=context,
        )

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors


@pytest.mark.django_db
class TestUpdateAccessRequestSerializer:
    def test_valid_cancel_by_user(self, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        serializer = UpdateAccessRequestSerializer(
            access_request,
            data={"status": AccessRequest.Status.CANCELLED},
            partial=True,
            context={"as_admin": False},
        )

        assert serializer.is_valid(), serializer.errors

    def test_invalid_status_transition(self, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.ACCEPTED,
        )
        serializer = UpdateAccessRequestSerializer(
            access_request,
            data={"status": AccessRequest.Status.CANCELLED},
            partial=True,
            context={"as_admin": False},
        )

        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_user_cannot_accept_request(self, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        serializer = UpdateAccessRequestSerializer(
            access_request,
            data={"status": AccessRequest.Status.ACCEPTED},
            partial=True,
            context={"as_admin": False},
        )

        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_admin_can_accept_user_request(self, user, admin_user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
            status=AccessRequest.Status.PENDING,
        )
        serializer = UpdateAccessRequestSerializer(
            access_request,
            data={"status": AccessRequest.Status.ACCEPTED},
            partial=True,
            context={"as_admin": True},
        )

        assert serializer.is_valid(), serializer.errors

    def test_user_cannot_change_hidden_for_admin(self, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
        )
        serializer = UpdateAccessRequestSerializer(
            access_request,
            data={"hidden_for_admin": True},
            partial=True,
            context={"as_admin": False},
        )

        assert not serializer.is_valid()
        assert "hidden_for_admin" in serializer.errors

    def test_admin_cannot_change_hidden_for_user(self, user, barrier):
        access_request = AccessRequest.objects.create(
            user=user,
            barrier=barrier,
            request_type=AccessRequest.RequestType.FROM_USER,
        )
        serializer = UpdateAccessRequestSerializer(
            access_request,
            data={"hidden_for_user": True},
            partial=True,
            context={"as_admin": True},
        )

        assert not serializer.is_valid()
        assert "hidden_for_user" in serializer.errors
