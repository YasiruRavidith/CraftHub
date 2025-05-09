from django.contrib import admin
from .models import RFQ, Quote, Order, OrderItem

class QuoteInline(admin.TabularInline):
    model = Quote
    extra = 0
    fields = ('supplier', 'total_price', 'valid_until', 'status', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False # Usually quotes are not deleted directly from RFQ admin

@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'buyer', 'status', 'deadline_for_quotes', 'created_at')
    list_filter = ('status', 'buyer')
    search_fields = ('title', 'description', 'buyer__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [QuoteInline]
    actions = ['mark_as_open', 'mark_as_closed']

    def mark_as_open(self, request, queryset):
        queryset.update(status='open')
    mark_as_open.short_description = "Mark selected RFQs as Open"

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = "Mark selected RFQs as Closed"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'rfq_display', 'supplier', 'buyer', 'total_price', 'status', 'valid_until')
    list_filter = ('status', 'supplier', 'buyer')
    search_fields = ('rfq__title', 'supplier__username', 'buyer__username', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('rfq', 'supplier', 'buyer') # For easier selection with many users/RFQs

    def rfq_display(self, obj):
        return obj.rfq.title if obj.rfq else "Direct Quote"
    rfq_display.short_description = "RFQ/Context"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_display', 'quantity', 'unit_price', 'subtotal', 'seller')
    readonly_fields = ('subtotal', 'product_display')
    raw_id_fields = ('material', 'design', 'seller')

    def product_display(self, obj):
        return obj.item_name
    product_display.short_description = "Product"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'order_total', 'status', 'created_at', 'payment_intent_id')
    list_filter = ('status', 'buyer')
    search_fields = ('id', 'buyer__username', 'payment_intent_id')
    readonly_fields = ('id', 'order_total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    raw_id_fields = ('buyer', 'related_quote')
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_completed']

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as Processing"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected orders as Completed"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item_name', 'quantity', 'unit_price', 'subtotal', 'seller')
    list_filter = ('seller',)
    search_fields = ('order__id', 'material__name', 'design__title', 'custom_item_description', 'seller__username')
    readonly_fields = ('subtotal',)
    raw_id_fields = ('order', 'material', 'design', 'seller')