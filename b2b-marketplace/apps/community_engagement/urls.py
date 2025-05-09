from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from rest_framework_nested import routers as nested_routers # For potential nested URLs

from .views import (
    ForumCategoryViewSet, ForumThreadViewSet, ForumPostViewSet,
    ShowcaseViewSet, ShowcaseItemViewSet
)

router = DefaultRouter()
router.register(r'forum-categories', ForumCategoryViewSet, basename='forumcategory')
router.register(r'forum-threads', ForumThreadViewSet, basename='forumthread')
router.register(r'forum-posts', ForumPostViewSet, basename='forumpost')
router.register(r'showcases', ShowcaseViewSet, basename='showcase')
router.register(r'showcase-items', ShowcaseItemViewSet, basename='showcaseitem')

# --- Example of Nested Routers (Optional) ---
# If you wanted URLs like /forum-categories/{category_slug}/threads/
# or /forum-threads/{thread_slug}/posts/
# or /showcases/{showcase_slug}/items/

# forum_categories_router = nested_routers.NestedSimpleRouter(router, r'forum-categories', lookup='category')
# forum_categories_router.register(r'threads', ForumThreadViewSet, basename='category-threads')
# This would require ForumThreadViewSet to get category_slug from self.kwargs['category_pk'] (or category_slug)

# forum_threads_router = nested_routers.NestedSimpleRouter(router, r'forum-threads', lookup='thread') # Use 'thread' as lookup prefix for router
# forum_threads_router.register(r'posts', ForumPostViewSet, basename='thread-posts')
# This would require ForumPostViewSet to get thread_slug from self.kwargs['thread_pk'] (or thread_slug)
# The current ForumThreadViewSet.list_posts and .create_post_in_thread actions serve a similar purpose.

# showcases_router = nested_routers.NestedSimpleRouter(router, r'showcases', lookup='showcase')
# showcases_router.register(r'items', ShowcaseItemViewSet, basename='showcase-items-nested')
# This would require ShowcaseItemViewSet to get showcase_slug from self.kwargs['showcase_pk'] (or showcase_slug)
# The current ShowcaseViewSet.list_items and .add_showcase_item actions serve a similar purpose.

urlpatterns = [
    path('', include(router.urls)),
    # If using nested routers:
    # path('', include(forum_categories_router.urls)),
    # path('', include(forum_threads_router.urls)),
    # path('', include(showcases_router.urls)),
]