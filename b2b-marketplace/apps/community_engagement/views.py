from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, OuterRef, Subquery, F, Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from .models import ForumCategory, ForumThread, ForumPost, Showcase, ShowcaseItem
from .serializers import (
    ForumCategorySerializer, ForumThreadSerializer, ForumThreadDetailSerializer,
    ForumPostSerializer, ShowcaseSerializer, ShowcaseItemSerializer
)
from .permissions import IsAuthorOrReadOnly, IsOwnerOrReadOnly # Create these

class ForumCategoryViewSet(viewsets.ModelViewSet):
    queryset = ForumCategory.objects.annotate(threads_count_annotated=Count('threads')).all()
    serializer_class = ForumCategorySerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage categories
    lookup_field = 'slug'

    # Public list view
    def list(self, request, *args, **kwargs):
        self.permission_classes = [permissions.AllowAny]
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.permission_classes = [permissions.AllowAny]
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # Optionally, fetch threads for this category here or let client fetch separately
        # threads = ForumThread.objects.filter(category=instance).select_related('author__profile', 'category').order_by('-is_pinned', '-updated_at')[:10] # Example
        # threads_serializer = ForumThreadSerializer(threads, many=True, context={'request': request})
        # data = serializer.data
        # data['threads_preview'] = threads_serializer.data
        return Response(serializer.data)


class ForumThreadViewSet(viewsets.ModelViewSet):
    queryset = ForumThread.objects.select_related('author__profile', 'category').annotate(
        posts_count_annotated=Count('posts')
    ).order_by('-is_pinned', '-updated_at')
    # serializer_class = ForumThreadSerializer # Default, override in retrieve
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'category__slug': ['exact'],
        'author__username': ['exact'],
        'is_pinned': ['exact'],
        'is_locked': ['exact'],
    }

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ForumThreadDetailSerializer
        return ForumThreadSerializer

    def perform_create(self, serializer):
        # Author is set by CurrentUserDefault
        # Initial post content is handled in serializer's create method
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count (basic implementation)
        instance.views_count = F('views_count') + 1
        instance.save(update_fields=['views_count'])
        instance.refresh_from_db() # Get the updated views_count
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser]) # Or thread author
    def toggle_pin(self, request, slug=None):
        thread = self.get_object()
        thread.is_pinned = not thread.is_pinned
        thread.save(update_fields=['is_pinned'])
        return Response(ForumThreadSerializer(thread, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser]) # Or thread author
    def toggle_lock(self, request, slug=None):
        thread = self.get_object()
        thread.is_locked = not thread.is_locked
        thread.save(update_fields=['is_locked'])
        return Response(ForumThreadSerializer(thread, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='posts')
    def list_posts(self, request, slug=None):
        thread = self.get_object()
        # Paginate posts
        posts_queryset = thread.posts.select_related('author__profile').order_by('created_at')
        page = self.paginate_queryset(posts_queryset)
        if page is not None:
            serializer = ForumPostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ForumPostSerializer(posts_queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='create-post')
    def create_post_in_thread(self, request, slug=None):
        thread = self.get_object()
        if thread.is_locked and not request.user.is_staff:
             return Response({"detail": "This thread is locked."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ForumPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user, thread=thread)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForumPostViewSet(viewsets.ModelViewSet):
    queryset = ForumPost.objects.select_related('author__profile', 'thread__category')
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        thread_id = self.request.query_params.get('thread_id')
        if thread_id:
            qs = qs.filter(thread_id=thread_id) # Filter by thread_id if provided as query param
        return qs

    def perform_create(self, serializer):
        # Author is set by CurrentUserDefault
        # Thread ID must be provided in request data for serializer
        thread_id = self.request.data.get('thread_id')
        thread = get_object_or_404(ForumThread, id=thread_id)
        if thread.is_locked and not self.request.user.is_staff:
             raise permissions.PermissionDenied("This thread is locked. No new posts allowed.")
        serializer.save(thread=thread) # author is already set by default

    def perform_update(self, serializer):
        # IsAuthorOrReadOnly handles permission
        serializer.save()

    def perform_destroy(self, instance):
        # IsAuthorOrReadOnly handles permission
        super().perform_destroy(instance)


class ShowcaseViewSet(viewsets.ModelViewSet):
    queryset = Showcase.objects.filter(is_public=True).select_related('user__profile').prefetch_related(
        Prefetch('items', queryset=ShowcaseItem.objects.order_by('order'))
    )
    serializer_class = ShowcaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly] # Owner of showcase
    lookup_field = 'slug' # Or use 'user__username' and slug combination for uniqueness if slugs are not globally unique

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        username = self.request.query_params.get('username')
        if username: # Filter by username to see a specific user's public showcases
            return qs.filter(user__username=username, is_public=True)

        if user.is_authenticated:
            # Authenticated users see their own public/private showcases + others' public showcases
            return Showcase.objects.select_related('user__profile').prefetch_related(
                Prefetch('items', queryset=ShowcaseItem.objects.order_by('order'))
            ).filter(Q(is_public=True) | Q(user=user)).distinct()
        return qs # Unauthenticated users see only public showcases

    def perform_create(self, serializer):
        # User is set by CurrentUserDefault
        serializer.save()

    @action(detail=True, methods=['get'], url_path='items')
    def list_items(self, request, slug=None):
        showcase = self.get_object() # Permission check (IsOwnerOrReadOnly for private, AllowAny for public)
        items = showcase.items.all().order_by('order')
        serializer = ShowcaseItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-item', permission_classes=[IsOwnerOrReadOnly])
    def add_showcase_item(self, request, slug=None):
        showcase = self.get_object()
        serializer = ShowcaseItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(showcase=showcase)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShowcaseItemViewSet(viewsets.ModelViewSet):
    queryset = ShowcaseItem.objects.select_related('showcase__user__profile')
    serializer_class = ShowcaseItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly] # Owner of parent showcase

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Filter by showcase_id or showcase_slug
        showcase_id = self.request.query_params.get('showcase_id')
        showcase_slug = self.request.query_params.get('showcase_slug')

        if showcase_id:
            qs = qs.filter(showcase_id=showcase_id)
        elif showcase_slug:
            qs = qs.filter(showcase__slug=showcase_slug) # Assumes showcase slug is passed

        # Ensure user can only see items from public showcases or their own
        if user.is_authenticated:
            return qs.filter(Q(showcase__is_public=True) | Q(showcase__user=user)).distinct()
        return qs.filter(showcase__is_public=True)


    def perform_create(self, serializer):
        # Showcase_id must be provided in request data
        showcase_id = self.request.data.get('showcase_id')
        showcase = get_object_or_404(Showcase, id=showcase_id)
        if showcase.user != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only add items to your own showcases.")
        serializer.save(showcase=showcase)

    def perform_update(self, serializer):
        # Check if user owns the showcase of the item being updated
        if serializer.instance.showcase.user != self.request.user and not self.request.user.is_staff:
             raise permissions.PermissionDenied("You can only update items in your own showcases.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.showcase.user != self.request.user and not self.request.user.is_staff:
             raise permissions.PermissionDenied("You can only delete items from your own showcases.")
        super().perform_destroy(instance)