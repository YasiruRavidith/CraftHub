from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime

from .services import AnalyticsService
from .tasks import generate_report_task # For async report generation
from .serializers import ReportDataSerializer # If you create one for ReportData model
from .models import ReportData # If serving stored reports

class SalesSummaryReportAPIView(views.APIView):
    permission_classes = [permissions.IsAdminUser] # Or specific permission for accessing reports

    def get(self, request, *args, **kwargs):
        analytics_service = AnalyticsService()
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        user_id_for_report = request.query_params.get('user_id') # For seller-specific sales report

        start_date = parse_datetime(start_date_str) if start_date_str else None
        end_date = parse_datetime(end_date_str) if end_date_str else None
        target_user = None
        if user_id_for_report:
            try:
                from apps.accounts.models import CustomUser # Local import
                target_user = CustomUser.objects.get(id=user_id_for_report)
            except CustomUser.DoesNotExist:
                return Response({"error": "Specified user not found"}, status=status.HTTP_404_NOT_FOUND)


        # Example: Triggering an asynchronous report generation
        # report_params = {
        #     'start_date': start_date.isoformat() if start_date else None,
        #     'end_date': end_date.isoformat() if end_date else None,
        # }
        # task_result = generate_report_task.delay(
        #     report_type='sales_summary',
        #     user_id=target_user.id if target_user else None,
        #     report_params=report_params
        # )
        # return Response(
        #     {"message": "Sales summary report generation initiated.", "task_id": task_result.id},
        #     status=status.HTTP_202_ACCEPTED
        # )

        # Example: Synchronous report generation (for smaller reports or immediate needs)
        try:
            report_data = analytics_service.generate_sales_summary_report(
                start_date=start_date,
                end_date=end_date,
                for_user=target_user
            )
            return Response(report_data, status=status.HTTP_200_OK)
        except Exception as e:
            # Log e
            return Response({"error": f"Failed to generate report: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductRecommendationAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated] # Users get recommendations for themselves

    def get(self, request, *args, **kwargs):
        analytics_service = AnalyticsService()
        user = request.user
        product_id_context = request.query_params.get('product_id') # For item-to-item
        num_recs = int(request.query_params.get('count', 5))

        try:
            recommendations = analytics_service.get_product_recommendations(
                user=user,
                product_id=product_id_context,
                num_recommendations=num_recs
            )
            return Response(recommendations, status=status.HTTP_200_OK)
        except Exception as e:
            # Log e
            return Response({"error": f"Failed to get recommendations: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StoredReportDataViewSet(viewsets.ReadOnlyModelViewSet): # If serving stored ReportData
    queryset = ReportData.objects.all()
    # serializer_class = ReportDataSerializer # Create this serializer if needed
    permission_classes = [permissions.IsAdminUser] # Or specific report access permissions
    filterset_fields = ['report_type', 'generated_for_user__id']

    # For this placeholder, let's assume no specific serializer is defined yet for ReportData
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Basic representation if no serializer
        data = [{"id": str(r.id), "type": r.report_type, "user_id": str(r.generated_for_user_id) if r.generated_for_user_id else None, "created_at": r.created_at} for r in queryset]
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Basic representation
        data = {"id": str(instance.id), "type": instance.report_type, "user_id": str(instance.generated_for_user_id) if instance.generated_for_user_id else None, "data": instance.data, "created_at": instance.created_at}
        return Response(data)