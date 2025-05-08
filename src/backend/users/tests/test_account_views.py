from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from barriers.models import UserBarrier
from conftest import ADMIN_PASSWORD, OTHER_PHONE
from phones.models import BarrierPhone
from users.account_views import ChangePhoneView
from users.models import User
from verifications.models import Verification


@pytest.mark.django_db
class TestUserAccountView:
    """Tests for UserAccountView"""

    def test_get_user_profile(self, authenticated_client, user):
        """Test retrieving user profile"""

        response = authenticated_client.get(reverse("user_account"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone
        assert response.data["full_name"] == user.full_name

    def test_edit_user_profile(self, authenticated_client):
        """Test editing user profile"""

        data = {"full_name": "New Name", "phone_privacy": User.PhonePrivacy.PRIVATE}
        response = authenticated_client.patch(reverse("user_account"), data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "New Name"
        assert response.data["phone_privacy"] == User.PhonePrivacy.PRIVATE

    def test_delete_user_account(self, authenticated_client, user, delete_verification):
        """Test deleting user account"""

        response = authenticated_client.delete(
            reverse("user_account"),
            {"verification_token": delete_verification.verification_token},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert not user.is_active
        delete_verification.refresh_from_db()
        assert delete_verification.status == Verification.Status.USED

    @patch.object(BarrierPhone, "send_sms_to_delete")
    def test_delete_user_deactivates_links_and_phones(
        self,
        mock_send_sms,
        authenticated_client,
        user,
        delete_verification,
        barrier,
        create_barrier_phone,
    ):
        access_request = barrier.access_requests.create(user=user, status="accepted", request_type="from_user")
        UserBarrier.objects.create(user=user, barrier=barrier, access_request=access_request)

        phone = create_barrier_phone(user, barrier)

        response = authenticated_client.delete(
            reverse("user_account"), {"verification_token": delete_verification.verification_token}
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        user.refresh_from_db()
        assert not user.is_active

        user_barrier = UserBarrier.objects.get(user=user, barrier=barrier)
        assert not user_barrier.is_active

        phone.refresh_from_db()
        assert not phone.is_active
        mock_send_sms.assert_called_once()

    def test_delete_user_account_invalid_verification(self, authenticated_client, create_verification):
        """Test deleting user account with invalid verification token"""
        verification_token = create_verification(mode=Verification.Mode.LOGIN).verification_token

        response = authenticated_client.delete(reverse("user_account"), {"verification_token": verification_token})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Invalid verification mode."

    def test_put_method_not_allowed(self, authenticated_client):
        """Test that PUT method is not allowed on user account view"""

        response = authenticated_client.put(reverse("user_account"), {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data["detail"] == 'Method "PUT" not allowed.'


@pytest.mark.django_db
class TestChangePhoneView:
    """Tests for ChangePhoneView"""

    @patch.object(ChangePhoneView, "update_primary_phones_on_user_change")
    def test_change_phone_success(
        self, mock_update_phones, authenticated_client, user, old_phone_verification, new_phone_verification
    ):
        """Test changing phone number successfully"""

        data = {
            "new_phone": OTHER_PHONE,
            "old_verification_token": old_phone_verification.verification_token,
            "new_verification_token": new_phone_verification.verification_token,
        }
        response = authenticated_client.patch(reverse("change_phone"), data)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.phone == OTHER_PHONE

        old_phone_verification.refresh_from_db()
        new_phone_verification.refresh_from_db()
        assert old_phone_verification.status == Verification.Status.USED
        assert new_phone_verification.status == Verification.Status.USED

        mock_update_phones.assert_called_once_with(user, old_phone_verification.phone, OTHER_PHONE)

    @patch.object(BarrierPhone, "send_sms_to_delete")
    @patch.object(BarrierPhone, "send_sms_to_create")
    class TestChangePhonePrimaryReplacement:
        def test_primary_phone_replaced_on_change(
            self,
            mock_send_create,
            mock_send_delete,
            authenticated_client,
            user,
            barrier,
            create_access_request,
            old_phone_verification,
            new_phone_verification,
            create_barrier_phone,
        ):
            access_request = create_access_request(user=user, barrier=barrier, status="accepted")
            UserBarrier.objects.create(user=user, barrier=barrier, access_request=access_request)
            old_phone = user.phone
            new_phone = OTHER_PHONE

            phone = create_barrier_phone(user, barrier, phone=old_phone, type=BarrierPhone.PhoneType.PRIMARY)

            data = {
                "new_phone": new_phone,
                "old_verification_token": old_phone_verification.verification_token,
                "new_verification_token": new_phone_verification.verification_token,
            }

            response = authenticated_client.patch(reverse("change_phone"), data)
            assert response.status_code == 200

            user.refresh_from_db()
            assert user.phone == new_phone

            phone.refresh_from_db()
            assert not phone.is_active

            new_phone_obj = BarrierPhone.objects.get(
                user=user,
                barrier=barrier,
                phone=new_phone,
                type=BarrierPhone.PhoneType.PRIMARY,
                is_active=True,
            )
            assert new_phone_obj is not None

            mock_send_delete.assert_called_once_with()
            mock_send_create.assert_called_once_with()


@pytest.mark.django_db
class TestChangePasswordView:
    """Tests for ChangePasswordView"""

    def test_change_password_success(self, authenticated_admin_client, admin_user, password_verification):
        """Test changing password successfully"""

        data = {
            "old_password": ADMIN_PASSWORD,
            "new_password": "NewPass456!",
            "verification_token": password_verification.verification_token,
        }
        response = authenticated_admin_client.patch(reverse("admin_change_password"), data)

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewPass456!") is True

        password_verification.refresh_from_db()
        assert password_verification.status == Verification.Status.USED
