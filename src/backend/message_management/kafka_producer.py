import json
import os

from confluent_kafka import Producer
from django.utils import timezone

from message_management.enums import KafkaTopic
from message_management.models import SMSMessage

NUM_RETRIES = 5

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092")

producer = Producer(
    {
        "bootstrap.servers": KAFKA_SERVERS,
    }
)


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

    producer.produce(
        topic=topic.value,
        key=message.phone,
        value=json.dumps(payload),
    )
    producer.flush()
