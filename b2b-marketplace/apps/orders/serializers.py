from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from .models import RFQ, Quote, Order, OrderItem
from apps.accounts.serializers import UserSerializer # For buyer/supplier details
from apps.listings.serializers import MaterialSerializer, DesignSerializer # For item details
from apps.listings.models import Material, Design # To fetch products
from django.contrib.auth import get_user_model # ADD THIS
User = get_user_model() 

class RFQSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    buyer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='buyer'),
        source='buyer',
        write_only=True,
        # default=serializers.CurrentUserDefault() # Auto-set buyer if user is creating
    )
    quotes_count = serializers.IntegerField(source='quotes.count', read_only=True)
    specifications_file_url = serializers.FileField(source='specifications_file', read_only=True)

    class Meta:
        model = RFQ
        fields = [
            'id', 'buyer', 'buyer_id', 'title', 'description', 'specifications_file', 'specifications_file_url',
            'quantity_required', 'unit_of_measurement', 'deadline_for_quotes',
            'status', 'created_at', 'updated_at', 'quotes_count'
        ]
        read_only_fields = ('id', 'status', 'created_at', 'updated_at', 'quotes_count', 'specifications_file_url')
        extra_kwargs = {
            'specifications_file': {'write_only': True, 'required': False}
        }

    def validate(self, data):
        # Set buyer automatically if not provided and user is authenticated
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if 'buyer' not in data and 'buyer_id' not in data : # Check if buyer_id is also not in data
                if request.user.user_type == 'buyer':
                    data['buyer'] = request.user
                else:
                    raise serializers.ValidationError("Only users of type 'buyer' can create RFQs for themselves.")
            elif 'buyer_id' in data and data.get('buyer_id') != request.user and not request.user.is_staff:
                 raise serializers.ValidationError("You can only create RFQs for yourself.")

        return data


class QuoteSerializer(serializers.ModelSerializer):
    supplier = UserSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type__in=['seller', 'manufacturer']),
        source='supplier',
        write_only=True
    )
    buyer = UserSerializer(read_only=True) # Buyer is often derived from RFQ
    rfq_id = serializers.PrimaryKeyRelatedField(queryset=RFQ.objects.all(), source='rfq', write_only=True, required=False, allow_null=True)
    rfq_title = serializers.CharField(source='rfq.title', read_only=True, allow_null=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'rfq', 'rfq_id', 'rfq_title', 'supplier', 'supplier_id', 'buyer',
            'price_per_unit', 'total_price', 'quantity_offered', 'lead_time_days',
            'valid_until', 'notes', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'status', 'created_at', 'updated_at', 'buyer', 'rfq_title')

    def validate(self, data):
        request = self.context.get('request')
        supplier = data.get('supplier') or (request.user if request and hasattr(request, 'user') else None)

        if not supplier or not (supplier.user_type in ['seller', 'manufacturer'] or supplier.is_staff):
            raise serializers.ValidationError("Only sellers or manufacturers can create quotes.")

        if 'supplier' not in data and 'supplier_id' not in data: # If write_only supplier_id is not passed
            data['supplier'] = supplier
        elif 'supplier_id' in data and data.get('supplier_id') != supplier and not request.user.is_staff:
            raise serializers.ValidationError("You can only create quotes for yourself.")

        rfq = data.get('rfq')
        if rfq:
            if rfq.status not in ['open', 'pending']: # Or just 'open'
                 raise serializers.ValidationError(f"Cannot submit quote for RFQ with status '{rfq.status}'.")
            if rfq.deadline_for_quotes and rfq.deadline_for_quotes < serializers.DateTimeField().to_internal_value(None).date(): # Compare with today
                 raise serializers.ValidationError("The deadline for submitting quotes for this RFQ has passed.")
            if rfq.buyer == supplier:
                raise serializers.ValidationError("You cannot submit a quote for your own RFQ.")
            data['buyer'] = rfq.buyer # Set buyer from RFQ
        elif not data.get('buyer_id') and not self.instance: # If direct quote, buyer must be specified
            # For direct quotes (no RFQ), buyer_id must be provided (not implemented in this basic serializer yet)
            # This would require adding buyer_id as a writeable field for direct quotes.
            # For now, we assume quotes are primarily for RFQs.
            pass

        return data


