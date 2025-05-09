import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

from apps.listings.models import Material, Design # Assuming Material/Design can be ordered
from apps.core.models import AbstractBaseModel # For created_at, updated_at


# If core.AbstractBaseModel isn't defined yet, you'll need to add
# created_at = models.DateTimeField(auto_now_add=True)
# updated_at = models.DateTimeField(auto_now=True)
# to each model that needs it.

class RFQ(AbstractBaseModel):
    """
    Request For Quotation
    A buyer creates an RFQ for a custom material, design, or manufacturing service.
    """
    RFQ_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('open', 'Open for Quotes'), # Suppliers can submit quotes
        ('closed', 'Closed for Quotes'), # No more quotes accepted
        ('awarded', 'Awarded'), # A quote has been selected
        ('cancelled', 'Cancelled'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rfqs_created', limit_choices_to={'user_type': 'buyer'})
    title = models.CharField(max_length=255)
    description = models.TextField()
    specifications_file = models.FileField(upload_to='rfqs/specifications/', blank=True, null=True)
    quantity_required = models.PositiveIntegerField(blank=True, null=True)
    unit_of_measurement = models.CharField(max_length=50, blank=True, null=True)
    deadline_for_quotes = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=RFQ_STATUS_CHOICES, default='pending')
    # Potentially link to specific Material/Design types if RFQ is for modification
    # related_material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    # related_design = models.ForeignKey(Design, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"RFQ-{self.id}: {self.title} by {self.buyer.username}"

class Quote(AbstractBaseModel):
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quotes_provided',
        limit_choices_to={'user_type__in': ['seller', 'manufacturer']}
    )
    buyer = models.ForeignKey( # Denormalized for easier querying, or derive from RFQ
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quotes_received'
    )
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_offered = models.PositiveIntegerField(null=True, blank=True)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    valid_until = models.DateField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=QUOTE_STATUS_CHOICES, default='submitted')
    # If quote is for specific item not in RFQ (e.g. direct quote request for existing listing)
    # material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    # design = models.ForeignKey(Design, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.rfq:
            return f"Quote for RFQ-{self.rfq.id} by {self.supplier.username}"
        return f"Direct Quote-{self.id} by {self.supplier.username} to {self.buyer.username}"

    def save(self, *args, **kwargs):
        if self.rfq and not self.buyer_id: # Set buyer from RFQ if not directly set
            self.buyer = self.rfq.buyer
        super().save(*args, **kwargs)


class Order(AbstractBaseModel):
    ORDER_STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('payment_failed', 'Payment Failed'),
        ('processing', 'Processing'),          # Seller/Manufacturer confirmed, working on it
        ('shipped', 'Shipped'),                # For physical goods
        ('delivered', 'Delivered'),            # For physical goods
        ('completed', 'Completed'),            # For services or digital goods
        ('cancelled_by_buyer', 'Cancelled by Buyer'),
        ('cancelled_by_seller', 'Cancelled by Seller'),
        ('refunded', 'Refunded'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders_placed', limit_choices_to={'user_type': 'buyer'})
    # Seller is determined by the items in the order, but can be denormalized if all items from one seller.
    # For multi-vendor carts, seller is on OrderItem.
    # If an order is always from one seller:
    # seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders_received', limit_choices_to={'user_type__in': ['seller', 'manufacturer']})

    order_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='pending_payment')
    shipping_address = models.TextField(blank=True, null=True) # Could be a ForeignKey to an Address model
    billing_address = models.TextField(blank=True, null=True)  # Could be a ForeignKey to an Address model
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True) # For Stripe etc.
    related_quote = models.OneToOneField(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_from_quote')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.buyer.username if self.buyer else 'N/A'}"

    def update_total(self):
        total = self.items.aggregate(total=models.Sum(models.F('quantity') * models.F('unit_price')))['total']
        self.order_total = total if total else Decimal('0.00')
        self.save(update_fields=['order_total'])


class OrderItem(AbstractBaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # Link to the product being ordered
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    design = models.ForeignKey(Design, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    # If custom item from RFQ/Quote not tied to existing listing:
    custom_item_description = models.CharField(max_length=255, blank=True, null=True)

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit at the time of order")
    # Denormalize seller here for multi-vendor carts
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='sold_items',
        limit_choices_to={'user_type__in': ['seller', 'manufacturer', 'designer']} # Designer can sell designs
    )

    # Ensure either material, design, or custom_item_description is provided
    # This can be enforced in a clean method or serializer validation

    @property
    def item_name(self):
        if self.material:
            return self.material.name
        if self.design:
            return self.design.title
        if self.custom_item_description:
            return self.custom_item_description
        return "N/A"

    @property
    def subtotal(self):
        if self.quantity is not None and self.unit_price is not None:
            try:
                # Ensure they are of types that can be multiplied
                return Decimal(self.quantity) * Decimal(self.unit_price)
            except (TypeError, ValueError):
                # Handle cases where conversion to Decimal might fail if they are not numeric
                return Decimal('0.00')
        return Decimal('0.00') # Default to 0.00 if either is None

    def __str__(self):
        return f"{self.quantity or 0} x {self.item_name} in Order {self.order.id}" 

        super().save(*args, **kwargs)
        # Update order total after saving an item
        if self.order:
            self.order.update_total()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.update_total()