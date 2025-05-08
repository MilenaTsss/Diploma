from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError

from conftest import BARRIER_SCHEDULE_PHONE, BARRIER_TEMPORARY_PHONE
from phones.constants import MINIMUM_TIME_INTERVAL_MINUTES
from phones.models import BarrierPhone
from scheduler.task_manager import ACCESS_OPENING_SHIFT, DELETE_PHONE_AFTER_SCHEDULING_MINUTES, PhoneTaskManager
from scheduler.utils import JobAction


@pytest.mark.django_db
class TestAddTasks:
    @patch("scheduler.task_manager.schedule_once_sms")
    def test_temporary_phone(self, mock_schedule_once_sms, temporary_barrier_phone):
        phone, log = temporary_barrier_phone
        manager = PhoneTaskManager(phone, log)
        manager.add_tasks()

        assert mock_schedule_once_sms.call_count == 3  # open, close, delete
        actions = [call.args[1] for call in mock_schedule_once_sms.call_args_list]
        assert JobAction.OPEN in actions
        assert JobAction.CLOSE in actions
        assert JobAction.DELETE in actions

    @patch("scheduler.task_manager.schedule_cron_sms")
    def test_schedule_phone(self, mock_schedule_cron_sms, schedule_barrier_phone):
        phone, log = schedule_barrier_phone
        manager = PhoneTaskManager(phone, log)
        manager.add_tasks()

        assert mock_schedule_cron_sms.call_count == 4
        actions = [call.args[1] for call in mock_schedule_cron_sms.call_args_list]
        assert actions.count(JobAction.OPEN) == 2
        assert actions.count(JobAction.CLOSE) == 2


@pytest.mark.django_db
class TestEditTasks:
    @patch.object(PhoneTaskManager, "cancel_all_tasks")
    @patch.object(PhoneTaskManager, "_schedule_temporary_tasks")
    @patch.object(PhoneTaskManager, "sync_access")
    def test_edit_flow(self, mock_sync, mock_schedule, mock_cancel, temporary_barrier_phone):
        phone, log = temporary_barrier_phone
        manager = PhoneTaskManager(phone, log)
        manager.edit_tasks()

        mock_cancel.assert_called_once()
        mock_sync.assert_called_once_with("edit")
        mock_schedule.assert_called_once()


@pytest.mark.django_db
class TestDeleteTasks:
    @patch.object(PhoneTaskManager, "cancel_all_tasks")
    @patch.object(PhoneTaskManager, "sync_access")
    def test_delete_flow(self, mock_close, mock_cancel, temporary_barrier_phone):
        phone, log = temporary_barrier_phone
        manager = PhoneTaskManager(phone, log)
        manager.delete_tasks()

        mock_cancel.assert_called_once()
        mock_close.assert_called_once()


@pytest.mark.django_db
class TestCancelAllTasks:
    @pytest.fixture
    def scheduler_mock(self):
        scheduler = MagicMock()
        with patch("scheduler.task_manager.get_scheduler", return_value=scheduler):
            yield scheduler

    def test_removes_matching_jobs(self, scheduler_mock, temporary_barrier_phone):
        phone, log = temporary_barrier_phone
        job1 = type("Job", (), {"id": f"temporary_open_{phone.id}"})()
        job2 = type("Job", (), {"id": f"temporary_close_{phone.id}"})()
        scheduler_mock.get_jobs.return_value = [job1, job2]

        manager = PhoneTaskManager(phone, log)
        manager.scheduler = scheduler_mock

        manager.cancel_all_tasks()

        scheduler_mock.remove_job.assert_any_call(job1.id)
        scheduler_mock.remove_job.assert_any_call(job2.id)


