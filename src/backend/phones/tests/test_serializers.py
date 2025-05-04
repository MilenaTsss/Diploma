from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils.timezone import now
from rest_framework.exceptions import NotFound, PermissionDenied

from conftest import BARRIER_PERMANENT_PHONE
from phones.constants import MINIMUM_TIME_INTERVAL_MINUTES
from phones.models import BarrierPhone
from phones.serializers import (
    CreateBarrierPhoneSerializer,
    ScheduleSerializer,
    ScheduleTimeIntervalSerializer,
    UpdateBarrierPhoneSerializer,
    UpdatePhoneScheduleSerializer,
)


@pytest.mark.django_db
class TestScheduleTimeIntervalSerializer:
    def test_valid_interval(self):
        data = {"start_time": time(9, 0), "end_time": time(10, 0)}
        serializer = ScheduleTimeIntervalSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_start_time_after_end_time(self):
        data = {"start_time": time(12, 0), "end_time": time(11, 0)}
        serializer = ScheduleTimeIntervalSerializer(data=data)

        assert not serializer.is_valid()
        assert serializer.errors["time"][0] == "start_time must be earlier than end_time."

    def test_interval_too_short(self):
        start = time(10, 0)
        end = (datetime.combine(date.today(), start) + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES - 1)).time()
        data = {"start_time": start, "end_time": end}
        serializer = ScheduleTimeIntervalSerializer(data=data)

        assert not serializer.is_valid()
        expected = f"Interval must be at least {MINIMUM_TIME_INTERVAL_MINUTES} minutes long."
        assert serializer.errors["time"][0] == expected


@pytest.mark.django_db
class TestScheduleSerializer:
    def test_valid_schedule(self):
        data = {
            "monday": [
                {"start_time": time(9, 0), "end_time": time(10, 0)},
                {"start_time": time(10, 40), "end_time": time(11, 20)},
            ]
        }
        serializer = ScheduleSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_overlapping_intervals(self):
        data = {
            "tuesday": [
                {"start_time": time(9, 0), "end_time": time(10, 0)},
                {"start_time": time(9, 50), "end_time": time(11, 0)},
            ]
        }
        serializer = ScheduleSerializer(data=data)
        assert not serializer.is_valid()
        expected = "Intervals on tuesday overlap: '09:00:00–10:00:00 and 09:50:00–11:00:00'"
        assert serializer.errors["schedule"][0] == expected

    def test_gap_too_small_between_intervals(self):
        gap = MINIMUM_TIME_INTERVAL_MINUTES - 1
        data = {
            "wednesday": [
                {"start_time": time(9, 0), "end_time": time(10, 0)},
                {"start_time": time(10, gap), "end_time": time(11, 0)},
            ]
        }
        serializer = ScheduleSerializer(data=data)
        assert not serializer.is_valid()
        expected = (
            f"Intervals on wednesday must have at least {MINIMUM_TIME_INTERVAL_MINUTES} minutes between them: "
            f"'09:00:00–10:00:00 and 10:{gap}:00–11:00:00'"
        )
        assert serializer.errors["schedule"][0] == expected

    def test_empty_days_are_filled_on_output(self):
        data = {
            "friday": [
                {"start_time": time(8, 0), "end_time": time(9, 0)},
            ]
        }
        serializer = ScheduleSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        output = serializer.to_representation(serializer.validated_data)
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            assert day in output


