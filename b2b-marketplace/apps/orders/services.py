from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from decimal import Decimal

from .models import Order, OrderItem, Quote, RFQ
from apps.listings.models import Material, Design
# from apps.payments_monetization.services import PaymentService # Assuming a PaymentService for payment processing

User = settings.AUTH_USER_MODEL

class OrderService:
    """
    Service layer for handling complex order-related business logic.
    """

    @transaction.atomic
    def create_order(self, buyer: User, items_data: list,
                     shipping_address: str = None, billing_address: str = None,
                     related_quote_id: str = None) -> Order:
        """
        Creates a new order.
        items_data: list of dicts, e.g.,
                    [{'material_id': id, 'quantity': q, 'unit_price': p (optional)},
                     {'design_id': id, 'quantity': q, 'unit_price': p (optional)},
                     {'custom_item_description': 'desc', 'quantity': q, 'unit_price': p, 'seller_id': id}]
        """
        if buyer.user_type != 'buyer' and not buyer.is_staff:
            raise PermissionDenied("Only buyers can create orders.")

        related_quote = None
        if related_quote_id:
            try:
                related_quote = Quote.objects.select_related('supplier', 'rfq__buyer').get(id=related_quote_id)
                if related_quote.buyer != buyer and (related_quote.rfq and related_quote.rfq.buyer != buyer):
                    raise PermissionDenied("This quote is not addressed to you.")
                if related_quote.status not in ['accepted', 'submitted', 'viewed']: # Ensure quote is in a valid state
                    raise DjangoValidationError(f"Cannot create order from quote with status '{related_quote.status}'.")
                if related_quote.valid_until < timezone.now().date():
                    related_quote.status = 'expired'
                    related_quote.save()
                    raise DjangoValidationError("The quote has expired and cannot be converted to an order.")

            except Quote.DoesNotExist:
                raise DjangoValidationError("Related quote not found.")

        order = Order.objects.create(
            buyer=buyer,
            shipping_address=shipping_address,
            billing_address=billing_address,
            related_quote=related_quote,
            status='pending_payment' # Initial status
        )

        if related_quote:
            # Create order item from quote
            OrderItem.objects.create(
                order=order,
                custom_item_description=f"From Quote {related_quote.id}: {related_quote.rfq.title if related_quote.rfq else related_quote.notes or 'Quoted Item'}",
                quantity=related_quote.quantity_offered or 1,
                unit_price=related_quote.total_price / (related_quote.quantity_offered or Decimal('1.0')), # Ensure Decimal division
                seller=related_quote.supplier
            )
            related_quote.status = 'ordered'
            related_quote.save(update_fields=['status'])
            if related_quote.rfq:
                related_quote.rfq.status = 'awarded' # Mark RFQ as awarded
                related_quote.rfq.save(update_fields=['status'])
        else:
            # Create order items from items_data (cart-like scenario)
            if not items_data:
                order.delete() # Clean up if no items
                raise DjangoValidationError("Order must contain at least one item.")

            for item_data in items_data:
                material_id = item_data.get('material_id')
                design_id = item_data.get('design_id')
                custom_desc = item_data.get('custom_item_description')
                quantity = item_data.get('quantity')
                unit_price = item_data.get('unit_price') # Price at the time of adding to cart/order
                seller = None # Seller for the item

                if not quantity or int(quantity) <= 0:
                    order.delete()
                    raise DjangoValidationError("Item quantity must be positive.")

                product_obj = None
                if material_id:
                    try:
                        product_obj = Material.objects.get(id=material_id, is_active=True)
                        seller = product_obj.seller
                        unit_price = Decimal(unit_price) if unit_price is not None else product_obj.price_per_unit
                        # Check stock if applicable (simplified here)
                        # if product_obj.stock_quantity is not None and product_obj.stock_quantity < quantity:
                        #     raise DjangoValidationError(f"Not enough stock for {product_obj.name}")
                    except Material.DoesNotExist:
                        order.delete()
                        raise DjangoValidationError(f"Material with id {material_id} not found or inactive.")
                elif design_id:
                    try:
                        product_obj = Design.objects.get(id=design_id, is_active=True)
                        seller = product_obj.designer
                        unit_price = Decimal(unit_price) if unit_price is not None else product_obj.price
                    except Design.DoesNotExist:
                        order.delete()
                        raise DjangoValidationError(f"Design with id {design_id} not found or inactive.")
                elif custom_desc:
                    if unit_price is None: # For custom items, price must be given
                        order.delete()
                        raise DjangoValidationError(f"Unit price must be provided for custom item: {custom_desc}")
                    unit_price = Decimal(unit_price)
                    seller_id = item_data.get('seller_id')
                    if not seller_id:
                        order.delete()
                        raise DjangoValidationError(f"Seller must be specified for custom item: {custom_desc}")
                    try:
                        seller = User.objects.get(id=seller_id, user_type__in=['seller', 'manufacturer', 'designer'])
                    except User.DoesNotExist:
                        order.delete()
                        raise DjangoValidationError(f"Seller with id {seller_id} not found for custom item.")
                else:
                    order.delete()
                    raise DjangoValidationError("Each order item must specify a product or custom description.")

                if unit_price is None : # Should be caught earlier
                    order.delete()
                    raise DjangoValidationError("Unit price could not be determined for an item.")


                OrderItem.objects.create(
                    order=order,
                    material=product_obj if isinstance(product_obj, Material) else None,
                    design=product_obj if isinstance(product_obj, Design) else None,
                    custom_item_description=custom_desc if not product_obj else None,
                    quantity=quantity,
                    unit_price=unit_price,
                    seller=seller
                )

        order.update_total() # Calculate and save the final order total
        # Here you might trigger notifications, reduce stock, etc.
        return order

    @transaction.atomic
    def create_order_from_quote(self, quote: Quote, buyer: User) -> Order:
        """Creates an order directly from an accepted quote."""
        if quote.buyer != buyer and (quote.rfq and quote.rfq.buyer != buyer):
            raise PermissionDenied("This quote is not addressed to you or the associated RFQ buyer.")
        if quote.status not in ['accepted', 'submitted', 'viewed']: # Ensure quote is in a valid state to be ordered
            raise DjangoValidationError(f"Cannot create order from quote with status '{quote.status}'.")
        if quote.valid_until < timezone.now().date():
            quote.status = 'expired'
            quote.save()
            raise DjangoValidationError("The quote has expired and cannot be converted to an order.")

        order = Order.objects.create(
            buyer=buyer,
            related_quote=quote,
            shipping_address=buyer.profile.address_line1, # Example: default from profile
            billing_address=buyer.profile.address_line1,  # Example: default from profile
            status='pending_payment'
        )
        OrderItem.objects.create(
            order=order,
            custom_item_description=f"From Quote {quote.id}: {quote.rfq.title if quote.rfq else quote.notes or 'Quoted Item'}",
            quantity=quote.quantity_offered or 1,
            unit_price=quote.total_price / (quote.quantity_offered or Decimal('1.0')),
            seller=quote.supplier
        )
        order.update_total()

        quote.status = 'ordered'
        quote.save(update_fields=['status'])
        if quote.rfq:
            quote.rfq.status = 'awarded'
            quote.rfq.save(update_fields=['status'])

        # Trigger notifications, etc.
        return order

    @transaction.atomic
    def update_order_status(self, order: Order, new_status: str, updated_by: User) -> Order:
        """
        Updates the order status with permission checks and potential side effects.
        """
        if new_status not in [s[0] for s in Order.ORDER_STATUS_CHOICES]:
            raise DjangoValidationError(f"Invalid status: {new_status}")

        # Permission checks (can be more elaborate based on CanUpdateOrderStatus logic)
        can_update = False
        if updated_by.is_staff:
            can_update = True
        elif order.buyer == updated_by:
            if new_status == 'cancelled_by_buyer' and order.status in ['pending_payment', 'processing']:
                can_update = True
        # Check for sellers (simplified: assumes one seller or any seller of items can update for now)
        elif updated_by.user_type in ['seller', 'manufacturer', 'designer'] and order.items.filter(seller=updated_by).exists():
            if new_status == 'processing' and order.status == 'pending_payment': # after payment confirmation
                can_update = True
            elif new_status == 'shipped' and order.status == 'processing':
                can_update = True
            elif new_status == 'completed' and order.status in ['shipped', 'delivered', 'processing']:
                can_update = True
            elif new_status == 'cancelled_by_seller' and order.status in ['pending_payment', 'processing']:
                can_update = True

        if not can_update:
            raise PermissionDenied(f"User {updated_by.username} cannot change order {order.id} status from '{order.status}' to '{new_status}'.")

        # Business logic for status transitions (e.g., stock adjustment, notifications)
        # Example: If order is 'shipped', update inventory for materials.
        # if new_status == 'shipped' and order.status != 'shipped':
        #     for item in order.items.filter(material__isnull=False):
        #         if item.material.stock_quantity is not None:
        #             item.material.stock_quantity -= item.quantity
        #             item.material.save(update_fields=['stock_quantity'])

        # Example: If order is 'completed', grant access to digital design files.
        # if new_status == 'completed' and order.status != 'completed':
        #     for item in order.items.filter(design__isnull=False):
        #         # Logic to grant access to item.design.design_files_link
        #         pass

        order.status = new_status
        order.save(update_fields=['status'])

        # Send notifications to buyer/seller about status change
        # self.send_status_update_notification(order, old_status=order.status, new_status=new_status)

        return order

    def initiate_payment_for_order(self, order: Order) -> dict:
        """
        Initiates the payment process for an order.
        Interacts with a payment gateway (e.g., Stripe).
        Returns payment information (e.g., client_secret for Stripe).
        """
        if order.status != 'pending_payment':
            raise DjangoValidationError(f"Order status is '{order.status}'. Payment cannot be initiated.")
        if order.order_total <= 0:
            raise DjangoValidationError("Order total must be greater than zero to initiate payment.")

        # Placeholder for payment gateway integration
        # payment_service = PaymentService() # From apps.payments_monetization.services
        # try:
        #     payment_intent = payment_service.create_payment_intent(
        #         amount=int(order.order_total * 100), # Amount in cents
        #         currency='usd', # Or your default currency
        #         description=f"Order {order.id} for {order.buyer.username}",
        #         order_id=str(order.id),
        #         customer_id=order.buyer.stripe_customer_id # If you store Stripe customer IDs
        #     )
        #     order.payment_intent_id = payment_intent.id
        #     order.save(update_fields=['payment_intent_id'])
        #     return {"client_secret": payment_intent.client_secret, "payment_intent_id": payment_intent.id}
        # except Exception as e:
        #     # Log the error
        #     print(f"Error initiating payment for order {order.id}: {e}")
        #     raise DjangoValidationError(f"Payment gateway error: {e}")

        # Mock response if no payment gateway is integrated yet
        print(f"Mocking payment initiation for order {order.id} with total {order.order_total}")
        order.payment_intent_id = f"mock_pi_{order.id}" # Mock payment intent ID
        order.save(update_fields=['payment_intent_id'])
        return {"client_secret": f"mock_cs_{order.id}", "payment_intent_id": order.payment_intent_id, "message": "Mock payment initiated."}

    # def send_status_update_notification(self, order, old_status, new_status):
    #     # Logic to send email or in-app notification
    #     # (e.g., to buyer when order is shipped, to seller when order is placed)
    #     print(f"Notification: Order {order.id} status changed from {old_status} to {new_status}")
    #     pass