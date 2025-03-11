import random
import re
import string
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from users.constants import CHOICE_MAX_LENGTH, PHONE_MAX_LENGTH, VERIFICATION_CODE_MAX_LENGTH
from users.validators import PhoneNumberValidator, VerificationCodeValidator

MAX_LENGTH = 255


class UserManager(BaseUserManager):
    """Custom manager for the User model"""

    # TODO - maybe delete
    @classmethod
    def normalize_phone(cls, phone: str) -> str:
        """
        Normalize phone number:
        - Remove all non-numeric characters except "+"
        - Convert "8" or "7" at the beginning to "+7"
        - Ensure exactly 10 digits after "+7"
        """
        phone = re.sub(r"[^\d+]", "", phone)  # Remove all non-numeric characters except "+"

        if phone.startswith("+7"):
            phone = "+7" + phone[2:]  # Keep +7 and the rest
        elif phone.startswith("8") or phone.startswith("7"):
            phone = "+7" + phone[1:]  # Convert 8/7 to +7
        elif not phone.startswith("+7"):
            raise ValueError("Invalid phone number format")

        if not re.fullmatch(r"\+7\d{10}", phone):
            raise ValueError("Phone number must be in format +7XXXXXXXXXX")

        return phone

    def create_user(self, phone, password=None, **extra_fields):
        """Creates a regular user"""
        if not phone:
            raise ValueError("Phone number must be provided")

        phone = self.normalize_phone(phone)

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

    phone_validator = PhoneNumberValidator()
    code_validator = VerificationCodeValidator()

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        db_index=True,
        help_text=_("Enter a phone number in the format +7XXXXXXXXXX."),
        validators=[phone_validator],
    )
    code = models.CharField(max_length=VERIFICATION_CODE_MAX_LENGTH, validators=[code_validator])
    mode = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=Mode.choices)
    status = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=Status.choices, default=Status.SENT)
    failed_attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.phone} - {self.mode} - {self.status}"

    @staticmethod
    def generate_code(length=6):
        """Generates a random numeric verification code of specified length."""

        return "".join(random.choices(string.digits, k=length))

    @classmethod
    def clean(cls):
        """Deletes outdated verification codes and marks old sent codes as expired."""

        now_time = now()
        expiration_time = now_time - timedelta(minutes=1)
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

    @classmethod
    def get_recent_verification(cls, phone):
        """Returns the most recent verification code."""

        return cls.objects.filter(phone=phone).order_by("-created_at").first()
