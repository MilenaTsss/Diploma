import logging

from django.contrib.auth import authenticate
from django.shortcuts import render
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.generics import RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.serializers import (
    AdminPasswordVerificationSerializer,
    ChangePasswordSerializer,
    ChangePhoneSerializer,
    CheckAdminSerializer,
    DeleteUserSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    SearchUserSerializer,
    UpdateUserSerializer,
    UserSerializer,
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
            return Response({"error": "Invalid phone or password."}, status=status.HTTP_403_FORBIDDEN)

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

        verification.status = Verification.Status.USED
        verification.save(update_fields=["status"])
        user.last_login = now()
        user.save(update_fields=["last_login"])

        return Response(
            {
                "access_token": access_token,
                "refresh_token": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


@authentication_classes([])
@permission_classes([AllowAny])
class CheckAdminView(APIView):
    """Check, if user with given phone number is admin or not."""

    def post(self, request):
        serializer = CheckAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone=phone, is_active=True).first()

        if not user:
            return Response({"is_admin": False}, status=status.HTTP_200_OK)

        return Response({"is_admin": user.role != User.Role.USER}, status=status.HTTP_200_OK)


class UserAccountView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete the user profile"""

    serializer_class = UserSerializer

    def get_object(self):
        """Retrieve the current user's profile"""

        return self.request.user

    def patch(self, request, *args, **kwargs):
        """Edit profile (full_name, phone privacy)"""

        user = self.get_object()
        serializer = UpdateUserSerializer(self.get_object(), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Deactivate account (verification required)"""

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
        user.save(update_fields=["is_active"])

        verification.status = Verification.Status.USED
        verification.save(update_fields=["status"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePhoneView(APIView):
    """Update user's main phone number (verification required with old and new phones)"""

    def patch(self, request):
        serializer = ChangePhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_phone = user.phone
        new_phone = serializer.validated_data["new_phone"]
        old_verification_token = serializer.validated_data["old_verification_token"]
        new_verification_token = serializer.validated_data["new_verification_token"]

        verification_old, error_message, error_status_code = VerificationService.confirm_verification(
            old_phone, old_verification_token, Verification.Mode.CHANGE_PHONE_OLD
        )
        if not verification_old:
            return Response({"error": error_message}, status=error_status_code)

        verification_new, error_message, error_status_code = VerificationService.confirm_verification(
            new_phone, new_verification_token, Verification.Mode.CHANGE_PHONE_NEW
        )
        if not verification_new:
            return Response({"error": error_message}, status=error_status_code)

        # TODO - add changing phone with other tables like barrier
        user.phone = new_phone
        user.save(update_fields=["phone"])

        verification_old.status = Verification.Status.USED
        verification_old.save(update_fields=["status"])
        verification_new.status = Verification.Status.USED
        verification_new.save(update_fields=["status"])

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@permission_classes([IsAdminUser])
class ChangePasswordView(APIView):
    """Update admin password (verification required)"""

    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        phone = user.phone
        new_password = serializer.validated_data["new_password"]
        verification_token = serializer.validated_data["verification_token"]

        verification, error_message, error_status_code = VerificationService.confirm_verification(
            phone, verification_token, Verification.Mode.CHANGE_PASSWORD
        )
        if not verification:
            return Response({"error": error_message}, status=error_status_code)

        user.set_password(new_password)
        user.save()

        verification.status = Verification.Status.USED
        verification.save(update_fields=["status"])

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@authentication_classes([])
@permission_classes([AllowAny])
class ResetPasswordView(APIView):
    """Reset admin password (verification required)"""

    def patch(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(phone=serializer.validated_data["phone"]).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user.is_active:
            return Response({"error": "User is blocked."}, status=status.HTTP_403_FORBIDDEN)
        if user.role == User.Role.USER:
            return Response({"error": "Only for admins."}, status=status.HTTP_403_FORBIDDEN)

        phone = user.phone
        new_password = serializer.validated_data["new_password"]
        verification_token = serializer.validated_data["verification_token"]

        verification, error_message, error_status_code = VerificationService.confirm_verification(
            phone, verification_token, Verification.Mode.RESET_PASSWORD
        )
        if not verification:
            return Response({"error": error_message}, status=error_status_code)

        user.set_password(new_password)
        user.save()

        verification.status = Verification.Status.USED
        verification.save(update_fields=["status"])

        return Response({"message": "Password successfully reset."}, status=status.HTTP_200_OK)


@permission_classes([IsAdminUser])
class AdminUserAccountView(generics.RetrieveAPIView):
    """Get user details (for admins only)."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "id"


@permission_classes([IsAdminUser])
class AdminBlockUserView(APIView):
    """Block user (for admins only)."""

    def patch(self, request, id):
        user = get_object_or_404(User, id=id)

        reason = request.data.get("reason")
        if not reason:
            return Response({"error": "Reason is required for blocking a user."}, status=status.HTTP_400_BAD_REQUEST)

        if user.role != User.Role.USER:
            return Response({"error": "You cannot block an admin."}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_active:
            return Response({"error": "User is already blocked."}, status=status.HTTP_400_BAD_REQUEST)

        user.block_reason = reason
        user.is_active = False
        user.save(update_fields=["is_active", "block_reason"])

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@permission_classes([IsAdminUser])
class AdminUnblockUserView(APIView):
    """Unblock a user (for admins only)."""

    def patch(self, request, id):
        user = get_object_or_404(User, id=id)

        if user.is_active:
            return Response({"error": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)

        if user.role != User.Role.USER:
            return Response({"error": "You cannot unblock an admin."}, status=status.HTTP_403_FORBIDDEN)

        user.block_reason = ""
        user.is_active = True
        user.save()

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@permission_classes([IsAdminUser])
class AdminSearchUserView(APIView):
    """Search user by given phone number (for admins only)."""

    def post(self, request):
        serializer = SearchUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        user = User.objects.filter(phone=phone).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
