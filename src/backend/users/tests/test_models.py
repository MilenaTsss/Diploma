import pytest

from users.models import User


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self, user):
        """Test creating a regular user."""

        assert user.phone == "+79991234567"
        assert user.is_active is True
        assert user.role == User.Role.USER
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_admin(self, admin_user):
        """Test creating an admin user."""

        assert admin_user.phone == "+79995554433"
        assert admin_user.is_staff is True
        assert admin_user.role == User.Role.ADMIN
        assert admin_user.is_superuser is False

    def test_create_superuser(self, superuser):
        """Test creating a superuser."""

        assert superuser.phone == "+79991254567"
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.role == User.Role.SUPERUSER

    def test_get_full_name(self):
        """Test get_full_name method."""

        user = User.objects.create_user(phone="+79991234567", full_name="John Doe")
        assert user.get_full_name() == "John Doe"

    def test_get_phone(self, user):
        """Test get_phone method."""

        assert user.get_phone() == "+79991234567"

    def test_is_phone_blocked(self):
        """Test checking if a user with a given phone number is blocked."""

        User.objects.create_user(phone="+79991234567", is_active=True)
        User.objects.create_user(phone="+79998887766", is_active=False)

        assert not User.is_phone_blocked("+79991234567")
        assert User.is_phone_blocked("+79998887766")
        assert not User.is_phone_blocked("+79991112233")

    def test_is_blocked_user(self):
        """Test checking if a user is blocked."""

        active_user = User.objects.create_user(phone="+79991234567", is_active=True)
        blocked_user = User.objects.create_user(phone="+79998887766", is_active=False)

        assert not active_user.is_blocked_user()
        assert blocked_user.is_blocked_user()
