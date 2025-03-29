from message_management.models import SMSMessage
from message_management.config_loader import find_setting_by_key, find_phone_command_by_name, build_message
from message_management.kafka_producer import send_sms_to_kafka
from verifications.models import Verification


def send_verification(verification_id: int):
    verification = Verification.objects.get(id=verification_id)
    message = SMSMessage.objects.create(
        message_type=SMSMessage.MessageType.VERIFICATION_CODE,
        content=f"Ваш код подтверждения: {verification.code}",
        phone=verification.phone
    )
    send_sms_to_kafka("sms_verification", message)


def send_phone_command(barrier_id: int, phone_id: int, command_key: str):
    barrier = Barrier.objects.get(id=barrier_id)
    phone = AdditionalPhones.objects.get(id=phone_id)
    params = {
        "pwd": barrier.password,
        "phone": phone.phone,
        "index": phone.index,
    }

    command = find_phone_command_by_name(barrier.device_type, command_key)
    content = build_message(command["template"], params)

    message = SMSMessage.objects.create(
        message_type=SMSMessage.MessageType.PHONE_COMMAND,
        content=content,
        phone=barrier.phone,
        metadata=params,
    )
    send_sms_to_kafka("sms_configuration", message)


def send_barrier_setting(barrier_id: int, setting_key: str, params: dict):
    barrier = Barrier.objects.get(id=barrier_id)

    setting = find_setting_by_key(barrier.device_type, setting_key)
    content = build_message(setting["template"], params)

    message = SMSMessage.objects.create(
        message_type=SMSMessage.MessageType.BARRIER_SETTING,
        content=content,
        phone=barrier.phone,
        metadata=params,
    )
    send_sms_to_kafka("sms_configuration", message)
