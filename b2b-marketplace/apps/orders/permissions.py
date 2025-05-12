# apps/orders/permissions.py
from rest_framework import permissions
# from .models import Order, Quote, RFQ # Import models if needed for complex checks, not here

class IsBuyerOwnerOrAdminForRFQ(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj): # obj is RFQ
        if request.method in permissions.SAFE_METHODS:
            if obj.status == 'open' or obj.buyer == request.user or request.user.is_staff:
                return True
            if obj.quotes.filter(supplier=request.user).exists():
                return True
            return False
        return obj.buyer == request.user or request.user.is_staff

class IsSupplierOwnerOrAdminForQuote(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj): # obj is Quote
        if request.method in permissions.SAFE_METHODS:
            is_supplier = obj.supplier == request.user
            is_buyer = (obj.rfq and obj.rfq.buyer == request.user) or (obj.buyer == request.user)
            is_admin = request.user.is_staff
            return is_supplier or is_buyer or is_admin
        return obj.supplier == request.user or request.user.is_staff

class IsBuyerOwnerOrAdminForOrder(permissions.BasePermission):
    def has_permission(self, request, view):
        print(f"IsBuyerOwnerOrAdminForOrder: has_permission called by user {request.user} for view action: {view.action if hasattr(view, 'action') else 'N/A'}") # DEBUG
        if not request.user or not request.user.is_authenticated:
            print("IsBuyerOwnerOrAdminForOrder: Denied - User not authenticated.")
            return False
        
        # For creating a new order (POST to list endpoint)
        if hasattr(view, 'action') and view.action == 'create':
            # The actual check if user is 'buyer' is in perform_create for a more specific error message.
            # Here, we just ensure they are authenticated.
            print("IsBuyerOwnerOrAdminForOrder: Allowed (create action) - User authenticated.")
            return True 
        
        # For listing orders (GET to list endpoint)
        if hasattr(view, 'action') and view.action == 'list':
            print("IsBuyerOwnerOrAdminForOrder: Allowed (list action) - User authenticated.")
            return True
            
        # For detail views (retrieve, update, partial_update, destroy) or custom actions on an object,
        # has_object_permission will be called after this returns True.
        # If the action isn't 'create' or 'list', it's assumed to be a detail-level or custom action.
        print(f"IsBuyerOwnerOrAdminForOrder: Defaulting to True for action {view.action if hasattr(view, 'action') else 'N/A'} (has_object_permission will handle specifics if applicable).")
        return True

    def has_object_permission(self, request, view, obj): # obj is Order instance
        print(f"IsBuyerOwnerOrAdminForOrder: has_object_permission called for order {obj.id}, action: {view.action if hasattr(view, 'action') else 'N/A'}, user: {request.user}") # DEBUG
        user = request.user
        # Authenticated check is redundant if class has IsAuthenticated, but good for clarity.
        if not user.is_authenticated: 
            return False

        if user.is_staff: # Admins can do anything to specific objects
            print("IsBuyerOwnerOrAdminForOrder: Allowed - User is staff.")
            return True

        is_buyer = (obj.buyer == user)
        is_seller_of_item = obj.items.filter(seller=user).exists()

        # For SAFE_METHODS (GET, HEAD, OPTIONS) on a specific order object
        if request.method in permissions.SAFE_METHODS:
            allowed = is_buyer or is_seller_of_item
            print(f"IsBuyerOwnerOrAdminForOrder (SAFE_METHOD): Buyer={is_buyer}, SellerOfItem={is_seller_of_item}, Allowed={allowed}")
            return allowed

        # For unsafe methods (PUT, PATCH, DELETE) on an existing object
        # Only the buyer of the order should be able to modify/delete their own order directly.
        # Admins are already covered. Sellers cannot modify an order directly this way.
        if view.action in ['update', 'partial_update', 'destroy']:
             print(f"IsBuyerOwnerOrAdminForOrder (UNSAFE_METHOD - update/destroy): Buyer={is_buyer}, Allowed={is_buyer}")
             return is_buyer 
        
        # For custom actions on an object, allow if they are buyer or seller of item,
        # then let the action itself do more fine-grained checks if needed.
        # (e.g. update_status and initiate_payment have their own specific permission logic too)
        if hasattr(view, 'action') and view.action in ['update_status', 'initiate_payment', 'list_items']:
            allowed = is_buyer or is_seller_of_item
            print(f"IsBuyerOwnerOrAdminForOrder (custom action {view.action}): Buyer={is_buyer}, SellerOfItem={is_seller_of_item}, Allowed={allowed}")
            return allowed

        print("IsBuyerOwnerOrAdminForOrder: Denied - Default fall-through for object permission.")
        return False


class IsParticipantOrAdminReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj): # obj is RFQ
        if request.method not in permissions.SAFE_METHODS:
            return False
        user = request.user
        is_rfq_buyer = obj.buyer == user
        is_quoting_supplier = obj.quotes.filter(supplier=user).exists()
        is_admin = user.is_staff
        return is_rfq_buyer or is_quoting_supplier or is_admin

class CanUpdateOrderStatus(permissions.BasePermission):
    def has_object_permission(self, request, view, obj): # obj is Order
        user = request.user
        if not user.is_authenticated: return False
        if user.is_staff: return True

        new_status = request.data.get('status')
        if obj.buyer == user:
            if new_status == 'cancelled_by_buyer' and obj.status in ['pending_payment', 'processing']:
                return True
        if user.user_type in ['seller', 'manufacturer', 'designer'] and obj.items.filter(seller=user).exists():
            if new_status == 'processing' and obj.status == 'pending_payment': return True
            if new_status == 'shipped' and obj.status == 'processing': return True
            if new_status == 'completed' and obj.status in ['shipped', 'delivered', 'processing']: return True
            if new_status == 'cancelled_by_seller' and obj.status in ['pending_payment', 'processing']: return True
        return False