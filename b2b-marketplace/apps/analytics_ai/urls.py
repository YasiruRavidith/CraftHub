from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesSummaryReportAPIView,
    ProductRecommendationAPIView,
    StoredReportDataViewSet # If serving stored reports
)

router = DefaultRouter()
# Register ViewSets if you have more complex CRUD for analytics entities
if StoredReportDataViewSet.queryset is not None: # Check if queryset is defined (i.e., model exists)
    router.register(r'stored-reports', StoredReportDataViewSet, basename='storedreport')


urlpatterns = [
    path('reports/sales-summary/', SalesSummaryReportAPIView.as_view(), name='report-sales-summary'),
    path('recommendations/products/', ProductRecommendationAPIView.as_view(), name='recommendations-products'),
    # Include router URLs if any ViewSets are registered
    path('', include(router.urls)),
]