from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError

from conftest import BARRIER_SCHEDULE_PHONE
from phones.constants import MINIMUM_TIME_INTERVAL_MINUTES
from phones.models import BarrierPhone
from scheduler.task_manager import DELETE_PHONE_AFTER_SCHEDULING_MINUTES, PhoneTaskManager
from scheduler.utils import JobAction


@pytest.mark.django_db
class TestAddTasks:
    @patch("scheduler.task_manager.schedule_once_sms")
    def test_temporary_phone(self, mock_schedule_once_sms, temporary_barrier_phone):
        manager = PhoneTaskManager(temporary_barrier_phone)
        manager.add_tasks()

        assert mock_schedule_once_sms.call_count == 3  # open, close, delete
        actions = [call.args[1] for call in mock_schedule_once_sms.call_args_list]
        assert JobAction.OPEN in actions
        assert JobAction.CLOSE in actions
        assert JobAction.DELETE in actions

    @patch("scheduler.task_manager.schedule_cron_sms")
    def test_schedule_phone(self, mock_schedule_cron_sms, schedule_barrier_phone):
        manager = PhoneTaskManager(schedule_barrier_phone)
        manager.add_tasks()

        assert mock_schedule_cron_sms.call_count == 4
        actions = [call.args[1] for call in mock_schedule_cron_sms.call_args_list]
        assert actions.count(JobAction.OPEN) == 2
        assert actions.count(JobAction.CLOSE) == 2


@pytest.mark.django_db
class TestEditTasks:
    @patch.object(PhoneTaskManager, "cancel_all_tasks")
    @patch.object(PhoneTaskManager, "add_tasks")
    @patch.object(PhoneTaskManager, "_close_if_not_allowed_now")
    def test_edit_flow(self, mock_close, mock_add, mock_cancel, temporary_barrier_phone):
        manager = PhoneTaskManager(temporary_barrier_phone)
        manager.edit_tasks()

        mock_cancel.assert_called_once()
        mock_close.assert_called_once()
        mock_add.assert_called_once()


@pytest.mark.django_db
class TestDeleteTasks:
    @patch.object(PhoneTaskManager, "cancel_all_tasks")
    @patch.object(PhoneTaskManager, "_close_if_not_allowed_now")
    def test_delete_flow(self, mock_close, mock_cancel, temporary_barrier_phone):
        manager = PhoneTaskManager(temporary_barrier_phone)
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
        job1 = type("Job", (), {"id": f"temporary_open_{temporary_barrier_phone.id}"})()
        job2 = type("Job", (), {"id": f"temporary_close_{temporary_barrier_phone.id}"})()
        scheduler_mock.get_jobs.return_value = [job1, job2]

        manager = PhoneTaskManager(temporary_barrier_phone)
        manager.scheduler = scheduler_mock

        manager.cancel_all_tasks()

        scheduler_mock.remove_job.assert_any_call(job1.id)
        scheduler_mock.remove_job.assert_any_call(job2.id)


@pytest.mark.django_db
class TestCloseIfNotAllowedNow:
    @patch("scheduler.task_manager.now")
    @patch("message_management.services.SMSService.send_delete_phone_command")
    def test_outside_interval(self, mock_send_sms, mock_now, create_barrier_phone, user, barrier):
        fixed_now = datetime(2025, 5, 5, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        mock_now.return_value = fixed_now

        schedule = {"monday": [{"start_time": time(15, 55), "end_time": time(18, 5)}]}
        phone = create_barrier_phone(
            user, barrier, BARRIER_SCHEDULE_PHONE, BarrierPhone.PhoneType.SCHEDULE, schedule=schedule
        )
        manager = PhoneTaskManager(phone)

        manager._close_if_not_allowed_now()

        mock_send_sms.assert_called_once_with(phone)

    @patch("scheduler.task_manager.now")
    @patch("message_management.services.SMSService.send_delete_phone_command")
    def test_inside_interval(self, mock_send_sms, mock_now, create_barrier_phone, user, barrier):
        fixed_now = datetime(2025, 5, 5, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        mock_now.return_value = fixed_now

        schedule = {"monday": [{"start_time": time(11, 55), "end_time": time(12, 5)}]}
        phone = create_barrier_phone(
            user, barrier, BARRIER_SCHEDULE_PHONE, BarrierPhone.PhoneType.SCHEDULE, schedule=schedule
        )
        manager = PhoneTaskManager(phone)

        manager._close_if_not_allowed_now()

        mock_send_sms.assert_not_called()


@pytest.mark.django_db
class TestScheduleTemporaryTasks:
    @patch("scheduler.task_manager.schedule_once_sms")
    def test_schedules_all_tasks_with_correct_times(self, mock_schedule_once_sms, temporary_barrier_phone):
        start_time = temporary_barrier_phone.start_time
        end_time = temporary_barrier_phone.end_time
        open_expected = start_time - timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES - 1)
        delete_expected = end_time + timedelta(minutes=DELETE_PHONE_AFTER_SCHEDULING_MINUTES)

        manager = PhoneTaskManager(temporary_barrier_phone)
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
        temporary_barrier_phone.start_time = None
        temporary_barrier_phone.end_time = None

        manager = PhoneTaskManager(temporary_barrier_phone)
        with pytest.raises(ValidationError, match="Temporary phones must have both start_time and end_time."):
            manager._schedule_temporary_tasks()


@pytest.mark.django_db
class TestScheduleScheduleTasks:
    @patch("scheduler.task_manager.schedule_cron_sms")
    def test_schedules_cron_tasks_with_shift(self, mock_schedule_cron_sms, create_barrier_phone, user, barrier):
        schedule = {"monday": [{"start_time": time(0, 1), "end_time": time(1, 0)}]}
        phone = create_barrier_phone(
            user, barrier, "BARRIER_SCHEDULE_PHONE", BarrierPhone.PhoneType.SCHEDULE, schedule=schedule
        )

        manager = PhoneTaskManager(phone)
        manager._schedule_schedule_tasks()

        assert mock_schedule_cron_sms.call_count == 2
        actions = [call.args[1] for call in mock_schedule_cron_sms.call_args_list]
        assert JobAction.OPEN in actions
        assert JobAction.CLOSE in actions

    @patch("scheduler.task_manager.schedule_cron_sms")
    def test_schedules_cron_tasks_without_shift(self, mock_schedule_cron_sms, create_barrier_phone, user, barrier):
        schedule = {"monday": [{"start_time": time(12, 0), "end_time": time(13, 0)}]}
        phone = create_barrier_phone(
            user, barrier, "BARRIER_SCHEDULE_PHONE", BarrierPhone.PhoneType.SCHEDULE, schedule=schedule
        )

        manager = PhoneTaskManager(phone)
        manager._schedule_schedule_tasks()

        assert mock_schedule_cron_sms.call_count == 2
        actions = [call.args[1] for call in mock_schedule_cron_sms.call_args_list]
        assert JobAction.OPEN in actions
        assert JobAction.CLOSE in actions
