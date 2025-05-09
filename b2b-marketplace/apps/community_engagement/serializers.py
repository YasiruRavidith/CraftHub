from rest_framework import serializers
from django.conf import settings
from .models import ForumCategory, ForumThread, ForumPost, Showcase, ShowcaseItem
from apps.accounts.serializers import UserSerializer # For author/user details
from django.contrib.auth import get_user_model

User = get_user_model()

class ForumCategorySerializer(serializers.ModelSerializer):
    threads_count = serializers.IntegerField(source='threads.count', read_only=True)
    # last_activity = serializers.SerializerMethodField() # Could show last thread/post time

    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'slug', 'description', 'threads_count', 'created_at']
        read_only_fields = ['slug', 'created_at', 'threads_count']

    # def get_last_activity(self, obj):
    #     last_thread = obj.threads.order_by('-updated_at').first()
    #     if last_thread:
    #         return ForumThreadSerializer(last_thread, context=self.context, fields=['updated_at', 'slug', 'title']).data # Example minimal data
    #     return None

class ForumPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='author', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    thread_id = serializers.PrimaryKeyRelatedField(queryset=ForumThread.objects.all(), source='thread')

    class Meta:
        model = ForumPost
        fields = ['id', 'thread_id', 'author', 'author_id', 'content', 'is_edited', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_edited', 'created_at', 'updated_at']

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        thread = data.get('thread')

        if thread and thread.is_locked and not user.is_staff:
            raise serializers.ValidationError("This thread is locked. No new posts allowed.")
        # Further validation: ensure user has permission to post in this category/thread (e.g. private forums)
        return data


class ForumThreadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='author', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    category_slug = serializers.SlugRelatedField(queryset=ForumCategory.objects.all(), slug_field='slug', source='category')
    # category = ForumCategorySerializer(read_only=True) # Alternative for nested category details

    posts_count = serializers.SerializerMethodField(read_only=True)
    # initial_post = ForumPostSerializer(read_only=True) # For displaying the first post details
    last_activity_at = serializers.DateTimeField(source='get_last_post_created_at', read_only=True)
    last_activity_by = UserSerializer(source='get_last_post_author', read_only=True, allow_null=True)


    class Meta:
        model = ForumThread
        fields = [
            'id', 'category_slug', 'author', 'author_id', 'title', 'slug',
            'is_pinned', 'is_locked', 'views_count', 'posts_count',
            'last_activity_at', 'last_activity_by',
            'created_at', 'updated_at'
            # 'initial_post'
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'posts_count', 'created_at', 'updated_at', 'last_activity_at', 'last_activity_by']

    def get_posts_count(self, obj):
        return obj.posts.count()

    # def get_initial_post(self, obj):
    #     first_post = obj.posts.order_by('created_at').first()
    #     if first_post:
    #         return ForumPostSerializer(first_post, context=self.context).data
    #     return None

    def create(self, validated_data):
        # If thread creation also requires an initial post:
        initial_post_content = self.context.get('request').data.get('initial_post_content')
        if not initial_post_content:
            raise serializers.ValidationError({"initial_post_content": "An initial post is required to create a thread."})

        thread = super().create(validated_data)

        # Create the initial post for the thread
        ForumPost.objects.create(
            thread=thread,
            author=thread.author, # Author of thread is author of first post
            content=initial_post_content
        )
        return thread


class ForumThreadDetailSerializer(ForumThreadSerializer):
    """Serializer for thread detail view, includes posts."""
    posts = ForumPostSerializer(many=True, read_only=True)
    category = ForumCategorySerializer(read_only=True) # Full category details

    class Meta(ForumThreadSerializer.Meta): # Inherit fields from ForumThreadSerializer
        fields = ForumThreadSerializer.Meta.fields + ['posts', 'category']


class ShowcaseItemSerializer(serializers.ModelSerializer):
    showcase_id = serializers.PrimaryKeyRelatedField(queryset=Showcase.objects.all(), source='showcase')
    image_url = serializers.ImageField(source='image', read_only=True, allow_null=True)
    file_url = serializers.FileField(source='file', read_only=True, allow_null=True)

    class Meta:
        model = ShowcaseItem
        fields = [
            'id', 'showcase_id', 'title', 'description', 'image', 'image_url', 'file', 'file_url',
            'url_link', 'item_type', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'image_url', 'file_url']
        extra_kwargs = {
            'image': {'write_only': True, 'required': False},
            'file': {'write_only': True, 'required': False},
        }

    def validate(self, data):
        item_type = data.get('item_type')
        image = data.get('image')
        file_obj = data.get('file') # Renamed to avoid conflict
        url_link = data.get('url_link')

        if item_type == 'image' and not image:
            if not (self.instance and self.instance.image): # Allow update without new image if one exists
                raise serializers.ValidationError({"image": "Image is required for item_type 'image'."})
        elif item_type == 'file' and not file_obj:
            if not (self.instance and self.instance.file):
                raise serializers.ValidationError({"file": "File is required for item_type 'file'."})
        elif item_type == 'link' and not url_link:
            raise serializers.ValidationError({"url_link": "URL link is required for item_type 'link'."})
        return data


class ShowcaseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    items = ShowcaseItemSerializer(many=True, read_only=True) # Read-only here, manage items via separate endpoint
    cover_image_url = serializers.ImageField(source='cover_image', read_only=True, allow_null=True)

    class Meta:
        model = Showcase
        fields = [
            'id', 'user', 'user_id', 'title', 'slug', 'description',
            'cover_image', 'cover_image_url', 'is_public', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'items', 'created_at', 'updated_at', 'cover_image_url']
        extra_kwargs = {
            'cover_image': {'write_only': True, 'required': False}
        }