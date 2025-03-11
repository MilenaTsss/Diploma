from rest_framework import serializers

from users.constants import PHONE_MAX_LENGTH, VERIFICATION_CODE_MAX_LENGTH
from users.models import User, UserManager, Verification
from users.validators import PhoneNumberValidator, VerificationCodeValidator


class SendVerificationCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    mode = serializers.ChoiceField(choices=Verification.Mode.choices)


class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    code = serializers.CharField(max_length=VERIFICATION_CODE_MAX_LENGTH, validators=[VerificationCodeValidator()])


class AdminPasswordVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    password = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=PHONE_MAX_LENGTH, validators=[PhoneNumberValidator()])
    code = serializers.CharField(max_length=VERIFICATION_CODE_MAX_LENGTH, validators=[VerificationCodeValidator()])


# TODO rewrite below
class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user data"""

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "full_name",
            "role",
            "phone_privacy",
            "is_active",
            "is_blocked",
            "date_joined",
            "last_login",
        ]

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""

    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ["phone", "full_name", "role", "phone_privacy", "password"]

    @staticmethod
    def validate_phone(value):
        """Normalize phone number"""
        return UserManager.normalize_phone(value)

    def validate(self, data):
        """Ensure only admins/superusers need a password"""
        role = data.get("role", User.Role.USER)
        password = data.get("password")

        if role in [User.Role.ADMIN, User.Role.SUPERUSER] and not password:
            raise serializers.ValidationError({"password": "Password is required for admin users."})
        return data

    def create(self, validated_data):
        """Create a user"""
        password = validated_data.pop("password", None)
        user = User.objects.create_user(**validated_data, password=password)
        return user


# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#
#
# class LoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             return Response({"message": "Login successful"})
#         return Response(serializer.errors, status=400)
