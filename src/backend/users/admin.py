from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from users.models import User
from users.validators import PhoneNumberValidator


class AdminCreationForm(forms.ModelForm):
    """Custom form for creating an admin via Django Admin"""

    phone = forms.CharField(
        label=_("Phone"),
        validators=[PhoneNumberValidator()],  # Проверяем номер телефона
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

    def clean_password(self):
        """Validate the password"""
        password = self.cleaned_data.get("password")
        validate_password(password)
        return password

    def save(self, commit=True):
        """Hashes the password before saving"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_staff = True  # Ensure it's an admin
        user.role = User.Role.ADMIN
        if commit:
            user.save()
        return user


class UserAdmin(BaseUserAdmin):
    """Custom UserAdmin for managing users in Django Admin"""

    def add_view(self, request, form_url="", extra_context=None):
        """Меняем заголовок страницы 'Add user' -> 'Add admin'"""
        extra_context = extra_context or {}
        extra_context["title"] = _("Add admin")
        return super().add_view(request, form_url, extra_context)

    def has_view_permission(self, request, obj=None):
        """Позволяет суперпользователю видеть пользователей"""
        return request.user.is_staff

    def has_module_permission(self, request):
        """Позволяет суперпользователю видеть Users в админке"""
        return request.user.is_staff

    def has_add_permission(self, request):
        """Только суперпользователь может создавать новых пользователей"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление пользователей"""
        return request.user.is_superuser

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
admin.site.unregister(Group)
