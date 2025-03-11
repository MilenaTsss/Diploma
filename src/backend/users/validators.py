from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class PhoneNumberValidator(validators.RegexValidator):
    """
    Validator for phone numbers in the format +7XXXXXXXXXX (Russian numbers).
    """

    regex = r"^\+7\d{10}$"
    message = _("Enter a valid phone number in the format +7XXXXXXXXXX.")
    flags = 0


@deconstructible
class VerificationCodeValidator(validators.RegexValidator):
    """
    Validator for verification codes consisting of exactly 6 digits.
    """

    regex = r"^\d{6}$"
    message = _("Enter a valid 6-digit verification code.")
    flags = 0
