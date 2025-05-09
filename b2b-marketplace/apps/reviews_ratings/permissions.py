from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a review to edit or delete it.
    Read-only for others. Admins can always edit/delete.
    """
    def has_object_permission(self, request, view, obj): # obj is Review instance
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of the review or admin.
        return obj.author == request.user or request.user.is_staff


class IsReviewOwnerOrAdminForReply(permissions.BasePermission):
    """
    Permission for ReviewReply.
    - Allows author of reply to edit/delete their reply.
    - Allows owner of the originally reviewed item to create a reply (handled in serializer/view create).
    - Allows admin to do anything.
    """
    def has_object_permission(self, request, view, obj): # obj is ReviewReply instance
        if request.method in permissions.SAFE_METHODS:
            return True # Anyone can read replies

        # Write permissions for reply author or admin
        if obj.author == request.user or request.user.is_staff:
            return True

        # Allow owner of the *reviewed item* to delete a reply to a review on their item (optional)
        # This logic can be complex as it involves checking obj.review.content_object owner.
        # For simplicity, we'll stick to reply author or admin for modification.
        # The creation of a reply (who can create it) is better handled in the view's perform_create
        # or serializer's validate method, ensuring the replier is the owner of the reviewed item.
        return False

    def has_permission(self, request, view):
        # For creating a reply (POST), the logic is more about *who* can reply to *which* review.
        # This is better handled in the serializer or view's perform_create.
        # This base permission check ensures user is authenticated for non-safe methods.
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated