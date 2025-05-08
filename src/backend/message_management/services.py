from barriers.models import Barrier
from message_management.config_loader import build_message, get_phone_command, get_setting
from message_management.enums import KafkaTopic, PhoneCommand
from message_management.kafka_producer import send_sms_to_kafka
from message_management.models import SMSMessage
from phones.models import BarrierPhone
from verifications.models import Verification


class SMSService:
    """Service class for sending different types of SMS messages."""

    @staticmethod
    def send_verification(verification: Verification):
        message = SMSMessage.objects.create(
            message_type=SMSMessage.MessageType.VERIFICATION_CODE,
            content=f"CODE: {verification.code}",
            phone=verification.phone,
        )
        send_sms_to_kafka(KafkaTopic.SMS_VERIFICATION, message)

    @staticmethod
    def send_add_phone_command(phone: BarrierPhone):
        SMSService._send_phone_command(phone, PhoneCommand.ADD)

    @staticmethod
    def send_delete_phone_command(phone: BarrierPhone):
        SMSService._send_phone_command(phone, PhoneCommand.DELETE)

    @staticmethod
    def send_barrier_setting(barrier: Barrier, setting_key: str, params: dict):
        setting = get_setting(barrier.device_model, setting_key)
        if barrier.device_password:
            params["pwd"] = barrier.device_password
        content = build_message(setting["template"], params)

        message = SMSMessage.objects.create(
            message_type=SMSMessage.MessageType.BARRIER_SETTING,
            content=content,
            phone=barrier.device_phone,
            metadata=params,
        )
        send_sms_to_kafka(KafkaTopic.SMS_CONFIGURATION, message)

    @staticmethod
    def _send_phone_command(phone: BarrierPhone, command: PhoneCommand):
        barrier = phone.barrier

        command_config = get_phone_command(barrier.device_model, command)
        params = {
            "pwd": barrier.device_password,
            "phone": phone.phone.removeprefix("+7"),
            "index": phone.device_serial_number,
        }
        content = build_message(command_config["template"], params)

        message = SMSMessage.objects.create(
            message_type=SMSMessage.MessageType.PHONE_COMMAND,
            content=content,
            phone=barrier.device_phone,
            metadata=params,
        )
        send_sms_to_kafka(KafkaTopic.SMS_CONFIGURATION, message)
