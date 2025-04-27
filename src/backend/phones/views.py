from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import MethodNotAllowed, NotFound, PermissionDenied
from rest_framework.generics import RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser

from barriers.models import Barrier, UserBarrier
from core.pagination import BasePaginatedListView
from core.utils import created_response, success_response
from phones.models import BarrierPhone, ScheduleTimeInterval
from phones.serializers import (
    BarrierPhoneSerializer,
    CreateBarrierPhoneSerializer,
    ScheduleSerializer,
    UpdateBarrierPhoneSerializer,
    UpdatePhoneScheduleSerializer,
)


def get_barrier(user, barrier_id, as_admin):
    barrier = get_object_or_404(Barrier, id=barrier_id, is_active=True)

    if as_admin and barrier.owner != user:
        raise PermissionDenied("You are not the owner of this barrier.")
    if not as_admin and not UserBarrier.user_has_access_to_barrier(user, barrier):
        raise PermissionDenied("You don't have access to this barrier.")

    return barrier


class BaseCreateBarrierPhoneView(generics.CreateAPIView):
    """Base view for creating access requests"""

    serializer_class = CreateBarrierPhoneSerializer
    as_admin = False

    def get_serializer_context(self):
        """Pass request to serializer for access to current user."""

        context = super().get_serializer_context()
        context.update(
            {
                "request": self.request,
                "as_admin": self.as_admin,
                "barrier": get_barrier(self.request.user, self.kwargs["id"], self.as_admin),
            }
        )
        return context

    def perform_create(self, serializer):
        barrier = get_barrier(self.request.user, self.kwargs["id"], self.as_admin)

        if self.as_admin:
            user = serializer.validated_data["user"]
        else:
            user = self.request.user

        serializer.save(user=user, barrier=barrier)

    def create(self, request, *args, **kwargs):
        """Handle access request creation and return proper response."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = BarrierPhoneSerializer(serializer.instance, context=self.get_serializer_context())
        return created_response(response_serializer.data)


class UserCreateBarrierPhoneView(BaseCreateBarrierPhoneView):
    """Create a new access request (by user)."""

    as_admin = False


@permission_classes([IsAdminUser])
class AdminCreateBarrierPhoneView(BaseCreateBarrierPhoneView):
    """Create a new access request (by admin)."""

    as_admin = True


class BaseBarrierPhoneListView(BasePaginatedListView):
    """Base view for listing phones in barrier with filtering and sorting for user or admin"""

    serializer_class = BarrierPhoneSerializer
    pagination_response_key = "phones"

    DEFAULT_ORDERING = "phone"
    ALLOWED_ORDERING_FIELDS = {"phone", "name", "type"}

    lookup_field = "id"

    as_admin = False

    def get_queryset(self):
        user = self.request.user
        barrier = get_barrier(user, self.kwargs["id"], self.as_admin)

        ordering = self.request.query_params.get("ordering", self.DEFAULT_ORDERING)
        if ordering.lstrip("-") not in self.ALLOWED_ORDERING_FIELDS:
            ordering = self.DEFAULT_ORDERING

        queryset = BarrierPhone.objects.filter(barrier=barrier, is_active=True)

        if self.as_admin:
            user_id = self.request.query_params.get("user")
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:
            queryset = queryset.filter(user=user)

        # Optional filters
        phone_filter = self.request.query_params.get("phone", "").strip()
        if phone_filter:
            queryset = queryset.filter(phone__icontains=phone_filter)

        name_filter = self.request.query_params.get("name", "").strip()
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        type_filter = self.request.query_params.get("type", "").strip()
        if type_filter in BarrierPhone.PhoneType.values:
            queryset = queryset.filter(type=type_filter)

        return queryset.order_by(ordering)


class UserBarrierPhoneListView(BaseBarrierPhoneListView):
    """List phones of current user in a barrier"""

    as_admin = False


@permission_classes([IsAdminUser])
class AdminBarrierPhoneListView(BaseBarrierPhoneListView):
    """List phones of any user in admin's barrier"""

    as_admin = True


class BaseBarrierPhoneDetailView(RetrieveUpdateDestroyAPIView):
    """Base view for retrieving, updating, and deactivating a phone"""

    queryset = BarrierPhone.objects.filter(is_active=True)
    serializer_class = BarrierPhoneSerializer
    lookup_field = "id"
    as_admin = False

    def get_object(self):
        phone = super().get_object()
        user = self.request.user

        if self.as_admin and phone.barrier.owner != user or not self.as_admin and phone.user != user:
            raise PermissionDenied("You don't have access to this phone.")

        return phone

    def patch(self, request, *args, **kwargs):
        phone = self.get_object()
        serializer = UpdateBarrierPhoneSerializer(phone, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(BarrierPhoneSerializer(phone).data)

    def put(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")

    def delete(self, request, *args, **kwargs):
        phone = self.get_object()

        if phone.type == BarrierPhone.PhoneType.PRIMARY:
            raise PermissionDenied("Primary phone number cannot be deleted.")

        phone.remove()
        return success_response({"status": "Phone deleted."})


class UserBarrierPhoneDetailView(BaseBarrierPhoneDetailView):
    """User can view, update or deactivate their own phone"""

    as_admin = False


@permission_classes([IsAdminUser])
class AdminBarrierPhoneDetailView(BaseBarrierPhoneDetailView):
    """Admin can view, update or deactivate any phone in their barriers"""

    as_admin = True


class BaseBarrierPhoneScheduleView(RetrieveUpdateAPIView):
    """Base view for retrieving and updating a phone schedule"""

    serializer_class = UpdatePhoneScheduleSerializer
    lookup_field = "id"
    as_admin = False

    def get_phone(self):
        phone_id = self.kwargs["id"]
        phone = BarrierPhone.objects.filter(id=phone_id, is_active=True).first()
        if not phone:
            raise NotFound("Phone not found.")

        user = self.request.user
        if self.as_admin and phone.barrier.owner != user or not self.as_admin and phone.user != user:
            raise PermissionDenied("You don't have access to this phone.")

        return phone

    def get(self, request, *args, **kwargs):
        phone = self.get_phone()
        schedule = ScheduleTimeInterval.get_schedule_grouped_by_day(phone)

        return success_response(ScheduleSerializer(schedule).data)

    def put(self, request, *args, **kwargs):
        phone = self.get_phone()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(phone, serializer.validated_data)

        grouped_schedule = ScheduleTimeInterval.get_schedule_grouped_by_day(phone)

        return success_response(ScheduleSerializer(grouped_schedule).data)

    def patch(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH")


class UserBarrierPhoneScheduleView(BaseBarrierPhoneScheduleView):
    """User can view and update their own phone schedule"""

    as_admin = False


@permission_classes([IsAdminUser])
class AdminBarrierPhoneScheduleView(BaseBarrierPhoneScheduleView):
    """Admin can view and update phone schedule for phones in their barriers."""

    as_admin = True
