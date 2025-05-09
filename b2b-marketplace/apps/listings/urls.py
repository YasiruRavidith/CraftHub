from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, MaterialViewSet, DesignViewSet,
    TechPackViewSet, CertificationViewSet, TagViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'certifications', CertificationViewSet, basename='certification')
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'designs', DesignViewSet, basename='design')
router.register(r'tech-packs', TechPackViewSet, basename='techpack') # If standalone CRUD is needed

urlpatterns = [
    path('', include(router.urls)),
]