from datetime import datetime
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied

from action_history.models import BarrierActionLog
from conftest import BARRIER_PERMANENT_PHONE, BARRIER_PERMANENT_PHONE_NAME, USER_PHONE
from core.utils import ConflictError
from phones.models import BarrierPhone, ScheduleTimeInterval


@pytest.mark.django_db
class TestBarrierPhoneModel:
    @pytest.fixture
    def create_barrier_phone_obj(self):
        """Factory fixture to create a barrier phone entry"""

        def _create_barrier_phone(
            user,
            barrier,
            phone=BARRIER_PERMANENT_PHONE,
            type=BarrierPhone.PhoneType.PERMANENT,
            name=BARRIER_PERMANENT_PHONE_NAME,
            device_serial_number=1,
            start_time=None,
            end_time=None,
        ):
            return BarrierPhone.objects.create(
                user=user,
                barrier=barrier,
                phone=phone,
                type=type,
                name=name,
                device_serial_number=device_serial_number,
                start_time=start_time,
                end_time=end_time,
            )

        return _create_barrier_phone

    def test_str(self, barrier_phone):
        phone, _ = barrier_phone
        assert str(phone) == f"Phone: {phone.phone} ({phone.user}, {phone.barrier})"

    class TestBarrierPhoneSerialNumber:
        def test_get_available_serial_number_returns_min_free(self, barrier, user, create_barrier_phone_obj):
            barrier.device_phones_amount = 4
            barrier.save()
            create_barrier_phone_obj(user, barrier)
            create_barrier_phone_obj(
                user, barrier, phone=USER_PHONE, type=BarrierPhone.PhoneType.PRIMARY, device_serial_number=3
            )

            assert BarrierPhone.get_available_serial_number(barrier) == 2

        def test_get_available_serial_number_returns_none(self, barrier, user, create_barrier_phone_obj):
            barrier.device_phones_amount = 2
            barrier.save()
            create_barrier_phone_obj(user, barrier)
            create_barrier_phone_obj(
                user, barrier, phone=USER_PHONE, type=BarrierPhone.PhoneType.PRIMARY, device_serial_number=2
            )

            assert BarrierPhone.get_available_serial_number(barrier) is None

    @pytest.mark.django_db
    class TestBarrierPhoneSendSMSCreate:
        @patch("message_management.services.SMSService.send_add_phone_command")
        def test_send_sms_to_create_primary_calls_sms(self, mock_send, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.PRIMARY
            phone.send_sms_to_create(log)
            mock_send.assert_called_once_with(phone, log)

        @patch("message_management.services.SMSService.send_add_phone_command")
        def test_send_sms_to_create_permanent_calls_sms(self, mock_send, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.PERMANENT
            phone.send_sms_to_create(log)
            mock_send.assert_called_once_with(phone, log)

        @patch("scheduler.task_manager.PhoneTaskManager")
        def test_send_sms_to_create_temporary_schedules_task(self, mock_task_manager_class, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.TEMPORARY

            mock_task_manager = mock_task_manager_class.return_value

            phone.send_sms_to_create(log)

            mock_task_manager_class.assert_called_once_with(phone, log)
            mock_task_manager.add_tasks.assert_called_once_with()

        @patch("scheduler.task_manager.PhoneTaskManager")
        def test_send_sms_to_create_schedule_schedules_task(self, mock_task_manager_class, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.SCHEDULE

            mock_task_manager = mock_task_manager_class.return_value

            phone.send_sms_to_create(log)

            mock_task_manager_class.assert_called_once_with(phone, log)
            mock_task_manager.add_tasks.assert_called_once_with()

    @pytest.mark.django_db
    class TestBarrierPhoneSendSMSDelete:
        @patch("message_management.services.SMSService.send_delete_phone_command")
        def test_send_sms_to_delete_primary_calls_sms(self, mock_send, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.PRIMARY
            phone.send_sms_to_delete(log)
            mock_send.assert_called_once_with(phone, log)

        @patch("message_management.services.SMSService.send_delete_phone_command")
        def test_send_sms_to_delete_permanent_calls_sms(self, mock_send, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.PERMANENT
            phone.send_sms_to_delete(log)
            mock_send.assert_called_once_with(phone, log)

        @patch("scheduler.task_manager.PhoneTaskManager.delete_tasks")
        def test_send_sms_to_delete_temporary_schedules_task(self, mock_delete_tasks, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.TEMPORARY
            phone.send_sms_to_delete(log)
            mock_delete_tasks.assert_called_once()

        @patch("scheduler.task_manager.PhoneTaskManager.delete_tasks")
        def test_send_sms_to_delete_schedule_schedules_task(self, mock_delete_tasks, barrier_phone):
            phone, log = barrier_phone
            phone.type = BarrierPhone.PhoneType.SCHEDULE
            phone.send_sms_to_delete(log)
            mock_delete_tasks.assert_called_once()

    class TestBarrierPhoneRemoval:
        def test_delete_raises_error(self, barrier_phone):
            phone, _ = barrier_phone
            with pytest.raises(PermissionDenied):
                phone.delete()

        def test_remove_sets_inactive(self, barrier_phone):
            phone, _ = barrier_phone
            phone.remove(author=BarrierActionLog.Author.USER, reason=BarrierActionLog.Reason.BARRIER_EXIT)
            assert not phone.is_active

        def test_remove_creates_log_and_deactivates(self, barrier_phone):
            phone, _ = barrier_phone
            phone.is_active = True
            phone.save()

            phone, log = phone.remove(author=BarrierActionLog.Author.USER, reason=BarrierActionLog.Reason.BARRIER_EXIT)

            assert not phone.is_active
            assert log.phone == phone
            assert log.reason == BarrierActionLog.Reason.BARRIER_EXIT
            assert log.action_type == BarrierActionLog.ActionType.DELETE_PHONE

    class TestBarrierPhoneCreate:
        def test_create_duplicate_phone_raises(self, user, barrier):
            BarrierPhone.create(
                user=user, barrier=barrier, phone=BARRIER_PERMANENT_PHONE, type=BarrierPhone.PhoneType.PERMANENT
            )
            with pytest.raises(ConflictError) as exc:
                BarrierPhone.create(
                    user=user, barrier=barrier, phone=BARRIER_PERMANENT_PHONE, type=BarrierPhone.PhoneType.PERMANENT
                )
            assert exc.value.detail == "Phone already exists for this user in the barrier."

        def test_create_primary_duplicate_raises(self, user, barrier):
            BarrierPhone.create(user=user, barrier=barrier, phone=user.phone, type=BarrierPhone.PhoneType.PRIMARY)
            with pytest.raises(ConflictError) as exc:
                BarrierPhone.create(user=user, barrier=barrier, phone=user.phone, type=BarrierPhone.PhoneType.PRIMARY)
            assert str(exc.value)

        def test_create_primary_with_wrong_number_raises(self, user, barrier):
            with pytest.raises(DRFPermissionDenied) as exc:
                BarrierPhone.create(
                    user=user, barrier=barrier, phone=BARRIER_PERMANENT_PHONE, type=BarrierPhone.PhoneType.PRIMARY
                )
            assert exc.value.detail == "Wrong phone given as primary. Primary phone should be users main number."

        @patch("phones.models.validate_limits")
        @patch("phones.models.validate_schedule_phone")
        @patch("phones.models.validate_temporary_phone")
        def test_validators_called(self, mock_temp, mock_sched, mock_limits, user, barrier):
            BarrierPhone.create(
                user=user, barrier=barrier, phone=BARRIER_PERMANENT_PHONE, type=BarrierPhone.PhoneType.PERMANENT
            )
            mock_limits.assert_called_once_with(BarrierPhone.PhoneType.PERMANENT, barrier, user)
            mock_temp.assert_called_once_with(BarrierPhone.PhoneType.PERMANENT, None, None)
            mock_sched.assert_called_once_with(BarrierPhone.PhoneType.PERMANENT, None, barrier)

        def test_create_fails_without_serial(self, user, barrier):
            barrier.device_phones_amount = 0
            barrier.save()
            with pytest.raises(ConflictError) as exc:
                BarrierPhone.create(user=user, barrier=barrier, phone=user.phone, type=BarrierPhone.PhoneType.PRIMARY)
            assert exc.value.detail == "Barrier has reached the maximum number of phone numbers."

        def test_create_schedule_creates_intervals(self, user, barrier):
            schedule = {
                "monday": [
                    {
                        "start_time": datetime.strptime("09:00", "%H:%M").time(),
                        "end_time": datetime.strptime("10:00", "%H:%M").time(),
                    }
                ]
            }
            phone, log = BarrierPhone.create(
                user=user,
                barrier=barrier,
                phone=BARRIER_PERMANENT_PHONE,
                type=BarrierPhone.PhoneType.SCHEDULE,
                schedule=schedule,
                author=BarrierActionLog.Author.SYSTEM,
                reason=BarrierActionLog.Reason.MANUAL,
            )

            assert ScheduleTimeInterval.objects.filter(phone=phone).exists()
            assert log.phone == phone
            assert log.barrier == barrier
            assert log.author == BarrierActionLog.Author.SYSTEM
            assert log.action_type == BarrierActionLog.ActionType.ADD_PHONE
            assert log.reason == BarrierActionLog.Reason.MANUAL
            assert "schedule=" in log.new_value
