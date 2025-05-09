from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, TransactionLog
from apps.accounts.serializers import UserSerializer # For user details in subscription/transaction

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'description', 'price', 'currency',
            'interval', 'interval_count', 'features', 'is_active',
            'stripe_plan_id', 'paypal_plan_id', 'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'stripe_plan_id', 'paypal_plan_id'] # Gateway IDs usually managed by admin/service

class UserSubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        source='plan',
        write_only=True,
        required=False # For creating/updating subscriptions, plan might be chosen
    )
    is_currently_active = serializers.BooleanField(source='is_active_or_trialing', read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'plan', 'plan_id', 'status', 'is_currently_active',
            'start_date', 'current_period_start', 'current_period_end',
            'cancel_at_period_end', 'cancelled_at', 'trial_start', 'trial_end',
            'stripe_subscription_id', 'stripe_customer_id', 'paypal_subscription_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', # Status is usually managed by webhooks/service
            'start_date', 'current_period_start', 'current_period_end',
            'cancelled_at', 'trial_start', 'trial_end',
            'stripe_subscription_id', 'stripe_customer_id', 'paypal_subscription_id',
            'created_at', 'updated_at', 'is_currently_active'
        ]
        # 'plan_id' is write_only for creating/changing subscriptions.
        # 'cancel_at_period_end' might be updatable by user.

class CreateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField(required=True)
    payment_method_id = serializers.CharField(max_length=255, required=False, allow_blank=True, help_text="e.g., Stripe PaymentMethod ID (pm_xxx)")
    # coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return plan # Return the plan instance
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Active subscription plan with this ID not found.")


class CancelSubscriptionSerializer(serializers.Serializer):
    # No fields needed, action is on the subscription itself.
    # feedback = serializers.CharField(max_length=500, required=False, allow_blank=True) # Optional cancellation feedback
    pass


class TransactionLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True, allow_null=True)
    # For displaying related object info concisely
    related_object_display = serializers.SerializerMethodField()

    class Meta:
        model = TransactionLog
        fields = [
            'id', 'user', 'transaction_type', 'amount', 'currency', 'status',
            'description', 'payment_gateway', 'gateway_transaction_id',
            'related_order_id', 'related_subscription_id', # Show IDs
            'related_object_display', # Show descriptive name
            'created_at'
        ]
        read_only_fields = '__all__' # Transactions are typically immutable records once created.

    def get_related_object_display(self, obj):
        if obj.related_order:
            return f"Order: {obj.related_order.id}"
        if obj.related_subscription:
            plan_name = obj.related_subscription.plan.name if obj.related_subscription.plan else "N/A"
            return f"Subscription: {plan_name} ({obj.related_subscription.id})"
        return None

# --- Webhook Serializers (Example for Stripe) ---
# These are not directly used by ModelViewSets but by webhook handler views.
# They help validate and structure the incoming webhook data.

class StripeWebhookEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    object = serializers.CharField()
    api_version = serializers.CharField(required=False)
    created = serializers.IntegerField()
    data = serializers.DictField() # The actual event data object
    livemode = serializers.BooleanField()
    pending_webhooks = serializers.IntegerField(required=False)
    request = serializers.DictField(required=False, allow_null=True) # Contains idempotency_key
    type = serializers.CharField() # The event type, e.g., 'invoice.paid', 'customer.subscription.deleted'

    # You would add more specific validation for event types you handle.
    # For example, for 'invoice.paid', you'd expect data.object to contain invoice details.