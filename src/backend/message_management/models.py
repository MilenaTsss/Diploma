from django.db import models

from users.constants import PHONE_MAX_LENGTH
from users.validators import PhoneNumberValidator
from django.utils.translation import gettext_lazy as _

CHOICE_MAX_LENGTH = 20

class SMSMessage(models.Model):

    class MessageType(models.TextChoices):
        VERIFICATION_CODE = "verification", "Verification Code"
        PHONE_COMMAND = "phone_command", "Phone Command"
        BARRIER_SETTING = "barrier_setting", "Barrier Setting"

    class Status(models.TextChoices):
        CREATED = "created", "Waiting for sending"
        SENT = "sent", "Sent"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"


    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        db_index=True,
        validators=[PhoneNumberValidator()],
        help_text=_("Enter a phone number in the format +7XXXXXXXXXX."),
    )
    message_type = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=MessageType.choices)
    content = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=CHOICE_MAX_LENGTH,
        choices=Status.choices,
        default=Status.CREATED
    )
    response_payload = models.JSONField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
