from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from barriers.validators import DevicePasswordValidator
from core.constants import PHONE_MAX_LENGTH, CHOICE_MAX_LENGTH
from core.validators import PhoneNumberValidator

MAX_LENGTH = 255


class Barrier(models.Model):
    """Barrier model representing a physical gate or access point."""

    class Meta:
        db_table = "barrier"

    # TODO - move into config file
    class Model(models.TextChoices):
        RTU5024 = "RTU5024", _("RTU5024")
        RTU5025 = "RTU5025", _("RTU5025")
        RTU5035 = "RTU5035", _("RTU5035")
        # TELEMETRICA = "Telemetrica", _("Telemetrica")
        # ELFOC = "Elfoc", _("Elfoc")

    address = models.CharField(
        max_length=MAX_LENGTH * 2,
        blank=False,
        db_index=True,
        null=False,
        help_text=_("Full address of the barrier, validated based on frontend suggestions.")
    )

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="owned_barriers",  # for searching barriers for user - user.managed_barriers.all()
        null=False,
        help_text=_("User who owns the barrier. Must be an admin.")
    )

    device_phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        unique=True,
        db_index=True,
        validators=[PhoneNumberValidator()],
        null=False,
        blank=False,
        help_text=_("Enter a phone number in the format +7XXXXXXXXXX.")
    )

    device_model = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=Model.choices)

    device_phones_amount = models.PositiveIntegerField(
        default=1,
        null=False,
        help_text=_("Number of registered device phones. Must be at least 1.")
    )

    # TODO - validator that depends on model? or no validator at all
    device_password = models.CharField(
        max_length=4,
        validators=[DevicePasswordValidator()],
        null=False,
        blank=False,
        help_text=_("Device password must be exactly 4 digits.")
    )

    additional_info = models.TextField(
        blank=True,
        null=False,
        help_text=_("Additional details about the barrier.")
    )

    is_public = models.BooleanField(
        default=True,
        null=False,
        help_text=_("Whether the barrier is visible to all users.")
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.address} ({self.owner.full_name})"

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Deletion of this object is not allowed.")


class UserBarrier(models.Model):
    """Таблица связи между пользователями и шлагбаумами"""

    class Meta:
        db_table = "user_barrier"
        unique_together = ("user", "barrier")

    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="barriers_access",
        help_text=_("Пользователь, имеющий доступ к шлагбауму.")
    )
    barrier = models.ForeignKey(
        "barriers.Barrier",
        on_delete=models.PROTECT,
        related_name="users_access",
        help_text=_("Шлагбаум, к которому есть доступ у пользователя.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO - add access request from which this was created

    def __str__(self):
        return f"{self.user} - {self.barrier}"
