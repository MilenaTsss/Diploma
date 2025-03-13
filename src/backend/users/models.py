import random
import string
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from users.constants import (
    CHOICE_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    VERIFICATION_CODE_MAX_LENGTH,
    VERIFICATION_TOKEN_MAX_LENGTH,
)
from users.validators import PhoneNumberValidator, VerificationCodeValidator, VerificationTokenValidator

MAX_LENGTH = 255


class UserManager(BaseUserManager):
    """Custom manager for the User model"""

    phone_validator = PhoneNumberValidator()

    def validate_phone(self, phone: str):
        """Validate phone number using PhoneNumberValidator"""
        try:
            self.phone_validator(phone)
        except ValidationError as e:
            raise ValidationError(_("Invalid phone number: ") + str(e))
        return phone

    def create_user(self, phone, password=None, **extra_fields):
        """Creates a regular user"""
        if not phone:
            raise ValueError("Phone number must be provided")

        phone = self.validate_phone(phone)

        extra_fields.setdefault("role", User.Role.USER)
        extra_fields.setdefault("is_active", True)

        if extra_fields["role"] == User.Role.USER:
            password = None

        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)  # Only admins have a password
        user.save(using=self._db)
        return user

    def create_admin(self, phone, password=None, **extra_fields):
        """Creates an admin (can only be created via Django Admin)"""
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)

        if password is None:
            raise ValueError("Admin users require a password")

        return self.create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        """Creates a superuser"""
        if self.model.objects.filter(role=User.Role.SUPERUSER).exists():
            raise ValueError("There can be only one superuser")

        extra_fields.setdefault("role", User.Role.SUPERUSER)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)

        if password is None:
            raise ValueError("Superuser requires a password")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model"""

    class Meta:
        db_table = "user"

    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        USER = "user", _("User")
        SUPERUSER = "superuser", _("Superuser")

    class PhonePrivacy(models.TextChoices):
        PUBLIC = "public", _("Public")
        PRIVATE = "private", _("Private")
        PROTECTED = "protected", _("Protected")

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        unique=True,
        help_text=_("Enter a phone number in the format +7XXXXXXXXXX."),
        validators=[PhoneNumberValidator()],
        error_messages={"unique": _("A user with this phone number already exists.")},
    )
    full_name = models.CharField(max_length=MAX_LENGTH, blank=True, default="")
    password = models.CharField(max_length=MAX_LENGTH, blank=True, default="")

    role = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=Role.choices, default=Role.USER)

    phone_privacy = models.CharField(
        max_length=CHOICE_MAX_LENGTH, choices=PhonePrivacy.choices, default=PhonePrivacy.PRIVATE
    )

    is_staff = models.BooleanField(
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_superuser = models.BooleanField(
        default=False, help_text=_("Designates whether the user can manage all aspects of the system.")
    )
    is_blocked = models.BooleanField(
        default=False,
        help_text=_(
            "If the user is blocked, they will be restricted from performing certain actions, "
            "but their account remains active."
        ),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. " "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(default=now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name", "role"]

    def __str__(self):
        return self.phone + " " + self.full_name

    def get_full_name(self):
        return self.full_name

    def get_phone(self):
        return self.phone


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
    def create_new_verification(cls, phone, mode):
        """Creates a new verification entry with a random verification token."""

        code = "".join(random.choices(string.digits, k=VERIFICATION_CODE_MAX_LENGTH))
        verification_token = "".join(
            random.choices(string.ascii_letters + string.digits, k=VERIFICATION_TOKEN_MAX_LENGTH)
        )

        return cls.objects.create(
            phone=phone,
            code=code,
            verification_token=verification_token,
            mode=mode,
            status=cls.Status.SENT,
        )

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

    @classmethod
    def clean(cls):
        """Deletes outdated verification codes and marks old sent codes as expired."""

        now_time = now()
        expiration_time = now_time - timedelta(minutes=15)
        deletion_time = now_time - timedelta(days=1)

        cls.objects.filter(created_at__lte=deletion_time).delete()
        cls.objects.filter(status=cls.Status.SENT, created_at__lte=expiration_time).update(status=cls.Status.EXPIRED)

    @classmethod
    def count_failed_attempts(cls, phone):
        """Counts total failed verification attempts for the last 2 hours."""

        return (
            cls.objects.filter(
                phone=phone, created_at__gte=now() - timedelta(hours=2), failed_attempts__gt=0
            ).aggregate(total_attempts=models.Sum(models.F("failed_attempts"), default=0))["total_attempts"]
            or 0
        )

    @classmethod
    def count_unverified_codes(cls, phone):
        """Counts the number of unverified codes for a given phone number."""

        return cls.objects.filter(phone=phone).exclude(status=cls.Status.VERIFIED).count()
