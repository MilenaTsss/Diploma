from rest_framework import serializers

from barriers.models import Barrier
from barriers.validators import DevicePasswordValidator


class AdminBarrierSerializer(serializers.ModelSerializer):
    """Serializer for viewing a barrier from the admin's perspective"""

    class Meta:
        model = Barrier
        exclude = ("device_password",)


class CreateBarrierSerializer(serializers.ModelSerializer):
    """Serializer for creating a new barrier"""

    additional_info = serializers.CharField(required=True, allow_blank=True)
    device_phones_amount = serializers.IntegerField(required=True)

    class Meta:
        model = Barrier
        fields = [
            "address",
            "device_phone",
            "device_model",
            "device_phones_amount",
            "device_password",
            "additional_info",
            "is_public",
        ]

    def validate_address(self, value):
        """Convert the address to lowercase"""

        return value.lower().strip()

    def validate_device_phone(self, value):
        """Check if a device with the given phone number already exists"""

        if Barrier.objects.filter(device_phone=value).exists():
            raise serializers.ValidationError("A barrier with this phone number already exists.")
        return value

    def validate_device_phones_amount(self, value):
        """Ensure `device_phones_amount` is greater than 0"""

        if value <= 0:
            raise serializers.ValidationError("The number of device phone slots must be greater than 0.")
        return value

    def validate(self, attrs):
        """Conditional password validation based on device model"""

        model = attrs["device_model"]
        password = attrs.get("device_password")

        if model != Barrier.Model.TELEMETRICA:
            if not password:
                raise serializers.ValidationError({"device_password": "This field is required for this device model."})

            DevicePasswordValidator()(password)

        return attrs

    def create(self, validated_data):
        """Create a barrier and automatically assign the current user as the owner"""

        request = self.context["request"]
        validated_data["owner"] = request.user
        return super().create(validated_data)


class UpdateBarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        # TODO - how to change password? there need to be stop for sms when password changes!
        fields = ["device_password", "additional_info", "is_public"]
