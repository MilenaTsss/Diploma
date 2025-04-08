from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class PhoneNumberValidator(validators.RegexValidator):
    """Validator for phone numbers in the format +7XXXXXXXXXX (Russian numbers)."""

    regex = r"^\+7\d{10}$"
    message = _("Enter a valid phone number in the format +7XXXXXXXXXX.")
    flags = 0
