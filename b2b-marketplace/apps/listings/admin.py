from django.contrib import admin
from .models import Category, Material, Design, TechPack, Certification, Tag
import os

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent_category')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class TechPackInline(admin.StackedInline): # Or admin.TabularInline
    model = TechPack
    extra = 1 # Number of empty forms to display

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price_per_unit', 'unit', 'stock_quantity', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'seller__user_type')
    search_fields = ('name', 'description', 'seller__username')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    fieldsets = (
        (None, {
            'fields': ('seller', 'name', 'slug', 'description', 'category', 'tags')
        }),
        ('Pricing & Stock', {
            'fields': ('price_per_unit', 'unit', 'minimum_order_quantity', 'stock_quantity', 'sku')
        }),
        ('Properties', {
            'fields': ('composition', 'weight_gsm', 'width_cm', 'country_of_origin', 'lead_time_days')
        }),
        ('Media & Status', {
            'fields': ('main_image', 'additional_images', 'is_active', 'certifications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    #prepopulated_fields = {'slug': ('name',)}

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ('title', 'designer', 'category', 'price', 'is_active', 'slug', 'created_at') # Added slug
    list_filter = ('is_active', 'category', 'designer__user_type')
    search_fields = ('title', 'description', 'designer__username', 'slug') # Added slug
    inlines = [TechPackInline]
    readonly_fields = ('created_at', 'updated_at', 'slug') # slug is auto-generated and editable=False
    fieldsets = (
        (None, {
            'fields': ('designer', 'title', 'description', 'category', 'tags') # slug removed as it's readonly and auto
        }),
        ('Pricing & Details', {
            'fields': ('price', 'licensing_terms')
        }),
        ('Media & Status', {
            # 'fields': ('thumbnail_image', 'design_files', 'is_active', 'certifications') # OLD
            'fields': ('thumbnail_image', 'design_files_link', 'is_active', 'certifications') # NEW
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    # prepopulated_fields = {'slug': ('title',)} # Remove as slug is editable=False

@admin.register(TechPack)
class TechPackAdmin(admin.ModelAdmin):
    list_display = ('design', 'file_link_display', 'version', 'created_at') # Changed 'uploaded_at' to 'created_at'
    list_filter = ('design__title',)
    search_fields = ('design__title', 'notes', 'file')
    readonly_fields = ('created_at', 'updated_at', 'file_link_display') # Add created_at and updated_at here

    def file_link_display(self, obj):
        from django.utils.html import format_html
        if obj.file:
            return format_html("<a href='{url}'>{name}</a>", url=obj.file.url, name=os.path.basename(obj.file.name))
        return "No file"
    file_link_display.short_description = "File"
    file_link_display.admin_order_field = 'file' # Allows sorting by the file name if desired

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_body', 'valid_until')
    search_fields = ('name', 'issuing_body')