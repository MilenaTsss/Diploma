from unittest.mock import patch

import pytest

from message_management.enums import KafkaTopic, PhoneCommand
from message_management.models import SMSMessage
from message_management.services import SMSService


@pytest.mark.django_db
class TestSendVerification:
    @patch("message_management.services.send_sms_to_kafka")
    def test_send_verification_success(self, mock_send_sms, create_verification):
        verification = create_verification()
        SMSService.send_verification(verification)

        message = SMSMessage.objects.get(message_type=SMSMessage.MessageType.VERIFICATION_CODE)

        mock_send_sms.assert_called_once_with(KafkaTopic.SMS_VERIFICATION, message)
        assert message.content.startswith("CODE:")


@pytest.mark.django_db
class TestSendAddPhoneCommand:
    @patch("message_management.services.send_sms_to_kafka")
    @patch("message_management.services.build_message", return_value="ADD_COMMAND")
    @patch("message_management.services.get_phone_command")
    def test_send_add_phone_command_success(self, mock_get_command, mock_build_message, mock_send_sms, barrier_phone):
        mock_get_command.return_value = {"template": "{pwd}{index}{phone}"}

        SMSService.send_add_phone_command(barrier_phone)

        message = SMSMessage.objects.get(message_type=SMSMessage.MessageType.PHONE_COMMAND)

        mock_send_sms.assert_called_once_with(KafkaTopic.SMS_CONFIGURATION, message)
        mock_get_command.assert_called_once_with(barrier_phone.barrier.device_model, PhoneCommand.ADD)
        mock_build_message.assert_called_once()
        assert message.content == "ADD_COMMAND"


@pytest.mark.django_db
class TestSendDeletePhoneCommand:
    @patch("message_management.services.send_sms_to_kafka")
    @patch("message_management.services.build_message", return_value="DEL_COMMAND")
    @patch("message_management.services.get_phone_command")
    def test_send_delete_phone_command_success(
        self, mock_get_command, mock_build_message, mock_send_sms, barrier_phone
    ):
        mock_get_command.return_value = {"template": "{pwd}{index}{phone}"}

        SMSService.send_delete_phone_command(barrier_phone)

        message = SMSMessage.objects.get(message_type=SMSMessage.MessageType.PHONE_COMMAND)

        mock_send_sms.assert_called_once_with(KafkaTopic.SMS_CONFIGURATION, message)
        mock_get_command.assert_called_once_with(barrier_phone.barrier.device_model, PhoneCommand.DELETE)
        mock_build_message.assert_called_once()
        assert message.content == "DEL_COMMAND"


@pytest.mark.django_db
class TestSendBarrierSetting:
    @patch("message_management.services.send_sms_to_kafka")
    @patch("message_management.services.build_message", return_value="SETTING_COMMAND")
    @patch("message_management.services.get_setting")
    def test_send_barrier_setting_success(self, mock_get_setting, mock_build_message, mock_send_sms, barrier):
        mock_get_setting.return_value = {"template": "template_setting"}

        SMSService.send_barrier_setting(barrier, "start", {"param1": "value1"})

        message = SMSMessage.objects.get(message_type=SMSMessage.MessageType.BARRIER_SETTING)

        mock_send_sms.assert_called_once_with(KafkaTopic.SMS_CONFIGURATION, message)
        mock_get_setting.assert_called_once_with(barrier.device_model, "start")
        mock_build_message.assert_called_once()
        assert message.content == "SETTING_COMMAND"
