from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from core.constants import (
    CHOICE_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)
from core.validators import PhoneNumberValidator

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
    is_active = models.BooleanField(
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. " "Unselect this instead of deleting accounts."
        ),
    )
    block_reason = models.CharField(max_length=MAX_LENGTH, blank=True, default="")
    date_joined = models.DateTimeField(default=now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name", "role"]

    def __str__(self):
        return self.phone + " " + self.full_name

    def get_short_name(self):
        return self.phone

    def get_full_name(self):
        return self.full_name

    def get_phone(self):
        return self.phone

    @classmethod
    def is_phone_blocked(cls, phone: str) -> bool:
        """Checks if a user with the given phone number is blocked"""

        user = cls.objects.filter(phone=phone).first()
        return user.is_blocked_user() if user else False

    def is_blocked_user(self):
        """Returns True if the user is blocked (inactive)."""

        return not self.is_active

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Deletion of this object is not allowed.")
