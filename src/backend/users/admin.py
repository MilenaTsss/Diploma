from django import forms
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User
from users.validators import PhoneNumberValidator


class AdminCreationForm(forms.ModelForm):
    """Custom form for creating an admin via Django Admin"""

    phone = forms.CharField(
        label=_("Phone"),
        validators=[PhoneNumberValidator()],
        help_text=_("Enter a valid phone number in the format +7XXXXXXXXXX."),
    )

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        help_text=_("Set a password for the new admin."),
    )

    class Meta:
        model = User
        fields = ("phone", "full_name", "password")

    def save(self, commit=True):
        """Hashes the password before saving"""

        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_staff = True  # Ensure it's an admin
        user.role = User.Role.ADMIN
        if commit:
            user.save()
        return user


@admin.action(description="Toggle is_active status of selected users")
def toggle_users_active_status(modeladmin, request, queryset):
    """Allow only superusers to change is_active status, prevent self-blocking"""

    def has_permission_to_toggle_users(current_request, user_queryset):
        """Check if the current user has permission to toggle user activation."""
        if not current_request.user.is_superuser:
            return False, _("You do not have permission to modify user activation status.")
        if current_request.user in user_queryset:
            return False, _("You cannot deactivate your own account.")
        return True, None

    has_permission, error_message = has_permission_to_toggle_users(request, queryset)

    if not has_permission:
        modeladmin.message_user(request, error_message, level="error")
        return

    # Iterate over each user to log individual changes
    for user in queryset:
        old_status = user.is_active
        user.is_active = not user.is_active
        user.save()

        # Log the change in Django admin history
        LogEntry.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(User),
            object_id=user.id,
            object_repr=str(user),
            action_flag=CHANGE,
            change_message=f"Changed is_active from {old_status} to {user.is_active}",
        )

    queryset.update(is_active=models.F("is_active").bitxor(True))
    modeladmin.message_user(request, _("Selected users' active status has been toggled."))


class UserAdmin(BaseUserAdmin):
    """Custom UserAdmin for managing users in Django Admin"""

    actions = [toggle_users_active_status]

    def add_view(self, request, form_url="", extra_context=None):
        """Change the page title from 'Add user' to 'Add admin'"""
        extra_context = extra_context or {}
        extra_context["title"] = _("Add admin")
        return super().add_view(request, form_url, extra_context)

    def has_view_permission(self, request, obj=None):
        """Allows active admins and superusers to view users"""

        return request.user.is_staff and request.user.is_active

    def has_module_permission(self, request):
        """Allows active admins and superusers to see Users module in the admin panel"""

        return request.user.is_staff and request.user.is_active

    def has_add_permission(self, request):
        """Only superusers can create new users"""

        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Prevent user deleting"""

        return False

    list_display = ("phone", "full_name", "role", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("phone", "full_name")
    ordering = ("phone",)
    readonly_fields = (
        "role",
        "phone_privacy",
        "is_staff",
        "is_superuser",
        "is_blocked",
        "is_active",
        "date_joined",
        "last_login",
    )

    fieldsets = ((_("User Info"), {"fields": readonly_fields}),)

    add_form = AdminCreationForm  # Use custom form
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "password"),
            },
        ),
    )


# Register the model in admin
admin.site.register(User, UserAdmin)
# Delete the model for Groups managing
admin.site.unregister(Group)
