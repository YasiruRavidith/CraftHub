from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import UserSubscription, TransactionLog
# from .services import PaymentService # You would have a service to interact with gateways

# This is a simplified signal. In a real app, most subscription updates
# would be driven by webhooks from the payment gateway.
@receiver(post_save, sender=UserSubscription)
def user_subscription_updated(sender, instance: UserSubscription, created, **kwargs):
    """
    Handles actions when a UserSubscription instance is saved.
    This is a basic example; real-world logic would be more complex and
    likely triggered by payment gateway webhooks.
    """
    if created:
        # Log initial subscription creation if needed, though often the first payment transaction
        # from a webhook would be the primary record.
        print(f"New subscription created for {instance.user.username} to plan {instance.plan.name if instance.plan else 'N/A'}.")

    # Example: If status changes to 'cancelled' locally, ensure cancelled_at is set.
    # This might be redundant if webhooks are handling this.
    if instance.status == 'cancelled' and not instance.cancelled_at:
        instance.cancelled_at = timezone.now()
        # instance.save(update_fields=['cancelled_at']) # Avoid recursion if possible by checking update_fields
        # Be careful with calling save() inside a post_save signal without proper guards.

    # Example: If a subscription becomes active, ensure the user has appropriate roles/permissions.
    # This is business logic that might live elsewhere or be triggered by webhooks.
    # if instance.status == 'active' and (created or 'status' in (kwargs.get('update_fields') or [])):
    #     # from apps.accounts.utils import grant_subscriber_role
    #     # grant_subscriber_role(instance.user, instance.plan)
    #     print(f"Subscription for {instance.user.username} is now active.")
    # elif instance.status != 'active' and (not created and 'status' in (kwargs.get('update_fields') or [])):
    #     # from apps.accounts.utils import revoke_subscriber_role
    #     # revoke_subscriber_role(instance.user)
    #     print(f"Subscription for {instance.user.username} is no longer active (status: {instance.status}).")
    pass # Most logic will be in webhook handlers.


@receiver(post_save, sender=TransactionLog)
def transaction_log_saved(sender, instance: TransactionLog, created, **kwargs):
    """
    Handles actions when a TransactionLog instance is saved.
    """
    if created:
        print(f"New transaction logged: {instance.id} - {instance.transaction_type} for {instance.amount} {instance.currency}")

    # Example: If a subscription payment succeeds, ensure the UserSubscription is active.
    # This is highly dependent on webhook flows. A webhook for 'invoice.paid' (Stripe)
    # would typically update UserSubscription status and create this TransactionLog.
    # if instance.transaction_type == 'subscription_payment' and \
    #    instance.status == 'succeeded' and \
    #    instance.related_subscription:
    #
    #     subscription = instance.related_subscription
    #     if subscription.status not in ['active', 'trialing']:
    #         subscription.status = 'active'
    #         # Update period_end based on gateway data received via webhook, not directly here.
    #         # subscription.current_period_end = ...
    #         # subscription.save(update_fields=['status', ...])
    #         print(f"Subscription {subscription.id} marked active due to successful payment transaction {instance.id}")
    pass # Most logic will be in webhook handlers.

# REMINDER:
# The most critical part of a payment system is handling webhooks from your payment provider.
# These webhooks will inform your application about:
# - Successful payments (for orders or subscriptions)
# - Failed payments
# - Subscription status changes (created, updated, cancelled, trialing_ended)
# - Disputes, refunds, etc.
#
# A typical webhook handler view would:
# 1. Verify the webhook signature.
# 2. Parse the event payload.
# 3. Call a service method (e.g., from PaymentService) to process the event:
#    - Update UserSubscription model (status, period_end, etc.)
#    - Create/update TransactionLog model.
#    - Grant/revoke access to features.
#    - Send notifications to users.
#
# These local Django signals are secondary to robust webhook processing.