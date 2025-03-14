import logging

from django.contrib.auth import authenticate
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.serializers import (
    AdminPasswordVerificationSerializer,
    DeleteUserSerializer,
    LoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from verifications.models import Verification, VerificationService

logger = logging.getLogger(__name__)


def admin_block_password_change_view(request):
    """Custom admin view to block password changes via the Django admin panel."""

    return render(request, "admin/password_change.html", status=status.HTTP_403_FORBIDDEN)


@authentication_classes([])
@permission_classes([AllowAny])
class AdminPasswordVerificationView(APIView):
    """Verify the administrator's password."""

    def post(self, request):
        serializer = AdminPasswordVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        password = serializer.validated_data["password"]

        user = authenticate(username=phone, password=password)

        if user is None or user.role == User.Role.USER:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_403_FORBIDDEN)

        return Response({"message": "Password verified successfully."})


@authentication_classes([])
@permission_classes([AllowAny])
class LoginView(APIView):
    """Login using phone and verification token."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        verification_token = serializer.validated_data["verification_token"]

        # Find the verification entry
        verification, error_message, error_status_code = VerificationService.confirm_verification(
            phone, verification_token, Verification.Mode.LOGIN
        )
        if not verification:
            return Response({"error": error_message}, status=error_status_code)

        # Check if user exists, otherwise create a new one
        user, created = User.objects.get_or_create(phone=phone, defaults={"is_active": True})

        if not user.is_active:
            return Response(
                {"error": _("This account is blocked. Contact support for assistance.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {
                "access_token": access_token,
                "refresh_token": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class UserAccountView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete the user profile"""

    serializer_class = UserSerializer

    def get_object(self):
        """Retrieve the current user's profile"""

        return self.request.user

    def patch(self, request, *args, **kwargs):
        """Edit profile (full_name, phone privacy)"""

        user = self.get_object()
        serializer = UserUpdateSerializer(self.get_object(), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Deactivate account (verification code required)"""

        serializer = DeleteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        verification_token = request.data.get("verification_token")

        verification, error_message, error_status_code = VerificationService.confirm_verification(
            user.phone, verification_token, Verification.Mode.DELETE_ACCOUNT
        )
        if not verification:
            return Response({"error": error_message}, status=error_status_code)

        user.is_active = False
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
