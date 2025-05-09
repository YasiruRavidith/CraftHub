from rest_framework import permissions

class IsProjectOwnerOrMemberReadOnly(permissions.BasePermission):
    """
    Allows read access to project members.
    Allows write/delete access only to project owner or admin.
    """
    def has_object_permission(self, request, view, obj): # obj is Project
        is_member = request.user in obj.members.all() or request.user == obj.owner
        is_admin = request.user.is_staff

        if request.method in permissions.SAFE_METHODS:
            return is_member or is_admin # Members and admin can read

        # Write permissions only for owner or admin
        return obj.owner == request.user or is_admin


class IsProjectMember(permissions.BasePermission):
    """
    Allows access if the user is a member of the project (or owner).
    Used for accessing project-related sub-resources like tasks, files, comments.
    """
    def has_object_permission(self, request, view, obj): # obj can be Project, Task, ProjectFile, Comment
        user = request.user
        if user.is_staff:
            return True

        project = None
        if hasattr(obj, 'project'): # For Task, ProjectFile
            project = obj.project
        elif isinstance(obj, Project): # For Project itself
            project = obj
        elif hasattr(obj, 'task') and obj.task: # For Comment on Task
            project = obj.task.project
        elif hasattr(obj, 'project_comment') and obj.project_comment: # For Comment on Project (if using different related_name)
             project = obj.project_comment
        elif hasattr(obj, 'id') and view.basename == 'project': # If obj is Project, from generic view
             project = obj


        if project:
            return project.owner == user or project.members.filter(id=user.id).exists()
        return False # Deny if project context cannot be determined or user is not member

    def has_permission(self, request, view): # For list views where object is not yet fetched
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True

        # For list views, filtering happens in get_queryset.
        # This permission mainly works with has_object_permission for detail views.
        # However, for creating items related to a project, check here or in view.
        if view.action == 'create':
            project_id = request.data.get('project_id') or request.data.get('project')
            if project_id:
                try:
                    project = Project.objects.get(id=project_id)
                    return project.owner == request.user or project.members.filter(id=request.user.id).exists()
                except Project.DoesNotExist:
                    return False # Project not found, deny
            return False # Project ID required for creation of sub-resources
        return True # Allow other list/detail views, let has_object_permission handle detail.


class IsTaskAssigneeOrProjectMember(permissions.BasePermission):
    """
    Allows access if user is assigned to the task, or is a member of the task's project.
    Owner of project has full access.
    """
    def has_object_permission(self, request, view, obj): # obj is Task
        user = request.user
        if user.is_staff:
            return True

        project = obj.project
        is_project_owner = project.owner == user
        is_project_member = project.members.filter(id=user.id).exists()
        is_assignee = obj.assigned_to == user

        if request.method in permissions.SAFE_METHODS:
            return is_project_member or is_assignee # Members or assignee can read

        # Write permissions: Project owner, assignee (e.g., to update status), or project members (e.g., to comment - handled by comment perm)
        # For editing task details, usually project owner or assignee.
        return is_project_owner or is_assignee or (is_project_member and view.action in ['update', 'partial_update']) # Allow members to update tasks
        # return is_project_owner or is_assignee # Stricter: only owner or assignee can modify task details


class IsCommentAuthorOrProjectMemberReadOnly(permissions.BasePermission):
    """
    Allows read access to project members.
    Allows write/delete only to comment author or project owner/admin.
    """
    def has_object_permission(self, request, view, obj): # obj is Comment
        user = request.user
        if user.is_staff:
            return True

        project = None
        if obj.task:
            project = obj.task.project
        elif obj.project: # Direct comment on project
            project = obj.project

        if not project: return False # Should not happen if comment is valid

        is_project_member = project.members.filter(id=user.id).exists() or project.owner == user

        if request.method in permissions.SAFE_METHODS:
            return is_project_member

        # Write permissions for comment author or project owner
        return obj.author == user or project.owner == user


class IsThreadParticipant(permissions.BasePermission):
    """
    Allows access if the user is a participant in the message thread.
    """
    def has_object_permission(self, request, view, obj): # obj is MessageThread or Message
        user = request.user
        if user.is_staff:
            return True

        thread = None
        if isinstance(obj, MessageThread):
            thread = obj
        elif isinstance(obj, Message):
            thread = obj.thread
        else: # Should not happen for relevant views
            return False

        return thread.participants.filter(id=user.id).exists()

    def has_permission(self, request, view): # For list views or creating threads
        if not request.user or not request.user.is_authenticated:
            return False
        # For creating a thread, participants are specified in request.
        # The serializer/view should ensure the creator is a participant.
        # For listing threads, get_queryset filters by participation.
        return True