from django.contrib import admin
from .models import ReportData #, ProductRecommendationLog

@admin.register(ReportData)
class ReportDataAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_for_user', 'version', 'created_at')
    list_filter = ('report_type', 'generated_for_user', 'created_at')
    search_fields = ('report_type', 'generated_for_user__username', 'data') # Searching JSONField might be limited
    readonly_fields = ('created_at', 'updated_at')

# @admin.register(ProductRecommendationLog)
# class ProductRecommendationLogAdmin(admin.ModelAdmin):
#     list_display = ('user', 'algorithm_version', 'created_at')
#     list_filter = ('algorithm_version', 'user')
#     search_fields = ('user__username',)