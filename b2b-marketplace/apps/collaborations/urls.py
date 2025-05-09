from django.urls import path, include
#from rest_framework_nested import routers # For nested routing if needed
from .views import (
    ProjectViewSet, TaskViewSet, ProjectFileViewSet, CommentViewSet,
    MessageThreadViewSet #, MessageViewSet (if you decide to use it standalone)
)
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

# Primary router for top-level resources
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task') # Can be filtered by project_id query param
router.register(r'files', ProjectFileViewSet, basename='projectfile') # Can be filtered by project_id
router.register(r'comments', CommentViewSet, basename='comment') # Can be filtered by task_id or project_id
router.register(r'message-threads', MessageThreadViewSet, basename='messagethread')
# router.register(r'messages', MessageViewSet, basename='message') # If using a separate MessageViewSet

# Example of Nested Routers (optional, but good for clearly defined hierarchies)
# This allows URLs like /projects/{project_pk}/tasks/ and /tasks/{task_pk}/comments/

# projects_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
# projects_router.register(r'tasks', TaskViewSet, basename='project-tasks')
# projects_router.register(r'files', ProjectFileViewSet, basename='project-files')
# projects_router.register(r'comments', CommentViewSet, basename='project-comments') # For comments directly on projects

# tasks_router = routers.NestedSimpleRouter(projects_router, r'tasks', lookup='task')
# tasks_router.register(r'comments', CommentViewSet, basename='task-comments')

# message_threads_router = routers.NestedSimpleRouter(router, r'message-threads', lookup='thread')
# message_threads_router.register(r'messages', MessageViewSet, basename='thread-messages') # If messages were sub-resource of thread via router

urlpatterns = [
    path('', include(router.urls)),
    # If using nested routers:
    # path('', include(projects_router.urls)),
    # path('', include(tasks_router.urls)),
    # path('', include(message_threads_router.urls)),
]

# Note on Nested Routers:
# While powerful for URL structure, they can sometimes make view logic (especially for get_queryset
# and permissions that rely on URL kwargs like project_pk) a bit more complex if not planned carefully.
# The current views primarily use query parameters (e.g., ?project_id=) for filtering,
# which works well with the simple DefaultRouter.
# If you choose nested routers, you'd adjust views to get parent PKs from self.kwargs.
# For instance, in TaskViewSet nested under projects, you'd get project_pk via self.kwargs['project_pk'].
# The current `send_message` and `list_messages` actions on MessageThreadViewSet act like nested resources.