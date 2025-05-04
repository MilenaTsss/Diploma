import os

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "localhost:19092")

KAFKA_SMS_VERIFICATION_TOPIC = "sms_verification"
KAFKA_SMS_CONFIGURATION_TOPIC = "sms_configuration"
KAFKA_SMS_RESPONSES_TOPIC = "sms_responses"
KAFKA_FAILED_MESSAGES_TOPIC = "failed_messages"

NUMBER_OF_PARTITIONS = int(os.getenv("NUMBER_OF_PARTITIONS", "3"))

DB_PATH = os.getenv("DB_PATH", "sms_storage.sqlite3")

MODEM_USERNAME = os.getenv("MODEM_USERNAME", "admin")
MODEM_PASSWORD = os.getenv("MODEM_PASSWORD", "password")
MODEM_URL = f"http://{MODEM_USERNAME}:{MODEM_PASSWORD}@192.168.8.1/"

MESSAGE_RESPONSE_TIMEOUT_SECONDS = int(os.getenv("MESSAGE_RESPONSE_TIMEOUT_SECONDS", 600))
HAS_PHONES_RESTRICTION = os.getenv("HAS_PHONES_RESTRICTION", "True").lower() == "true"
AVAILABLE_PHONES = os.getenv("AVAILABLE_PHONES", "+79187058794").split(",")
