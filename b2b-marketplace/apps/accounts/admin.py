# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

class CustomUserAdmin(UserAdmin):
    # Add or customize fields shown in the admin
    # For example, if you add fields to CustomUser
    pass

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile)