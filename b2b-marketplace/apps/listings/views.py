from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Material, Design, TechPack, Certification, Tag
from .serializers import (
    CategorySerializer, MaterialSerializer, DesignSerializer,
    TechPackSerializer, CertificationSerializer, TagSerializer
)
from .permissions import IsOwnerOrReadOnly, IsSellerOrAdminOrReadOnly, IsDesignerOrAdminOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent_category__isnull=True).prefetch_related('subcategories') # Top-level categories
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow anyone to read, admin to modify
    lookup_field = 'slug'

    @action(detail=True, methods=['get'])
    def subcategories(self, request, slug=None):
        category = self.get_object()
        subcategories = category.subcategories.all()
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def materials(self, request, slug=None):
        category = self.get_object()
        materials = Material.objects.filter(category=category, is_active=True)
        # Add pagination
        page = self.paginate_queryset(materials)
        if page is not None:
            serializer = MaterialSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = MaterialSerializer(materials, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def designs(self, request, slug=None):
        category = self.get_object()
        designs = Design.objects.filter(category=category, is_active=True)
        page = self.paginate_queryset(designs)
        if page is not None:
            serializer = DesignSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = DesignSerializer(designs, many=True, context={'request': request})
        return Response(serializer.data)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage tags
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage certifications globally
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'issuing_body']

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.filter(is_active=True).select_related('seller__profile', 'category').prefetch_related('tags', 'certifications')
    serializer_class = MaterialSerializer
    permission_classes = [IsSellerOrAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category__slug': ['exact'],
        'seller__username': ['exact'],
        'tags__slug': ['in'],
        'country_of_origin': ['exact'],
        'price_per_unit': ['gte', 'lte'],
        'is_verified': ['exact'],
    }
    search_fields = ['name', 'description', 'composition', 'seller__username', 'category__name', 'tags__name']
    ordering_fields = ['name', 'price_per_unit', 'created_at', 'stock_quantity']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        # Ensure the logged-in user is set as the seller
        if self.request.user.user_type not in ['seller', 'manufacturer', 'admin']:
            raise permissions.PermissionDenied("You must be a seller or manufacturer to list materials.")
        serializer.save(seller=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        # Allow admins to see inactive listings
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Material.objects.all().select_related('seller__profile', 'category').prefetch_related('tags', 'certifications')
        
        # If a specific user wants to see their own (in)active listings
        owner_filter = self.request.query_params.get('owner', None)
        if owner_filter == 'me' and self.request.user.is_authenticated:
            return Material.objects.filter(seller=self.request.user).select_related('seller__profile', 'category').prefetch_related('tags', 'certifications')
            
        return qs


class DesignViewSet(viewsets.ModelViewSet):
    queryset = Design.objects.filter(is_active=True).select_related('designer__profile', 'category').prefetch_related('tags', 'certifications', 'tech_packs')
    serializer_class = DesignSerializer
    permission_classes = [IsDesignerOrAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category__slug': ['exact'],
        'designer__username': ['exact'],
        'tags__slug': ['in'],
        'price': ['gte', 'lte'],
        'is_verified': ['exact'],
    }
    search_fields = ['title', 'description', 'designer__username', 'category__name', 'tags__name']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        if self.request.user.user_type not in ['designer', 'admin']:
            raise permissions.PermissionDenied("You must be a designer to list designs.")
        serializer.save(designer=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Design.objects.all().select_related('designer__profile', 'category').prefetch_related('tags', 'certifications', 'tech_packs')
        
        owner_filter = self.request.query_params.get('owner', None)
        if owner_filter == 'me' and self.request.user.is_authenticated:
            return Design.objects.filter(designer=self.request.user).select_related('designer__profile', 'category').prefetch_related('tags', 'certifications', 'tech_packs')

        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly]) # Or specific permission for tech packs
    def upload_tech_pack(self, request, slug=None):
        design = self.get_object()
        if design.designer != request.user and not request.user.is_staff:
            return Response({'detail': 'Not authorized to upload tech pack for this design.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TechPackSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(design=design)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='tech-packs')
    def list_tech_packs(self, request, slug=None):
        design = self.get_object()
        tech_packs = design.tech_packs.all()
        serializer = TechPackSerializer(tech_packs, many=True, context={'request': request})
        return Response(serializer.data)


class TechPackViewSet(viewsets.ModelViewSet):
    queryset = TechPack.objects.all()
    serializer_class = TechPackSerializer
    permission_classes = [permissions.IsAuthenticated] # Adjust as needed, e.g., owner of design

    def get_queryset(self):
        # Users should only see tech packs related to designs they have access to,
        # or tech packs they uploaded. This needs more specific logic based on your rules.
        # For simplicity, admin sees all, others see none unless filtered.
        if self.request.user.is_staff:
            return TechPack.objects.all()
        # Example: filter by design_id passed in query params
        design_id = self.request.query_params.get('design_id')
        if design_id:
            try:
                design = Design.objects.get(pk=design_id)
                # Check if user owns the design or has other permissions
                if design.designer == self.request.user or self.request.user.is_staff:
                     return TechPack.objects.filter(design_id=design_id)
            except Design.DoesNotExist:
                return TechPack.objects.none()
        return TechPack.objects.none() # Default to none if no specific filter for non-admins

    def perform_create(self, serializer):
        # Logic to ensure user is authorized to add tech pack to the specified design
        design_id = serializer.validated_data.get('design').id
        try:
            design = Design.objects.get(pk=design_id)
            if design.designer != self.request.user and not self.request.user.is_staff:
                raise permissions.PermissionDenied("You are not the owner of this design.")
            serializer.save()
        except Design.DoesNotExist:
            raise serializers.ValidationError("Design not found.")