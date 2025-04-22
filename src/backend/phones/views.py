from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser

from barriers.models import Barrier, UserBarrier
from core.pagination import BasePaginatedListView
from core.utils import created_response
from phones.models import BarrierPhone
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


# TODO - fix barrier phone detail view
# class BaseBarrierPhoneDetailView(RetrieveUpdateDestroyAPIView):
#     """Base view for retrieving, updating, and deactivating a phone"""
#
#     queryset = BarrierPhone.objects.filter(is_active=True)
#     serializer_class = BarrierPhoneSerializer
#     lookup_field = "id"
#     as_admin = False
#
#     # TODO - remove or not
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context["as_admin"] = self.as_admin
#         return context
#
#     def get_object(self):
#         phone = super().get_object()
#         user = self.request.user
#
#         if self.as_admin and phone.barrier.owner != user or not self.as_admin and phone.user != user:
#             raise PermissionDenied("You don't have access to this phone.")
#
#         return phone
#
#     def patch(self, request, *args, **kwargs):
#         phone = self.get_object()
#         data = request.data
#
#         name = data.get("name")
#         start_time = data.get("start_time")
#         end_time = data.get("end_time")
#
#         if name is not None:
#             phone.name = name
#
#         if phone.type == BarrierPhone.PhoneType.TEMPORARY:
#             if start_time is not None:
#                 phone.start_time = start_time
#             if end_time is not None:
#                 phone.end_time = end_time
#             try:
#                 validate_temporary_phone(phone.type, phone.start_time, phone.end_time)
#             except DjangoValidationError as e:
#                 raise DRFValidationError(getattr(e, "message_dict", {"error": str(e)}))
#         elif start_time or end_time:
#             raise DRFValidationError({"error": "start_time and end_time can only be changed for temporary phones."})
#
#         phone.save()
#         return success_response(BarrierPhoneSerializer(phone).data)
#
#     def put(self, request, *args, **kwargs):
#         raise MethodNotAllowed("PUT")
#
#     def delete(self, request, *args, **kwargs):
#         phone = self.get_object()
#         phone.is_active = False
#         phone.save()
#         return success_response({"status": "Phone deactivated."})
#
#
# class UserBarrierPhoneDetailView(BaseBarrierPhoneDetailView):
#     """User can view, update or deactivate their own phone"""
#
#     as_admin = False
#
#
# @permission_classes([IsAdminUser])
# class AdminBarrierPhoneDetailView(BaseBarrierPhoneDetailView):
#     """Admin can view, update or deactivate any phone in their barriers"""
#
#     as_admin = True


# TODO - fix barrier phone schedule view
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
