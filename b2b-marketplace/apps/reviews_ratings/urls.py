from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from rest_framework_nested import routers as nested_routers # If using nested for reviews on specific items

from .views import ReviewViewSet, ReviewReplyViewSet, ListReviewsForObjectView

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'review-replies', ReviewReplyViewSet, basename='reviewreply')

# Example of how you might use nested routers if you wanted URLs like:
# /api/v1/listings/materials/{material_pk}/reviews/
# This would require ReviewViewSet to be adapted to handle kwargs from the URL.
# For this, you would typically register the base resource (e.g., materials)
# in apps.listings.urls and then nest the reviews router under it.

# Example (conceptual - actual registration would be in listings app's urls.py if nesting there):
# listings_router = nested_routers.DefaultRouter() (from listings app)
# material_reviews_router = nested_routers.NestedSimpleRouter(listings_router, r'materials', lookup='material')
# material_reviews_router.register(r'reviews', ReviewViewSet, basename='material-review')
# (This is just an illustration of the concept, not a direct implementation here)


urlpatterns = [
    path('', include(router.urls)),

    # URL for the generic view to list reviews for any model/object ID
    # e.g., /api/v1/reviews-ratings/for-item/material/<object_id>/
    # e.g., /api/v1/reviews-ratings/for-item/customuser/<object_id>/
    path(
        'for-item/<str:model_name>/<str:object_id>/', # Using str for object_id for flexibility with UUIDs/ints
        ListReviewsForObjectView.as_view(),
        name='reviews-for-object'
    ),
]