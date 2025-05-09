import stripe # For webhook signature verification
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt # For webhook endpoint
from rest_framework import viewsets, permissions, status, generics, mixins
from rest_framework.decorators import action, api_view, permission_classes as drf_permission_classes
from rest_framework.response import Response

from .models import SubscriptionPlan, UserSubscription, TransactionLog
from .serializers import (
    SubscriptionPlanSerializer, UserSubscriptionSerializer, TransactionLogSerializer,
    CreateSubscriptionSerializer, CancelSubscriptionSerializer, StripeWebhookEventSerializer
)
from .services import PaymentService
from .permissions import IsSubscriptionOwner # Create this


# Initialize Stripe API key for webhook verification if not already done in services
if hasattr(settings, 'STRIPE_SECRET_KEY') and not stripe.api_key:
    stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows subscription plans to be viewed.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('display_order', 'price')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny] # Plans are public

class UserSubscriptionViewSet(viewsets.GenericViewSet,
                              mixins.RetrieveModelMixin,
                              mixins.ListModelMixin): # Not providing update/destroy directly
    """
    API endpoint for users to view and manage their subscription.
    Creation and cancellation are handled by custom actions.
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubscriptionOwner]

    def get_queryset(self):
        # Users can only see their own subscription. Admin might see all.
        user = self.request.user
        if user.is_staff:
            return UserSubscription.objects.all().select_related('user', 'plan')
        return UserSubscription.objects.filter(user=user).select_related('user', 'plan')

    def list(self, request, *args, **kwargs):
        # A user typically has one active subscription, so list might not be needed often for user.
        # This effectively becomes a retrieve for the user's single subscription if it exists.
        queryset = self.filter_queryset(self.get_queryset())
        instance = queryset.first() # Get the first (and likely only) subscription for the user
        if not instance:
            return Response({"detail": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


    @action(detail=False, methods=['post'], url_path='create-subscription')
    def create_subscription_action(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.validated_data['plan_id'] # plan_id is validated to be a plan instance
            payment_method_id = serializer.validated_data.get('payment_method_id')
            # coupon_code = serializer.validated_data.get('coupon_code')

            payment_service = PaymentService()
            try:
                # The service method creates the Stripe subscription and local UserSubscription.
                # It might return Stripe's subscription object or parts of it (like client_secret if needed).
                stripe_response_data = payment_service.create_subscription(
                    user=request.user,
                    plan=plan,
                    payment_method_id=payment_method_id,
                    # coupon_code=coupon_code
                )
                # Fetch the local subscription to serialize it
                local_subscription = UserSubscription.objects.get(user=request.user, plan=plan) # Assuming one active
                response_serializer = UserSubscriptionSerializer(local_subscription)

                # If Stripe returned a client_secret for payment confirmation (e.g., 3DS)
                # include it in the response.
                api_response_data = response_serializer.data
                if hasattr(stripe_response_data, 'latest_invoice') and \
                   hasattr(stripe_response_data.latest_invoice, 'payment_intent') and \
                   stripe_response_data.latest_invoice.payment_intent:
                    api_response_data['client_secret'] = stripe_response_data.latest_invoice.payment_intent.client_secret
                elif hasattr(stripe_response_data, 'pending_setup_intent') and \
                     stripe_response_data.pending_setup_intent:
                    api_response_data['client_secret'] = stripe_response_data.pending_setup_intent.client_secret


                return Response(api_response_data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e: # Catch other Stripe or service errors
                # Log the full error e
                return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='cancel-subscription') # Operates on current user's subscription
    def cancel_subscription_action(self, request):
        serializer = CancelSubscriptionSerializer(data=request.data) # Optional: for feedback
        if serializer.is_valid():
            try:
                user_subscription = UserSubscription.objects.get(user=request.user) # Assuming one active sub
                if user_subscription.status == 'cancelled':
                    return Response({"detail": "Subscription is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

                payment_service = PaymentService()
                # Default: cancel at period end. To cancel immediately, pass at_period_end=False
                updated_subscription = payment_service.cancel_subscription(user_subscription, at_period_end=True)
                return Response(UserSubscriptionSerializer(updated_subscription).data, status=status.HTTP_200_OK)
            except UserSubscription.DoesNotExist:
                return Response({"detail": "No active subscription found to cancel."}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows a user's transaction logs to be viewed.
    """
    serializer_class = TransactionLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff: # Admins can see all transactions (be careful with data volume)
            # Add filtering for admin if needed, e.g., by user_id query param
            user_id_filter = self.request.query_params.get('user_id')
            if user_id_filter:
                return TransactionLog.objects.filter(user_id=user_id_filter).select_related('user', 'related_order', 'related_subscription__plan')
            return TransactionLog.objects.all().select_related('user', 'related_order', 'related_subscription__plan')
        return TransactionLog.objects.filter(user=user).select_related('user', 'related_order', 'related_subscription__plan')


