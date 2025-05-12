# apps/orders/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.validators import MinValueValidator

from .models import RFQ, Quote, Order, OrderItem
from apps.accounts.serializers import UserSerializer
from apps.listings.models import Material, Design
# from apps.listings.serializers import MaterialSerializer, DesignSerializer # Only if used for read_only nested display

User = get_user_model()

class RFQSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    buyer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='buyer'), source='buyer', write_only=True, required=False
    ) # required=False if perform_create sets it
    quotes_count = serializers.IntegerField(source='quotes.count', read_only=True)
    specifications_file_url = serializers.FileField(source='specifications_file', read_only=True, required=False)

    class Meta:
        model = RFQ
        fields = [
            'id', 'buyer', 'buyer_id', 'title', 'description', 
            'specifications_file', 'specifications_file_url',
            'quantity_required', 'unit_of_measurement', 'deadline_for_quotes',
            'status', 'created_at', 'updated_at', 'quotes_count'
        ]
        read_only_fields = ('id', 'status', 'created_at', 'updated_at', 'quotes_count', 'specifications_file_url', 'buyer')
        extra_kwargs = {
            'specifications_file': {'write_only': True, 'required': False}
        }

    def validate(self, data):
        request = self.context.get('request')
        # If creating and buyer_id is not provided, set current user as buyer
        if not self.instance and 'buyer' not in data and 'buyer_id' not in data and request and hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.user_type == 'buyer':
                data['buyer'] = request.user
            else:
                raise serializers.ValidationError({"detail": "Only buyers can create RFQs for themselves without specifying a buyer ID."})
        # If buyer_id is provided, ensure it's the current user (unless admin)
        elif data.get('buyer_id') and request and hasattr(request, 'user') and data.get('buyer_id') != request.user and not request.user.is_staff:
             raise serializers.ValidationError({"detail": "You can only create RFQs for yourself."})
        return data

class QuoteSerializer(serializers.ModelSerializer):
    supplier = UserSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type__in=['seller', 'manufacturer']), source='supplier', write_only=True, required=False
    ) # required=False if perform_create sets it
    buyer = UserSerializer(read_only=True)
    rfq_id = serializers.PrimaryKeyRelatedField(
        queryset=RFQ.objects.all(), source='rfq', write_only=True, required=False, allow_null=True
    )
    rfq_title = serializers.CharField(source='rfq.title', read_only=True, allow_null=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'rfq', 'rfq_id', 'rfq_title', 'supplier', 'supplier_id', 'buyer',
            'price_per_unit', 'total_price', 'quantity_offered', 'lead_time_days',
            'valid_until', 'notes', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'status', 'created_at', 'updated_at', 'buyer', 'rfq_title', 'rfq', 'supplier')

    def validate(self, data):
        request = self.context.get('request')
        # Determine supplier if not provided via supplier_id
        if not self.instance and 'supplier' not in data and 'supplier_id' not in data and request and hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.user_type in ['seller', 'manufacturer'] or request.user.is_staff:
                data['supplier'] = request.user
            else:
                raise serializers.ValidationError("Only sellers or manufacturers can create quotes.")
        elif data.get('supplier_id') and request and hasattr(request, 'user') and data.get('supplier_id') != request.user and not request.user.is_staff:
            raise serializers.ValidationError("You can only create quotes for yourself.")

        rfq = data.get('rfq') # This will be an RFQ instance if rfq_id was valid
        if rfq:
            # If supplier field was resolved from supplier_id, use that for comparison
            supplier_instance = data.get('supplier', request.user if request else None)
            if rfq.status not in ['open', 'pending']:
                 raise serializers.ValidationError(f"Cannot submit quote for RFQ with status '{rfq.status}'.")
            if rfq.deadline_for_quotes and rfq.deadline_for_quotes < serializers.DateTimeField().to_internal_value(None).date():
                 raise serializers.ValidationError("The deadline for this RFQ has passed.")
            if rfq.buyer == supplier_instance: # Compare RFQ buyer with resolved supplier instance
                raise serializers.ValidationError("You cannot submit a quote for your own RFQ.")
            data['buyer'] = rfq.buyer
        return data

