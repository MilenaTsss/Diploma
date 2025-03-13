import pytest

from users.serializers import AdminPasswordVerificationSerializer, LoginSerializer


@pytest.mark.parametrize(
    "data, is_valid",
    [
        ({"phone": "+79991234567", "password": "SecurePass123"}, True),
        ({"phone": "79991234567", "password": "SecurePass123"}, False),
        ({"phone": "+79991234567"}, False),
    ],
)
def test_admin_password_verification_serializer(data, is_valid):
    serializer = AdminPasswordVerificationSerializer(data=data)
    assert serializer.is_valid() == is_valid


@pytest.mark.parametrize(
    "data, is_valid",
    [
        ({"phone": "+79991234567", "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6"}, True),
        ({"phone": "89991234567", "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6"}, False),
        ({"phone": "+79991234567"}, False),
    ],
)
def test_login_serializer(data, is_valid):
    serializer = LoginSerializer(data=data)
    assert serializer.is_valid() == is_valid
