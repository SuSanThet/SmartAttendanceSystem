from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = UserAdmin.list_display + (
        "account_id",
        "role",
    )

    fieldsets = UserAdmin.fieldsets + (
        ("Account Information", {
            "fields": ("account_id", "role"),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Account Information", {
            "fields": ("account_id", "role"),
        }),
    )