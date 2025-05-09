from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Prefetch, OuterRef, Subquery, F
from django.shortcuts import get_object_or_404

from .models import Project, Task, ProjectFile, Comment, MessageThread, Message
from .serializers import (
    ProjectSerializer, TaskSerializer, ProjectFileSerializer, CommentSerializer,
    MessageThreadSerializer, MessageSerializer
)
from .permissions import ( # You'll need to create these
    IsProjectOwnerOrMemberReadOnly, IsProjectMember,
    IsTaskAssigneeOrProjectMember, IsCommentAuthorOrProjectMemberReadOnly,
    IsThreadParticipant
)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related('owner__profile', 'related_order').prefetch_related(
        'members__profile',
        Prefetch('tasks', queryset=Task.objects.order_by('priority', 'due_date')), # Example prefetch for tasks
        'files',
        Prefetch('comments', queryset=Comment.objects.filter(task__isnull=True).select_related('author__profile')) # Project-level comments
    )
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwnerOrMemberReadOnly]
    lookup_field = 'id' # UUID

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none() # Projects are not public by default

        # Admins see all projects
        if user.is_staff or user.is_superuser:
            return super().get_queryset()

        # Users see projects they own or are members of
        return super().get_queryset().filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        # Owner is set by CurrentUserDefault in serializer
        project = serializer.save()
        # Model's save method now ensures owner is added to members

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsProjectOwnerOrMemberReadOnly]) # Owner can manage members
    def add_member(self, request, id=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_to_add = settings.AUTH_USER_MODEL.objects.get(id=user_id)
            if user_to_add in project.members.all():
                return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)
            project.members.add(user_to_add)
            return Response(ProjectSerializer(project, context={'request': request}).data)
        except settings.AUTH_USER_MODEL.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsProjectOwnerOrMemberReadOnly]) # Owner can manage members
    def remove_member(self, request, id=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_to_remove = settings.AUTH_USER_MODEL.objects.get(id=user_id)
            if user_to_remove == project.owner:
                return Response({"detail": "Cannot remove the project owner."}, status=status.HTTP_400_BAD_REQUEST)
            if user_to_remove not in project.members.all():
                return Response({"detail": "User is not a member of this project."}, status=status.HTTP_400_BAD_REQUEST)
            project.members.remove(user_to_remove)
            # Also unassign from tasks if they were assigned
            Task.objects.filter(project=project, assigned_to=user_to_remove).update(assigned_to=None)
            return Response(ProjectSerializer(project, context={'request': request}).data)
        except settings.AUTH_USER_MODEL.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='tasks', permission_classes=[permissions.IsAuthenticated, IsProjectMember])
    def list_tasks(self, request, id=None):
        project = self.get_object()
        tasks = project.tasks.all().select_related('assigned_to__profile', 'reporter__profile').prefetch_related('comments')
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='files', permission_classes=[permissions.IsAuthenticated, IsProjectMember])
    def list_files(self, request, id=None):
        project = self.get_object()
        files = project.files.all().select_related('uploaded_by__profile')
        serializer = ProjectFileSerializer(files, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='comments', permission_classes=[permissions.IsAuthenticated, IsProjectMember])
    def list_comments(self, request, id=None): # Comments directly on the project
        project = self.get_object()
        comments = project.comments.filter(task__isnull=True).select_related('author__profile')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related('project', 'assigned_to__profile', 'reporter__profile').prefetch_related('comments__author__profile')
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskAssigneeOrProjectMember]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        if user.is_staff:
            return super().get_queryset()

        # Filter tasks based on project membership or assignment
        project_id = self.request.query_params.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                if project.members.filter(id=user.id).exists() or project.owner == user:
                    return super().get_queryset().filter(project_id=project_id)
                else: # User not a member of the specified project
                    return Task.objects.none()
            except Project.DoesNotExist:
                return Task.objects.none() # Project not found

        # Default: show tasks from projects user is member of, or tasks assigned to user
        return super().get_queryset().filter(
            Q(project__members=user) | Q(assigned_to=user)
        ).distinct()

    def perform_create(self, serializer):
        project_id = self.request.data.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        if not project.members.filter(id=self.request.user.id).exists() and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You must be a member of the project to create tasks.")
        # Reporter is set by CurrentUserDefault in serializer
        serializer.save(project=project)

    @action(detail=True, methods=['get'], url_path='comments', permission_classes=[permissions.IsAuthenticated, IsTaskAssigneeOrProjectMember])
    def list_comments(self, request, pk=None):
        task = self.get_object()
        comments = task.comments.all().select_related('author__profile')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)


