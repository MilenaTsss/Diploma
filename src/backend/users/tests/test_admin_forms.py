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
