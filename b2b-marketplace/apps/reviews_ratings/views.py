from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action

from .models import Review, ReviewReply
from .serializers import ReviewSerializer, ReviewReplySerializer
from .permissions import IsAuthorOrReadOnly, IsReviewOwnerOrAdminForReply # Create these

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.filter(is_approved=True).select_related('author__profile').prefetch_related('replies__author__profile')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'rating': ['exact'],
        'content_type__model': ['exact'], # e.g., ?content_type__model=material
        'object_id_str': ['exact'],       # e.g., ?object_id_str=<uuid_or_id>
        'author__id': ['exact']
    }

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Allow admin/staff to see unapproved reviews
        if user.is_authenticated and user.is_staff:
            qs = Review.objects.all().select_related('author__profile').prefetch_related('replies__author__profile')

        # Specific filtering by content_type and object_id_str from URL kwargs if using nested routes (not current setup)
        # Example if nested:
        # content_type_kwarg = self.kwargs.get('content_type_model_kwarg')
        # object_id_kwarg = self.kwargs.get('object_id_kwarg')
        # if content_type_kwarg and object_id_kwarg:
        #     try:
        #         ct = ContentType.objects.get(model=content_type_kwarg)
        #         qs = qs.filter(content_type=ct, object_id_str=object_id_kwarg)
        #     except ContentType.DoesNotExist:
        #         return Review.objects.none()
        return qs

    def perform_create(self, serializer):
        # Author is set by CurrentUserDefault in serializer
        # GFK validation is done in serializer's validate method
        serializer.save() # is_approved defaults to True or as set in model

    def perform_update(self, serializer):
        # Permission IsAuthorOrReadOnly checks if user is author
        # Serializer's update method handles which fields can be updated
        serializer.save()

    def perform_destroy(self, instance):
        # Permission IsAuthorOrReadOnly checks if user is author
        # The signal review_deleted_handler will update average ratings
        super().perform_destroy(instance)

    # Action for admin to approve/unapprove reviews
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser], url_path='toggle-approval')
    def toggle_approval(self, request, pk=None):
        review = self.get_object()
        review.is_approved = not review.is_approved
        review.save(update_fields=['is_approved'])
        # Signal will be triggered by save to update average rating
        return Response(ReviewSerializer(review, context={'request': request}).data)


class ReviewReplyViewSet(viewsets.ModelViewSet):
    queryset = ReviewReply.objects.all().select_related('author__profile', 'review__author')
    serializer_class = ReviewReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrAdminForReply]

    def get_queryset(self):
        qs = super().get_queryset()
        review_id = self.request.query_params.get('review_id')
        if review_id:
            qs = qs.filter(review_id=review_id)
        return qs

    def perform_create(self, serializer):
        # Author is set by CurrentUserDefault in serializer
        # Validation in serializer checks if user is authorized to reply
        review_id = self.request.data.get('review_id') # From serializer field
        review = get_object_or_404(Review, id=review_id)

        # Additional check here if serializer didn't cover all cases or for clarity
        # Example: Check if user is owner of the item reviewed by 'review.content_object'
        # This logic is partly in ReviewReplySerializer.validate()
        # For simplicity, we rely on serializer validation for authorization to reply.
        serializer.save(review=review)

    def perform_update(self, serializer):
        # IsReviewOwnerOrAdminForReply checks if user is author of reply or admin
        serializer.save()

    def perform_destroy(self, instance):
        # IsReviewOwnerOrAdminForReply checks if user is author of reply or admin
        super().perform_destroy(instance)


# Generic view to list reviews for any model instance (if not using query params on ReviewViewSet)
# This is an alternative way to fetch reviews for a specific item.
# Example URL: /api/v1/reviews/for-item/{model_name}/{object_id}/
class ListReviewsForObjectView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny] # Publicly viewable reviews

    def get_queryset(self):
        model_name = self.kwargs.get('model_name').lower()
        object_id = self.kwargs.get('object_id') # This will be a string

        try:
            content_type = ContentType.objects.get(model=model_name)
            # Fetch the actual object to ensure it exists before listing reviews (optional but good practice)
            # model_class = content_type.model_class()
            # get_object_or_404(model_class, pk=object_id)
        except ContentType.DoesNotExist:
            return Review.objects.none() # Or raise Http404

        return Review.objects.filter(
            content_type=content_type,
            object_id_str=str(object_id), # Ensure object_id is string for GFK
            is_approved=True
        ).select_related('author__profile').prefetch_related('replies__author__profile')