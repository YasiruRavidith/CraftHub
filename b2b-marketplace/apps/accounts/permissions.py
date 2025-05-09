from rest_framework import permissions

class IsOwnerOrReadOnlyProfile(permissions.BasePermission):
    """
    Custom permission to only allow owners of a profile to edit it.
    Read-only for others.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the profile.
        # 'obj' here is a Profile instance.
        return obj.user == request.user