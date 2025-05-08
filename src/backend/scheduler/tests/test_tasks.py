from unittest.mock import patch

import pytest

from scheduler.tasks import send_close_sms, send_delete_phone, send_open_sms


@pytest.mark.django_db
@patch("scheduler.tasks.SMSService.send_add_phone_command")
def test_send_open_sms_calls_add_command(mock_send_add, barrier_phone):
    send_open_sms(barrier_phone)

    mock_send_add.assert_called_once_with(barrier_phone)


@pytest.mark.django_db
@patch("scheduler.tasks.SMSService.send_delete_phone_command")
def test_send_close_sms_calls_delete_command(mock_send_delete, barrier_phone):
    send_close_sms(barrier_phone)

    mock_send_delete.assert_called_once_with(barrier_phone)


@pytest.mark.django_db
def test_send_delete_phone_deactivates_phone(barrier_phone):
    send_delete_phone(barrier_phone)
    barrier_phone.refresh_from_db()

    assert not barrier_phone.is_active
