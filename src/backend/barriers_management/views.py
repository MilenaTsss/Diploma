import logging

from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from barriers.models import Barrier, BarrierLimit
from barriers.serializers import BarrierLimitSerializer
from barriers_management.serializers import (
    AdminBarrierSerializer,
    CreateBarrierSerializer,
    UpdateBarrierLimitSerializer,
    UpdateBarrierSerializer,
)
from core.pagination import BasePaginatedListView

logger = logging.getLogger(__name__)


@permission_classes([IsAdminUser])
class CreateBarrierView(generics.CreateAPIView):
    """Create a new barrier (admin only)."""

    queryset = Barrier.objects.all()
    serializer_class = CreateBarrierSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        barrier = serializer.save()
        BarrierLimit.objects.create(barrier=barrier)

    def create(self, request, *args, **kwargs):
        """Use a different serializer for the response"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = AdminBarrierSerializer(serializer.instance, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@permission_classes([IsAdminUser])
class MyAdminBarrierListView(BasePaginatedListView):
    """Get a list of barriers managed by the current admin"""

    serializer_class = AdminBarrierSerializer
    pagination_response_key = "barriers"

    ALLOWED_ORDERING_FIELDS = {"address", "created_at", "updated_at"}
    DEFAULT_ORDERING = "address"

    def get_queryset(self):
        """
        Use the `ordering` query parameter to sort results.
        Prefix with `-` for descending order (e.g., ?ordering=-created_at for newest first),
        or use the field name directly for ascending order (e.g., ?ordering=created_at for oldest first).
        """

        ordering = self.request.query_params.get("ordering", self.DEFAULT_ORDERING)
        if ordering.lstrip("-") not in self.ALLOWED_ORDERING_FIELDS:
            ordering = self.DEFAULT_ORDERING

        queryset = Barrier.objects.filter(owner=self.request.user, is_active=True)

        return queryset.order_by(ordering)


@permission_classes([IsAdminUser])
class AdminBarrierView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a barrier by ID (admin only)."""

    queryset = Barrier.objects.filter(is_active=True)
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UpdateBarrierSerializer
        return AdminBarrierSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_object(self):
        """Add explicit permission check and better 403 response"""

        barrier = super().get_object()
        if barrier.owner != self.request.user:
            raise PermissionDenied(detail="You do not have permission to access this barrier.")

        return barrier

    def patch(self, request, *args, **kwargs):
        """Update barrier fields (partial update)"""

        barrier = self.get_object()
        serializer = self.get_serializer(barrier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminBarrierSerializer(barrier).data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Mark the barrier as inactive (soft delete)"""

        barrier = self.get_object()
        barrier.is_active = False
        barrier.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")


@permission_classes([IsAdminUser])
class AdminBarrierLimitUpdateView(generics.UpdateAPIView):
    """Update or create limits for a barrier (admins only)"""

    serializer_class = UpdateBarrierLimitSerializer
    queryset = Barrier.objects.filter(is_active=True)
    lookup_field = "id"

    def get_object(self):
        barrier = super().get_object()

        if barrier.owner != self.request.user:
            raise PermissionDenied("You are not the owner of this barrier.")

        limit, _ = BarrierLimit.objects.get_or_create(barrier=barrier)
        return limit

    def patch(self, request, *args, **kwargs):
        limit = self.get_object()
        serializer = self.get_serializer(limit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(BarrierLimitSerializer(limit).data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")
