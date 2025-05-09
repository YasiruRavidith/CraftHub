import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from apps.core.models import AbstractBaseModel # For created_at, updated_at
from apps.orders.models import Order # Optional: Link transactions to orders

# If AbstractBaseModel is not defined:
# class AbstractBaseModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         abstract = True

class SubscriptionPlan(AbstractBaseModel):
    PLAN_INTERVAL_CHOICES = (
        ('month', 'Monthly'),
        ('year', 'Yearly'),
        ('week', 'Weekly'), # Less common for B2B SaaS
        ('day', 'Daily'),   # Even less common
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD') # e.g., USD, EUR
    interval = models.CharField(max_length=10, choices=PLAN_INTERVAL_CHOICES, default='month')
    interval_count = models.PositiveSmallIntegerField(default=1, help_text="e.g., 1 for every month, 3 for every 3 months")
    stripe_plan_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID from Stripe or other payment gateway")
    paypal_plan_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID from PayPal")
    features = models.JSONField(default=list, blank=True, help_text="List of features for this plan")
    # e.g., {"listings_limit": 10, "priority_support": true, "analytics_access": "basic"}
    is_active = models.BooleanField(default=True, help_text="Whether this plan can be subscribed to")
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency}/{self.interval})"


class UserSubscription(AbstractBaseModel):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'), # User cancelled, but still within paid period
        ('past_due', 'Past Due'), # Payment failed
        ('cancelled', 'Cancelled'), # Paid period ended after cancellation
        ('trialing', 'Trialing'),
        ('incomplete', 'Incomplete'), # Payment initiated but not confirmed
        ('incomplete_expired', 'Incomplete Expired'),
        ('unpaid', 'Unpaid'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription') # Usually one active sub per user
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, related_name='user_subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    start_date = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    # Payment Gateway Specific IDs
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, db_index=True) # Often stored on User/Profile
    paypal_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    # latest_invoice_id = models.CharField(max_length=255, blank=True, null=True) # For Stripe

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s subscription to {self.plan.name if self.plan else 'N/A'} ({self.status})"

    def is_active_or_trialing(self):
        return self.status in ['active', 'trialing'] and \
               (self.current_period_end is None or self.current_period_end >= timezone.now())

    def has_feature(self, feature_key: str):
        if not self.plan or not self.is_active_or_trialing():
            return False
        return self.plan.features.get(feature_key, False) # Assumes features is a dict


class TransactionLog(AbstractBaseModel):
    TRANSACTION_TYPE_CHOICES = (
        ('subscription_payment', 'Subscription Payment'),
        ('order_payment', 'Order Payment'),
        ('platform_fee', 'Platform Fee'), # Fee taken from a seller's transaction
        ('payout', 'Payout'), # Payout to a seller/manufacturer
        ('refund', 'Refund'),
        ('vas_payment', 'Value Added Service Payment'), # VAS = Value Added Service
        ('other', 'Other'),
    )
    TRANSACTION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'), # Full or partial
        ('disputed', 'Disputed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    payment_gateway = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Stripe, PayPal")
    gateway_transaction_id = models.CharField(max_length=255, blank=True, null=True, db_index=True) # ID from payment gateway
    gateway_charge_id = models.CharField(max_length=255, blank=True, null=True) # For Stripe charge ID if different from transaction
    gateway_response = models.JSONField(default=dict, blank=True, null=True, help_text="Full response from gateway, for debugging")

    # Links to other relevant models
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    related_subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    # related_payout_batch = ... (if you have payout batching)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.id} ({self.transaction_type} - {self.status}) for {self.amount} {self.currency}"

# --- Payment Method Storage (e.g., for Stripe Setup Intents / PaymentMethods) ---
# This is highly dependent on your payment gateway. Storing raw card details is NOT recommended and likely not PCI compliant.
# Usually, you store a token or ID provided by the payment gateway that represents the payment method.

# class UserPaymentMethod(AbstractBaseModel):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
#     gateway_payment_method_id = models.CharField(max_length=255, unique=True) # e.g., Stripe PaymentMethod ID (pm_xxx)
#     card_brand = models.CharField(max_length=50, blank=True, null=True) # e.g., Visa, Mastercard
#     last4 = models.CharField(max_length=4, blank=True, null=True)
#     exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
#     exp_year = models.PositiveSmallIntegerField(null=True, blank=True)
#     is_default = models.BooleanField(default=False)
#     gateway_name = models.CharField(max_length=50, default='stripe') # To support multiple gateways
#
#     def __str__(self):
#         return f"{self.user.username}'s {self.card_brand} ending in {self.last4}"

# It's often better to store the customer ID from the gateway (e.g., Stripe Customer ID cus_xxx)
# on the User or Profile model, and then manage payment methods directly within the gateway's ecosystem.
# Profile model in accounts could have:
# stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
# paypal_payer_id = models.CharField(max_length=255, blank=True, null=True)