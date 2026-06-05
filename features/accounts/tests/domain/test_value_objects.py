import pytest

from features.accounts.domain.exceptions import InvalidEmailError, InvalidPhoneError
from features.accounts.domain.value_objects import Email, Phone


def test_email_invalid_raises():
    invalid_emails = ["", "not-an-email", "missing@domain", "@nodomain.com", "user@.com"]
    for raw in invalid_emails:
        with pytest.raises(InvalidEmailError):
            Email(raw)


def test_email_valid_normalizes():
    email = Email("  User@Example.COM  ")
    assert email.value == "user@example.com"


def test_phone_format():
    phone = Phone("+57 300 123 4567")
    assert phone.value == "+573001234567"

    phone_clean = Phone("+573001234567")
    assert phone.value == phone_clean.value


def test_phone_invalid_raises():
    invalid_phones = ["", "3001234567", "+57abc", "+123", "573001234567"]
    for raw in invalid_phones:
        with pytest.raises(InvalidPhoneError):
            Phone(raw)
