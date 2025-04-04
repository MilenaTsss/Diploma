from django.urls import path

from barriers_management.views import (
    AdminBarrierLimitUpdateView,
    AdminBarrierView,
    CreateBarrierView,
    MyAdminBarrierListView,
)

urlpatterns = [
    path("admin/barriers/", CreateBarrierView.as_view(), name="create_barrier"),
    path("admin/barriers/my/", MyAdminBarrierListView.as_view(), name="admin_my_barriers"),
    path("admin/barriers/<int:id>/", AdminBarrierView.as_view(), name="admin_barrier_view"),
    path("admin/barriers/<int:id>/limits/", AdminBarrierLimitUpdateView.as_view(), name="update_barrier_limit"),
]
