# In apps/analytics_ai/serializers.py (create this file if it doesn't exist)
from rest_framework import serializers
from .models import ReportData
from apps.accounts.serializers import UserSerializer

class ReportDataSerializer(serializers.ModelSerializer):
    generated_for_user = UserSerializer(read_only=True, allow_null=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)

    class Meta:
        model = ReportData
        fields = [
            'id', 'report_type', 'report_type_display', 'generated_for_user',
            'report_parameters', 'data', 'version', 'created_at'
        ]
        read_only_fields = '__all__'