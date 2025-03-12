from rest_framework import serializers

from users.constants import PHONE_MAX_LENGTH, VERIFICATION_CODE_MAX_LENGTH, VERIFICATION_TOKEN_MAX_LENGTH
from users.models import Verification
from users.validators import PhoneNumberValidator, VerificationCodeValidator, VerificationTokenValidator


class SendVerificationCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    mode = serializers.ChoiceField(choices=Verification.Mode.choices)


class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    code = serializers.CharField(max_length=VERIFICATION_CODE_MAX_LENGTH, validators=[VerificationCodeValidator()])
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )


class AdminPasswordVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    password = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    verification_token = serializers.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH, validators=[VerificationTokenValidator()]
    )
