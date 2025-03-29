from django.utils import timezone
from kafka import KafkaProducer
import json

from message_management.models import SMSMessage

NUM_RETRIES = 5

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def send_sms_to_kafka(topic: str, message: SMSMessage):
    message.status = SMSMessage.Status.SENT
    message.updated_at = timezone.now()
    message.save()
    msg = {
        "message_id": message.id,
        "phone": message.phone,
        "content": message.content,
        "retries": NUM_RETRIES,
    }

    producer.send(topic, value=msg)
