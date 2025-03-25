import logging

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAdminUser

from rest_framework import generics
from rest_framework.response import Response

from barriers.models import Barrier
from barriers_management.serializers import CreateBarrierSerializer, AdminBarrierSerializer
from core.pagination import CustomPageNumberPagination

logger = logging.getLogger(__name__)


@permission_classes([IsAdminUser])
class CreateBarrierView(generics.CreateAPIView):
    """Создание нового шлагбаума (только для администраторов)."""

    queryset = Barrier.objects.all()
    serializer_class = CreateBarrierSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


@permission_classes([IsAdminUser])
class MyAdminBarrierView(generics.ListAPIView):
    """Получение списка шлагбаумов, которыми управляет админ"""

    serializer_class = AdminBarrierSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """Выбираем только те шлагбаумы, которыми владеет текущий админ"""

        return Barrier.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        """Добавляем в ответ total_count, current_page и page_size"""

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_paginated_response(self, data):
        """Формируем ответ с учетом параметров пагинации"""

        paginator = self.pagination_class()
        paginator.page = self.paginator.page

        return Response({
            "total_count": paginator.page.paginator.count,
            "current_page": paginator.page.number,
            "page_size": paginator.get_page_size(self.request),
            "barriers": data,
        })
