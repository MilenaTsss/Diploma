from django.urls import path

from barriers.views import ListBarriersView

urlpatterns = [
    path("barriers/", ListBarriersView.as_view(), name="list_barriers"),
    # path("barriers/my/", MyBarrierListView.as_view(), name="my_barriers"),
]
