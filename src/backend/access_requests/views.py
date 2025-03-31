import logging

from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from access_requests.models import AccessRequest
from access_requests.serializers import (
    AccessRequestSerializer,
    AdminCreateAccessRequestSerializer,
    CreateAccessRequestSerializer,
)

logger = logging.getLogger(__name__)


class BaseCreateAccessRequestView(generics.CreateAPIView):
    """Base view for creating access requests"""

    queryset = AccessRequest.objects.all()

    def get_serializer_context(self):
        """Pass request to serializer for access to current user."""

        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        """Handle access request creation and return proper response."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Check as_admin - true if it is instance of AdminCreate
        as_admin = isinstance(self, AdminCreateAccessRequestView)

        response_serializer = AccessRequestSerializer(
            serializer.instance, context={**self.get_serializer_context(), "as_admin": as_admin}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CreateAccessRequestView(BaseCreateAccessRequestView):
    """Create a new access request (by user)."""

    serializer_class = CreateAccessRequestSerializer


@permission_classes([IsAdminUser])
class AdminCreateAccessRequestView(BaseCreateAccessRequestView):
    """Create a new access request (by admin)."""

    serializer_class = AdminCreateAccessRequestSerializer
