from django.db import models
from django.conf import settings
from apps.core.models import AbstractBaseModel # For created_at, updated_at

# Example Model: Storing aggregated report data or AI prediction results.
# This is highly dependent on your specific analytics/AI features.

class ReportData(AbstractBaseModel):
    REPORT_TYPE_CHOICES = (
        ('sales_summary', 'Sales Summary'),
        ('user_activity', 'User Activity'),
        ('trend_analysis', 'Trend Analysis'),
        # Add more as needed
    )
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    generated_for_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Report generated for a specific user (e.g., seller dashboard)"
    )
    report_parameters = models.JSONField(default=dict, blank=True, help_text="Parameters used to generate the report")
    data = models.JSONField(default=dict, help_text="The actual report data or AI output")
    # Or, if data is very large, store a reference to a file in S3/etc.
    # data_file_path = models.CharField(max_length=512, blank=True, null=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name_plural = "Report Data Entries"
        ordering = ['-created_at']

    def __str__(self):
        user_info = f" for {self.generated_for_user.username}" if self.generated_for_user else ""
        return f"{self.get_report_type_display()} Report{user_info} (v{self.version}) - {self.created_at.strftime('%Y-%m-%d')}"


# Example: Model for storing results of a specific AI prediction task
# class ProductRecommendationLog(AbstractBaseModel):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     source_product_id = models.UUIDField(null=True, blank=True) # If recommendation is based on a product
#     recommended_product_ids = models.JSONField(default=list) # List of recommended product IDs
#     algorithm_version = models.CharField(max_length=50)
#     # score = models.FloatField(null=True, blank=True) # Confidence score
#
#     def __str__(self):
#         return f"Recommendations for {self.user.username} at {self.created_at}"