# apps/orders/models.py
import uuid
from django.db import models, transaction
from django.db.models import F, Sum
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

# Assuming Material and Design are correctly imported and have 'name'/'title' attributes
from apps.listings.models import Material, Design
from apps.core.models import AbstractBaseModel # For created_at, updated_at

# Ensure User model is accessible
User = settings.AUTH_USER_MODEL


class RFQ(AbstractBaseModel): # Inherits created_at, updated_at from AbstractBaseModel
    """
    Request For Quotation
    A buyer creates an RFQ for a custom material, design, or manufacturing service.
    """
    RFQ_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('open', 'Open for Quotes'),
        ('closed', 'Closed for Quotes'),
        ('awarded', 'Awarded'),
        ('cancelled', 'Cancelled'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rfqs_created',
        limit_choices_to={'user_type': 'buyer'}
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    specifications_file = models.FileField(upload_to='rfqs/specifications/%Y/%m/%d/', blank=True, null=True)
    quantity_required = models.PositiveIntegerField(blank=True, null=True)
    unit_of_measurement = models.CharField(max_length=50, blank=True, null=True)
    deadline_for_quotes = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=RFQ_STATUS_CHOICES, default='pending')
    # currency = models.CharField(max_length=3, default='USD') # Optional

    class Meta:
        verbose_name = "Request For Quotation"
        verbose_name_plural = "Requests For Quotations"
        ordering = ['-created_at'] # This will work as AbstractBaseModel has created_at

    def __str__(self):
        return f"RFQ-{str(self.id)[:8]}: {self.title} (by {self.buyer.username})"


class Quote(AbstractBaseModel): # Inherits created_at, updated_at
    """
    A Seller/Manufacturer provides a Quote in response to an RFQ or a direct inquiry.
    """
    QUOTE_STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('viewed', 'Viewed by Buyer'),
        ('accepted', 'Accepted by Buyer'),
        ('rejected', 'Rejected by Buyer'),
        ('expired', 'Expired'),
        ('ordered', 'Converted to Order'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='quotes', null=True, blank=True)
    supplier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quotes_provided',
        limit_choices_to={'user_type__in': ['seller', 'manufacturer']}
    )
    buyer = models.ForeignKey( # Denormalized from RFQ or set for direct quotes
        User,
        on_delete=models.CASCADE,
        related_name='quotes_received'
        # Not limited by user_type, as any user could receive a direct quote
    )
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2) # Should always be set
    quantity_offered = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    valid_until = models.DateField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=QUOTE_STATUS_CHOICES, default='submitted')
    # currency = models.CharField(max_length=3, default='USD') # Optional

    class Meta:
        verbose_name = "Quote"
        verbose_name_plural = "Quotes"
        ordering = ['-created_at']

    def __str__(self):
        if self.rfq:
            return f"Quote for RFQ-{str(self.rfq.id)[:8]} by {self.supplier.username}"
        return f"Direct Quote-{str(self.id)[:8]} from {self.supplier.username} to {self.buyer.username}"

    def save(self, *args, **kwargs):
        if self.rfq and not self.buyer_id: # If buyer isn't set and RFQ exists, populate from RFQ
            self.buyer = self.rfq.buyer
        
        # Auto-calculate total_price if components are there and total_price isn't explicitly set
        # This assumes total_price should be derived if not given.
        if self.price_per_unit is not None and self.quantity_offered is not None and self.total_price is None : # Or force recalculate
             self.total_price = self.price_per_unit * Decimal(self.quantity_offered)
        elif self.total_price is None: # Ensure total_price is not None if components are not there to calculate
            self.total_price = Decimal('0.00') # Fallback, though serializer should enforce this

        super().save(*args, **kwargs)


