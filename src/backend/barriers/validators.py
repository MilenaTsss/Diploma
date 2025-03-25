from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class DevicePasswordValidator(validators.RegexValidator):
    """
    Validator for device numbers password containing exactly 4 digits.
    """

    regex = r"^\d{4}$"
    message = _("Enter a valid device password. Must be exactly 4 digits.")
    flags = 0
