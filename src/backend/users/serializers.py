from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.constants import PHONE_MAX_LENGTH
from users.models import User
from users.validators import PhoneNumberValidator
from verifications.constants import VERIFICATION_TOKEN_MAX_LENGTH
from verifications.validators import VerificationTokenValidator


class AdminPasswordVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    password = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "full_name", "role", "phone_privacy"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone_privacy"]


class UserDeleteSerializer(serializers.Serializer):
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )


class PhoneChangeSerializer(serializers.Serializer):
    new_phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    old_verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )
    new_verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )

    @staticmethod
    def validate_new_phone(value):
        """Check if new phone number is already in use."""

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("This phone number is already in use by another user.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )

    def validate_old_password(self, value):
        """Проверка, что старый пароль введён верно"""

        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль неверен.")
        return value


class PasswordResetSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )
