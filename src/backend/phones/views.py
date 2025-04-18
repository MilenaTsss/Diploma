from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser

from barriers.models import Barrier, UserBarrier
from core.pagination import BasePaginatedListView
from core.utils import created_response
from phones.models import BarrierPhone, TimeInterval
from phones.serializers import BarrierPhoneSerializer, CreateBarrierPhoneSerializer


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


# class UserBarrierPhoneUpdateView(generics.UpdateAPIView):
#     """Update phone of current user in a barrier"""
#
#     serializer_class = CreateBarrierPhoneSerializer  # можно создать отдельный UpdateSerializer при необходимости
#
#     def get_object(self):
#         user = self.request.user
#         barrier = get_object_or_404(Barrier, id=self.kwargs["barrier_id"], is_active=True)
#         phone = get_object_or_404(BarrierPhone, id=self.kwargs["phone_id"], user=user, barrier=barrier)
#
#         if not UserBarrier.user_has_access_to_barrier(user, barrier):
#             raise PermissionDenied("You don't have access to this barrier.")
#
#         return phone
#
#
# class UserBarrierPhoneDeleteView(generics.DestroyAPIView):
#     """Delete phone of current user in a barrier"""
#
#     def get_object(self):
#         user = self.request.user
#         barrier = get_object_or_404(Barrier, id=self.kwargs["barrier_id"], is_active=True)
#         phone = get_object_or_404(BarrierPhone, id=self.kwargs["phone_id"], user=user, barrier=barrier)
#
#         if not UserBarrier.user_has_access_to_barrier(user, barrier):
#             raise PermissionDenied("You don't have access to this barrier.")
#
#         return phone
#
#     def delete(self, request, *args, **kwargs):
#         phone = self.get_object()
#         phone.delete()  # soft delete если нужно — можно заменить на is_active = False
#         return deleted_response()
#
#
# @permission_classes([IsAdminUser])
# class AdminBarrierPhoneUpdateView(generics.UpdateAPIView):
#     """Admin updates a phone for user in own barrier"""
#
#     serializer_class = CreateBarrierPhoneSerializer
#
#     def get_object(self):
#         barrier = get_object_or_404(Barrier, id=self.kwargs["barrier_id"], is_active=True)
#         if barrier.owner != self.request.user:
#             raise PermissionDenied("You are not the owner of this barrier.")
#
#         return get_object_or_404(
#             BarrierPhone, id=self.kwargs["phone_id"], barrier=barrier, user_id=self.kwargs["user_id"]
#         )
#
#
# @permission_classes([IsAdminUser])
# class AdminBarrierPhoneDeleteView(generics.DestroyAPIView):
#     """Admin deletes phone of user in own barrier"""
#
#     def get_object(self):
#         barrier = get_object_or_404(Barrier, id=self.kwargs["barrier_id"], is_active=True)
#         if barrier.owner != self.request.user:
#             raise PermissionDenied("You are not the owner of this barrier.")
#
#         return get_object_or_404(
#             BarrierPhone, id=self.kwargs["phone_id"], barrier=barrier, user_id=self.kwargs["user_id"]
#         )
#
#     def delete(self, request, *args, **kwargs):
#         phone = self.get_object()
#         phone.delete()
#         return deleted_response()


# class BasePhoneScheduleView(generics.GenericAPIView):
#     serializer_class = PhoneScheduleSerializer
#
#     def get_phone(self):
#         barrier_id = self.kwargs["barrier_id"]
#         user_id = self.kwargs["user_id"]
#         phone_id = self.kwargs["phone_id"]
#         user = self.request.user
#
#         barrier = get_object_or_404(Barrier, id=barrier_id, is_active=True)
#         phone = get_object_or_404(BarrierPhone, id=phone_id, user_id=user_id, barrier=barrier)
#
#         if user.role == user.Role.ADMIN:
#             if barrier.owner != user:
#                 raise PermissionDenied("Not your barrier.")
#         else:
#             if user.id != user_id:
#                 raise PermissionDenied("Cannot access another user's phone.")
#
#         return phone
#
#     def get_object(self):
#         phone = self.get_phone()
#         return getattr(phone, "schedule", None)
#
#
# class PhoneScheduleRetrieveView(BasePhoneScheduleView, generics.RetrieveAPIView):
#     """GET /barriers/{barrier_id}/users/{user_id}/phones/{phone_id}/schedule/"""
#
#     def retrieve(self, request, *args, **kwargs):
#         schedule = self.get_object()
#         if not schedule:
#             raise NotFound("No schedule found for this phone.")
#         serializer = self.get_serializer(schedule)
#         return success_response(serializer.data)
#
#
# class PhoneScheduleUpdateView(BasePhoneScheduleView, generics.UpdateAPIView):
#     """PUT /barriers/{barrier_id}/users/{user_id}/phones/{phone_id}/schedule/"""
#
#     def update(self, request, *args, **kwargs):
#         phone = self.get_phone()
#         data = request.data.get("schedule")
#         if not data:
#             return success_response({"message": "Empty schedule submitted."})
#
#         schedule, _ = PhoneSchedule.objects.get_or_create(phone=phone)
#         serializer = self.get_serializer(schedule, data={"schedule": data}, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return success_response(serializer.data)
