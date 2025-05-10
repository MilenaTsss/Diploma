from django.http import Http404
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAdminUser

from barriers.models import Barrier, UserBarrier
from core.pagination import BasePaginatedListView
from message_management.models import SMSMessage
from message_management.serializers import SMSMessageSerializer


def get_barrier(user, barrier_id, as_admin):
    try:
        barrier = Barrier.objects.get(id=barrier_id)
    except Barrier.DoesNotExist:
        raise NotFound("Barrier not found.")

    if as_admin and barrier.owner != user:
        raise PermissionDenied("You do not have access to this barrier.")
    if not as_admin and not UserBarrier.user_has_access_to_barrier(user, barrier):
        raise PermissionDenied("You do not have access to this barrier.")

    return barrier


class BaseSMSMessageListView(BasePaginatedListView):
    serializer_class = SMSMessageSerializer
    pagination_response_key = "sms"

    DEFAULT_ORDERING = ["-updated_at"]
    ALLOWED_ORDERING_FIELDS = {
        "message_type",
        "phone_command_type",
        "status",
        "sent_at",
        "updated_at",
        "log__phone",
        "log__created_at",
    }

    lookup_field = "id"

    as_admin = False

    def get_queryset(self):
        user = self.request.user
        barrier = get_barrier(user, self.kwargs["id"], self.as_admin)

        ordering = self.request.query_params.get("ordering", "").strip()
        ordering_fields = [f.strip() for f in ordering.split(",") if f.strip()]
        safe_ordering = [f for f in ordering_fields if f.lstrip("-") in self.ALLOWED_ORDERING_FIELDS]
        if not safe_ordering:
            safe_ordering = self.DEFAULT_ORDERING

        queryset = SMSMessage.objects.filter(log__barrier=barrier).exclude(
            message_type=SMSMessage.MessageType.VERIFICATION_CODE
        )

        if not self.as_admin:
            queryset = queryset.filter(log__phone__user=user, message_type=SMSMessage.MessageType.PHONE_COMMAND)

        phone_id = self.request.query_params.get("phone", "").strip()
        if phone_id and phone_id.isdigit():
            queryset = queryset.filter(log__phone_id=int(phone_id))

        log_id = self.request.query_params.get("log", "").strip()
        if log_id and log_id.isdigit():
            queryset = queryset.filter(log_id=log_id)

        message_type = self.request.query_params.get("message_type", "").strip()
        if message_type:
            queryset = queryset.filter(message_type=message_type)

        phone_command_type = self.request.query_params.get("phone_command_type", "").strip()
        if phone_command_type:
            queryset = queryset.filter(phone_command_type=phone_command_type)

        status = self.request.query_params.get("status", "").strip()
        if status:
            queryset = queryset.filter(status=status)

        sent_from = self.request.query_params.get("sent_from", "").strip()
        if sent_from:
            dt = parse_datetime(sent_from)
            if dt:
                queryset = queryset.filter(sent_at__gte=dt)

        sent_to = self.request.query_params.get("sent_to", "").strip()
        if sent_to:
            dt = parse_datetime(sent_to)
            if dt:
                queryset = queryset.filter(sent_at__lte=dt)

        updated_from = self.request.query_params.get("updated_from", "").strip()
        if updated_from:
            dt = parse_datetime(updated_from)
            if dt:
                queryset = queryset.filter(updated_at__gte=dt)

        updated_to = self.request.query_params.get("updated_to", "").strip()
        if updated_to:
            dt = parse_datetime(updated_to)
            if dt:
                queryset = queryset.filter(updated_at__lte=dt)

        return queryset.order_by(*safe_ordering)


class UserSMSMessageListView(BaseSMSMessageListView):
    as_admin = False


@permission_classes([IsAdminUser])
class AdminSMSMessageListView(BaseSMSMessageListView):
    as_admin = True


class BaseSMSMessageDetailView(RetrieveAPIView):
    serializer_class = SMSMessageSerializer
    lookup_field = "id"
    as_admin = False

    def get_queryset(self):
        return SMSMessage.objects.all()

    def get_object(self):
        try:
            sms = super().get_object()
        except Http404:
            raise NotFound("Sms message not found.")
        user = self.request.user
        log = sms.log

        if not log:
            raise NotFound("You do not have access to this SMS.")

        barrier = log.barrier
        phone = log.phone

        if self.as_admin and barrier.owner != user:
            raise PermissionDenied("You do not have access to this SMS.")
        if not self.as_admin:
            if not phone or phone.user != user:
                raise PermissionDenied("You do not have access to this SMS.")
            if sms.message_type == SMSMessage.MessageType.BARRIER_SETTING:
                raise PermissionDenied("You do not have access to this SMS.")

        return sms


class UserSMSMessageDetailView(BaseSMSMessageDetailView):
    as_admin = False


@permission_classes([IsAdminUser])
class AdminSMSMessageDetailView(BaseSMSMessageDetailView):
    as_admin = True
