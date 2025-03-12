from django.contrib.auth import authenticate
from django.shortcuts import render
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, Verification
from users.serializers import (
    AdminPasswordVerificationSerializer,
    LoginSerializer,
    SendVerificationCodeSerializer,
    VerifyCodeSerializer,
)

VERIFICATION_CODE_RESEND_DELAY = 60


def admin_block_password_change_view(request):
    """Custom admin view to block password changes via the Django admin panel."""
    return render(request, "admin/password_change.html", status=status.HTTP_403_FORBIDDEN)


@authentication_classes([])
@permission_classes([AllowAny])
class SendVerificationCodeView(APIView):
    """Send a verification code to the user's phone."""

    def post(self, request):
        serializer = SendVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        mode = serializer.validated_data["mode"]

        # Check if user with this phone is blocked or not.
        user = User.objects.filter(phone=phone).first()
        if user and not user.is_active:
            return Response(
                {"error": _("This account is blocked. Contact support for assistance.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Remove old codes
        Verification.clean()

        # Count all failed attempts for the last 2 hours and return 429 if exceeded
        if Verification.count_failed_attempts(phone) >= 5:
            return Response(
                {"error": _("Too many verification attempts. Try again later.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Check if there are too many unverified codes for this phone number, further requests will be blocked
        if Verification.count_unverified_codes(phone) >= 5:
            return Response(
                {"error": _("Too many unverified codes. Try again later.")}, status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Check if a code was sent within the last minutes
        recent_verification = Verification.get_recent_verification(phone, VERIFICATION_CODE_RESEND_DELAY)
        if recent_verification:
            resend_delay = VERIFICATION_CODE_RESEND_DELAY - (now() - recent_verification.created_at).seconds
            return Response(
                {"error": _("Verification code was already sent. Try again later."), "retry_after": resend_delay},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(resend_delay)},
            )

        verification = Verification.create_new_verification(phone, mode)

        # TODO!: Here send the code via SMS, REMOVE code from answer
        return Response(
            {
                "message": _("Verification code sent."),
                "verification_token": verification.verification_token,
                "code": verification.code,
            },
            status=status.HTTP_201_CREATED,
        )


@authentication_classes([])
@permission_classes([AllowAny])
class VerifyCodeView(APIView):
    """Verify the code sent to the user's phone using a verification token."""

    def patch(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]
        verification_token = serializer.validated_data["verification_token"]

        # Check if user with this phone is blocked or not.
        user = User.objects.filter(phone=phone).first()
        if user and not user.is_active:
            return Response(
                {"error": _("This account is blocked. Contact support for assistance.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Remove old codes
        Verification.clean()

        # Count all failed attempts for the last 2 hours and return 429 if exceeded
        if Verification.count_failed_attempts(phone) >= 5:
            return Response(
                {"error": _("Too many verification attempts. Try again later.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Retrieve verification entry by token
        verification = Verification.get_verification_by_token(verification_token)

        error_responses = {
            None: (_("No verification codes found."), status.HTTP_400_BAD_REQUEST),
            Verification.Status.VERIFIED: (
                _("This code has already been used. Please request a new one."),
                status.HTTP_409_CONFLICT,
            ),
            Verification.Status.EXPIRED: (_("This code has expired. Please request a new one."), status.HTTP_410_GONE),
        }

        if verification is None or verification.status in error_responses:
            message, response_status = error_responses[verification.status if verification else None]
            return Response({"error": message}, status=response_status)

        if verification.code != code:
            verification.failed_attempts += 1
            verification.save()
            return Response({"error": _("Invalid code.")}, status=status.HTTP_400_BAD_REQUEST)

        verification.status = Verification.Status.VERIFIED
        verification.save()

        return Response({"message": _("Code verified successfully.")}, status=status.HTTP_200_OK)


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
        verification = Verification.get_verification_by_token(verification_token)

        if not verification or verification.phone != phone or verification.mode != Verification.Mode.LOGIN:
            return Response(
                {"error": _("Invalid verification token or phone number.")}, status=status.HTTP_404_NOT_FOUND
            )

        if verification.status != Verification.Status.VERIFIED:
            return Response({"error": _("Phone number has not been verified.")}, status=status.HTTP_400_BAD_REQUEST)

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
