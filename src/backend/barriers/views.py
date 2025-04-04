from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from barriers.models import Barrier, UserBarrier
from barriers.serializers import BarrierLimitSerializer, BarrierSerializer
from core.pagination import BasePaginatedListView


class ListBarriersView(BasePaginatedListView):
    """List all public barriers with search by address, ordering, pagination"""

    serializer_class = BarrierSerializer
    pagination_response_key = "barriers"

    ALLOWED_ORDERING_FIELDS = {"address"}
    DEFAULT_ORDERING = "address"

    def get_queryset(self):
        """
        Use the `ordering` query parameter to sort results.
        """

        ordering = self.request.query_params.get("ordering", self.DEFAULT_ORDERING)
        if ordering.lstrip("-") not in self.ALLOWED_ORDERING_FIELDS:
            ordering = self.DEFAULT_ORDERING

        queryset = Barrier.objects.filter(is_public=True, is_active=True)
        address = self.request.query_params.get("address", "").strip()
        if address:
            queryset = queryset.filter(Q(address__icontains=address.lower()))

        return queryset.order_by(ordering)


class MyBarriersListView(BasePaginatedListView):
    """Retrieve a list of barriers accessible by the current user"""

    serializer_class = BarrierSerializer
    pagination_response_key = "barriers"

    ALLOWED_ORDERING_FIELDS = {"address"}
    DEFAULT_ORDERING = "address"

    def get_queryset(self):
        """
        Use the `ordering` query parameter to sort results.
        """

        ordering = self.request.query_params.get("ordering", self.DEFAULT_ORDERING)
        if ordering.lstrip("-") not in self.ALLOWED_ORDERING_FIELDS:
            ordering = self.DEFAULT_ORDERING

        queryset = Barrier.objects.filter(users_access__user=self.request.user, is_active=True)

        return queryset.order_by(ordering)


class BarrierView(generics.RetrieveAPIView):
    """
    Retrieve detailed information about a single barrier by ID.
    Accessible only if the barrier is public or the user has access.
    """

    serializer_class = BarrierSerializer
    queryset = Barrier.objects.filter(is_active=True)
    lookup_field = "id"

    def get_object(self):
        barrier = super().get_object()
        user = self.request.user

        if barrier.is_public or (UserBarrier.user_has_access_to_barrier(user, barrier)):
            return barrier

        raise PermissionDenied("You do not have access to this barrier.")


class BarrierLimitView(generics.RetrieveAPIView):
    """Retrieve limits for a specific barrier (for all authenticated users)"""

    serializer_class = BarrierLimitSerializer
    queryset = Barrier.objects.filter(is_active=True)
    lookup_field = "id"

    def get_object(self):
        barrier = super().get_object()
        user = self.request.user

        if barrier.is_public or UserBarrier.user_has_access_to_barrier(user, barrier):
            return getattr(barrier, "limits", None)  # Can be None

        raise PermissionDenied("You do not have access to this barrier.")

    def get(self, request, *args, **kwargs):
        limit = self.get_object()
        if limit is None:
            return Response({}, status=status.HTTP_200_OK)
        return self.retrieve(request, *args, **kwargs)
