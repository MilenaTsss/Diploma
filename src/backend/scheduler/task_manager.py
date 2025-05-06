import logging
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils.timezone import now

from phones.constants import MINIMUM_TIME_INTERVAL_MINUTES
from phones.models import BarrierPhone, ScheduleTimeInterval
from scheduler.jobs import schedule_cron_sms, schedule_once_sms
from scheduler.scheduler import get_scheduler
from scheduler.utils import JobAction, generate_job_id, parse_job_id

logger = logging.getLogger(__name__)

DELETE_PHONE_AFTER_SCHEDULING_MINUTES = 20


class PhoneTaskManager:
    def __init__(self, phone: BarrierPhone):
        self.phone = phone
        self.scheduler = get_scheduler()

    def add_tasks(self):
        if self.phone.type == BarrierPhone.PhoneType.TEMPORARY:
            self._schedule_temporary_tasks()
        elif self.phone.type == BarrierPhone.PhoneType.SCHEDULE:
            self._schedule_schedule_tasks()

    def edit_tasks(self):
        self.cancel_all_tasks()
        self._close_if_not_allowed_now()
        self.add_tasks()

    def delete_tasks(self):
        self.cancel_all_tasks()
        self._close_if_not_allowed_now()

    def cancel_all_tasks(self):
        logger.info(f"Cancelling all tasks for phone: {self.phone.id}")

        for job in self.scheduler.get_jobs():
            try:
                job_meta = parse_job_id(job.id)
            except ValidationError:
                continue
            if job_meta["phone_id"] == self.phone.id:
                self.scheduler.remove_job(job.id)

    def _close_if_not_allowed_now(self):
        from message_management.services import SMSService

        logger.info(f"Closing access if editing schedule phone: {self.phone.id}")

        current_dt = now()
        current_time = current_dt.replace(second=0, microsecond=0).time()
        current_weekday = current_dt.strftime("%A").lower()

        if self.phone.type == BarrierPhone.PhoneType.SCHEDULE:
            active_intervals = self.phone.schedule_intervals.filter(day=current_weekday)
            for interval in active_intervals:
                if interval.start_time <= current_time <= interval.end_time:
                    return  # Access is currently valid — don't close
            SMSService.send_delete_phone_command(self.phone)

    def _schedule_temporary_tasks(self):
        logger.info(f"Scheduling temporary tasks for phone: {self.phone.id}")

        if not self.phone.start_time or not self.phone.end_time:
            raise ValidationError("Temporary phones must have both start_time and end_time.")

        open_time = self.phone.start_time - timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES - 1)
        open_job_id = generate_job_id(JobAction.OPEN, self.phone.id, BarrierPhone.PhoneType.TEMPORARY)
        schedule_once_sms(self.phone, JobAction.OPEN, open_job_id, run_time=open_time)

        close_job_id = generate_job_id(JobAction.CLOSE, self.phone.id, BarrierPhone.PhoneType.TEMPORARY)
        schedule_once_sms(self.phone, JobAction.CLOSE, close_job_id, run_time=self.phone.end_time)

        delete_time = self.phone.end_time + timedelta(minutes=DELETE_PHONE_AFTER_SCHEDULING_MINUTES)
        delete_job_id = generate_job_id(JobAction.DELETE, self.phone.id, BarrierPhone.PhoneType.TEMPORARY)
        schedule_once_sms(self.phone, JobAction.DELETE, delete_job_id, run_time=delete_time)

    def _schedule_schedule_tasks(self):
        logger.info(f"Scheduling schedule tasks for phone: {self.phone.id}")

        def _shift_day_back(day: str) -> str:
            days = list(ScheduleTimeInterval.DayOfWeek.values)
            idx = days.index(day)
            return days[(idx - 1) % 7]

        for interval in self.phone.schedule_intervals.all():
            day = interval.day

            open_time = (
                datetime.combine(datetime.today(), interval.start_time)
                - timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES - 1)
            ).time()
            open_day = _shift_day_back(day) if open_time > interval.start_time else day
            open_job_id = generate_job_id(
                JobAction.OPEN, self.phone.id, BarrierPhone.PhoneType.SCHEDULE, day=open_day, time_=open_time
            )
            schedule_cron_sms(self.phone, JobAction.OPEN, open_job_id, day=open_day, time_=open_time)

            close_time = interval.end_time

            close_job_id = generate_job_id(
                JobAction.CLOSE, self.phone.id, BarrierPhone.PhoneType.SCHEDULE, day=day, time_=close_time
            )
            schedule_cron_sms(self.phone, JobAction.CLOSE, close_job_id, day=day, time_=close_time)
