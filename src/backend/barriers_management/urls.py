from django.urls import path

from barriers_management.views import CreateBarrierView, MyAdminBarrierView

urlpatterns = [
    path("admin/barriers/", CreateBarrierView.as_view(), name="create_barrier"),
    path("admin/barriers/my/", MyAdminBarrierView.as_view(), name="my_barriers"),

]