class OrderItemSerializer(serializers.ModelSerializer):
    item_name_display = serializers.CharField(source='item_name_display', read_only=True, required=False)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, required=False)
    seller_username = serializers.CharField(source='seller.username', read_only=True, allow_null=True, required=False)

    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.filter(is_active=True), source='material', 
        required=False, allow_null=True, write_only=True
    )
    design_id = serializers.PrimaryKeyRelatedField(
        queryset=Design.objects.filter(is_active=True), source='design', 
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 
            'material_id', 'design_id', 'custom_item_description',
            'quantity', 'unit_price', 
            'item_name_display', 'subtotal', 'seller_username',
        ]
        read_only_fields = ('id', 'item_name_display', 'subtotal', 'seller_username')
        extra_kwargs = {
            'custom_item_description': {'required': False, 'allow_null': True},
            'unit_price': {'required': True, 'min_value': Decimal('0.01')},
            'quantity': {'required': True, 'validators': [MinValueValidator(1)]},
        }
        
    def validate(self, data):
        material_instance = data.get('material')
        design_instance = data.get('design')
        custom_description = data.get('custom_item_description')

        if not (material_instance or design_instance or custom_description):
            raise serializers.ValidationError({"product_choice": "OrderItem must specify a material, design, or custom description."})
        if sum(bool(x) for x in [material_instance, design_instance, custom_description]) > 1:
            raise serializers.ValidationError({"product_choice": "OrderItem can only be for one product type or custom description."})
        return data

class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True) # Writable for creating order with items
    
    related_quote_id = serializers.PrimaryKeyRelatedField(
        queryset=Quote.objects.all(), source='related_quote', 
        write_only=True, required=False, allow_null=True
    )
    related_quote_details = QuoteSerializer(source='related_quote', read_only=True, required=False)
    order_total_display = serializers.CharField(source='order_total', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'items', 'order_total', 'order_total_display', 'status',
            'shipping_address', 'billing_address', 'payment_intent_id',
            'related_quote_id', 'related_quote_details', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'buyer', 'order_total', 'order_total_display', 'status', 
                            'payment_intent_id', 'created_at', 'updated_at', 'related_quote_details')

    def validate_items(self, items_data):
        if not items_data:
            raise serializers.ValidationError("Order must contain at least one item.")
        if not isinstance(items_data, list):
            raise serializers.ValidationError("Items must be a list.")
        return items_data

    @transaction.atomic
    def create(self, validated_data):
        items_payload = validated_data.pop('items')
        buyer_instance = validated_data.pop('buyer') # Injected by ViewSet's perform_create

        order_specific_data = {
            key: value for key, value in validated_data.items() 
            if key in [f.name for f in Order._meta.get_fields() if f.name != 'id' and not f.one_to_many and not f.many_to_many]
        } # Filter for direct Order fields
        
        order = Order.objects.create(buyer=buyer_instance, **order_specific_data)

        for item_data_from_payload in items_payload:
            # item_data_from_payload is what OrderItemSerializer expects for its fields
            # 'material' or 'design' are resolved from 'material_id'/'design_id' by OrderItemSerializer
            item_serializer = OrderItemSerializer(data=item_data_from_payload, context=self.context)
            if item_serializer.is_valid(raise_exception=True):
                validated_item_data = item_serializer.validated_data
                
                material_instance = validated_item_data.pop('material', None)
                design_instance = validated_item_data.pop('design', None)
                
                item_seller = None
                if material_instance:
                    item_seller = material_instance.seller
                elif design_instance:
                    item_seller = design_instance.designer
                # Add logic for custom item seller if needed

                OrderItem.objects.create(
                    order=order,
                    material=material_instance,
                    design=design_instance,
                    seller=item_seller,
                    **validated_item_data # quantity, unit_price, custom_item_description
                )
            # else: errors raised by raise_exception=True
        
        order.update_total(commit=True)
        return order

    def update(self, instance, validated_data):
        allowed_update_fields = ['shipping_address', 'billing_address']
        fields_to_update_on_model = []
        
        for field in allowed_update_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
                fields_to_update_on_model.append(field)
        
        if fields_to_update_on_model:
            instance.save(update_fields=fields_to_update_on_model)
        return instance

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        if value not in dict(Order.ORDER_STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status value.")
        return value