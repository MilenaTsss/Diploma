from rest_framework import serializers

from access_requests.models import AccessRequest


class AccessRequestSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = AccessRequest
        fields = "__all__"

    def get_type(self, obj):
        """Determine request direction (incoming or outgoing) based on context"""

        as_admin = self.context.get("as_admin", False)

        if as_admin:
            return "outgoing" if obj.request_type == AccessRequest.RequestType.FROM_BARRIER else "incoming"
        else:
            return "outgoing" if obj.request_type == AccessRequest.RequestType.FROM_USER else "incoming"


class BaseCreateAccessRequestSerializer(serializers.ModelSerializer):
    """Base serializer for creating access requests with shared validation logic."""

    class Meta:
        model = AccessRequest
        fields = ["user", "barrier"]

    request_type: str  # This will be overridden in subclasses

    def validate(self, attrs):
        attrs["request_type"] = self.request_type

        current_user = self.context["request"].user
        user = attrs["user"]
        barrier = attrs["barrier"]

        if not self.request_type:
            raise NotImplementedError("Subclasses must set request_type")

        # Check for existing pending request
        if AccessRequest.objects.filter(user=user, barrier=barrier, status=AccessRequest.Status.PENDING).exists():
            raise serializers.ValidationError("An active request already exists for this user and barrier.")

        if not barrier.is_active:
            raise serializers.ValidationError("Cannot create access request for an inactive barrier.")

        if not user.is_active:
            raise serializers.ValidationError("Cannot create access request for an inactive user.")

        # Call specific validation hook
        self.run_custom_validation(current_user, user, barrier)

        return attrs

    def run_custom_validation(self, current_user, user, barrier):
        """Custom validation to be overridden by subclasses."""

        raise NotImplementedError("Subclasses must implement run_custom_validation()")


class CreateAccessRequestSerializer(BaseCreateAccessRequestSerializer):
    """Serializer for creating a new access request - by user"""

    request_type = AccessRequest.RequestType.FROM_USER

    def run_custom_validation(self, current_user, user, barrier):
        if not barrier.is_public:
            raise serializers.ValidationError("Cannot request access to a private barrier.")

        if user != current_user:
            raise serializers.ValidationError("Users can only create requests for themselves.")


class AdminCreateAccessRequestSerializer(BaseCreateAccessRequestSerializer):
    """Serializer for creating a new access request - by admin"""

    request_type = AccessRequest.RequestType.FROM_BARRIER

    def run_custom_validation(self, current_user, user, barrier):
        if barrier.owner != current_user:
            raise serializers.ValidationError("You are not the owner of this barrier.")
