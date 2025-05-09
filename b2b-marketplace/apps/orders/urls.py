from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RFQViewSet, QuoteViewSet, OrderViewSet #, OrderItemViewSet (if used)

router = DefaultRouter()
router.register(r'rfqs', RFQViewSet, basename='rfq')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'orders', OrderViewSet, basename='order')
# If you had a separate OrderItemViewSet for standalone CRUD on order items:
# router.register(r'order-items', OrderItemViewSet, basename='orderitem')

urlpatterns = [
    path('', include(router.urls)),
]