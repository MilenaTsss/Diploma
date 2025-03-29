import logging

from message_management.models import SMSMessage

logger = logging.getLogger(__name__)

def handle_sms_response(message: dict):
    message_id = message.get("message_id")
    status = message.get("status")

    try:
        sms = SMSMessage.objects.get(id=message_id)
    except SMSMessage.DoesNotExist:
        logger.warning(f"SMS with ID: `{message_id}` not found")
        return

    if status == "success":
        sms.status = SMSMessage.Status.SENT
    else:
        sms.status = SMSMessage.Status.FAILED

    sms.response_payload = message
    sms.save()
