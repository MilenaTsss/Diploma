from django.urls import path

from message_management.views import (
    AdminSMSMessageDetailView,
    AdminSMSMessageListView,
    UserSMSMessageDetailView,
    UserSMSMessageListView,
)

urlpatterns = [
    path("barriers/<int:id>/sms/", UserSMSMessageListView.as_view(), name="user_sms_list"),
    path("sms/<int:id>/", UserSMSMessageDetailView.as_view(), name="user_sms_detail"),
    path("admin/barriers/<int:id>/sms/", AdminSMSMessageListView.as_view(), name="admin_sms_list"),
    path("admin/sms/<int:id>/", AdminSMSMessageDetailView.as_view(), name="admin_sms_detail"),
]
