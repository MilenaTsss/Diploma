from rest_framework import serializers
from barriers.models import Barrier


class AdminBarrierSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра шлагбаума со стороны админа"""

    owner_id = serializers.IntegerField(source="owner.id")

    class Meta:
        model = Barrier
        fields = [
            "id", "address", "owner_id", "device_phone", "device_model", "device_phones_amount",
            "additional_info", "is_public", "is_active"
        ]


class CreateBarrierSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового шлагбаума"""

    is_public = serializers.BooleanField(required=True)
    additional_info = serializers.CharField(required=True, allow_blank=True)
    device_phones_amount = serializers.IntegerField(required=True)

    class Meta:
        model = Barrier
        fields = [
            "address", "device_phone", "device_model", "device_phones_amount",
            "device_password", "additional_info", "is_public"
        ]

    def validate_address(self, value):
        """Приводим адрес к нижнему регистру"""

        return value.lower().strip()

    def validate_device_phone(self, value):
        """Проверяем, существует ли уже устройство с таким номером"""

        if Barrier.objects.filter(device_phone=value).exists():
            raise serializers.ValidationError("Шлагбаум с таким номером телефона уже существует.")
        return value

    def validate_device_phones_amount(self, value):
        """Проверка, что `device_phones_amount` больше 0"""

        if value <= 0:
            raise serializers.ValidationError("Количество номеров в устройстве должно быть больше 0.")
        return value

    def create(self, validated_data):
        """Создаёт шлагбаум и автоматически назначает владельцем текущего пользователя"""

        request = self.context["request"]
        validated_data["owner"] = request.user
        return super().create(validated_data)


class UpdateBarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        # TODO - как менять пароль? нужно как-то запретить изменения на время
        #  сделать так чтобы все запросы отработали и только после этого менять пароль
        #  ну или ничего не делать, но всё блин может сломаться
        fields = ["device_password", "additional_info", "is_public"]
