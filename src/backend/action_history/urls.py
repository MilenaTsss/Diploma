from django.urls import path

from action_history.views import (
    AdminBarrierActionLogDetailView,
    AdminBarrierActionLogListView,
    UserBarrierActionLogDetailView,
    UserBarrierActionLogListView,
)

urlpatterns = [
    path(
        "barriers/<int:barrier_id>/actions/",
        UserBarrierActionLogListView.as_view(),
        name="user_action_history_list_view",
    ),
    path(
        "barriers/<int:barrier_id>/actions/<int:id>/",
        UserBarrierActionLogDetailView.as_view(),
        name="user_action_history_detail_view",
    ),
    path(
        "admin/barriers/<int:barrier_id>/actions/",
        AdminBarrierActionLogListView.as_view(),
        name="admin_action_history_list_view",
    ),
    path(
        "admin/barriers/<int:barrier_id>/actions/<int:id>/",
        AdminBarrierActionLogDetailView.as_view(),
        name="admin_action_history_detail_view",
    ),
]
