from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the listing.
        # Assumes the object has a 'seller' or 'designer' attribute.
        if hasattr(obj, 'seller'):
            return obj.seller == request.user
        if hasattr(obj, 'designer'):
            return obj.designer == request.user
        # Fallback for other objects if needed, or deny if no owner attribute
        # For TechPack, ownership might be tied to the Design's owner.
        if hasattr(obj, 'design'): # For TechPack
            return obj.design.designer == request.user
        return False


class IsSellerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only for anyone.
    Allows write access if user is the seller or an admin.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # For POST (create) requests
        if request.method == 'POST':
            return request.user and request.user.is_authenticated and \
                   (request.user.user_type in ['seller', 'manufacturer'] or request.user.is_staff)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # For PUT, PATCH, DELETE (object-level)
        return request.user and request.user.is_authenticated and \
               (obj.seller == request.user or request.user.is_staff)


class IsDesignerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only for anyone.
    Allows write access if user is the designer or an admin.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # For POST (create) requests
        if request.method == 'POST':
            return request.user and request.user.is_authenticated and \
                   (request.user.user_type == 'designer' or request.user.is_staff)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # For PUT, PATCH, DELETE (object-level)
        return request.user and request.user.is_authenticated and \
               (obj.designer == request.user or request.user.is_staff)