import json
import logging
import time

from confluent_kafka import Message

from config import MESSAGE_RESPONSE_TIMEOUT_MINUTES
from kafka.producer import send_to_failed, send_to_responses
from modem.huawei_modem_client import HuaweiModemClient

logger = logging.getLogger("__name__")


def wait_for_reply_from_phone(modem: HuaweiModemClient, phone: str):
    """Wait for an incoming SMS from the specified phone number within the timeout."""

    # TODO - need to understand what are new messages?, how to get only unread messages?

    logger.debug("Waiting for reply from phone: %s", phone)

    start = time.time()
    while time.time() - start < MESSAGE_RESPONSE_TIMEOUT_MINUTES:
        new_messages = modem.read_sms()
        for msg in new_messages:
            if msg["phone"] == phone and msg["message_type"] == "incoming":
                logger.info("Received reply from phone: %s", phone)
                return msg["content"]
        time.sleep(2)
    logger.warning("Timeout waiting for reply from phone: %s", phone)


def handle_sms_configuration(modem: HuaweiModemClient, message: Message) -> bool:
    try:
        value = message.value()
        if value is None:
            logger.warning("Received message with no value.")
            return False

        data = json.loads(value.decode("utf-8"))
        phone = data["phone"]
        content = data["content"]
        retries = data["retries"]
        message_id = data["message_id"]

        logger.info("Handling configuration SMS for phone: %s", phone)

        for attempt in range(retries):
            logger.debug("Attempt %d to send configuration SMS to %s", attempt + 1, phone)
            success = modem.send_sms(phone, content)
            if success:
                logger.info("Configuration SMS sent to %s, now waiting for reply...", phone)
                break  # Exit cycle after successful send
            logger.error("Failed to send configuration SMS to %s, attempt %d", phone, attempt + 1)
        else:
            # <-- Error after all attempts
            logger.error("All attempts to send SMS failed for phone: %s, sending to failed_messages topic", phone)
            send_to_failed(data, phone)
            return False

        reply = wait_for_reply_from_phone(modem, phone)
        if reply:
            logger.info("Reply received from %s, sending to responses topic", phone)
            send_to_responses({"message_id": message_id, "phone": phone, "content": reply}, phone)
            return True
        else:
            logger.warning("No reply received from phone: %s", phone)
            send_to_failed(data, phone)
            return False

    except Exception as e:
        logger.exception("Unexpected error while handling configuration SMS: %s", e)
        return False  # <-- Any unexpected error