# --- Stripe Webhook Handler View ---
@api_view(['POST'])
@csrf_exempt # Important: Stripe webhooks don't send CSRF tokens
@drf_permission_classes([permissions.AllowAny]) # Webhook is public, security is via signature
def stripe_webhook_receiver(request):
    """
    Handles incoming webhooks from Stripe.
    """
    if not hasattr(settings, 'STRIPE_WEBHOOK_SECRET') or not settings.STRIPE_WEBHOOK_SECRET:
        print("ERROR: Stripe webhook secret not configured.")
        return HttpResponse("Webhook secret not configured.", status=500)
    if not stripe.api_key: # Ensure API key is set for stripe.Webhook.construct_event
        print("ERROR: Stripe API key not configured for webhook.")
        return HttpResponse("Stripe API key not configured.", status=500)


    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e: # Invalid payload
        print(f"Webhook ValueError: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e: # Invalid signature
        print(f"Webhook SignatureVerificationError: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        print(f"Webhook general error during construction: {e}")
        return HttpResponse(status=400)


    # Validate the event structure (optional, but good practice)
    # event_serializer = StripeWebhookEventSerializer(data=event) # event is already a StripeObject, not raw dict
    # if not event_serializer.is_valid():
    #     print(f"Webhook event data invalid: {event_serializer.errors}")
    #     return HttpResponse(status=400) # Or log and return 200 to Stripe to stop retries

    # Handle the event
    payment_service = PaymentService()
    event_type = event['type']
    event_data = event['data'] # The 'data' field of the Stripe Event object

    print(f"Received Stripe webhook event: {event_type}")

    if event_type == 'invoice.paid':
        payment_service.handle_invoice_paid(event_data)
    elif event_type == 'invoice.payment_failed':
        # payment_service.handle_invoice_payment_failed(event_data)
        print(f"Unhandled event type: {event_type}")
        pass # Implement handler
    elif event_type == 'customer.subscription.created':
        # payment_service.handle_customer_subscription_created(event_data)
        # Often initial status, main updates on invoice.paid or trial end.
        print(f"Unhandled event type: {event_type}")
        pass
    elif event_type == 'customer.subscription.updated':
        payment_service.handle_customer_subscription_updated(event_data)
    elif event_type == 'customer.subscription.deleted': # 'deleted' means cancelled
        payment_service.handle_customer_subscription_updated(event_data) # Can use same handler
    elif event_type == 'customer.subscription.trial_will_end':
        # payment_service.handle_subscription_trial_will_end(event_data)
        # Send notification to user
        print(f"Unhandled event type: {event_type}")
        pass
    elif event_type == 'payment_intent.succeeded':
        payment_service.handle_payment_intent_succeeded(event_data)
    elif event_type == 'payment_intent.payment_failed':
        # payment_service.handle_payment_intent_failed(event_data)
        # Update order status to 'payment_failed'
        print(f"Unhandled event type: {event_type}")
        pass
    # ... handle other event types as needed ...
    # e.g., 'charge.refunded', 'checkout.session.completed' (if using Stripe Checkout)
    else:
        print(f'Unhandled Stripe event type: {event_type}')

    return HttpResponse(status=200) # Signal to Stripe that webhook was received successfully