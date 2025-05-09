from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, CustomAuthTokenLoginView, UserProfileViewSet, UserDetailView

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile') # e.g., /api/v1/accounts/profiles/me/ or /api/v1/accounts/profiles/<pk>/

urlpatterns = [
    path('register/', RegisterView.as_view(), name='account_register'),
    path('login/', CustomAuthTokenLoginView.as_view(), name='account_login'),
    path('users/me/', UserDetailView.as_view(), name='user-detail-me'), # For current user details
    path('', include(router.urls)),
]