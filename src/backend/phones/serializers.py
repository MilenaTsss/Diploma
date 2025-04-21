from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from phones.constants import MINIMUM_TIME_INTERVAL_MINUTES
from phones.models import BarrierPhone, TimeInterval
from users.models import User


class BarrierPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPhone
        exclude = ["device_serial_number", "is_active"]


class TimeIntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeInterval
        fields = ["start_time", "end_time"]

    def validate(self, attrs):
        start = attrs["start_time"]
        end = attrs["end_time"]

        if start >= end:
            raise serializers.ValidationError({"error": "start_time must be earlier than end_time."})

        duration = datetime.combine(date.today(), end) - datetime.combine(date.today(), start)
        if duration < timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES):
            message = f"Interval must be at least {MINIMUM_TIME_INTERVAL_MINUTES} minutes long."
            raise serializers.ValidationError({"error": message})

        return attrs


class ScheduleSerializer(serializers.Serializer):
    monday = TimeIntervalSerializer(many=True, required=False)
    tuesday = TimeIntervalSerializer(many=True, required=False)
    wednesday = TimeIntervalSerializer(many=True, required=False)
    thursday = TimeIntervalSerializer(many=True, required=False)
    friday = TimeIntervalSerializer(many=True, required=False)
    saturday = TimeIntervalSerializer(many=True, required=False)
    sunday = TimeIntervalSerializer(many=True, required=False)

    @staticmethod
    def validate_intervals(day, intervals):
        if not intervals:
            return

        sorted_intervals = sorted(intervals, key=lambda i: i["start_time"])
        for i in range(1, len(sorted_intervals)):
            prev = sorted_intervals[i - 1]
            curr = sorted_intervals[i]
            if curr["start_time"] <= prev["end_time"]:
                message = (
                    f"Intervals on {day} overlap: "
                    f"'{prev['start_time']}–{prev['end_time']} and {curr['start_time']}–{curr['end_time']}'"
                )
                raise serializers.ValidationError({"error": message})

            prev_end = datetime.combine(date.today(), prev["end_time"])
            curr_start = datetime.combine(date.today(), curr["start_time"])
            gap = curr_start - prev_end
            if gap < timedelta(minutes=MINIMUM_TIME_INTERVAL_MINUTES):
                message = (
                    f"Intervals on {day} must have at least {MINIMUM_TIME_INTERVAL_MINUTES} minutes between them: "
                    f"'{prev['start_time']}–{prev['end_time']} and {curr['start_time']}–{curr['end_time']}'"
                )
                raise serializers.ValidationError({"error": message})

    def validate(self, attrs):
        for day, intervals in attrs.items():
            self.validate_intervals(day, intervals)
        return attrs

    def to_representation(self, instance):
        result = super().to_representation(instance)

        for day in TimeInterval.DayOfWeek.values:
            result.setdefault(day, [])

        return result


class CreateBarrierPhoneSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        write_only=True,
        help_text="User for whom the phone is being created (required for admins).",
    )

    schedule = ScheduleSerializer(required=False, write_only=True)

    class Meta:
        model = BarrierPhone
        fields = ["phone", "type", "name", "start_time", "end_time", "user", "schedule"]

    def validate(self, attrs):
        request = self.context["request"]
        as_admin = self.context.get("as_admin", False)
        barrier = self.context.get("barrier")

        if not barrier:
            raise serializers.ValidationError("Barrier context is required.")

        if as_admin:
            user = attrs.get("user")
            if not user:
                raise serializers.ValidationError({"user": "This field is required for admins."})
        else:
            user = request.user

        attrs["user"] = user
        attrs["barrier"] = barrier

        # if (serial := BarrierPhone.get_available_serial_number(barrier)) is None:
        #     raise serializers.ValidationError({"error": "Cannot add phone: all slots are occupied."})
        # attrs["device_serial_number"] = serial
        #
        # phone_type = attrs.get("type")
        # schedule = attrs.get("schedule")  # TODO self.initial_data.get("schedule")
        # validate_temporary_phone(phone_type, attrs.get("start_time"), attrs.get("end_time"))
        # validate_schedule_phone(phone_type, schedule, barrier)
        # validate_limits(phone_type, barrier, user)

        return attrs

    # def create(self, validated_data):
    #     schedule_data = validated_data.pop("schedule", None)
    #     phone = super().create(validated_data)
    #
    #     if schedule_data:
    #         TimeInterval.create_schedule(phone, schedule_data)
    #
    #     return phone

    def create(self, validated_data):
        schedule_data = validated_data.pop("schedule", None)
        try:
            return BarrierPhone.create(
                user=validated_data["user"],
                barrier=validated_data["barrier"],
                phone=validated_data["phone"],
                type=validated_data["type"],
                name=validated_data.get("name", ""),
                start_time=validated_data.get("start_time"),
                end_time=validated_data.get("end_time"),
                schedule=schedule_data,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(getattr(e, "message_dict", {"error": str(e)}))


class UpdatePhoneScheduleSerializer(ScheduleSerializer):
    """Partial update of schedule: only update the days that were explicitly passed."""

    # TODO - check everything
    def update(self, phone: BarrierPhone, validated_data):
        TimeInterval.replace_schedule(phone, validated_data)
        return phone