@pytest.mark.django_db
class TestSyncAccess:
    @patch("scheduler.task_manager.now")
    @patch("phones.validators.now")
    @patch("message_management.services.SMSService.send_add_phone_command")
    @patch("message_management.services.SMSService.send_delete_phone_command")
    @pytest.mark.parametrize(
        "phone_type,mode,in_interval,expect_add,expect_delete",
        [
            # Schedule phone
            (BarrierPhone.PhoneType.SCHEDULE, "add", True, True, False),
            (BarrierPhone.PhoneType.SCHEDULE, "add", False, False, False),
            (BarrierPhone.PhoneType.SCHEDULE, "edit", True, True, False),
            (BarrierPhone.PhoneType.SCHEDULE, "edit", False, False, True),
            (BarrierPhone.PhoneType.SCHEDULE, "delete", True, False, True),
            (BarrierPhone.PhoneType.SCHEDULE, "delete", False, False, False),
            # Temporary phone
            (BarrierPhone.PhoneType.TEMPORARY, "add", False, False, False),
            (BarrierPhone.PhoneType.TEMPORARY, "edit", False, False, True),
            (BarrierPhone.PhoneType.TEMPORARY, "delete", True, False, True),
            (BarrierPhone.PhoneType.TEMPORARY, "delete", False, False, False),
        ],
    )
    def test_schedule_phone_sync_access(
        self,
        mock_send_delete,
        mock_send_add,
        mock_now_scheduler,
        mock_now_phones,
        create_barrier_phone,
        user,
        barrier,
        phone_type,
        mode,
        in_interval,
        expect_add,
        expect_delete,
    ):
        fixed_now = datetime(2025, 5, 5, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        mock_now_scheduler.return_value = fixed_now
        mock_now_phones.return_value = fixed_now

        if phone_type == BarrierPhone.PhoneType.SCHEDULE:
            schedule = {
                "monday": (
                    [{"start_time": time(11, 55), "end_time": time(12, 5)}]
                    if in_interval
                    else [{"start_time": time(15, 0), "end_time": time(16, 0)}]
                )
            }
            phone, log = create_barrier_phone(user, barrier, BARRIER_SCHEDULE_PHONE, phone_type, schedule=schedule)
        else:
            start_time = fixed_now + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES + 1)
            end_time = start_time + timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES)

            phone, log = create_barrier_phone(
                user, barrier, phone=BARRIER_TEMPORARY_PHONE, type=phone_type, start_time=start_time, end_time=end_time
            )

            if in_interval:
                fixed_now = datetime(2025, 5, 5, 12, 2, tzinfo=ZoneInfo("Europe/Moscow"))
                mock_now_scheduler.return_value = fixed_now
                mock_now_phones.return_value = fixed_now

        manager = PhoneTaskManager(phone, log)

        manager.sync_access(mode)

        if expect_add:
            mock_send_add.assert_called_once_with(phone, log)
        else:
            mock_send_add.assert_not_called()

        if expect_delete:
            mock_send_delete.assert_called_once_with(phone, log)
        else:
            mock_send_delete.assert_not_called()


@pytest.mark.django_db
class TestScheduleTemporaryTasks:
    @patch("scheduler.task_manager.schedule_once_sms")
    def test_schedules_all_tasks_with_correct_times(self, mock_schedule_once_sms, temporary_barrier_phone):
        phone, log = temporary_barrier_phone
        start_time = phone.start_time
        end_time = phone.end_time
        open_expected = start_time - ACCESS_OPENING_SHIFT
        delete_expected = end_time + timedelta(minutes=DELETE_PHONE_AFTER_SCHEDULING_MINUTES)

        manager = PhoneTaskManager(phone, log)
        manager._schedule_temporary_tasks()

        assert mock_schedule_once_sms.call_count == 3

        expected = {
            JobAction.OPEN: open_expected,
            JobAction.CLOSE: end_time,
            JobAction.DELETE: delete_expected,
        }

        for call in mock_schedule_once_sms.call_args_list:
            action = call.args[1]
            run_time = call.kwargs["run_time"]
            expected_msg = f"{action} has wrong run_time: expected {expected[action]}, got {run_time}"
            assert run_time == expected[action], expected_msg

    @patch("scheduler.task_manager.schedule_once_sms")
    def test_raises_if_start_or_end_time_missing(self, mock_schedule_once_sms, temporary_barrier_phone):
        phone, log = temporary_barrier_phone
        phone.start_time = None
        phone.end_time = None

        manager = PhoneTaskManager(phone, log)
        with pytest.raises(ValidationError, match="Temporary phones must have both start_time and end_time."):
            manager._schedule_temporary_tasks()


@pytest.mark.django_db
class TestScheduleScheduleTasks:
    @patch("scheduler.task_manager.schedule_cron_sms")
    def test_schedules_cron_tasks_with_shift(self, mock_schedule_cron_sms, create_barrier_phone, user, barrier):
        schedule = {"monday": [{"start_time": time(0, 1), "end_time": time(1, 0)}]}
        phone, log = create_barrier_phone(
            user, barrier, "BARRIER_SCHEDULE_PHONE", BarrierPhone.PhoneType.SCHEDULE, schedule=schedule
        )

        manager = PhoneTaskManager(phone, log)
        manager._schedule_schedule_tasks()

        assert mock_schedule_cron_sms.call_count == 2
        actions = [call.args[1] for call in mock_schedule_cron_sms.call_args_list]
        assert JobAction.OPEN in actions
        assert JobAction.CLOSE in actions

    @patch("scheduler.task_manager.schedule_cron_sms")
    def test_schedules_cron_tasks_without_shift(self, mock_schedule_cron_sms, create_barrier_phone, user, barrier):
        schedule = {"monday": [{"start_time": time(12, 0), "end_time": time(13, 0)}]}
        phone, log = create_barrier_phone(
            user, barrier, "BARRIER_SCHEDULE_PHONE", BarrierPhone.PhoneType.SCHEDULE, schedule=schedule
        )

        manager = PhoneTaskManager(phone, log)
        manager._schedule_schedule_tasks()

        assert mock_schedule_cron_sms.call_count == 2
        actions = [call.args[1] for call in mock_schedule_cron_sms.call_args_list]
        assert JobAction.OPEN in actions
        assert JobAction.CLOSE in actions
