import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models

from barriers.models import Barrier
from core.constants import CHOICE_MAX_LENGTH, PHONE_MAX_LENGTH, STRING_MAX_LENGTH
from core.validators import PhoneNumberValidator
from phones.validators import validate_limits, validate_schedule_phone, validate_temporary_phone
from users.models import User

logger = logging.getLogger(__name__)


class BarrierPhone(models.Model):
    """Model to store phone numbers associated with barriers"""

    class Meta:
        db_table = "barrier_phone"

    class PhoneType(models.TextChoices):
        PRIMARY = "primary", "Primary"
        PERMANENT = "permanent", "Permanent"
        TEMPORARY = "temporary", "Temporary"
        SCHEDULE = "schedule", "Schedule"

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="barrier_phones",
        help_text="User who owns this phone number.",
    )

    barrier = models.ForeignKey(
        Barrier,
        on_delete=models.PROTECT,
        related_name="barrier_phones",
        help_text="Barrier where this phone number is registered.",
    )

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        db_index=True,
        validators=[PhoneNumberValidator()],
        null=False,
        blank=False,
        help_text="Enter a phone number in the format +7XXXXXXXXXX.",
    )

    type = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=PhoneType.choices)

    name = models.CharField(max_length=STRING_MAX_LENGTH, blank=True, default="")

    device_serial_number = models.PositiveIntegerField(
        null=False, blank=False, help_text="Index of this phone in the barrier's device memory."
    )

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # TODO - add a field to track the status and the last action performed with this phone
    # class Status(models.TextChoices):
    #     ACTIVE = "active", "Active"
    #     ADDING = "adding", "Adding"
    #     ADD_FAILED = "add_failed", "Add failed"
    #     REMOVING = "removing", "Removing"
    #     REMOVED = "removed", "Removed"
    #     REMOVE_FAILED = "remove_failed", "Remove failed"
    #
    # status = models.CharField(
    #     max_length=CHOICE_MAX_LENGTH,
    #     choices=Status.choices,
    #     default=Status.ACTIVE,
    # )
    # last_action = models.ForeignKey(
    #     "ActionHistory",
    #     null=True, blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="related_phones"
    # )

    def __str__(self):
        return f"Phone: {self.phone} ({self.user}, {self.barrier})"

    @staticmethod
    def get_available_serial_number(barrier):
        """
        Returns the first available serial number for a phone in the given barrier.
        If all slots are occupied, returns None.
        """

        existing_numbers = set(
            BarrierPhone.objects.filter(
                barrier=barrier,
                is_active=True,
            ).values_list("device_serial_number", flat=True)
        )

        all_numbers = set(range(1, barrier.device_phones_amount + 1))
        free_numbers = all_numbers - existing_numbers

        return min(free_numbers) if free_numbers else None

    @classmethod
    def create(cls, *, user, barrier, phone, type, name="", start_time=None, end_time=None, schedule=None):
        """Creates a new BarrierPhone instance with validation and optional schedule."""

        if cls.objects.filter(user=user, barrier=barrier, phone=phone, is_active=True).exists():
            raise ValidationError("This phone number already exists for this user in the barrier.")
        if type == cls.PhoneType.PRIMARY:
            if cls.objects.filter(user=user, barrier=barrier, type=cls.PhoneType.PRIMARY, is_active=True).exists():
                raise ValidationError("User already has a primary phone number in this barrier.")

        validate_limits(type, barrier, user)
        validate_temporary_phone(type, start_time, end_time)
        validate_schedule_phone(type, schedule, barrier)

        if (serial_number := cls.get_available_serial_number(barrier)) is None:
            raise ValidationError("Barrier has reached the maximum number of phone numbers.")

        phone_instance = cls.objects.create(
            user=user,
            barrier=barrier,
            phone=phone,
            type=type,
            name=name,
            start_time=start_time,
            end_time=end_time,
            device_serial_number=serial_number,
        )

        if type == cls.PhoneType.SCHEDULE and schedule:
            ScheduleTimeInterval.create_schedule(phone_instance, schedule)

        return phone_instance

    def send_sms_to_create(self):
        from message_management.services import SMSService

        # TODO - else schedule
        if self.type == self.PhoneType.PRIMARY or self.PhoneType.PERMANENT:
            SMSService.send_add_phone_command(self)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Deletion of this object is not allowed.")

    def remove(self, *args, **kwargs):
        """Deactivate the phone and send a delete SMS command."""

        if not self.is_active:
            logger.warning("Attempt to remove an already inactive phone.")
            return

        self.is_active = False
        self.save()

        from message_management.services import SMSService

        if self.type == self.PhoneType.PRIMARY or self.type == self.PhoneType.PERMANENT:
            SMSService.send_delete_phone_command(self)
        # TODO - else schedule


class ScheduleTimeInterval(models.Model):
    """Model to store schedule intervals for barrier phones"""

    class Meta:
        db_table = "phone_schedule_time_interval"
        ordering = ["day", "start_time"]
        unique_together = ("phone", "day", "start_time", "end_time")

    class DayOfWeek(models.TextChoices):
        MONDAY = "monday", "Monday"
        TUESDAY = "tuesday", "Tuesday"
        WEDNESDAY = "wednesday", "Wednesday"
        THURSDAY = "thursday", "Thursday"
        FRIDAY = "friday", "Friday"
        SATURDAY = "saturday", "Saturday"
        SUNDAY = "sunday", "Sunday"

    phone = models.ForeignKey(
        BarrierPhone,
        on_delete=models.CASCADE,
        related_name="schedule_intervals",
        help_text="Phone to which this interval belongs",
    )

    day = models.CharField(max_length=CHOICE_MAX_LENGTH, choices=DayOfWeek.choices)
    start_time = models.TimeField(help_text="Start time in HH:MM")
    end_time = models.TimeField(help_text="End time in HH:MM")

    def __str__(self):
        return f"'{self.phone.phone}': {self.day} {self.start_time}-{self.end_time}"

    @classmethod
    def create_schedule(cls, phone, schedule_data):
        """Creates schedule intervals for a phone."""

        intervals = []
        for day, day_intervals in schedule_data.items():
            for interval in day_intervals:
                intervals.append(
                    cls(phone=phone, day=day, start_time=interval["start_time"], end_time=interval["end_time"])
                )

        cls.objects.bulk_create(intervals)

    @classmethod
    def replace_schedule(cls, phone, schedule_data):
        cls.objects.filter(phone=phone).delete()
        cls.create_schedule(phone, schedule_data)

    @classmethod
    def get_schedule_grouped_by_day(cls, phone):
        """Returns a grouped schedule for the given phone."""

        intervals = cls.objects.filter(phone=phone).order_by("day", "start_time")
        grouped = {day: [] for day in cls.DayOfWeek.values}
        for interval in intervals:
            grouped[interval.day].append(
                {
                    "start_time": interval.start_time,
                    "end_time": interval.end_time,
                }
            )
        return grouped
