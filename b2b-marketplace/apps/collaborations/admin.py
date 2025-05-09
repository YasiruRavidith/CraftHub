from django.contrib import admin
from .models import Project, Task, ProjectFile, Comment, MessageThread, Message

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('title', 'status', 'assigned_to', 'due_date', 'priority')
    raw_id_fields = ('assigned_to',)

class ProjectFileInline(admin.TabularInline):
    model = ProjectFile
    extra = 1
    raw_id_fields = ('uploaded_by',)

class CommentInlineForProject(admin.TabularInline): # Comments directly on Project
    model = Comment
    extra = 0
    fields = ('author', 'text', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('author',)
    fk_name = 'project' # Specify if model has multiple FKs to Project or if generic

    def get_queryset(self, request):
        # Filter to show only comments directly related to the project, not tasks
        return super().get_queryset(request).filter(task__isnull=True)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'start_date', 'due_date', 'related_order_id_display')
    list_filter = ('status', 'owner')
    search_fields = ('name', 'description', 'owner__username', 'related_order__id')
    inlines = [TaskInline, ProjectFileInline, CommentInlineForProject]
    raw_id_fields = ('owner', 'members', 'related_order')
    filter_horizontal = ('members',) # Better UI for ManyToMany

    def related_order_id_display(self, obj):
        return obj.related_order.id if obj.related_order else None
    related_order_id_display.short_description = 'Related Order ID'


class CommentInlineForTask(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('author', 'text', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('author',)
    fk_name = 'task'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'assigned_to', 'reporter', 'due_date', 'priority')
    list_filter = ('status', 'priority', 'project', 'assigned_to', 'reporter')
    search_fields = ('title', 'description', 'project__name', 'assigned_to__username')
    raw_id_fields = ('project', 'assigned_to', 'reporter')
    inlines = [CommentInlineForTask]


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'project', 'uploaded_by', 'created_at')
    list_filter = ('project', 'uploaded_by')
    search_fields = ('file__name', 'description', 'project__name')
    raw_id_fields = ('project', 'uploaded_by')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'text_snippet', 'target_object_display', 'created_at')
    list_filter = ('author', 'task__project') # Filter by project via task
    search_fields = ('text', 'author__username', 'task__title', 'project__name')
    raw_id_fields = ('author', 'task', 'project')

    def text_snippet(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_snippet.short_description = 'Text'

    def target_object_display(self, obj):
        if obj.task:
            return f"Task: {obj.task.title}"
        if obj.project:
            return f"Project: {obj.project.name}"
        return "N/A"
    target_object_display.short_description = "Target"


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'content', 'timestamp')
    readonly_fields = ('timestamp',)
    raw_id_fields = ('sender',)

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_name_display', 'participant_count', 'created_at')
    search_fields = ('project__name', 'participants__username')
    raw_id_fields = ('project',)
    filter_horizontal = ('participants',)
    inlines = [MessageInline]

    def project_name_display(self, obj):
        return obj.project.name if obj.project else "Direct Message Thread"
    project_name_display.short_description = "Project/Context"

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = "Participants"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'thread_id_display', 'content_snippet', 'timestamp')
    list_filter = ('thread__project', 'sender')
    search_fields = ('content', 'sender__username', 'thread__id')
    raw_id_fields = ('thread', 'sender')

    def thread_id_display(self, obj):
        return obj.thread.id
    thread_id_display.short_description = "Thread ID"

    def content_snippet(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_snippet.short_description = "Content"