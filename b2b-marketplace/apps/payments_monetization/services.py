import stripe # Example: Assuming Stripe is used
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import SubscriptionPlan, UserSubscription, TransactionLog
from apps.orders.models import Order
from apps.accounts.models import CustomUser # Or your User model

# Initialize Stripe API key (should be in your .env and settings)
# stripe.api_key = settings.STRIPE_SECRET_KEY # This line should be in settings or app init.
# For safety, let's assume it's configured elsewhere if settings.STRIPE_SECRET_KEY exists.
if hasattr(settings, 'STRIPE_SECRET_KEY'):
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    print("Warning: STRIPE_SECRET_KEY not found in settings. Payment service will be non-functional.")
    stripe.api_key = None # Prevent errors if not configured

class PaymentService:
    """
    Service layer for handling payment gateway interactions and monetization logic.
    This is a simplified example, primarily focused on Stripe.
    """

    def _get_or_create_stripe_customer(self, user: CustomUser) -> stripe.Customer | None:
        """
        Retrieves an existing Stripe Customer for the user or creates a new one.
        Stores/updates the stripe_customer_id on the user's profile.
        """
        if not stripe.api_key: return None

        if hasattr(user, 'profile') and user.profile.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(user.profile.stripe_customer_id)
                return customer
            except stripe.error.StripeError as e:
                print(f"Error retrieving Stripe customer {user.profile.stripe_customer_id}: {e}")
                # Fall through to create a new one if not found or error
        try:
            customer_params = {
                "email": user.email,
                "name": user.get_full_name() or user.username,
                "metadata": {"django_user_id": str(user.id)}
            }
            customer = stripe.Customer.create(**customer_params)
            if hasattr(user, 'profile'):
                user.profile.stripe_customer_id = customer.id
                user.profile.save(update_fields=['stripe_customer_id'])
            else: # If stripe_customer_id is directly on CustomUser
                user.stripe_customer_id = customer.id # Assuming CustomUser has this field
                user.save(update_fields=['stripe_customer_id'])

            return customer
        except stripe.error.StripeError as e:
            print(f"Error creating Stripe customer for user {user.id}: {e}")
            # Consider raising a custom exception
            return None


    @transaction.atomic
    def create_subscription(self, user: CustomUser, plan: SubscriptionPlan, payment_method_id: str = None, coupon_code: str = None) -> UserSubscription | None:
        """
        Creates a new subscription for a user with a given plan.
        Interacts with Stripe to create the actual subscription.
        `payment_method_id` is typically from Stripe Elements (e.g., pm_xxx).
        """
        if not stripe.api_key:
            raise Exception("Stripe API key not configured.")

        if UserSubscription.objects.filter(user=user, status__in=['active', 'trialing', 'past_due']).exists():
            raise ValueError("User already has an active or trialing subscription.")
        if not plan.stripe_plan_id:
            raise ValueError(f"Subscription plan '{plan.name}' does not have a Stripe Plan ID.")

        stripe_customer = self._get_or_create_stripe_customer(user)
        if not stripe_customer:
            raise Exception("Could not create or retrieve Stripe customer.")

        subscription_params = {
            "customer": stripe_customer.id,
            "items": [{"price": plan.stripe_plan_id}], # Use price ID for Stripe plans
            "expand": ["latest_invoice.payment_intent", "pending_setup_intent"],
            # "payment_behavior": "default_incomplete", # If payment confirmation is async
            # "proration_behavior": "create_prorations",
        }
        if payment_method_id:
            # Attach the payment method to the customer and set as default for subscription
            try:
                stripe.PaymentMethod.attach(payment_method_id, customer=stripe_customer.id)
                stripe.Customer.modify(stripe_customer.id, invoice_settings={"default_payment_method": payment_method_id})
            except stripe.error.StripeError as e:
                raise ValueError(f"Error attaching payment method: {e}")

        if coupon_code:
            # subscription_params["coupon"] = coupon_code # Or handle promotions
            pass

        try:
            stripe_sub = stripe.Subscription.create(**subscription_params)
        except stripe.error.StripeError as e:
            # Handle card errors, etc.
            print(f"Stripe subscription creation error: {e}")
            raise ValueError(f"Could not create Stripe subscription: {e}") # Or a more specific error

        # Create local UserSubscription record
        # Status and period_end will be updated by webhooks for invoice.paid, etc.
        local_sub = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status=stripe_sub.status, # Initial status from Stripe (e.g., 'active', 'trialing', 'incomplete')
            stripe_subscription_id=stripe_sub.id,
            stripe_customer_id=stripe_customer.id, # Store customer ID from user profile
            current_period_start=timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub.current_period_start)) if stripe_sub.current_period_start else None,
            current_period_end=timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub.current_period_end)) if stripe_sub.current_period_end else None,
            trial_start=timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub.trial_start)) if stripe_sub.trial_start else None,
            trial_end=timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub.trial_end)) if stripe_sub.trial_end else None,
        )
        print(f"Local subscription {local_sub.id} created, Stripe sub ID: {stripe_sub.id}")
        # The client should handle the payment_intent or setup_intent if further action is needed
        # For example, if 3D Secure is required.
        return local_sub # Return the stripe_sub object or parts of it for client to handle

    @transaction.atomic
    def cancel_subscription(self, user_subscription: UserSubscription, at_period_end: bool = True) -> UserSubscription:
        """
        Cancels a user's subscription, either immediately or at the end of the current billing period.
        Interacts with Stripe to cancel the actual subscription.
        """
        if not stripe.api_key:
            raise Exception("Stripe API key not configured.")
        if not user_subscription.stripe_subscription_id:
            raise ValueError("Subscription does not have a Stripe Subscription ID.")
        if user_subscription.status == 'cancelled':
            raise ValueError("Subscription is already cancelled.")

        try:
            if at_period_end:
                stripe_sub = stripe.Subscription.modify(
                    user_subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                user_subscription.cancel_at_period_end = True
                # Status might remain 'active' until period end, webhooks will update later.
            else: # Immediate cancellation (less common for SaaS)
                stripe_sub = stripe.Subscription.delete(user_subscription.stripe_subscription_id)
                user_subscription.status = 'cancelled' # Or based on Stripe response
                user_subscription.cancelled_at = timezone.now()
                user_subscription.current_period_end = timezone.now() # Effectively ends now

            user_subscription.save()
            print(f"Stripe subscription {stripe_sub.id} cancellation initiated (at_period_end={at_period_end}).")
            return user_subscription
        except stripe.error.StripeError as e:
            print(f"Stripe subscription cancellation error: {e}")
            raise ValueError(f"Could not cancel Stripe subscription: {e}")

    def create_payment_intent_for_order(self, order: Order, user: CustomUser, payment_method_id: str = None) -> stripe.PaymentIntent | None:
        """
        Creates a Stripe PaymentIntent for a one-time order payment.
        """
        if not stripe.api_key:
            raise Exception("Stripe API key not configured.")
        if order.order_total <= 0:
            raise ValueError("Order total must be positive.")
        if order.status != 'pending_payment':
             raise ValueError(f"Order status is '{order.status}', cannot process payment.")

        stripe_customer = self._get_or_create_stripe_customer(user)
        if not stripe_customer:
            raise Exception("Could not retrieve or create Stripe customer.")

        intent_params = {
            "amount": int(order.order_total * 100),  # Amount in cents
            "currency": order.items.first().material.currency if order.items.first() and order.items.first().material else 'usd', # Get currency from order or default
            "customer": stripe_customer.id,
            "description": f"Payment for Order ID: {order.id}",
            "metadata": {"order_id": str(order.id), "django_user_id": str(user.id)},
            # "payment_method_types": ["card"], # Let Stripe infer or specify
            # "confirm": True, # If payment_method_id is provided and you want to confirm immediately
            # "payment_method": payment_method_id, # If confirming immediately
            "setup_future_usage": "on_session", # If you want to save card for later
        }
        if payment_method_id:
            intent_params["payment_method"] = payment_method_id
            intent_params["confirm"] = True # Attempt to confirm immediately

        try:
            intent = stripe.PaymentIntent.create(**intent_params)
            # Store intent_id on order for reconciliation via webhooks
            order.payment_intent_id = intent.id
            order.save(update_fields=['payment_intent_id'])

            # If intent requires action (e.g., 3D Secure), client_secret is used by frontend.
            # If confirmed and succeeded, webhook 'payment_intent.succeeded' will update order status.
            return intent
        except stripe.error.StripeError as e:
            print(f"Stripe PaymentIntent creation error: {e}")
            # Potentially update order status to 'payment_failed' here or based on error type
            raise ValueError(f"Could not create PaymentIntent: {e}")


    # --- Webhook Handling Methods (called by webhook views) ---
    # These methods would parse Stripe event objects and update local DB.

    @transaction.atomic
    def handle_invoice_paid(self, event_data: dict):
        """Handles 'invoice.paid' Stripe webhook event."""
        invoice = event_data['object']
        stripe_subscription_id = invoice.get('subscription')
        stripe_customer_id = invoice.get('customer')

        if not stripe_subscription_id:
            print("Invoice paid event without a subscription ID, possibly for a one-time charge.")
            # Handle one-time invoice payments if necessary (e.g. metered billing final invoice)
            order_id = invoice.get('metadata', {}).get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    if order.status != 'completed': # Or 'shipped' etc.
                        # This assumes payment for order was deferred to invoice
                        # More common is payment_intent.succeeded for orders
                        print(f"Invoice paid for order {order_id}, but direct order payment flow is preferred.")
                except Order.DoesNotExist:
                    print(f"Order {order_id} not found for invoice.paid event.")
            return

        try:
            subscription = UserSubscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            subscription.status = 'active' # Or based on Stripe subscription status in invoice.lines
            subscription.current_period_start = timezone.make_aware(timezone.datetime.fromtimestamp(invoice['lines']['data'][0]['period']['start']))
            subscription.current_period_end = timezone.make_aware(timezone.datetime.fromtimestamp(invoice['lines']['data'][0]['period']['end']))
            subscription.cancel_at_period_end = False # Payment successful, so not cancelling
            subscription.save()

            TransactionLog.objects.create(
                user=subscription.user,
                related_subscription=subscription,
                transaction_type='subscription_payment',
                amount=Decimal(invoice['amount_paid']) / 100,
                currency=invoice['currency'].upper(),
                status='succeeded',
                payment_gateway='Stripe',
                gateway_transaction_id=invoice['id'], # Invoice ID
                gateway_charge_id=invoice.get('charge'), # Charge ID if available
                description=f"Subscription payment for {subscription.plan.name if subscription.plan else 'plan'}",
            )
            print(f"Handled invoice.paid for Stripe subscription {stripe_subscription_id}. Local sub: {subscription.id}")
        except UserSubscription.DoesNotExist:
            print(f"UserSubscription with Stripe ID {stripe_subscription_id} not found.")
        except Exception as e:
            print(f"Error handling invoice.paid: {e}")
            # Consider re-raising or logging to a monitoring service

    @transaction.atomic
    def handle_payment_intent_succeeded(self, event_data: dict):
        """Handles 'payment_intent.succeeded' Stripe webhook event (often for one-time payments)."""
        payment_intent = event_data['object']
        order_id = payment_intent.get('metadata', {}).get('order_id')
        django_user_id = payment_intent.get('metadata', {}).get('django_user_id')

        if not order_id:
            print(f"PaymentIntent {payment_intent.id} succeeded without an order_id in metadata.")
            # Could be for other purposes, or a subscription setup.
            return

        try:
            order = Order.objects.get(id=order_id, payment_intent_id=payment_intent.id)
            if order.status == 'pending_payment': # Or other statuses from which it can transition
                order.status = 'processing' # Or 'completed' if digital, or based on your flow
                order.save(update_fields=['status'])

                user = order.buyer # Get user from order
                TransactionLog.objects.get_or_create(
                    gateway_transaction_id=payment_intent.id, # Use PI as main ID
                    payment_gateway='Stripe',
                    defaults={
                        'user': user,
                        'related_order': order,
                        'transaction_type': 'order_payment',
                        'amount': Decimal(payment_intent['amount_received']) / 100,
                        'currency': payment_intent['currency'].upper(),
                        'status': 'succeeded',
                        'description': f"Payment for Order {order.id}",
                        'gateway_charge_id': payment_intent.get('latest_charge'), # Get the charge ID
                    }
                )
                print(f"Handled payment_intent.succeeded for Order {order.id}.")
                # Trigger order fulfillment, notifications, etc.
            else:
                print(f"PaymentIntent {payment_intent.id} succeeded for Order {order.id}, but order status was already '{order.status}'.")

        except Order.DoesNotExist:
            print(f"Order with ID {order_id} and PaymentIntent ID {payment_intent.id} not found.")
        except Exception as e:
            print(f"Error handling payment_intent.succeeded: {e}")

    @transaction.atomic
    def handle_customer_subscription_updated(self, event_data: dict):
        """Handles 'customer.subscription.updated' or 'customer.subscription.deleted' (cancelled) events."""
        stripe_sub_event = event_data['object']
        stripe_subscription_id = stripe_sub_event.id

        try:
            subscription = UserSubscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            new_status = stripe_sub_event.status
            if new_status == 'canceled': # Stripe uses 'canceled'
                new_status = 'cancelled' # Align with local model choice

            subscription.status = new_status
            subscription.cancel_at_period_end = stripe_sub_event.cancel_at_period_end
            if stripe_sub_event.canceled_at:
                subscription.cancelled_at = timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub_event.canceled_at))
            if stripe_sub_event.current_period_start:
                 subscription.current_period_start = timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub_event.current_period_start))
            if stripe_sub_event.current_period_end:
                 subscription.current_period_end = timezone.make_aware(timezone.datetime.fromtimestamp(stripe_sub_event.current_period_end))

            # Update plan if it changed (e.g., upgrade/downgrade)
            stripe_price_id = stripe_sub_event['items']['data'][0]['price']['id']
            try:
                new_plan = SubscriptionPlan.objects.get(stripe_plan_id=stripe_price_id)
                if subscription.plan != new_plan:
                    subscription.plan = new_plan
                    print(f"Subscription {subscription.id} plan updated to {new_plan.name}.")
            except SubscriptionPlan.DoesNotExist:
                print(f"Warning: Stripe Price ID {stripe_price_id} not found in local SubscriptionPlans.")


            subscription.save()
            print(f"Handled customer.subscription.updated/deleted for Stripe subscription {stripe_subscription_id}. New status: {new_status}")
        except UserSubscription.DoesNotExist:
            print(f"UserSubscription with Stripe ID {stripe_subscription_id} not found for update/delete event.")
        except Exception as e:
            print(f"Error handling customer.subscription event: {e}")

    # Add more handlers for other events like:
    # - invoice.payment_failed
    # - customer.subscription.trial_will_end
    # - charge.refunded (for order payment refunds)
    # - etc.