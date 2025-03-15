import pytest

from users.serializers import (
    AdminPasswordVerificationSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
    PhoneChangeSerializer,
    UserDeleteSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data, is_valid",
    [
        ({"phone": "+79991234567", "full_name": "John Doe", "role": "user", "phone_privacy": "public"}, True),
        ({"phone": "89991234567", "full_name": "John Doe", "role": "admin", "phone_privacy": "private"}, False),
        ({"full_name": "John Doe", "role": "superuser", "phone_privacy": "protected"}, False),
        ({"phone": "+79991234567", "full_name": "John Doe", "role": "new", "phone_privacy": "protected"}, False),
    ],
)
def test_user_serializer(data, is_valid):
    serializer = UserSerializer(data=data)
    assert serializer.is_valid() == is_valid


@pytest.mark.parametrize(
    "data, is_valid",
    [
        ({"full_name": "John Doe", "phone_privacy": "private"}, True),
        ({"full_name": "John Doe", "phone_privacy": "public"}, True),
        ({"full_name": "", "phone_privacy": "protected"}, True),
        ({"full_name": "", "phone_privacy": "invalid"}, False),
        ({}, True),
    ],
)
def test_user_update_serializer(data, is_valid):
    serializer = UserUpdateSerializer(data=data)
    assert serializer.is_valid() == is_valid


@pytest.mark.parametrize(
    "data, is_valid",
    [
        ({"verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6"}, True),
        ({"verification_token": "aaa"}, False),
        ({}, False),
    ],
)
def test_user_delete_serializer(data, is_valid):
    serializer = UserDeleteSerializer(data=data)
    assert serializer.is_valid() == is_valid


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data, is_valid",
    [
        (
            {
                "new_phone": "+79991234567",
                "old_verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
                "new_verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            True,
        ),
        (
            {
                "new_phone": "89991234567",
                "old_verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
                "new_verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            False,
        ),
        ({"new_phone": "+79991234567", "old_verification_token": "a1b2c3d4e5"}, False),
        (
            {
                "new_phone": "+79991234567",
                "old_verification_token": "a1b2c3d4e5",
                "new_verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            False,
        ),
    ],
)
def test_phone_change_serializer(data, is_valid):
    serializer = PhoneChangeSerializer(data=data)
    assert serializer.is_valid() == is_valid


@pytest.mark.parametrize(
    "data, is_valid",
    [
        (
            {
                "old_password": "OldPass123!",
                "new_password": "NewPass456!",
                "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            True,
        ),
        (
            {
                "old_password": "",
                "new_password": "NewPass456!",
                "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            False,
        ),
        (
            {
                "old_password": "OldPass123!",
                "new_password": "short",
                "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            False,
        ),
    ],
)
def test_password_change_serializer(data, is_valid, mocker):
    request_mock = mocker.Mock()
    request_mock.user.check_password.return_value = data.get("old_password") == "OldPass123!"

    serializer = PasswordChangeSerializer(data=data, context={"request": request_mock})
    assert serializer.is_valid() == is_valid


@pytest.mark.parametrize(
    "data, is_valid",
    [
        (
            {
                "phone": "+79991234567",
                "new_password": "NewSecurePass!",
                "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            True,
        ),
        (
            {
                "phone": "89991234567",
                "new_password": "NewSecurePass!",
                "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            False,
        ),
        (
            {
                "phone": "+79991234567",
                "new_password": "short",
                "verification_token": "a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6",
            },
            False,
        ),
    ],
)
def test_password_reset_serializer(data, is_valid):
    serializer = PasswordResetSerializer(data=data)
    assert serializer.is_valid() == is_valid
