from rest_framework import serializers
from django.conf import settings
from .models import Project, Task, ProjectFile, Comment, MessageThread, Message
from apps.accounts.serializers import UserSerializer # For owner, members, assigned_to, author etc.
from apps.orders.serializers import OrderSerializer # For related_order details (optional)
from django.contrib.auth import get_user_model
from apps.orders.models import Order

User = get_user_model()

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='author', write_only=True,
        default=serializers.CurrentUserDefault() # Auto set author to current user
    )
    # For polymorphism if using GenericForeignKey (not in current simple model)
    # content_type = serializers.CharField(source='content_type.model', read_only=True)
    # object_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'task', 'project', 'author', 'author_id', 'text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'task': {'required': False, 'allow_null': True},
            'project': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        task = data.get('task')
        project_obj = data.get('project') # Renamed to avoid conflict with project context
        request = self.context.get('request')
        user = request.user if request else None

        if not (task or project_obj):
            raise serializers.ValidationError("Comment must be associated with a task or a project.")
        if task and project_obj:
            raise serializers.ValidationError("Comment cannot be associated with both a task and a project simultaneously.")

        # Check if user is a member of the project associated with the task or project
        target_project = None
        if task:
            target_project = task.project
        elif project_obj:
            target_project = project_obj

        if user and target_project and not target_project.members.filter(id=user.id).exists() and not user.is_staff:
            raise serializers.ValidationError("You must be a member of the project to comment.")

        # Set author if not explicitly provided by CurrentUserDefault
        if 'author' not in data and user:
            data['author'] = user
        return data


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True, allow_null=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assigned_to', write_only=True, allow_null=True, required=False
    )
    reporter = UserSerializer(read_only=True, allow_null=True)
    reporter_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='reporter', write_only=True, allow_null=True, required=False,
        default=serializers.CurrentUserDefault()
    )
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), source='project', write_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    comments = CommentSerializer(many=True, read_only=True) # Nested comments

    class Meta:
        model = Task
        fields = [
            'id', 'project_id', 'project_name', 'title', 'description', 'status', 'priority',
            'assigned_to', 'assigned_to_id', 'reporter', 'reporter_id',
            'due_date', 'estimated_hours', 'actual_hours',
            'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'project_name', 'comments']

    def validate_assigned_to_id(self, value):
        # Ensure assigned_to user is a member of the project
        project = self.initial_data.get('project_id') # Get project_id from initial data for validation
        if value and project: # project is ID here, needs to be instance
            try:
                project_instance = Project.objects.get(id=project)
                if not project_instance.members.filter(id=value.id).exists():
                    raise serializers.ValidationError(f"User {value.username} is not a member of project {project_instance.name}.")
            except Project.DoesNotExist:
                 raise serializers.ValidationError(f"Project with id {project} not found.") # Should be caught by project_id validation
        return value

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        project = data.get('project') # This is project instance now after project_id field

        if user and project and not project.members.filter(id=user.id).exists() and not user.is_staff:
            # On create, only members or admin can create tasks for a project
            if not self.instance: # Only for creation
                 raise serializers.ValidationError("You must be a member of the project to create tasks.")

        # Reporter is set by default, no need to check if user is member for reporting
        return data


class ProjectFileSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True, allow_null=True)
    uploaded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='uploaded_by', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), source='project')
    file_url = serializers.FileField(source='file', read_only=True)

    class Meta:
        model = ProjectFile
        fields = ['id', 'project_id', 'uploaded_by', 'uploaded_by_id', 'file', 'file_url', 'description', 'created_at']
        read_only_fields = ['id', 'created_at', 'file_url']
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        project = data.get('project')

        if user and project and not project.members.filter(id=user.id).exists() and not user.is_staff:
            raise serializers.ValidationError("You must be a member of the project to upload files.")
        return data


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='owner', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='members', write_only=True, many=True, required=False
    )
    related_order_details = OrderSerializer(source='related_order', read_only=True, allow_null=True)
    related_order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), source='related_order', write_only=True, allow_null=True, required=False
    )
    tasks = TaskSerializer(many=True, read_only=True) # Optionally nest tasks
    files = ProjectFileSerializer(many=True, read_only=True) # Optionally nest files
    comments = CommentSerializer(many=True, read_only=True) # Comments directly on the project

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'owner', 'owner_id', 'members', 'member_ids',
            'status', 'start_date', 'due_date',
            'related_order_id', 'related_order_details',
            'tasks', 'files', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tasks', 'files', 'comments', 'related_order_details']

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        owner = validated_data.get('owner') # Owner is already set by CurrentUserDefault or validated

        project = super().create(validated_data)

        # Add owner to members if not already (model's save method handles this now)
        # if owner and owner not in project.members.all():
        #    project.members.add(owner)

        if member_ids:
            project.members.add(*member_ids)
        return project

    def update(self, instance, validated_data):
        member_ids = validated_data.pop('member_ids', None) # Use None to detect if field was passed
        project = super().update(instance, validated_data)

        if member_ids is not None: # If member_ids was part of the request data
            project.members.set(member_ids) # .set() replaces existing members
            # Ensure owner remains a member if not explicitly removed and still owner
            if project.owner and not project.members.filter(id=project.owner.id).exists():
                project.members.add(project.owner)

        return project

    def validate(self, data):
        # Ensure the owner (if being set/changed) and members are valid users.
        # DRF's PrimaryKeyRelatedField handles existence checks.
        # Further validation: e.g., only certain user types can own projects.
        request = self.context.get('request')
        user = request.user if request else None

        # On creation, owner is set by default.
        # On update, check if user has permission to change owner or members.
        if self.instance: # If updating
            if user != self.instance.owner and not user.is_staff:
                # Non-owners (and non-admins) cannot change project ownership or core details easily
                # This should be primarily handled by permissions, but good to have a check.
                if 'owner_id' in data and data['owner_id'] != self.instance.owner:
                     raise serializers.ValidationError("Only the project owner or admin can change ownership.")
                # Potentially restrict changing members too if not owner/admin
                # if 'member_ids' in data and data['member_ids'] != list(self.instance.members.values_list('id', flat=True)):
                #    raise serializers.ValidationError("Only project owner or admin can change members list.")

        # Check if all member_ids are valid and active users
        # (PrimaryKeyRelatedField handles existence, add active check if needed)
        return data


