import json
from unittest.mock import patch

import pytest
from django.utils import timezone

from message_management.enums import KafkaTopic
from message_management.kafka_producer import send_sms_to_kafka
from message_management.models import SMSMessage


@pytest.mark.django_db
@patch("message_management.kafka_producer.producer")
def test_send_sms_to_kafka(mock_producer):
    sms_message = SMSMessage.objects.create(
        message_type=SMSMessage.MessageType.VERIFICATION_CODE,
        content="Test SMS content",
        phone="+71234567890",
    )

    send_sms_to_kafka(KafkaTopic.SMS_VERIFICATION, sms_message)

    sms_message.refresh_from_db()
    assert sms_message.status == SMSMessage.Status.SENT
    assert sms_message.updated_at <= timezone.now()

    mock_producer.produce.assert_called_once()

    args, kwargs = mock_producer.produce.call_args

    assert kwargs["topic"] == KafkaTopic.SMS_VERIFICATION.value
    assert kwargs["key"] == sms_message.phone
    payload = json.loads(kwargs["value"])

    assert payload["message_id"] == sms_message.id
    assert payload["phone"] == sms_message.phone
    assert payload["content"] == sms_message.content
    assert payload["retries"] == 5

    mock_producer.flush.assert_called_once()
