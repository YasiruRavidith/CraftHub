from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, TransactionLog #, UserPaymentMethod

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'interval', 'interval_count', 'is_active', 'display_order', 'stripe_plan_id')
    list_filter = ('is_active', 'interval', 'currency')
    search_fields = ('name', 'description', 'stripe_plan_id')
    list_editable = ('is_active', 'display_order', 'price') # Use with caution

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name_display', 'status', 'current_period_end', 'stripe_subscription_id')
    list_filter = ('status', 'plan', 'cancel_at_period_end')
    search_fields = ('user__username', 'user__email', 'stripe_subscription_id', 'paypal_subscription_id')
    raw_id_fields = ('user', 'plan')
    readonly_fields = ('start_date', 'current_period_start', 'current_period_end', 'cancelled_at', 'trial_start', 'trial_end', 'created_at', 'updated_at')
    actions = ['mark_as_active_admin', 'cancel_subscription_admin']

    fieldsets = (
        (None, {'fields': ('user', 'plan', 'status')}),
        ('Period Details', {'fields': ('start_date', 'current_period_start', 'current_period_end', 'trial_start', 'trial_end')}),
        ('Cancellation', {'fields': ('cancel_at_period_end', 'cancelled_at')}),
        ('Gateway IDs', {'fields': ('stripe_subscription_id', 'stripe_customer_id', 'paypal_subscription_id')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)})
    )

    def plan_name_display(self, obj):
        return obj.plan.name if obj.plan else "N/A"
    plan_name_display.short_description = "Plan"

    def mark_as_active_admin(self, request, queryset):
        # This should ideally trigger logic to sync with payment gateway if needed,
        # or be used carefully for manual overrides.
        for sub in queryset:
            sub.status = 'active'
            # Potentially set current_period_start/end if manually activating
            sub.save(update_fields=['status'])
    mark_as_active_admin.short_description = "Admin: Mark selected subscriptions as Active"

    def cancel_subscription_admin(self, request, queryset):
        # This is a DANGEROUS action without proper gateway integration.
        # It should trigger cancellation at the payment gateway.
        # For now, it just updates local status.
        for sub in queryset:
            sub.status = 'cancelled'
            sub.cancel_at_period_end = True
            sub.cancelled_at = timezone.now()
            sub.save(update_fields=['status', 'cancel_at_period_end', 'cancelled_at'])
            # TODO: Trigger actual cancellation with payment gateway via a service.
            print(f"Admin: Marked subscription {sub.id} as cancelled. Gateway cancellation NOT implemented.")
    cancel_subscription_admin.short_description = "Admin: Cancel selected subscriptions (Local DB only)"


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email_display', 'transaction_type', 'amount_currency_display', 'status', 'payment_gateway', 'gateway_transaction_id', 'created_at')
    list_filter = ('transaction_type', 'status', 'payment_gateway', 'currency')
    search_fields = ('user__username', 'user__email', 'gateway_transaction_id', 'description', 'related_order__id')
    raw_id_fields = ('user', 'related_order', 'related_subscription')
    readonly_fields = ('created_at', 'updated_at')

    def amount_currency_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency_display.short_description = "Amount"

    def user_email_display(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email_display.short_description = "User Email"

# @admin.register(UserPaymentMethod)
# class UserPaymentMethodAdmin(admin.ModelAdmin):
#     list_display = ('user', 'gateway_payment_method_id', 'card_brand', 'last4', 'is_default', 'gateway_name')
#     list_filter = ('gateway_name', 'card_brand', 'is_default')
#     search_fields = ('user__username', 'gateway_payment_method_id')
#     raw_id_fields = ('user',)