@pytest.mark.django_db
class TestCreateBarrierPhoneSerializer:
    def test_valid_data_as_admin(self, admin_user, user, barrier):
        context = {"request": type("Request", (), {"user": admin_user})(), "as_admin": True, "barrier": barrier}
        data = {
            "phone": BARRIER_PERMANENT_PHONE,
            "type": BarrierPhone.PhoneType.PERMANENT,
            "name": "Test",
            "user": user.id,
        }
        serializer = CreateBarrierPhoneSerializer(data=data, context=context)
        assert serializer.is_valid(), serializer.errors

    def test_auto_assign_user_for_regular(self, user, barrier):
        context = {"request": type("Request", (), {"user": user})(), "as_admin": False, "barrier": barrier}
        data = {
            "phone": BARRIER_PERMANENT_PHONE,
            "type": BarrierPhone.PhoneType.PERMANENT,
            "name": "Test",
        }
        serializer = CreateBarrierPhoneSerializer(data=data, context=context)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"] == user

    def test_missing_user_for_admin(self, admin_user, barrier):
        context = {"request": type("Request", (), {"user": admin_user})(), "as_admin": True, "barrier": barrier}
        data = {
            "phone": BARRIER_PERMANENT_PHONE,
            "type": BarrierPhone.PhoneType.PERMANENT,
            "name": "Test",
        }
        serializer = CreateBarrierPhoneSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert serializer.errors["user"][0] == "This field is required."

    def test_user_not_found_raises_not_found(self, admin_user, barrier):
        context = {"request": type("Request", (), {"user": admin_user})(), "as_admin": True, "barrier": barrier}
        data = {
            "phone": BARRIER_PERMANENT_PHONE,
            "type": BarrierPhone.PhoneType.PERMANENT,
            "name": "Test",
            "user": 99999,
        }
        serializer = CreateBarrierPhoneSerializer(data=data, context=context)
        with pytest.raises(NotFound):
            serializer.is_valid(raise_exception=True)

    @patch("phones.serializers.BarrierPhone.create")
    def test_create_calls_model_create_and_sends_sms(self, mock_create, admin_user, user, barrier):
        mock_instance = MagicMock()
        mock_create.return_value = mock_instance

        context = {"request": type("Request", (), {"user": admin_user})(), "as_admin": True, "barrier": barrier}
        data = {
            "phone": BARRIER_PERMANENT_PHONE,
            "type": BarrierPhone.PhoneType.PERMANENT,
            "name": "Test",
            "user": user.id,
        }

        serializer = CreateBarrierPhoneSerializer(data=data, context=context)
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        mock_create.assert_called_once_with(
            user=user,
            barrier=barrier,
            phone=data["phone"],
            type=data["type"],
            name=data["name"],
            start_time=None,
            end_time=None,
            schedule=None,
        )
        mock_instance.send_sms_to_create.assert_called_once()


@pytest.mark.django_db
class TestUpdateBarrierPhoneSerializer:
    def test_valid_update_with_name_only(self, temporary_barrier_phone):
        serializer = UpdateBarrierPhoneSerializer(
            instance=temporary_barrier_phone,
            data={"name": "Just name"},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

    def test_valid_update_with_time(self, temporary_barrier_phone):
        serializer = UpdateBarrierPhoneSerializer(
            instance=temporary_barrier_phone,
            data={
                "name": "Updated Name",
                "start_time": now() + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES + 1),
                "end_time": now() + timedelta(hours=10),
            },
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

    def test_partial_time_update_start_only(self, temporary_barrier_phone):
        serializer = UpdateBarrierPhoneSerializer(
            instance=temporary_barrier_phone,
            data={"start_time": now() + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES + 10)},
            partial=True,
        )
        assert not serializer.is_valid()
        assert (
            serializer.errors["time"][0]
            == "Both start_time and end_time must be provided while updating temporary phones."
        )

    def test_temporary_phone_update_too_late(self, temporary_barrier_phone):
        temporary_barrier_phone.start_time = now()
        temporary_barrier_phone.save()

        serializer = UpdateBarrierPhoneSerializer(
            instance=temporary_barrier_phone,
            data={
                "start_time": now() + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES + 1),
                "end_time": now() + timedelta(hours=10),
            },
            partial=True,
        )
        with pytest.raises(PermissionDenied) as exc:
            serializer.is_valid(raise_exception=True)
        expected = (
            f"Temporary phone number cannot be updated less than "
            f"{MINIMUM_TIME_INTERVAL_MINUTES} minutes before start."
        )
        assert exc.value.detail == expected

    @patch("phones.serializers.validate_temporary_phone")
    def test_validation_function_called_when_both_times_provided(self, mock_validate, temporary_barrier_phone):
        start = now() + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES + 1)
        end = start + timedelta(hours=1)
        serializer = UpdateBarrierPhoneSerializer(
            instance=temporary_barrier_phone,
            data={"start_time": start, "end_time": end},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        mock_validate.assert_called_once_with(BarrierPhone.PhoneType.TEMPORARY, start, end)


@pytest.mark.django_db
class TestUpdatePhoneScheduleSerializer:
    def test_valid_update(self, schedule_barrier_phone):
        data = {
            "monday": [{"start_time": time(9, 0), "end_time": time(10, 0)}],
            "tuesday": [{"start_time": time(11, 0), "end_time": time(12, 0)}],
        }
        serializer = UpdatePhoneScheduleSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        with (
            patch("phones.serializers.ScheduleTimeInterval.replace_schedule") as mock_replace,
            patch("phones.serializers.validate_schedule_phone") as mock_validate,
        ):
            result = serializer.update(schedule_barrier_phone, serializer.validated_data)

        mock_validate.assert_called_once_with(
            schedule_barrier_phone.type, serializer.validated_data, schedule_barrier_phone.barrier
        )
        mock_replace.assert_called_once_with(schedule_barrier_phone, serializer.validated_data)
        assert result == schedule_barrier_phone
