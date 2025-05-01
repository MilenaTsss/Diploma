import json
from unittest.mock import patch

import pytest
from confluent_kafka import KafkaException
from django.utils import timezone

from message_management.enums import KafkaTopic
from message_management.kafka_producer import send_sms_to_kafka
from message_management.models import SMSMessage


@pytest.mark.django_db
class TestKafkaProducer:

    @pytest.fixture
    def sms_message(self):
        return SMSMessage.objects.create(
            message_type=SMSMessage.MessageType.VERIFICATION_CODE,
            content="Test message",
            phone="+71234567890",
        )

    @patch("message_management.kafka_producer.get_producer")
    def test_send_sms_to_kafka(self, mock_get_producer):
        sms_message = SMSMessage.objects.create(
            message_type=SMSMessage.MessageType.VERIFICATION_CODE,
            content="Test SMS content",
            phone="+71234567890",
        )

        producer_mock = mock_get_producer.return_value

        send_sms_to_kafka(KafkaTopic.SMS_VERIFICATION, sms_message)

        sms_message.refresh_from_db()
        assert sms_message.status == SMSMessage.Status.SENT
        assert sms_message.updated_at <= timezone.now()

        producer_mock.produce.assert_called_once()
        args, kwargs = producer_mock.produce.call_args

        assert kwargs["topic"] == KafkaTopic.SMS_VERIFICATION.value
        assert kwargs["key"] == sms_message.phone
        payload = json.loads(kwargs["value"])

        assert payload["message_id"] == sms_message.id
        assert payload["phone"] == sms_message.phone
        assert payload["content"] == sms_message.content
        assert payload["retries"] == 5

        producer_mock.flush.assert_called_once()

    @patch("message_management.kafka_producer.get_producer")
    def test_producer_buffer_error(self, get_producer_mock, sms_message):
        producer_mock = get_producer_mock.return_value
        producer_mock.produce.side_effect = BufferError("Queue full")

        send_sms_to_kafka(KafkaTopic.SMS_VERIFICATION, sms_message)

        producer_mock.flush.assert_not_called()

    @patch("message_management.kafka_producer.get_producer")
    def test_producer_kafka_exception(self, get_producer_mock, sms_message):
        producer_mock = get_producer_mock.return_value
        producer_mock.produce.side_effect = KafkaException("Connection lost")

        send_sms_to_kafka(KafkaTopic.SMS_VERIFICATION, sms_message)

        producer_mock.flush.assert_not_called()

    @patch("message_management.kafka_producer.get_producer")
    def test_producer_unexpected_exception(self, get_producer_mock, sms_message):
        producer_mock = get_producer_mock.return_value
        producer_mock.produce.side_effect = RuntimeError("Unknown error")

        send_sms_to_kafka(KafkaTopic.SMS_VERIFICATION, sms_message)

        producer_mock.flush.assert_not_called()
