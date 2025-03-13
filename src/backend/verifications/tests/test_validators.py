import pytest
from django.core.exceptions import ValidationError

from verifications.validators import VerificationCodeValidator, VerificationTokenValidator


@pytest.mark.parametrize(
    "code, is_valid",
    [
        ("123456", True),  # Valid code
        ("000000", True),  # Edge case: all zeros
        ("12345", False),  # Too short
        ("1234567", False),  # Too long
        ("12a456", False),  # Contains letter
        ("abcdef", False),  # All letters
    ],
)
def test_verification_code_validator(code, is_valid):
    validator = VerificationCodeValidator()
    if is_valid:
        assert validator(code) is None  # Should pass validation
    else:
        with pytest.raises(ValidationError):
            validator(code)  # Should raise ValidationError


@pytest.mark.parametrize(
    "token, is_valid",
    [
        ("a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6", True),  # Valid token
        ("A1B2C3D4E5F6G7H8J9K0L1M2N3P4Q5R6", True),  # Uppercase valid token
        ("a1b2c3d4e5f6", False),  # Too short
        ("a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r6s77777777777", False),  # Too long
        ("a1b2c3d4e5f6g7h8j9k0l1m2n3p4q5r$!!", False),  # Contains special character
    ],
)
def test_verification_token_validator(token, is_valid):
    validator = VerificationTokenValidator()
    if is_valid:
        assert validator(token) is None  # Should pass validation
    else:
        with pytest.raises(ValidationError):
            validator(token)  # Should raise ValidationError
