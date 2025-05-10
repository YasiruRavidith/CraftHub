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
    """
    API endpoint that allows materials to be viewed or edited.
    - General listing shows active materials.
    - Filtering by `seller__username=<current_user_username>` shows all of that user's materials (active/inactive).
    - Admins can see all materials.
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsSellerOrAdminOrReadOnly] # Adjust as needed for list vs. detail vs. owner
    lookup_field = 'slug'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category__slug': ['exact', 'in'],
        'seller__username': ['exact'], # Used by frontend for "My Materials"
        'tags__slug': ['in'],
        'country_of_origin': ['exact', 'in'],
        'price_per_unit': ['gte', 'lte', 'exact'],
        'is_verified': ['exact'],
        'is_active': ['exact'], # Allows explicit filtering by active status
        'unit': ['exact', 'in'],
        # Add other fields from Material model you want to filter on
        # 'composition': ['icontains'], # Example for text search within field
    }
    search_fields = [
        'name', 
        'description', 
        'composition', 
        'sku',
        'seller__username', # Search by seller's username
        'category__name',   # Search by category name
        'tags__name'        # Search by tag names
    ]
    ordering_fields = ['name', 'price_per_unit', 'created_at', 'updated_at', 'stock_quantity', 'average_rating']
    ordering = ['-created_at'] # Default ordering

    def get_queryset(self):
        """
        Dynamically determines the queryset based on the user.
        - Admins see all materials.
        - Authenticated users requesting their own materials (via `seller__username` query param)
          see all their materials (active and inactive).
        - Other requests (anonymous or general search by authenticated users) see only active materials.
        The `DjangoFilterBackend` will further apply filters specified in `filterset_fields`
        to the queryset returned by this method.
        """
        user = self.request.user
        
        # Base queryset including necessary related data for performance
        base_queryset = Material.objects.all().select_related(
            'seller__profile', 
            'category'
        ).prefetch_related(
            'tags', 
            'certifications'
        )

        # Admins can see everything, filters will apply on top of this
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return base_queryset

        # Check if the request is attempting to filter by the current user's username
        requested_seller_username = self.request.query_params.get('seller__username', None)

        if user.is_authenticated and requested_seller_username == user.username:
            # User is requesting their own materials.
            # DjangoFilterBackend will apply the 'seller__username' filter to base_queryset.
            # No need to filter by 'is_active' here, so they see all their own items.
            # Also, no need to filter by seller=user here, as DjangoFilterBackend will do it.
            return base_queryset
        else:
            # For anonymous users or general searches (not specifically for 'my materials')
            # only show active materials. DjangoFilterBackend will apply other filters on top.
            return base_queryset.filter(is_active=True)

    def perform_create(self, serializer):
        """
        Set the seller to the currently authenticated user when creating a new material.
        """
        if not self.request.user.is_authenticated:
            # This should ideally be caught by permission_classes first
            raise permissions.PermissionDenied("Authentication required to create a material.")
            
        if self.request.user.user_type not in ['seller', 'manufacturer', 'admin']:
            raise permissions.PermissionDenied("You must be a seller, manufacturer, or admin to list materials.")
        
        # Save the material instance with the current user as the seller
        # The 'seller_id' field in the serializer is marked as required=False,
        # so it doesn't need to be in the request payload.
        serializer.save(seller=self.request.user)

    def perform_update(self, serializer):
        """
        Handle updates. The permission class (IsSellerOrAdminOrReadOnly)
        should ensure only the owner or admin can update.
        """
        # You could add extra logic here if needed before saving.
        # For example, if certain fields can only be updated by admins.
        serializer.save()

    def perform_destroy(self, instance):
        """
        Handle deletion. The permission class should ensure only owner or admin can delete.
        """
        # You could add extra logic here (e.g., soft delete by setting is_active=False)
        # For a hard delete:
        instance.delete()

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