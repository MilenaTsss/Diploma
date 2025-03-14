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


class DeleteUserSerializer(serializers.Serializer):
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )
