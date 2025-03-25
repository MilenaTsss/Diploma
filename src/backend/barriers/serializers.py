from rest_framework import serializers
from barriers.models import Barrier
from users.models import User


class BarrierSerializer(serializers.ModelSerializer):
    """Сериализатор шлагбаумов с учетом приватности данных"""

    owner = serializers.SerializerMethodField()
    device_phone = serializers.SerializerMethodField()

    class Meta:
        model = Barrier
        fields = ["id", "address", "owner", "is_active", "device_phone", "additional_info"]

    def get_owner(self, obj):
        """Возвращает владельца с учетом `phone_privacy`"""

        if not obj.owner:
            return None

        # request = self.context.get("request")
        # request_user = request.user
        owner_data = {
            "id": obj.owner.id,
            "full_name": obj.owner.full_name,
            "phone": None,  # По умолчанию не показываем номер
        }

        # Если телефон публичный — показываем
        if obj.owner.phone_privacy == User.PhonePrivacy.PUBLIC:
            owner_data["phone"] = obj.owner.phone
        elif obj.owner.phone_privacy == User.PhonePrivacy.PROTECTED:
            # TODO Проверяем связь между пользователем и шлагбаумом
            owner_data["phone"] = obj.owner.phone

        return owner_data


    def get_device_phone(self, obj):
        """Проверяет можно ли показывать device_phone"""

        # request = self.context.get("request")
        # request_user = request.user

        # TODO Проверяем, есть ли связь между пользователем и шлагбаумом
        return obj.device_phone  # Показываем номер устройства

        # return None  # По умолчанию скрываем
