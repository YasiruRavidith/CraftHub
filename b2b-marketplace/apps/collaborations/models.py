import uuid
from django.db import models
from django.conf import settings
from apps.core.models import AbstractBaseModel # Assuming created_at, updated_at
from apps.orders.models import Order # Optional: Link projects to orders

# If AbstractBaseModel is not defined:
# class AbstractBaseModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         abstract = True


class Project(AbstractBaseModel):
    PROJECT_STATUS_CHOICES = (
        ('pending', 'Pending Start'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    # Owner/creator of the project. Could be buyer, seller, designer, etc.
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    # Members involved in the project.
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='collaborative_projects', blank=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='pending')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    # Optional: Link a project to a specific order if relevant
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Project: {self.name} ({self.id})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.owner: # Automatically add owner to members on creation
            self.members.add(self.owner)


class Task(AbstractBaseModel):
    TASK_STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
        ('blocked', 'Blocked'),
    )
    PRIORITY_CHOICES = (
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='todo')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2) # Medium
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tasks',
        limit_choices_to={'is_active': True} # Only assign to active users
    )
    reporter = models.ForeignKey( # User who created the task
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, # Could be system generated or allow null
        related_name='reported_tasks'
    )
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['priority', 'due_date', 'created_at']

    def __str__(self):
        return f"Task: {self.title} (Project: {self.project.name})"

    def clean(self):
        super().clean()
        if self.assigned_to and self.assigned_to not in self.project.members.all():
            raise models.ValidationError(f"User {self.assigned_to.username} is not a member of project {self.project.name} and cannot be assigned this task.")


class ProjectFile(AbstractBaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='project_files/%Y/%m/%d/')
    description = models.CharField(max_length=255, blank=True, null=True)
    # task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='files') # Optional: Link file to a specific task

    def __str__(self):
        return f"File: {self.file.name} (Project: {self.project.name})"


class Comment(AbstractBaseModel): # Generic comment model for tasks or projects
    # Using GenericForeignKey to allow comments on Tasks or Projects
    # from django.contrib.contenttypes.fields import GenericForeignKey
    # from django.contrib.contenttypes.models import ContentType
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # object_id = models.UUIDField() # Or PositiveIntegerField if PKs are int
    # content_object = GenericForeignKey('content_type', 'object_id')
    # For simplicity, let's start with comments on Tasks only.
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments', null=True, blank=True) # Or allow comments on projects
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_comments')
    text = models.TextField()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        target = self.task or self.project
        return f"Comment by {self.author.username} on {target if target else 'N/A'}"

    def clean(self):
        if not (self.task or self.project):
            raise models.ValidationError("Comment must be associated with a task or a project.")
        if self.task and self.project:
            raise models.ValidationError("Comment cannot be associated with both a task and a project simultaneously.")


# --- For Real-time Messaging (if using Django Channels) ---
class MessageThread(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='message_thread', null=True, blank=True)
    # Or allow generic threads not tied to a project, e.g., direct messages
    # name = models.CharField(max_length=100, null=True, blank=True) # For group chats not tied to project
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='message_threads')

    def __str__(self):
        if self.project:
            return f"Message Thread for Project: {self.project.name}"
        participant_names = ", ".join([user.username for user in self.participants.all()[:3]])
        return f"Thread ID: {self.id} ({participant_names})"


class Message(AbstractBaseModel):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True) # Redundant if AbstractBaseModel has created_at

    class Meta:
        ordering = ['timestamp'] # Or ['-timestamp'] for newest first in some views

    def __str__(self):
        return f"Message from {self.sender.username} in thread {self.thread.id} at {self.timestamp}"