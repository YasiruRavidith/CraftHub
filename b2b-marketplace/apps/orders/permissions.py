from rest_framework import permissions

class IsBuyerOwnerOrAdminForRFQ(permissions.BasePermission):
    """
    - Allows read for authenticated users (or adjust for public RFQs).
    - Allows write/delete only if user is the buyer of the RFQ or admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Logic for who can see RFQs (e.g., if RFQ is 'open' or user is participant)
            if obj.status == 'open' or obj.buyer == request.user or request.user.is_staff:
                return True
            # Suppliers who quoted can also see it
            if obj.quotes.filter(supplier=request.user).exists():
                return True
            return False

        # Write permissions (PUT, PATCH, DELETE)
        return obj.buyer == request.user or request.user.is_staff


class IsSupplierOwnerOrAdminForQuote(permissions.BasePermission):
    """
    - Allows read if user is supplier, buyer of related RFQ, or admin.
    - Allows write/delete only if user is the supplier of the Quote or admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            is_supplier = obj.supplier == request.user
            is_buyer = (obj.rfq and obj.rfq.buyer == request.user) or (obj.buyer == request.user)
            is_admin = request.user.is_staff
            return is_supplier or is_buyer or is_admin

        # Write permissions
        return obj.supplier == request.user or request.user.is_staff


class IsBuyerOwnerOrAdminForOrder(permissions.BasePermission):
    """
    - Allows read if user is buyer, a seller of an item in the order, or admin.
    - Allows write/delete only if user is the buyer of the Order or admin (for most fields).
    - Status updates might have more specific rules (see CanUpdateOrderStatus).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            is_buyer = obj.buyer == user
            is_seller_of_item = obj.items.filter(seller=user).exists()
            is_admin = user.is_staff
            return is_buyer or is_seller_of_item or is_admin

        # Write permissions (e.g., for updating shipping address by buyer)
        # More granular control for status updates is handled by CanUpdateOrderStatus.
        if view.action in ['update', 'partial_update', 'destroy']:
             return obj.buyer == user or user.is_staff
        return False # Default deny for other actions if not explicitly handled


class IsParticipantOrAdminReadOnly(permissions.BasePermission):
    """
    Allows read if user is buyer of RFQ, supplier who quoted, or admin.
    Used for actions like listing quotes on an RFQ.
    """
    def has_object_permission(self, request, view, obj): # obj is RFQ instance here
        if request.method not in permissions.SAFE_METHODS:
            return False # This permission is for read-only access to related data

        user = request.user
        is_rfq_buyer = obj.buyer == user
        is_quoting_supplier = obj.quotes.filter(supplier=user).exists()
        is_admin = user.is_staff
        return is_rfq_buyer or is_quoting_supplier or is_admin


class CanUpdateOrderStatus(permissions.BasePermission):
    """
    Defines who can update an order's status.
    - Buyer might cancel a 'pending_payment' or 'processing' order (if allowed).
    - Seller might update to 'processing', 'shipped'.
    - Admin can make any status change.
    """
    def has_object_permission(self, request, view, obj): # obj is Order instance
        user = request.user
        if not user.is_authenticated:
            return False

        if user.is_staff: # Admins can do anything
            return True

        current_status = obj.status
        new_status = request.data.get('status') # Assuming new status is in request.data

        # Buyer permissions
        if obj.buyer == user:
            if new_status == 'cancelled_by_buyer':
                # Define which statuses buyer can cancel from
                if current_status in ['pending_payment', 'processing']: # Example
                    return True
            # Potentially other transitions buyer can make

        # Seller/Manufacturer/Designer permissions
        # This requires knowing which seller is trying to update.
        # If one order can have items from multiple sellers, this gets complex.
        # For simplicity, assume a seller can update if they have ANY item in the order.
        # A more robust system would check if the specific item(s) they are responsible for
        # allow this status update, or if the order is solely from this seller.
        if user.user_type in ['seller', 'manufacturer', 'designer'] and obj.items.filter(seller=user).exists():
            if new_status == 'processing' and current_status in ['pending_payment']: # Payment confirmation might trigger this
                return True
            if new_status == 'shipped' and current_status == 'processing':
                return True
            if new_status == 'completed' and current_status in ['shipped', 'delivered', 'processing']: # For digital or services
                return True
            if new_status == 'cancelled_by_seller' and current_status in ['pending_payment', 'processing']:
                return True
            # Potentially other transitions seller can make

        return False # Deny by default