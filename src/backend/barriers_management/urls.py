from django.urls import path

from barriers_management.views import AdminBarrierView, CreateBarrierView, MyAdminBarrierView

urlpatterns = [
    path("admin/barriers/", CreateBarrierView.as_view(), name="create_barrier"),
    path("admin/barriers/my/", MyAdminBarrierView.as_view(), name="admin_my_barriers"),
    path("admin/barriers/<int:id>/", AdminBarrierView.as_view(), name="admin_barrier_view"),
]
