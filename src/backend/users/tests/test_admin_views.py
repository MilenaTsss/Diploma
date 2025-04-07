import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestAdminUserAccountView:
    """Tests for AdminUserAccountView"""

    def test_get_user_account_success(self, api_client, admin_user, user):
        """Test retrieving user details as an admin"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.get(reverse("admin_get_user", args=[user.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone

    def test_get_user_not_found(self, api_client, admin_user):
        """Test retrieving details of a non-existent user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.get(reverse("admin_get_user", args=[999999]))

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAdminBlockUserView:
    """Tests for AdminBlockUserView"""

    def test_admin_block_user_success(self, api_client, admin_user, user):
        """Test blocking a user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(reverse("admin_block_user", args=[user.id]), {"reason": "Spamming"})

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is False
        assert user.block_reason == "Spamming"

    def test_admin_block_user_missing_reason(self, api_client, admin_user, user):
        """Test blocking a user without providing a reason"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(reverse("admin_block_user", args=[user.id]), {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_block_already_blocked_user(self, api_client, admin_user, blocked_user):
        """Test blocking a user who is already blocked"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(
            reverse("admin_block_user", args=[blocked_user.id]), {"reason": "Multiple violations"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAdminUnblockUserView:
    """Tests for AdminUnblockUserView"""

    def test_admin_unblock_user_success(self, api_client, admin_user, blocked_user):
        """Test unblocking a user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(reverse("admin_unblock_user", args=[blocked_user.id]))

        assert response.status_code == status.HTTP_200_OK
        blocked_user.refresh_from_db()
        assert blocked_user.is_active is True

    def test_admin_unblock_already_active_user(self, api_client, admin_user, user):
        """Test trying to unblock a user who is already active"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(reverse("admin_unblock_user", args=[user.id]))

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_unblock_admin_user(self, api_client, admin_user, superuser):
        """Test trying to unblock an admin user"""

        superuser.is_active = False
        superuser.save()

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.patch(reverse("admin_unblock_user", args=[superuser.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminSearchUserView:
    """Tests for AdminSearchUserView"""

    def test_admin_search_user_success(self, api_client, admin_user, user):
        """Test searching for an existing user by phone"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.post(reverse("admin_search_user"), {"phone": user.phone})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone

    def test_admin_search_user_not_found(self, api_client, admin_user):
        """Test searching for a non-existent user"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.post(reverse("admin_search_user"), {"phone": "+79990000000"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_search_user_invalid_phone(self, api_client, admin_user):
        """Test searching with an invalid phone format"""

        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = api_client.post(reverse("admin_search_user"), {"phone": "invalid_phone"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
