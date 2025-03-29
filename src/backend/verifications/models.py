import logging
import random
import string
from datetime import timedelta

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from core.constants import CHOICE_MAX_LENGTH, PHONE_MAX_LENGTH
from core.validators import PhoneNumberValidator
from verifications.constants import (
    DELETION_DAYS,
    EXPIRATION_MINUTES,
    VERIFICATION_CODE_MAX_LENGTH,
    VERIFICATION_TOKEN_MAX_LENGTH,
)
from verifications.validators import VerificationCodeValidator, VerificationTokenValidator

logger = logging.getLogger(__name__)


class VerificationService:
    """Service class for handling verification-related queries."""

    @staticmethod
    def generate_verification_code():
        """Generates a random 6-digit verification code."""
        return "".join(random.choices(string.digits, k=VERIFICATION_CODE_MAX_LENGTH))

    @staticmethod
    def generate_verification_token():
        """Generates a random alphanumeric verification token."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=VERIFICATION_TOKEN_MAX_LENGTH))

    @staticmethod
    def create_new_verification(phone, mode):
        """Creates a new verification entry with a random verification token."""

        return Verification.objects.create(
            phone=phone,
            code=VerificationService.generate_verification_code(),
            verification_token=VerificationService.generate_verification_token(),
            mode=mode,
            status=Verification.Status.SENT,
        )

    @staticmethod
    def clean():
        """Deletes outdated verification codes and marks old sent codes as expired."""

        now_time = now()
        expiration_time = now_time - timedelta(minutes=EXPIRATION_MINUTES)
        deletion_time = now_time - timedelta(days=DELETION_DAYS)

        Verification.objects.filter(created_at__lte=deletion_time).delete()
        Verification.objects.filter(status=Verification.Status.SENT, created_at__lte=expiration_time).update(
            status=Verification.Status.EXPIRED
        )

    @staticmethod
    def count_failed_attempts(phone):
        """Counts total failed verification attempts for the last 2 hours."""

        return (
            Verification.objects.filter(
                phone=phone, created_at__gte=now() - timedelta(hours=2), failed_attempts__gt=0
            ).aggregate(total_attempts=models.Sum(models.F("failed_attempts"), default=0))["total_attempts"]
            or 0
        )

    @staticmethod
    def count_unverified_codes(phone):
        """Counts the number of unverified codes for a given phone number."""

        return Verification.objects.filter(phone=phone).exclude(status=Verification.Status.VERIFIED).count()

    @staticmethod
    def confirm_verification(phone, verification_token, mode):
        """Validates the verification token for given mode."""
        verification = Verification.objects.filter(verification_token=verification_token).first()

        if not verification:
            return None, _("Invalid verification token."), status.HTTP_404_NOT_FOUND

        if verification.phone != phone:
            return None, _("Invalid verification phone number."), status.HTTP_404_NOT_FOUND

        if verification.mode != mode:
            return None, _("Invalid verification mode."), status.HTTP_404_NOT_FOUND

        if verification.status != Verification.Status.VERIFIED:
            return None, _("Phone number has not been verified."), status.HTTP_400_BAD_REQUEST

        return verification, None, None


class Verification(models.Model):
    """Verification codes sent via SMS for user authentication and account-related actions."""

    class Meta:
        db_table = "verification"

    class Mode(models.TextChoices):
        LOGIN = "login", "Login"
        CHANGE_PHONE_OLD = "change_phone_old", "Change Old Phone"
        CHANGE_PHONE_NEW = "change_phone_new", "Change New Phone"
        RESET_PASSWORD = "reset_password", "Reset Password"
        CHANGE_PASSWORD = "change_password", "Change Password"
        DELETE_ACCOUNT = "delete_account", "Delete Account"

    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        VERIFIED = "verified", "Verified"
        USED = "used", _("Used")
        EXPIRED = "expired", "Expired"

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        db_index=True,
        validators=[PhoneNumberValidator()],
        help_text=_("Enter a phone number in the format +7XXXXXXXXXX."),
    )
    code = models.CharField(max_length=VERIFICATION_CODE_MAX_LENGTH, validators=[VerificationCodeValidator()])
    verification_token = models.CharField(
        max_length=VERIFICATION_TOKEN_MAX_LENGTH,
        unique=True,
        validators=[VerificationTokenValidator()],
        help_text=_("Unique token for verifying the code."),
    )
    mode = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=Mode.choices)
    status = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=Status.choices, default=Status.SENT)
    failed_attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.phone} - {self.mode} - {self.status} - {self.verification_token}"

    @classmethod
    def get_verification_by_token(cls, token):
        """Fetches the verification entry by its verification token."""

        return cls.objects.filter(verification_token=token).first()

    @classmethod
    def get_recent_verification(cls, phone, resend_delay):
        """Returns the most recent verification code within the resend delay window."""

        return (
            cls.objects.filter(phone=phone, created_at__gte=now() - timedelta(seconds=resend_delay))
            .order_by("-created_at")
            .first()
        )
