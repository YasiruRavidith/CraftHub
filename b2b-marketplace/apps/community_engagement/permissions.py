from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of an object to edit or delete it.
    Read-only for others. Admins can always edit/delete.
    (Used for ForumThread, ForumPost)
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    Object must have a 'user' attribute.
    (Used for Showcase, ShowcaseItem - checks showcase.user)
    """
    def has_object_permission(self, request, view, obj):
        # For ShowcaseItem, check ownership of the parent Showcase
        parent_showcase_user = None
        if hasattr(obj, 'showcase') and obj.showcase: # For ShowcaseItem
            parent_showcase_user = obj.showcase.user
        elif hasattr(obj, 'user'): # For Showcase
            parent_showcase_user = obj.user

        if request.method in permissions.SAFE_METHODS:
            # If object is Showcase and not public, only owner/admin can see
            if hasattr(obj, 'is_public') and not obj.is_public:
                return parent_showcase_user == request.user or request.user.is_staff
            return True # Public items are readable by anyone

        return parent_showcase_user == request.user or request.user.is_staff