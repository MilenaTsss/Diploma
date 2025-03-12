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


@deconstructible
class VerificationTokenValidator(validators.RegexValidator):
    """
    Validator for verification tokens consisting of exactly 32 ascii letters or digits.
    """

    regex = r"^[a-zA-Z0-9]{32}$"
    message = _("Enter a valid 32-character verification token (letters and digits only).")
    flags = 0
