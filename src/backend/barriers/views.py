from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.response import Response

from barriers.models import Barrier
from barriers.serializers import BarrierSerializer
from core.pagination import CustomPageNumberPagination


class ListBarriersView(generics.ListAPIView):
    """Список всех публичных шлагбаумов с поиском и пагинацией"""

    serializer_class = BarrierSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """Выбираем только публичные шлагбаумы и применяем фильтр по адресу"""

        queryset = Barrier.objects.filter(is_public=True, is_active=True)

        # Фильтрация по части адреса
        address = self.request.query_params.get("address", "").strip()
        if address:
            queryset = queryset.filter(Q(address__icontains = address.lower()))

        return queryset

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


class MyBarriersListView(generics.ListAPIView):
    """Получить список шлагбаумов, доступных текущему пользователю"""

    serializer_class = BarrierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Barrier.objects.filter(owner=self.request.user, is_active=True)


# class BarrierDetailView(generics.RetrieveAPIView):
#     """Получить информацию о конкретном шлагбауме"""
#
#     queryset = Barrier.objects.filter(is_active=True)
#     serializer_class = BarrierSerializer
#     permission_classes = [permissions.AllowAny]