class ProjectFileViewSet(viewsets.ModelViewSet):
    queryset = ProjectFile.objects.all().select_related('project', 'uploaded_by__profile')
    serializer_class = ProjectFileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember] # Must be member to interact with files

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return ProjectFile.objects.none()
        if user.is_staff: return super().get_queryset()

        project_id = self.request.query_params.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                if project.members.filter(id=user.id).exists() or project.owner == user:
                    return super().get_queryset().filter(project_id=project_id)
                return ProjectFile.objects.none()
            except Project.DoesNotExist:
                return ProjectFile.objects.none()

        return super().get_queryset().filter(project__members=user).distinct()


    def perform_create(self, serializer):
        project_id = self.request.data.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        if not project.members.filter(id=self.request.user.id).exists() and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You must be a member of the project to upload files.")
        # uploaded_by is set by CurrentUserDefault
        serializer.save(project=project)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related('author__profile', 'task__project', 'project') # task__project for filtering
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthorOrProjectMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return Comment.objects.none()
        if user.is_staff: return super().get_queryset()

        task_id = self.request.query_params.get('task_id')
        project_id = self.request.query_params.get('project_id') # For project-level comments

        q_filter = Q()
        if task_id:
            q_filter &= Q(task_id=task_id, task__project__members=user)
        elif project_id:
            q_filter &= Q(project_id=project_id, project__members=user, task__isnull=True)
        else: # General case: comments user can see (authored or on projects/tasks they are part of)
            q_filter = Q(author=user) | Q(task__project__members=user) | Q(project__members=user, task__isnull=True)

        return super().get_queryset().filter(q_filter).distinct()

    def perform_create(self, serializer):
        # Author is set by CurrentUserDefault
        # Validation in serializer checks if user is member of project/task's project
        task_id = self.request.data.get('task')
        project_id = self.request.data.get('project') # project_id if comment is on project directly

        target_project = None
        if task_id:
            task = get_object_or_404(Task, id=task_id)
            target_project = task.project
        elif project_id:
            target_project = get_object_or_404(Project, id=project_id)

        if target_project:
            if not target_project.members.filter(id=self.request.user.id).exists() and not self.request.user.is_staff:
                raise permissions.PermissionDenied("You must be a member of the project to comment.")
        else: # Should be caught by serializer validation (task or project must be specified)
            raise permissions.PermissionDenied("Comment must be associated with a task or project.")

        serializer.save()


# --- Messaging Views ---
class MessageThreadViewSet(viewsets.ModelViewSet):
    serializer_class = MessageThreadSerializer
    permission_classes = [permissions.IsAuthenticated, IsThreadParticipant]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return MessageThread.objects.none()

        # Annotate with last message for ordering/display (can also be done in serializer or model manager)
        last_message_subquery = Message.objects.filter(thread=OuterRef('pk')).order_by('-timestamp').values('timestamp')[:1]
        # last_message_content_subquery = Message.objects.filter(thread=OuterRef('pk')).order_by('-timestamp').values('content')[:1]

        queryset = MessageThread.objects.filter(participants=user).annotate(
            last_message_timestamp=Subquery(last_message_subquery),
            # last_message_content=Subquery(last_message_content_subquery) # if needed
        ).select_related('project').prefetch_related(
            'participants__profile',
            # Prefetch only the latest message for each thread for 'last_message' field if not done via annotation
            # Prefetch('messages', queryset=Message.objects.order_by('-timestamp')[:1], to_attr='latest_message_list')
        ).order_by(F('last_message_timestamp').desc(nulls_last=True), '-updated_at')
        return queryset

    def perform_create(self, serializer):
        # participant_ids are handled in serializer, including adding current user if DM
        # Ensure creator is participant is handled in serializer
        serializer.save() # participant_ids are set in serializer's create

    @action(detail=True, methods=['get'], url_path='messages')
    def list_messages(self, request, id=None):
        thread = self.get_object() # Permission check (IsThreadParticipant) done by get_object
        messages = thread.messages.all().select_related('sender__profile').order_by('timestamp')
        # Implement pagination for messages
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, id=None):
        thread = self.get_object() # Permission check
        serializer = MessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Ensure sender is current user and part of thread (serializer does this)
            # Ensure thread in request data matches the URL's thread
            if serializer.validated_data.get('thread') != thread:
                 return Response({"detail": "Mismatch in thread ID."}, status=status.HTTP_400_BAD_REQUEST)

            message = serializer.save(sender=request.user, thread=thread)
            # If using Django Channels, broadcast this message
            # from asgiref.sync import async_to_sync
            # from channels.layers import get_channel_layer
            # channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.group_send)(
            #     f"thread_{thread.id}",
            #     {
            #         "type": "chat.message", # Corresponds to a consumer method
            #         "message": MessageSerializer(message).data,
            #     }
            # )
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# If Message creation is only via MessageThreadViewSet.send_message, this might not be needed.
# class MessageViewSet(viewsets.ModelViewSet):
#     queryset = Message.objects.all()
#     serializer_class = MessageSerializer
#     permission_classes = [permissions.IsAuthenticated, IsThreadParticipantOfMessage] # Custom perm
#
#     def get_queryset(self):
#         user = self.request.user
#         if not user.is_authenticated: return Message.objects.none()
#         if user.is_staff: return super().get_queryset()
#         # Show messages from threads the user is part of
#         return super().get_queryset().filter(thread__participants=user)
#
#     def perform_create(self, serializer):
#         thread = serializer.validated_data.get('thread')
#         if not thread.participants.filter(id=self.request.user.id).exists():
#             raise permissions.PermissionDenied("You are not a participant of this thread.")
#         serializer.save(sender=self.request.user)