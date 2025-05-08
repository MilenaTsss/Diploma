import json
import logging
import os

from confluent_kafka import KafkaException, Producer
from django.utils import timezone

from message_management.enums import KafkaTopic
from message_management.models import SMSMessage

NUM_RETRIES = 5
KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092")
_producer = None

logger = logging.getLogger(__name__)


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": KAFKA_SERVERS})
    return _producer


def reset_producer():
    global _producer
    logger.warning("Resetting Kafka producer")
    _producer = None


def send_sms_to_kafka(topic: KafkaTopic, message: SMSMessage):
    message.status = SMSMessage.Status.SENT
    message.updated_at = timezone.now()
    message.save()

    payload = {
        "message_id": message.id,
        "phone": message.phone,
        "content": message.content,
        "retries": NUM_RETRIES,
    }

    try:
        producer = get_producer()
        producer.produce(
            topic=topic.value,
            key=message.phone,
            value=json.dumps(payload),
        )
        producer.flush()
        logger.info("SMS sent to Kafka topic %s for phone %s", topic.value, message.phone)

    except BufferError as e:
        logger.error("Kafka producer queue is full: %s", e)
        reset_producer()

    except KafkaException as e:
        logger.error("Kafka exception occurred: %s", e)
        reset_producer()

    except Exception as e:
        logger.exception(f"Unexpected error while producing to Kafka: {e}")
        reset_producer()
