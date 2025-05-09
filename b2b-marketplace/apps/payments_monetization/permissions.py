# apps/payments_monetization/permissions.py
from rest_framework import permissions

class IsSubscriptionOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a subscription to view/manage it.
    """
    def has_object_permission(self, request, view, obj): # obj is UserSubscription
        # User can only access their own subscription object.
        return obj.user == request.user or request.user.is_staff