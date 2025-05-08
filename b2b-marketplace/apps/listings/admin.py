# apps/listings/admin.py
from django.contrib import admin
from .models import Material, Design

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'fabric_type', 'quantity_available', 'price_per_unit', 'is_active', 'created_at')
    list_filter = ('fabric_type', 'is_active', 'seller')
    search_fields = ('name', 'description', 'seller__username', 'seller__email')
    # raw_id_fields = ('seller',) # Useful if you have many users

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ('title', 'designer', 'licensing_options', 'price', 'is_active', 'created_at')
    list_filter = ('licensing_options', 'is_active', 'designer')
    search_fields = ('title', 'description', 'tags', 'designer__username', 'designer__email')
    # raw_id_fields = ('designer',)