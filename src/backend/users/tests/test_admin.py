import pytest
from django.urls import reverse

from users.admin import AdminCreationForm
from users.models import User


@pytest.mark.django_db
def test_admin_creation_form_valid():
    """Check that the admin creation form correctly creates a user"""

    form_data = {"phone": "+79991234567", "full_name": "Admin User", "password": "SecurePass123"}
    form = AdminCreationForm(data=form_data)

    assert form.is_valid(), f"Form errors: {form.errors}"

    user = form.save()
    assert user.is_staff is True
    assert user.role == User.Role.ADMIN
    assert user.check_password("SecurePass123")


@pytest.mark.django_db
def test_admin_creation_form_invalid_phone():
    """Check that an invalid phone number triggers an error"""

    form_data = {"phone": "+123456", "full_name": "Admin User", "password": "SecurePass123"}
    form = AdminCreationForm(data=form_data)

    assert not form.is_valid()
    assert "phone" in form.errors


@pytest.mark.django_db
def test_superuser_cannot_deactivate_self(client_superuser, superuser):
    """Superadmin cannot deactivate themselves"""

    url = reverse("admin:users_user_change", args=[superuser.pk])
    response = client_superuser.post(url, {"is_active": False}, follow=True)
    assert superuser.is_active


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
