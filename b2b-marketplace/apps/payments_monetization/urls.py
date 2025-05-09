# D:\Stuuuuuuuuupid\Garment App\b2b-marketplace\apps\payments_monetization\urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet, UserSubscriptionViewSet, TransactionLogViewSet,
    stripe_webhook_receiver
)

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'my-subscription', UserSubscriptionViewSet, basename='usersubscription') # For current user
router.register(r'transactions', TransactionLogViewSet, basename='transactionlog')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/stripe/', stripe_webhook_receiver, name='stripe-webhook'),
    # Add other webhook URLs if using multiple gateways (e.g., /webhooks/paypal/)
]