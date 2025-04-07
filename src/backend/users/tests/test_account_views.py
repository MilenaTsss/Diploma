import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from conftest import ADMIN_PASSWORD, OTHER_PHONE
from users.models import User
from verifications.models import Verification


@pytest.mark.django_db
class TestUserAccountView:
    """Tests for UserAccountView"""

    def test_get_user_profile(self, api_client, user):
        """Test retrieving user profile"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.get(reverse("user_account"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone
        assert response.data["full_name"] == user.full_name

    def test_edit_user_profile(self, api_client, user):
        """Test editing user profile"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        new_data = {"full_name": "New Name", "phone_privacy": User.PhonePrivacy.PRIVATE}
        response = api_client.patch(reverse("user_account"), new_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "New Name"
        assert response.data["phone_privacy"] == User.PhonePrivacy.PRIVATE

    def test_delete_user_account(self, api_client, user, delete_verification):
        """Test deleting user account"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.delete(
            reverse("user_account"), {"verification_token": delete_verification.verification_token}
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert not user.is_active
        delete_verification.refresh_from_db()
        assert delete_verification.status == Verification.Status.USED

    def test_delete_user_account_invalid_verification(self, api_client, user):
        """Test deleting user account with invalid verification token"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.delete(reverse("user_account"), {"verification_token": "invalid"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChangePhoneView:
    """Tests for ChangePhoneView"""

    def test_change_phone_success(self, api_client, user, old_phone_verification, new_phone_verification):
        """Test changing phone number successfully"""

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(
            reverse("change_phone"),
            {
                "new_phone": OTHER_PHONE,
                "old_verification_token": old_phone_verification.verification_token,
                "new_verification_token": new_phone_verification.verification_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.phone == OTHER_PHONE

        old_phone_verification.refresh_from_db()
        new_phone_verification.refresh_from_db()
        assert old_phone_verification.status == Verification.Status.USED
        assert new_phone_verification.status == Verification.Status.USED


@pytest.mark.django_db
class TestChangePasswordView:
    """Tests for ChangePasswordView"""

    def test_change_password_success(self, api_client, admin_user, password_verification):
        """Test changing password successfully"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(
            reverse("admin_change_password"),
            {
                "old_password": ADMIN_PASSWORD,
                "new_password": "NewPass456!",
                "verification_token": password_verification.verification_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewPass456!") is True

        password_verification.refresh_from_db()
        assert password_verification.status == Verification.Status.USED
