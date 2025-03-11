from django.contrib.auth import authenticate
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User, Verification
from users.serializers import (
    AdminPasswordVerificationSerializer,
    LoginSerializer,
    SendVerificationCodeSerializer,
    VerifyCodeSerializer,
)

VERIFICATION_CODE_RESEND_DELAY = 60


@authentication_classes([])
@permission_classes([AllowAny])
class SendVerificationCodeView(APIView):
    """Send a verification code to the user's phone."""

    def post(self, request):
        serializer = SendVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        mode = serializer.validated_data["mode"]

        # Remove all old codes
        Verification.clean()

        # Count all failed attempts for last 2 hours with given phone and return 429 for too many failed requests
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
        recent_verification = Verification.get_recent_verification(phone)
        if recent_verification:
            resend_delay = VERIFICATION_CODE_RESEND_DELAY - (now() - recent_verification.created_at).seconds
            if resend_delay > 0:
                return Response(
                    {"error": _("Verification code was already sent. Try again later."), "retry_after": resend_delay},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(resend_delay)},
                )

        code = Verification.generate_code()
        Verification.objects.create(phone=phone, code=code, mode=mode)

        # TODO!: Here send the code via SMS, REMOVE code from answer

        return Response({"message": _("Verification code sent."), "code": code}, status=status.HTTP_201_CREATED)


@authentication_classes([])
@permission_classes([AllowAny])
class VerifyCodeView(APIView):
    """Verify the code sent to the user's phone."""

    def patch(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        # Remove all old codes
        Verification.clean()

        # Count all failed attempts for last 2 hours with given phone and return 429 for too many failed requests
        if Verification.count_failed_attempts(phone) >= 5:
            return Response(
                {"error": _("Too many verification attempts. Try again later.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Retrieve latest sent code
        recent_verification = Verification.get_recent_verification(phone)
        if recent_verification is None or recent_verification.status in [
            Verification.Status.EXPIRED,
            Verification.Status.VERIFIED,
        ]:
            error_messages = {
                Verification.Status.EXPIRED: _("This code has expired."),
                Verification.Status.VERIFIED: _("This code has already been used. Please request a new one."),
                None: _("No verification codes found."),
            }
            return Response(
                {"error": error_messages[recent_verification.status if recent_verification else None]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if recent_verification.code != code:
            recent_verification.failed_attempts += 1
            recent_verification.save()
            return Response({"error": _("Invalid code.")}, status=status.HTTP_400_BAD_REQUEST)

        recent_verification.status = Verification.Status.VERIFIED
        recent_verification.save()

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


class LoginView(APIView):
    """Login using phone and verification code."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        try:
            verification = Verification.objects.get(phone=phone, code=code, status=Verification.Status.VERIFIED)
        except Verification.DoesNotExist:
            return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(phone=phone)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


# class CreateUserView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [AllowAny]
