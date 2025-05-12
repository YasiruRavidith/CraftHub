# apps/orders/views.py
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import Http404
from rest_framework import serializers # For serializers.ValidationError

# Import your models
from .models import RFQ, Quote, Order, OrderItem
# from apps.listings.models import Material, Design # Not directly used in views, but by serializers
from django.contrib.auth import get_user_model

# Import your serializers
from .serializers import (
    RFQSerializer, QuoteSerializer, OrderSerializer,
    OrderItemSerializer, OrderStatusUpdateSerializer
)
# Import your permissions
from .permissions import (
    IsBuyerOwnerOrAdminForRFQ, IsSupplierOwnerOrAdminForQuote,
    IsBuyerOwnerOrAdminForOrder, IsParticipantOrAdminReadOnly,
    CanUpdateOrderStatus
)
# Import your services
from .services import OrderService

User = get_user_model()


class RFQViewSet(viewsets.ModelViewSet):
    queryset = RFQ.objects.all().select_related('buyer__profile').prefetch_related('quotes')
    serializer_class = RFQSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsBuyerOwnerOrAdminForRFQ]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RFQ.objects.filter(status='open', deadline_for_quotes__gte=timezone.now())

        if user.is_staff or user.is_superuser:
            return RFQ.objects.all().select_related('buyer__profile').prefetch_related('quotes')
        elif user.user_type == 'buyer':
            return RFQ.objects.filter(
                Q(buyer=user) | Q(status='open', deadline_for_quotes__gte=timezone.now())
            ).distinct().select_related('buyer__profile').prefetch_related('quotes')
        elif user.user_type in ['seller', 'manufacturer']:
            quoted_rfq_ids = Quote.objects.filter(supplier=user).values_list('rfq_id', flat=True)
            return RFQ.objects.filter(
                (Q(status='open', deadline_for_quotes__gte=timezone.now())) | Q(id__in=quoted_rfq_ids)
            ).distinct().select_related('buyer__profile').prefetch_related('quotes')
        return RFQ.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated: # Should be caught by permissions
            raise permissions.PermissionDenied("Authentication required.")
        if self.request.user.user_type != 'buyer' and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only buyers can create RFQs.")
        serializer.save(buyer=self.request.user, status='pending')

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsParticipantOrAdminReadOnly])
    def list_quotes(self, request, id=None):
        rfq = self.get_object()
        user = request.user
        if rfq.buyer == user or user.is_staff:
            quotes = rfq.quotes.all().select_related('supplier__profile')
        elif user.user_type in ['seller', 'manufacturer']:
            quotes = rfq.quotes.filter(supplier=user).select_related('supplier__profile')
        else:
            return Response({"detail": "You do not have permission to view these quotes."}, status=status.HTTP_403_FORBIDDEN)
        serializer = QuoteSerializer(quotes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBuyerOwnerOrAdminForRFQ])
    def award_quote(self, request, id=None):
        rfq = self.get_object()
        quote_id = request.data.get('quote_id')
        if not quote_id:
            return Response({"detail": "quote_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quote_to_award = Quote.objects.get(id=quote_id, rfq=rfq)
        except Quote.DoesNotExist:
            return Response({"detail": "Quote not found for this RFQ."}, status=status.HTTP_404_NOT_FOUND)
        if rfq.status == 'awarded':
            return Response({"detail": "This RFQ has already been awarded."}, status=status.HTTP_400_BAD_REQUEST)
        rfq.status = 'awarded'
        rfq.save(update_fields=['status'])
        quote_to_award.status = 'accepted'
        quote_to_award.save(update_fields=['status'])
        return Response({"detail": f"Quote {quote_to_award.id} has been awarded for RFQ {rfq.id}."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, id=None):
        rfq = self.get_object()
        new_status = request.data.get('status')
        if not new_status or new_status not in [s[0] for s in RFQ.RFQ_STATUS_CHOICES]:
            return Response({"detail": "Invalid or missing status."}, status=status.HTTP_400_BAD_REQUEST)
        if rfq.buyer != request.user and not request.user.is_staff:
            return Response({"detail": "You cannot change the status of this RFQ."}, status=status.HTTP_403_FORBIDDEN)
        rfq.status = new_status
        rfq.save(update_fields=['status'])
        return Response(RFQSerializer(rfq, context={'request': request}).data)


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.all().select_related('supplier__profile', 'buyer__profile', 'rfq')
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwnerOrAdminForQuote]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Quote.objects.none()
        if user.is_staff or user.is_superuser:
            return Quote.objects.all().select_related('supplier__profile', 'buyer__profile', 'rfq')
        return Quote.objects.filter(
            Q(supplier=user) | Q(buyer=user)
        ).distinct().select_related('supplier__profile', 'buyer__profile', 'rfq')

    def perform_create(self, serializer):
        rfq_id = self.request.data.get('rfq_id')
        rfq_instance = None
        buyer_instance = None
        if rfq_id:
            rfq_instance = get_object_or_404(RFQ, id=rfq_id)
            if rfq_instance.buyer == self.request.user:
                 raise permissions.PermissionDenied("You cannot submit a quote for your own RFQ.")
            if rfq_instance.status != 'open':
                 raise permissions.PermissionDenied(f"This RFQ is not open for quotes (status: {rfq_instance.status}).")
            if rfq_instance.deadline_for_quotes and rfq_instance.deadline_for_quotes < timezone.now():
                 raise permissions.PermissionDenied("The deadline for this RFQ has passed.")
            buyer_instance = rfq_instance.buyer
        
        if self.request.user.user_type not in ['seller', 'manufacturer'] and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only sellers or manufacturers can submit quotes.")
        serializer.save(supplier=self.request.user, rfq=rfq_instance, buyer=buyer_instance)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBuyerOwnerOrAdminForRFQ])
    def accept(self, request, id=None):
        quote = self.get_object()
        if quote.rfq and quote.rfq.buyer != request.user:
            return Response({"detail": "You are not authorized to accept this quote (not RFQ buyer)."}, status=status.HTTP_403_FORBIDDEN)
        if not quote.rfq and quote.buyer != request.user:
            return Response({"detail": "You are not authorized to accept this quote (not direct buyer)."}, status=status.HTTP_403_FORBIDDEN)

        if quote.status in ['accepted', 'ordered', 'rejected', 'expired']:
            return Response({"detail": f"Quote status is '{quote.status}' and cannot be accepted again."}, status=status.HTTP_400_BAD_REQUEST)
        if quote.valid_until < timezone.now().date():
            quote.status = 'expired'
            quote.save(update_fields=['status'])
            return Response({"detail": "This quote has expired."}, status=status.HTTP_400_BAD_REQUEST)

        order_service = OrderService()
        try:
            order = order_service.create_order_from_quote(quote, request.user)
            return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"An error occurred while creating order: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBuyerOwnerOrAdminForRFQ])
    def reject(self, request, id=None):
        quote = self.get_object()
        if (quote.rfq and quote.rfq.buyer != request.user) or (not quote.rfq and quote.buyer != request.user):
            return Response({"detail": "You are not authorized to reject this quote."}, status=status.HTTP_403_FORBIDDEN)
        quote.status = 'rejected'
        quote.save(update_fields=['status'])
        return Response({"detail": "Quote rejected."}, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related(
        'buyer__profile', 
        'related_quote__supplier__profile',
        'related_quote__rfq'
    ).prefetch_related(
        'items__material', 
        'items__design', 
        'items__seller__profile'
    )
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyerOwnerOrAdminForOrder]
    # To test if permissions are the cause of 405, uncomment below and comment above:
    # permission_classes = [permissions.IsAuthenticated] 
    # permission_classes = [permissions.AllowAny] # For extreme debugging of 405
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        base_qs = Order.objects.all().select_related( # Changed from super().get_queryset() for clarity
            'buyer__profile', 
            'related_quote__supplier__profile',
            'related_quote__rfq'
        ).prefetch_related(
            'items__material__category', # Example deeper prefetch
            'items__design__category',   # Example deeper prefetch
            'items__seller__profile'
        )
        if user.is_staff or user.is_superuser:
            return base_qs
        return base_qs.filter(Q(buyer=user) | Q(items__seller=user)).distinct()

    def create(self, request, *args, **kwargs):
        print(f"OrderViewSet: CREATE method CALLED by user: {request.user}")
        print("OrderViewSet: Request data:", request.data)
        try:
            serializer = self.get_serializer(data=request.data)
            print("OrderViewSet: Serializer instantiated")
            # Temporarily set raise_exception=False to see errors if is_valid fails
            if serializer.is_valid(raise_exception=False): 
                print("OrderViewSet: Serializer is valid")
                self.perform_create(serializer) # This calls serializer.save(buyer=request.user)
                headers = self.get_success_headers(serializer.data)
                print("OrderViewSet: Order creation successful in create method, returning 201")
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                print("OrderViewSet: Serializer errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"OrderViewSet: Exception in create method: {type(e).__name__} - {e}")
            # Log the full traceback here in a real app
            return Response({"detail": f"Server error during order creation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        print(f"OrderViewSet: perform_create CALLED by user: {self.request.user}")
        if not self.request.user.is_authenticated:
            raise permissions.PermissionDenied("Authentication required to create an order.")
        if self.request.user.user_type != 'buyer' and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only buyers or administrators can create orders.")
        try:
            serializer.save(buyer=self.request.user)
            print(f"OrderViewSet: Order saved by perform_create for buyer: {self.request.user.username}, Order ID: {serializer.instance.id}")
        except serializers.ValidationError as e:
            print(f"OrderViewSet: ValidationError in perform_create (from serializer.save): {e.detail}")
            raise
        except Exception as e:
            print(f"OrderViewSet: Unexpected error in perform_create: {type(e).__name__} - {e}")
            raise serializers.ValidationError({"detail": f"An unexpected error occurred in perform_create: {str(e)}"})
    
    @action(detail=True, methods=['post'], url_path='update-status', permission_classes=[permissions.IsAuthenticated, CanUpdateOrderStatus])
    def update_status(self, request, id=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True, context={'request': request, 'order': order})
        if serializer.is_valid():
            order_service = OrderService()
            try:
                updated_order = order_service.update_order_status(order, serializer.validated_data['status'], request.user)
                return Response(OrderSerializer(updated_order, context={'request': request}).data)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except permissions.PermissionDenied as e:
                return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                return Response({"detail": "An error occurred while updating status."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='initiate-payment')
    def initiate_payment(self, request, id=None):
        order = self.get_object()
        if order.buyer != request.user and not request.user.is_staff:
            return Response({"detail": "You are not authorized to initiate payment for this order."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'pending_payment':
            return Response({"detail": f"Order status is '{order.status}', payment cannot be initiated."}, status=status.HTTP_400_BAD_REQUEST)

        order_service = OrderService()
        try:
            payment_info = order_service.initiate_payment_for_order(order)
            return Response(payment_info, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Payment initiation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='items')
    def list_order_items(self, request, id=None):
        order = self.get_object()
        items = order.items.all().select_related('material', 'design', 'seller__profile')
        serializer = OrderItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)