from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .models import Review, ReviewReply
from apps.accounts.serializers import UserSerializer # For author details
from django.contrib.auth import get_user_model

User = get_user_model()

# Helper to get the actual reviewed object for display
def get_content_object_serializer(obj):
    # Dynamically choose serializer based on content_type (optional, for richer display)
    # This can get complex. For now, we'll just return a string representation.
    # from apps.listings.serializers import MaterialSerializer, DesignSerializer
    # if isinstance(obj, settings.AUTH_USER_MODEL):
    #     return UserSerializer(obj).data # Or a specific ProfileSerializer
    # elif isinstance(obj, Material):
    #     return MaterialSerializer(obj).data
    # elif isinstance(obj, Design):
    #     return DesignSerializer(obj).data
    return str(obj)


class ReviewReplySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='author', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    review_id = serializers.PrimaryKeyRelatedField(queryset=Review.objects.all(), source='review', write_only=True)

    class Meta:
        model = ReviewReply
        fields = ['id', 'review_id', 'author', 'author_id', 'comment', 'created_at', 'updated_at', 'is_edited']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_edited']

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        review = data.get('review') # This is Review instance due to source='review'

        # Check if the user replying is the owner of the reviewed item
        # This requires knowing who owns the 'content_object' of the review.
        if review and review.content_object:
            reviewed_item_owner = None
            # Determine owner of the reviewed item
            if hasattr(review.content_object, 'owner'): # e.g., Project
                reviewed_item_owner = review.content_object.owner
            elif hasattr(review.content_object, 'seller'): # e.g., Material
                reviewed_item_owner = review.content_object.seller
            elif hasattr(review.content_object, 'designer'): # e.g., Design
                reviewed_item_owner = review.content_object.designer
            elif isinstance(review.content_object, User): # If reviewing a User/Profile
                 # If a user can reply to reviews about themselves.
                 # Or if only admins can reply.
                 # This logic depends on your business rules.
                 # For now, let's assume the reviewed user can reply.
                reviewed_item_owner = review.content_object

            if reviewed_item_owner != user and not user.is_staff:
                raise serializers.ValidationError("You are not authorized to reply to this review.")
        else:
            # This should ideally not happen if review is valid
            raise serializers.ValidationError("Cannot determine context for review reply.")

        if 'author' not in data and user: # If CurrentUserDefault didn't set it
             data['author'] = user
        return data


class ReviewSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='author', write_only=True,
        default=serializers.CurrentUserDefault()
    )
    replies = ReviewReplySerializer(many=True, read_only=True)

    # For GFK fields during creation/update
    content_type_model = serializers.CharField(write_only=True, help_text="Model name (e.g., 'customuser', 'material', 'design', 'profile')")
    object_id_str = serializers.CharField(write_only=True, source='object_id_str_input', help_text="ID of the object being reviewed.") # Use a different source name to avoid conflict

    # For displaying reviewed object info
    reviewed_item_type = serializers.CharField(source='content_type.model', read_only=True)
    reviewed_item_id = serializers.CharField(source='object_id_str', read_only=True) # Displaying the stored string ID
    # reviewed_item_details = serializers.SerializerMethodField(read_only=True) # For richer display

    class Meta:
        model = Review
        fields = [
            'id', 'author', 'author_id', 'rating', 'title', 'comment',
            'content_type_model', 'object_id_str', # Write-only for GFK
            'reviewed_item_type', 'reviewed_item_id', #'reviewed_item_details', # Read-only for GFK display
            'is_approved', 'is_edited',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_approved', 'is_edited', 'created_at', 'updated_at',
            'replies', 'reviewed_item_type', 'reviewed_item_id', #'reviewed_item_details'
        ]

    # def get_reviewed_item_details(self, obj):
    #     if obj.content_object:
    #         return get_content_object_serializer(obj.content_object)
    #     return None

    def validate_content_type_model(self, value):
        value = value.lower()
        # Map user-friendly model names to actual ContentType model names if needed
        # e.g., if user sends 'user', map to 'customuser' (ContentType.model is usually lowercase model name)
        try:
            # Assuming 'value' is the model name as stored in ContentType (e.g., 'customuser', 'material')
            # You might need a mapping if user input is different:
            # model_map = {"user": "customuser", "profile": "profile", "material": "material", "design": "design"}
            # actual_model_name = model_map.get(value, value)
            ContentType.objects.get(model=value) # Check if content type exists
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid model name for review: {value}. Supported types are e.g. 'customuser', 'material', 'design'.")
        return value

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None

        content_type_model_name = data.get('content_type_model')
        object_id_input = data.get('object_id_str_input') # From source field

        if content_type_model_name and object_id_input:
            try:
                content_type_instance = ContentType.objects.get(model=content_type_model_name)
                target_model_class = content_type_instance.model_class()
                if target_model_class is None:
                    raise serializers.ValidationError(f"Could not resolve model class for '{content_type_model_name}'.")

                # Try to fetch the object to ensure it exists
                # Handle potential ValueError if object_id_input cannot be cast to target model's PK type
                try:
                    target_object = target_model_class.objects.get(pk=object_id_input)
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(f"{target_model_class.__name__} with ID '{object_id_input}' not found.")
                except ValueError: # If PK type mismatch, e.g., trying to use non-UUID string for UUIDField
                    raise serializers.ValidationError(f"Invalid ID format '{object_id_input}' for {target_model_class.__name__}.")


                # Prevent self-review if the target is a user/profile
                if (isinstance(target_object, User) and target_object == user) or \
                   (hasattr(target_object, 'user') and target_object.user == user): # e.g. Profile model
                    raise serializers.ValidationError("You cannot review yourself.")

                data['content_type'] = content_type_instance
                data['object_id_str'] = str(object_id_input) # Ensure it's stored as string

                # Check for existing review by the same author for the same object
                if not self.instance: # Only on create
                    if Review.objects.filter(
                        author=user,
                        content_type=content_type_instance,
                        object_id_str=str(object_id_input)
                    ).exists():
                        raise serializers.ValidationError("You have already reviewed this item.")

            except ContentType.DoesNotExist:
                # This should be caught by validate_content_type_model, but as a fallback
                raise serializers.ValidationError(f"Invalid content type: {content_type_model_name}")
        elif not self.instance: # On create, these fields are required
            raise serializers.ValidationError("content_type_model and object_id_str are required to create a review.")

        if 'author' not in data and user:
            data['author'] = user

        # Remove temporary fields not part of the model
        data.pop('content_type_model', None)
        data.pop('object_id_str_input', None)

        return data

    def update(self, instance, validated_data):
        # User can only update their own rating, title, comment. is_approved is admin-only.
        # GFK fields (content_type, object_id_str) should not be updatable.
        allowed_update_fields = {'rating', 'title', 'comment'}
        request = self.context.get('request')

        if request and request.user != instance.author and not request.user.is_staff:
            raise serializers.PermissionDenied("You can only edit your own reviews.")

        for field in list(validated_data.keys()):
            if field not in allowed_update_fields and not (request.user.is_staff and field == 'is_approved'):
                validated_data.pop(field) # Remove fields not allowed to be updated by user

        return super().update(instance, validated_data)