from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import RFQ, Quote, Order, OrderItem
from .serializers import (
    RFQSerializer, QuoteSerializer, OrderSerializer,
    OrderItemSerializer, OrderStatusUpdateSerializer
)
from .permissions import ( # You'll need to create these permissions
    IsBuyerOwnerOrAdminForRFQ, IsSupplierOwnerOrAdminForQuote,
    IsBuyerOwnerOrAdminForOrder, IsParticipantOrAdminReadOnly,
    CanUpdateOrderStatus
)
from .services import OrderService # We'll create this later for business logic

class RFQViewSet(viewsets.ModelViewSet):
    queryset = RFQ.objects.all().select_related('buyer__profile').prefetch_related('quotes')
    serializer_class = RFQSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsBuyerOwnerOrAdminForRFQ]
    lookup_field = 'id' # Use UUID

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RFQ.objects.filter(status='open', deadline_for_quotes__gte=timezone.now()) # Public, open RFQs

        if user.is_staff or user.is_superuser:
            return RFQ.objects.all().select_related('buyer__profile').prefetch_related('quotes')
        elif user.user_type == 'buyer':
            # Buyers see their own RFQs and open RFQs
            return RFQ.objects.filter(
                Q(buyer=user) | Q(status='open', deadline_for_quotes__gte=timezone.now())
            ).distinct().select_related('buyer__profile').prefetch_related('quotes')
        elif user.user_type in ['seller', 'manufacturer']:
            # Suppliers see open RFQs they haven't quoted on yet, and RFQs they have quoted on
            quoted_rfq_ids = Quote.objects.filter(supplier=user).values_list('rfq_id', flat=True)
            return RFQ.objects.filter(
                (Q(status='open', deadline_for_quotes__gte=timezone.now())) | Q(id__in=quoted_rfq_ids)
            ).distinct().select_related('buyer__profile').prefetch_related('quotes')
        return RFQ.objects.none()


    def perform_create(self, serializer):
        if self.request.user.user_type != 'buyer' and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only buyers can create RFQs.")
        serializer.save(buyer=self.request.user, status='pending') # Or 'open' if direct

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsParticipantOrAdminReadOnly])
    def list_quotes(self, request, id=None):
        """List all quotes submitted for a specific RFQ."""
        rfq = self.get_object()
        # Permissions: Buyer of RFQ, Suppliers who quoted, or Admin can see all quotes for an RFQ.
        # Other suppliers should not see competitors' quotes unless RFQ is closed and bids are public (not implemented here).
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

        # Business logic for awarding (e.g., update statuses)
        rfq.status = 'awarded'
        rfq.save(update_fields=['status'])
        quote_to_award.status = 'accepted' # Or a specific "awarded" status if needed
        quote_to_award.save(update_fields=['status'])

        # Reject other quotes for this RFQ
        # rfq.quotes.exclude(id=quote_to_award.id).update(status='rejected') # Or some other status

        return Response({"detail": f"Quote {quote_to_award.id} has been awarded for RFQ {rfq.id}."}, status=status.HTTP_200_OK)

    # Actions to change RFQ status (e.g., open, close, cancel)
    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, id=None):
        rfq = self.get_object()
        new_status = request.data.get('status')
        if not new_status or new_status not in [s[0] for s in RFQ.RFQ_STATUS_CHOICES]:
            return Response({"detail": "Invalid or missing status."}, status=status.HTTP_400_BAD_REQUEST)

        # Add permission check for who can change status (e.g., buyer or admin)
        if rfq.buyer != request.user and not request.user.is_staff:
            return Response({"detail": "You cannot change the status of this RFQ."}, status=status.HTTP_403_FORBIDDEN)

        rfq.status = new_status
        rfq.save(update_fields=['status'])
        return Response(RFQSerializer(rfq, context={'request': request}).data)


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.all().select_related('supplier__profile', 'buyer__profile', 'rfq')
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwnerOrAdminForQuote] # Or more granular
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Quote.objects.none() # Quotes are not generally public

        if user.is_staff or user.is_superuser:
            return Quote.objects.all().select_related('supplier__profile', 'buyer__profile', 'rfq')

        # Suppliers see quotes they provided. Buyers see quotes they received.
        return Quote.objects.filter(
            Q(supplier=user) | Q(buyer=user)
        ).distinct().select_related('supplier__profile', 'buyer__profile', 'rfq')


    def perform_create(self, serializer):
        rfq_id = self.request.data.get('rfq_id')
        rfq = None
        if rfq_id:
            rfq = get_object_or_404(RFQ, id=rfq_id)
            if rfq.buyer == self.request.user:
                 raise permissions.PermissionDenied("You cannot submit a quote for your own RFQ.")
            if rfq.status != 'open':
                 raise permissions.PermissionDenied(f"This RFQ is not open for quotes (status: {rfq.status}).")
            if rfq.deadline_for_quotes and rfq.deadline_for_quotes < timezone.now():
                 raise permissions.PermissionDenied("The deadline for this RFQ has passed.")

        if self.request.user.user_type not in ['seller', 'manufacturer'] and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only sellers or manufacturers can submit quotes.")

        serializer.save(supplier=self.request.user, rfq=rfq, buyer=rfq.buyer if rfq else None) # Buyer from RFQ

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBuyerOwnerOrAdminForRFQ]) # Buyer of RFQ accepts
    def accept(self, request, id=None):
        quote = self.get_object()
        if quote.rfq and quote.rfq.buyer != request.user:
            return Response({"detail": "You are not authorized to accept this quote."}, status=status.HTTP_403_FORBIDDEN)
        if quote.buyer != request.user: # For direct quotes
            return Response({"detail": "You are not authorized to accept this quote."}, status=status.HTTP_403_FORBIDDEN)


        if quote.status == 'accepted' or quote.status == 'ordered':
            return Response({"detail": f"Quote is already {quote.status}."}, status=status.HTTP_400_BAD_REQUEST)
        if quote.valid_until < timezone.now().date():
            quote.status = 'expired'
            quote.save()
            return Response({"detail": "This quote has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # OrderService can handle the creation of order from quote
        order_service = OrderService()
        try:
            order = order_service.create_order_from_quote(quote, request.user)
            quote.status = 'ordered' # Or 'accepted' then 'ordered'
            quote.save(update_fields=['status'])
            if quote.rfq:
                quote.rfq.status = 'awarded'
                quote.rfq.save(update_fields=['status'])
            return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBuyerOwnerOrAdminForRFQ]) # Buyer of RFQ rejects
    def reject(self, request, id=None):
        quote = self.get_object()
        if (quote.rfq and quote.rfq.buyer != request.user) or (not quote.rfq and quote.buyer != request.user) :
            return Response({"detail": "You are not authorized to reject this quote."}, status=status.HTTP_403_FORBIDDEN)

        quote.status = 'rejected'
        quote.save(update_fields=['status'])
        return Response({"detail": "Quote rejected."}, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related('buyer__profile', 'related_quote').prefetch_related('items__material', 'items__design', 'items__seller__profile')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyerOwnerOrAdminForOrder] # Or specific for seller/admin
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()

        if user.is_staff or user.is_superuser:
            return self.queryset # Admin sees all

        if user.user_type == 'buyer':
            return self.queryset.filter(buyer=user)
        elif user.user_type in ['seller', 'manufacturer', 'designer']:
            # Sellers/Manufacturers/Designers see orders containing their items
            return self.queryset.filter(items__seller=user).distinct()
        return Order.objects.none()

    def perform_create(self, serializer):
        if self.request.user.user_type != 'buyer' and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only buyers can create orders.")
        # The OrderService will handle the creation logic, including items
        order_service = OrderService()
        try:
            # Pass request.data directly if serializer handles items internally,
            # or pass structured data to service
            items_data = serializer.validated_data.get('items', [])
            related_quote_id = serializer.validated_data.get('related_quote_id') # Corrected: Use related_quote_id if it's in validated_data from serializer
            shipping_address = serializer.validated_data.get('shipping_address')
            billing_address = serializer.validated_data.get('billing_address')

            order = order_service.create_order(
                buyer=self.request.user,
                items_data=items_data,
                related_quote_id=related_quote_id.id if related_quote_id else None, # Pass the id of the quote object
                shipping_address=shipping_address,
                billing_address=billing_address
            )
            # The serializer.save() will actually call OrderSerializer.create now.
            # So, the logic in perform_create might be redundant if serializer's create is robust.
            # Let's rely on serializer.save() for now, assuming it handles everything.
            serializer.save(buyer=self.request.user) # The serializer's create method will be called
        except Exception as e:
            # This exception handling might be too broad here if serializer handles it
            raise serializers.ValidationError(str(e))


    @action(detail=True, methods=['post'], url_path='update-status', permission_classes=[permissions.IsAuthenticated, CanUpdateOrderStatus])
    def update_status(self, request, id=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True, context={'request': request, 'order': order})
        if serializer.is_valid():
            # OrderService could also handle status transitions and side effects
            order_service = OrderService()
            try:
                updated_order = order_service.update_order_status(order, serializer.validated_data['status'], request.user)
                return Response(OrderSerializer(updated_order, context={'request': request}).data)
            except ValueError as e: # For invalid transitions
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except permissions.PermissionDenied as e:
                return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='initiate-payment')
    def initiate_payment(self, request, id=None):
        order = self.get_object()
        if order.buyer != request.user and not request.user.is_staff:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'pending_payment':
            return Response({"detail": f"Order status is '{order.status}', cannot initiate payment."}, status=status.HTTP_400_BAD_REQUEST)

        order_service = OrderService()
        try:
            # Assuming payment_info contains client_secret for Stripe, etc.
            payment_info = order_service.initiate_payment_for_order(order)
            return Response(payment_info, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Payment initiation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='items')
    def list_order_items(self, request, id=None):
        order = self.get_object()
        # Permissions should ensure user can view this order (handled by ViewSet's permission_classes)
        items = order.items.all().select_related('material', 'design', 'seller__profile')
        serializer = OrderItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

# If you need separate CRUD for OrderItems (less common, usually managed via Order)
# class OrderItemViewSet(viewsets.ModelViewSet):
#     queryset = OrderItem.objects.all()
#     serializer_class = OrderItemSerializer
#     permission_classes = [permissions.IsAuthenticated] # Highly restrictive, e.g., admin only or specific order owner logic