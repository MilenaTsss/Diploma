import concurrent.futures
import logging
import os
import sys
import time

from confluent_kafka import Consumer, Message, TopicPartition

from config import (
    DB_PATH,
    KAFKA_SMS_VERIFICATION_TOPIC,
    MODEM_PASSWORD,
    MODEM_URL,
    MODEM_USERNAME,
    NUMBER_OF_PARTITIONS,
)
from kafka.consumers import create_sms_verification_consumer
from kafka.handlers.verification_handler import handle_sms_verification
from modem.huawei_modem_client import HuaweiModemClient

logger = logging.getLogger(__name__)


def setup_logging():
    log_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    os.makedirs("logs", exist_ok=True)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    file_handler = logging.FileHandler("logs/service.log", encoding="utf-8")
    file_handler.setFormatter(log_formatter)

    logging.basicConfig(
        level=logging.DEBUG if os.getenv("LOGLEVEL", "debug") == "debug" else logging.INFO,
        handlers=[console_handler, file_handler],
    )


def consume_loop(consumer: Consumer, handler, partition_id: int, topic_name: str, modem: HuaweiModemClient):
    """Continuously listen for messages from a specific partition."""

    while True:
        try:
            logger.debug(f"Assigning partition {partition_id} in topic {topic_name}")
            consumer.assign([TopicPartition(topic_name, partition_id)])
            logger.debug(f"Assigned partition id: {partition_id} in topic: {topic_name}")

            while True:
                msg: Message = consumer.poll(timeout=10.0)
                if msg is None:
                    logger.debug(f"No new message on partition {partition_id}. Waiting...")
                    continue
                if msg.error():
                    logger.error("Consumer error: %s", msg.error())
                    continue

                logger.debug("Message received: %s", msg.value())

                logger.debug("Handling message from partition %s, offset %s", partition_id, msg.offset())
                success = handler(modem, msg)
                if not success:
                    logger.error(
                        "Handler returned failure for message at offset %s. Will recreate consumer.", msg.offset()
                    )
                    raise Exception("Handler failure")

                consumer.commit(message=msg)
                logger.debug("Committed offset %s on partition %s", msg.offset(), partition_id)

        except Exception as e:
            logger.error("Error in consumer loop. Reinitializing consumer for partition %s. Error: %s", partition_id, e)

            try:
                consumer.close()
                logger.debug("Consumer closed successfully.")
            except Exception as close_error:
                logger.error("Error closing consumer: %s", close_error)

            time.sleep(5)  # delay before reconnect

            consumer = create_sms_verification_consumer()


def main():
    logger.debug("Initializing Huawei modem client...")
    modem = HuaweiModemClient(url=MODEM_URL, db_path=DB_PATH, username=MODEM_USERNAME, password=MODEM_PASSWORD)

    logger.debug("Creating Kafka consumers...")
    sms_verification_consumer = create_sms_verification_consumer()
    # sms_configuration_consumer = create_sms_configuration_consumer()

    # Thread pool for processing messages per partition
    logger.debug("Starting thread pool with %s workers", NUMBER_OF_PARTITIONS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_PARTITIONS) as executor:
        # For all partitions in verification topic
        for partition in range(NUMBER_OF_PARTITIONS):
            executor.submit(
                consume_loop,
                sms_verification_consumer,
                handle_sms_verification,
                partition,
                KAFKA_SMS_VERIFICATION_TOPIC,
                modem,
            )

        # For all partitions in configuration topic
        # TODO UNCOMMENT THIS WHEN READY
        # for partition in range(NUMBER_OF_PARTITIONS):
        #     executor.submit(
        #         consume_loop,
        #         sms_configuration_consumer,
        #         handle_sms_configuration,
        #         partition,
        #         KAFKA_SMS_CONFIGURATION_TOPIC,
        #         modem,
        #     )

        logger.info("Service started. Listening for messages.")

        while True:
            time.sleep(10)


if __name__ == "__main__":
    setup_logging()
    main()