class OrderItemSerializer(serializers.ModelSerializer):
    # For displaying product info
    material_details = MaterialSerializer(source='material', read_only=True)
    design_details = DesignSerializer(source='design', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    item_name = serializers.CharField(read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True, allow_null=True)

    # For creating/updating order items
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.filter(is_active=True), source='material', write_only=True, required=False, allow_null=True
    )
    design_id = serializers.PrimaryKeyRelatedField(
        queryset=Design.objects.filter(is_active=True), source='design', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'material_id', 'design_id', 'custom_item_description',
            'quantity', 'unit_price', 'subtotal', 'item_name', 'seller', 'seller_username',
            'material_details', 'design_details'
        ]
        read_only_fields = ('id', 'order', 'subtotal', 'item_name', 'seller', 'seller_username') # order is set by OrderSerializer

    def validate(self, data):
        material = data.get('material')
        design = data.get('design')
        custom_description = data.get('custom_item_description')

        if not (material or design or custom_description):
            raise serializers.ValidationError("OrderItem must have a material, design, or custom item description.")
        if sum(bool(x) for x in [material, design, custom_description]) > 1:
            raise serializers.ValidationError("OrderItem can only be for one type: material, design, or custom.")

        # Unit price should be set, possibly fetched if not a custom item
        if not data.get('unit_price'):
            if material:
                data['unit_price'] = material.price_per_unit
            elif design:
                data['unit_price'] = design.price # Assuming design has a price
            # For custom_item_description, unit_price must be provided in the request.
            # Or it's derived from a Quote.
            elif not self.instance: # For new items, if custom and no price, it's an error
                raise serializers.ValidationError("Unit price must be provided for custom items.")
        return data


class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True) # For creating orders with items
    # items_read = OrderItemSerializer(many=True, read_only=True, source='items') # Separate for reading if needed

    related_quote_id = serializers.PrimaryKeyRelatedField(
        queryset=Quote.objects.all(), source='related_quote', write_only=True, required=False, allow_null=True
    )
    related_quote_details = QuoteSerializer(source='related_quote', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'items', 'order_total', 'status',
            'shipping_address', 'billing_address', 'payment_intent_id',
            'related_quote_id', 'related_quote_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'order_total', 'status', 'payment_intent_id', 'created_at', 'updated_at')

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if not self.instance: # On creation
                if request.user.user_type != 'buyer' and not request.user.is_staff:
                    raise serializers.ValidationError("Only 'buyer' type users can create orders.")
            # For updates, permissions should handle who can update.
        else:
            raise serializers.ValidationError("User must be authenticated.")
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        buyer = request.user

        # Handle order from quote
        related_quote = validated_data.get('related_quote')
        if related_quote:
            if related_quote.status not in ['accepted', 'submitted']: # Or just 'accepted'
                raise serializers.ValidationError(f"Cannot create order from quote with status '{related_quote.status}'.")
            if related_quote.buyer != buyer:
                raise serializers.ValidationError("This quote was not addressed to you.")
            # Create order
            order = Order.objects.create(buyer=buyer, related_quote=related_quote, **validated_data)
            # Create order item from quote details
            OrderItem.objects.create(
                order=order,
                custom_item_description=f"Order from Quote {related_quote.id}: {related_quote.rfq.title if related_quote.rfq else 'Direct Quote'}", # Or more specific
                quantity=related_quote.quantity_offered or 1,
                unit_price=related_quote.total_price / (related_quote.quantity_offered or 1), # Or just total_price as unit if quantity is 1
                seller=related_quote.supplier
            )
            related_quote.status = 'ordered'
            related_quote.save(update_fields=['status'])
        else: # Order from cart/direct items
            order = Order.objects.create(buyer=buyer, **validated_data)
            order_total = 0
            for item_data in items_data:
                material = item_data.get('material')
                design = item_data.get('design')
                unit_price = item_data.get('unit_price')
                seller = None

                if material:
                    unit_price = unit_price or material.price_per_unit
                    seller = material.seller
                elif design:
                    unit_price = unit_price or design.price
                    seller = design.designer
                # For custom_item_description, unit_price must be provided.
                # And seller also needs to be determined (e.g., from a pre-negotiation not captured by Quote model).
                # This part needs more robust logic for custom items not from quotes.

                if not unit_price: # Should be caught by OrderItemSerializer.validate
                    raise serializers.ValidationError(f"Unit price missing for item: {item_data.get('custom_item_description') or material or design}")

                OrderItem.objects.create(order=order, seller=seller, unit_price=unit_price, **item_data)
        
        order.update_total() # Recalculate and save total
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        # Basic update for fields like shipping_address, billing_address.
        # Updating items for an existing order can be complex (add, remove, change quantity).
        # For simplicity, this basic update won't handle item modifications.
        # You might want a separate endpoint for managing order items of an existing order.
        items_data = validated_data.pop('items', None) # Not handling item updates in this basic version

        # Only certain fields should be updatable by the user, and status by admin/system
        allowed_user_update_fields = ['shipping_address', 'billing_address']
        # Status updates should be handled by specific actions or admin.

        for attr, value in validated_data.items():
            if attr in allowed_user_update_fields:
                setattr(instance, attr, value)
            # Add more logic if other fields are updatable under certain conditions

        instance.save()

        # If you were to handle item updates:
        # if items_data:
        #     # Logic to add/remove/update items. Could involve deleting existing items and recreating.
        #     instance.items.all().delete() # Simplistic: clear and re-add
        #     for item_data in items_data:
        #         OrderItem.objects.create(order=instance, **item_data)
        #     instance.update_total()

        return instance


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        # Add any specific validation for status transitions if needed
        # For example, an order cannot go from 'shipped' back to 'processing' by a regular user.
        # This might be better handled in view permissions or service layer.
        if value not in dict(Order.ORDER_STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status value.")
        return value