# --- For Messaging ---
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='sender', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    thread_id = serializers.PrimaryKeyRelatedField(queryset=MessageThread.objects.all(), source='thread')

    class Meta:
        model = Message
        fields = ['id', 'thread_id', 'sender', 'sender_id', 'content', 'timestamp', 'created_at']
        read_only_fields = ['id', 'timestamp', 'created_at'] # timestamp is Message model field, created_at from AbstractBaseModel

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        thread = data.get('thread')

        if user and thread and not thread.participants.filter(id=user.id).exists() and not user.is_staff:
            raise serializers.ValidationError("You must be a participant in the thread to send messages.")
        return data

class MessageThreadSerializer(serializers.ModelSerializer):
    project_details = ProjectSerializer(source='project', read_only=True, allow_null=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), source='project', write_only=True, allow_null=True, required=False
    )
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='participants', write_only=True, many=True
    )
    messages = MessageSerializer(many=True, read_only=True) # Optionally nest last N messages
    last_message = MessageSerializer(read_only=True, allow_null=True) # For displaying latest message in thread list

    class Meta:
        model = MessageThread
        fields = [
            'id', 'project_id', 'project_details', 'participants', 'participant_ids',
            'messages', 'last_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'messages', 'last_message', 'project_details']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        project = validated_data.get('project')
        request = self.context.get('request')
        user = request.user if request else None

        # If thread is for a project, participants should be project members.
        if project:
            # Ensure all provided participant_ids are members of the project
            project_member_ids = set(project.members.values_list('id', flat=True))
            for pid in participant_ids:
                if pid.id not in project_member_ids: # pid is User instance
                    raise serializers.ValidationError(f"User {pid.username} is not a member of project {project.name}.")
            # Automatically add all project members to the thread if not specified or add logic.
            # For now, we use the provided participant_ids.
        else: # Direct message thread
            if user and user.id not in [p.id for p in participant_ids]: # Ensure creator is in participants
                participant_ids.append(user)

        if not participant_ids:
             raise serializers.ValidationError("A message thread must have participants.")


        # Prevent duplicate threads for the same set of participants (especially for DM)
        # This logic can be complex. For project threads, it's usually 1-to-1 with project.
        # For DMs, if you want to find existing thread:
        # if not project and len(participant_ids) == 2:
        #     user1, user2 = participant_ids[0], participant_ids[1]
        #     existing_thread = MessageThread.objects.annotate(num_participants=models.Count('participants')) \
        #         .filter(num_participants=2, project__isnull=True) \
        #         .filter(participants=user1).filter(participants=user2).first()
        #     if existing_thread:
        #         return existing_thread # Return existing DM thread

        thread = MessageThread.objects.create(**validated_data)
        thread.participants.set(participant_ids)
        return thread