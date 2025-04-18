from django.db import models

from barriers.models import Barrier
from core.constants import CHOICE_MAX_LENGTH, PHONE_MAX_LENGTH, STRING_MAX_LENGTH
from core.validators import PhoneNumberValidator
from users.models import User


class BarrierPhone(models.Model):
    """Model to store phone numbers associated with barriers"""

    class Meta:
        db_table = "barrier_phone"
        unique_together = ("user", "barrier", "phone")

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

        for num in range(1, barrier.device_phones_amount + 1):
            if num not in existing_numbers:
                return num

        return None


class TimeInterval(models.Model):
    """Model to store schedule intervals for barrier phones"""

    class Meta:
        db_table = "phone_schedule_interval"
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
        cls.objects.filter(phone=phone, day__in=schedule_data.keys()).delete()
        cls.create_schedule(phone, schedule_data)
