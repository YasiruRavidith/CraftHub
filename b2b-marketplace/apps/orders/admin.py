# apps/orders/admin.py
from django.contrib import admin
from django.utils.html import format_html # For potential linking in admin
from .models import RFQ, Quote, Order, OrderItem

class QuoteInline(admin.TabularInline):
    model = Quote
    extra = 0 # Don't show empty forms by default
    fields = ('supplier_link', 'total_price', 'valid_until', 'status', 'created_at')
    readonly_fields = ('created_at', 'supplier_link')
    can_delete = False
    show_change_link = True # Allows clicking to the Quote change page from the inline

    def supplier_link(self, obj):
        if obj.supplier:
            # Assuming your CustomUser admin is registered and has a change_list view
            # This requires knowing the app_label and model_name for CustomUser
            # user_app_label = obj.supplier._meta.app_label
            # user_model_name = obj.supplier._meta.model_name
            # url = reverse(f"admin:{user_app_label}_{user_model_name}_change", args=[obj.supplier.pk])
            # return format_html('<a href="{}">{}</a>', url, obj.supplier.username)
            return obj.supplier.username # Simpler display
        return "N/A"
    supplier_link.short_description = "Supplier"


@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'buyer_link', 'status', 'deadline_for_quotes', 'quotes_count_display', 'created_at')
    list_filter = ('status', 'buyer__username') # Filter by username for buyer
    search_fields = ('id__iexact', 'title', 'description', 'buyer__username') # id__iexact for exact UUID search
    readonly_fields = ('id', 'created_at', 'updated_at', 'quotes_count_display')
    inlines = [QuoteInline]
    actions = ['mark_as_open', 'mark_as_closed', 'mark_as_cancelled']
    date_hierarchy = 'created_at'
    raw_id_fields = ('buyer',)

    def buyer_link(self, obj):
        if obj.buyer:
            # user_app_label = obj.buyer._meta.app_label
            # user_model_name = obj.buyer._meta.model_name
            # url = reverse(f"admin:{user_app_label}_{user_model_name}_change", args=[obj.buyer.pk])
            # return format_html('<a href="{}">{}</a>', url, obj.buyer.username)
            return obj.buyer.username
        return "N/A"
    buyer_link.short_description = "Buyer"
    buyer_link.admin_order_field = 'buyer__username'

    def quotes_count_display(self, obj):
        return obj.quotes.count()
    quotes_count_display.short_description = "Quotes Recvd."

    def mark_as_open(self, request, queryset):
        queryset.update(status='open')
    mark_as_open.short_description = "Mark selected: Open for Quotes"

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = "Mark selected: Closed for Quotes"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = "Mark selected: Cancel RFQ"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'rfq_link', 'supplier_username', 'buyer_username', 'total_price_display', 'status', 'valid_until', 'created_at')
    list_filter = ('status', 'supplier__username', 'buyer__username', 'valid_until')
    search_fields = ('id__iexact', 'rfq__title', 'supplier__username', 'buyer__username', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at', 'buyer_username', 'supplier_username', 'rfq_link')
    raw_id_fields = ('rfq', 'supplier', 'buyer')
    date_hierarchy = 'created_at'

    def rfq_link(self, obj):
        if obj.rfq:
            # url = reverse("admin:orders_rfq_change", args=[obj.rfq.pk])
            # return format_html('<a href="{}">{} (RFQ-{})</a>', url, obj.rfq.title, str(obj.rfq.id)[:8])
            return f"{obj.rfq.title} (RFQ-{str(obj.rfq.id)[:8]})"
        return "Direct Quote"
    rfq_link.short_description = "RFQ / Context"
    rfq_link.admin_order_field = 'rfq__title'

    def supplier_username(self, obj):
        return obj.supplier.username if obj.supplier else "N/A"
    supplier_username.short_description = "Supplier"
    supplier_username.admin_order_field = 'supplier__username'

    def buyer_username(self, obj):
        return obj.buyer.username if obj.buyer else "N/A"
    buyer_username.short_description = "Buyer"
    buyer_username.admin_order_field = 'buyer__username'

    def total_price_display(self, obj):
        return f"{obj.total_price} {obj.rfq.currency if obj.rfq and hasattr(obj.rfq, 'currency') else 'USD'}" # Assuming currency
    total_price_display.short_description = "Total Price"
    total_price_display.admin_order_field = 'total_price'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 # Start with no empty forms for existing orders
    fields = ('product_display_link', 'quantity', 'unit_price', 'calculated_subtotal', 'seller_link')
    readonly_fields = ('calculated_subtotal', 'product_display_link', 'seller_link')
    raw_id_fields = ('material', 'design', 'seller') # Keep these for easy selection
    autocomplete_fields = ['material', 'design', 'seller'] # Enable autocomplete if search_fields are set on related admins

    def product_display_link(self, obj):
        # Uses the item_name property from the OrderItem model
        # You could make this a link to the material/design admin page if desired
        return obj.item_name_display # Assuming model has item_name_display property
    product_display_link.short_description = "Product"

    def calculated_subtotal(self, obj):
        # Uses the subtotal property from the OrderItem model
        return obj.subtotal # Assuming model has subtotal property
    calculated_subtotal.short_description = "Subtotal"

    def seller_link(self,obj):
        if obj.seller:
            return obj.seller.username
        return "N/A"
    seller_link.short_description = "Item Seller"
    seller_link.admin_order_field = 'seller__username'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_username', 'order_total_display', 'status', 'item_count', 'related_quote_id_display', 'created_at', 'payment_intent_id')
    list_filter = ('status', 'buyer__username', 'created_at')
    search_fields = ('id__iexact', 'buyer__username', 'payment_intent_id', 'items__material__name', 'items__design__title')
    readonly_fields = ('id', 'order_total', 'created_at', 'updated_at', 'item_count', 'buyer_username', 'related_quote_id_display')
    inlines = [OrderItemInline]
    raw_id_fields = ('buyer', 'related_quote')
    date_hierarchy = 'created_at'
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_completed', 'mark_as_cancelled_by_seller']

    def buyer_username(self, obj):
        return obj.buyer.username if obj.buyer else "N/A"
    buyer_username.short_description = "Buyer"
    buyer_username.admin_order_field = 'buyer__username'

    def order_total_display(self, obj):
        # Assuming currency is on the order or can be derived
        return f"{obj.order_total} {getattr(obj, 'currency', 'USD')}"
    order_total_display.short_description = "Order Total"
    order_total_display.admin_order_field = 'order_total'
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"

    def related_quote_id_display(self, obj):
        return str(obj.related_quote_id)[:8]+"..." if obj.related_quote_id else "N/A"
    related_quote_id_display.short_description = "From Quote"
    related_quote_id_display.admin_order_field = "related_quote"


    def mark_as_processing(self, request, queryset):
        updated_count = queryset.update(status='processing')
        self.message_user(request, f"{updated_count} order(s) marked as Processing.")
    mark_as_processing.short_description = "Mark selected: Processing"

    def mark_as_shipped(self, request, queryset):
        updated_count = queryset.update(status='shipped')
        self.message_user(request, f"{updated_count} order(s) marked as Shipped.")
    mark_as_shipped.short_description = "Mark selected: Shipped"

    def mark_as_delivered(self, request, queryset): # Added delivered
        updated_count = queryset.update(status='delivered')
        self.message_user(request, f"{updated_count} order(s) marked as Delivered.")
    mark_as_delivered.short_description = "Mark selected: Delivered"

    def mark_as_completed(self, request, queryset):
        updated_count = queryset.update(status='completed')
        self.message_user(request, f"{updated_count} order(s) marked as Completed.")
    mark_as_completed.short_description = "Mark selected: Completed"

    def mark_as_cancelled_by_seller(self, request, queryset): # Added specific cancel action
        updated_count = queryset.update(status='cancelled_by_seller')
        self.message_user(request, f"{updated_count} order(s) marked as Cancelled by Seller.")
    mark_as_cancelled_by_seller.short_description = "Mark selected: Cancel by Seller"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'item_name_property', 'quantity', 'unit_price', 'subtotal_property', 'seller_username')
    list_filter = ('seller__username', 'material__category', 'design__category') # Example filters
    search_fields = ('order__id__iexact', 'material__name', 'design__title', 'custom_item_description', 'seller__username')
    readonly_fields = ('subtotal_property', 'item_name_property', 'order_link', 'seller_username')
    raw_id_fields = ('order', 'material', 'design', 'seller')
    autocomplete_fields = ['order', 'material', 'design', 'seller']

    def order_link(self, obj):
        if obj.order:
            # url = reverse("admin:orders_order_change", args=[obj.order.pk])
            # return format_html('<a href="{}">Order #{}</a>', url, str(obj.order.id)[:8])
            return f"Order #{str(obj.order.id)[:8]}"
        return "N/A"
    order_link.short_description = "Order"
    order_link.admin_order_field = 'order__id'

    def item_name_property(self, obj):
        return obj.item_name_display # Use the model property
    item_name_property.short_description = "Product Name"
    # item_name_property.admin_order_field = ... # Can't easily order by property directly like this

    def subtotal_property(self, obj):
        return obj.subtotal # Use the model property
    subtotal_property.short_description = "Subtotal"
    # subtotal_property.admin_order_field = ... # Can't order by property this way

    def seller_username(self, obj):
        return obj.seller.username if obj.seller else "N/A"
    seller_username.short_description = "Seller"
    seller_username.admin_order_field = 'seller__username'