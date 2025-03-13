import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_superuser_can_view_users(client_superuser):
    """Superuser can view the user list"""

    url = reverse("admin:users_user_changelist")
    response = client_superuser.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_cannot_add_users(client_admin):
    """Regular admin cannot add users"""

    url = reverse("admin:users_user_add")
    response = client_admin.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_can_add_users(client_superuser):
    """Superuser can add users"""

    url = reverse("admin:users_user_add")
    response = client_superuser.get(url)
    assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_cannot_delete_user(client_superuser, admin_user):
        """Even a superuser cannot delete a user"""

        url = reverse("admin:users_user_delete", args=[admin_user.pk])
        response = client_superuser.post(url, follow=True)
        assert response.status_code == 403