class Order(AbstractBaseModel): # Inherits created_at, updated_at
    ORDER_STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('payment_failed', 'Payment Failed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled_by_buyer', 'Cancelled by Buyer'),
        ('cancelled_by_seller', 'Cancelled by Seller'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, 
        null=True, # Required if on_delete=SET_NULL
        related_name='orders_placed',
        limit_choices_to={'user_type': 'buyer'}
    )
    order_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    # currency = models.CharField(max_length=3, default='USD') # Consider adding
    status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='pending_payment')
    shipping_address = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    related_quote = models.OneToOneField(
        Quote,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='order_from_quote'
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        buyer_username = self.buyer.username if self.buyer else "N/A"
        return f"Order {str(self.id)[:8]} by {buyer_username} - Status: {self.get_status_display()}"

    @transaction.atomic # Good for multiple item updates if order save triggers item saves
    def update_total(self, commit=True):
        """Calculates and optionally saves the order total from its items."""
        calculated_total = self.items.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total']
        
        self.order_total = calculated_total if calculated_total is not None else Decimal('0.00')
        if commit:
            # Call super().save() to avoid potential recursion if self.save() is overridden
            # with more complex logic than just saving fields.
            # However, if Order.save() is just the default Django save or simple AbstractBaseModel save,
            # self.save() is fine. For clarity and safety with update_fields:
            super(Order, self).save(update_fields=['order_total']) 
        return self.order_total


class OrderItem(AbstractBaseModel): # Inherits created_at, updated_at
    # ID will be auto-incrementing BigAutoField by default from AbstractBaseModel
    # unless AbstractBaseModel defines a UUID id and primary_key=True.
    # Let's assume OrderItem uses default auto ID.

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    design = models.ForeignKey(Design, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    custom_item_description = models.CharField(max_length=255, blank=True, null=True)

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit at the time of order")
    
    seller = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, # Allow null if seller can be deleted
        related_name='sold_items',
        limit_choices_to={'user_type__in': ['seller', 'manufacturer', 'designer']}
    )

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ['created_at'] # Order items by creation time within an order

    @property
    def item_name_display(self):
        if self.material:
            return self.material.name
        if self.design:
            return self.design.name # Uses the 'name' property which returns 'title'
        if self.custom_item_description:
            return self.custom_item_description
        return "N/A (Item unspecified)"

    @property
    def subtotal(self):
        # Ensure quantity and unit_price are not None before multiplication
        if self.quantity is not None and self.unit_price is not None:
            try:
                return Decimal(self.quantity) * Decimal(self.unit_price)
            except (TypeError, ValueError): # Should not happen if fields are validated
                return Decimal('0.00')
        return Decimal('0.00')

    def __str__(self):
        # Ensure order_id is accessed safely, especially if order might not be set yet (though unlikely for existing OrderItem)
        order_id_str = str(self.order_id)[:8] if self.order_id else "N/A"
        return f"{self.quantity or 0} x {self.item_name_display} in Order {order_id_str}"

    def save(self, *args, **kwargs):
        # Auto-populate seller if not explicitly set and product is linked
        if not self.seller_id:
            if self.material and self.material.seller_id:
                self.seller = self.material.seller
            elif self.design and self.design.designer_id:
                self.seller = self.design.designer
            elif self.order and self.order.related_quote and self.order.related_quote.supplier_id:
                # If item is from a quote without direct product link, use quote's supplier
                self.seller = self.order.related_quote.supplier
        
        # Ensure quantity and unit_price have valid defaults if not set by form/serializer
        # (This is defensive; ideally, form/serializer ensures these are set)
        if self.quantity is None: self.quantity = 1 
        if self.unit_price is None: self.unit_price = Decimal('0.00')

        super().save(*args, **kwargs)
        
        # Update order total after an OrderItem is saved or changed
        if self.order: # Check if order is set
            self.order.update_total(commit=True) # Ensure commit=True to save the order

    def delete(self, *args, **kwargs):
        order_to_update = self.order # Get order instance before deleting self
        super().delete(*args, **kwargs)
        if order_to_update:
            order_to_update.update_total(commit=True) # Ensure commit=True