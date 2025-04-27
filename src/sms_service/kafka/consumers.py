from confluent_kafka import Consumer

from config import KAFKA_SERVERS


def create_sms_verification_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": KAFKA_SERVERS,
            "group.id": "sms_verification_group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


def create_sms_configuration_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": KAFKA_SERVERS,
            "group.id": "sms_configuration_group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
