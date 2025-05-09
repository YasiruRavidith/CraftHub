from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from django.contrib.contenttypes.models import ContentType

from .models import Review

# List of models that can be reviewed and have 'average_rating' and 'review_count' fields
# You'll need to ensure these fields exist on the respective models.
# Example:
# from apps.accounts.models import Profile # or CustomUser if rating is directly on User
# from apps.listings.models import Material, Design
# REVIEWABLE_MODELS_WITH_RATING_FIELDS = [Profile, Material, Design]

# To make it more dynamic without explicit imports here, we can check attributes.

def update_average_rating(instance_content_type, instance_object_id):
    """
    Calculates and updates the average rating and review count for a given object.
    """
    if not (instance_content_type and instance_object_id):
        return

    try:
        # Get the actual model class for the reviewed object
        reviewed_model_class = instance_content_type.model_class()
        if reviewed_model_class is None:
            print(f"Could not find model class for ContentType: {instance_content_type}")
            return

        # Fetch the specific reviewed object
        reviewed_object = reviewed_model_class.objects.filter(pk=instance_object_id).first()
        if not reviewed_object:
            print(f"Reviewed object not found: {reviewed_model_class.__name__} with pk {instance_object_id}")
            return

        # Check if the model has the necessary fields
        has_avg_rating_field = hasattr(reviewed_model_class, 'average_rating')
        has_review_count_field = hasattr(reviewed_model_class, 'review_count')

        if not (has_avg_rating_field and has_review_count_field):
            # print(f"Model {reviewed_model_class.__name__} does not have 'average_rating' and/or 'review_count' fields.")
            return # Silently return if fields are not present, or log warning

        # Calculate new average rating and count
        # Only consider approved reviews for the calculation
        agg_data = Review.objects.filter(
            content_type=instance_content_type,
            object_id_str=str(instance_object_id), # Ensure ID is string for GFK
            is_approved=True
        ).aggregate(
            average_rating_calc=Avg('rating'),
            review_count_calc=Count('id')
        )

        new_average_rating = agg_data['average_rating_calc'] if agg_data['average_rating_calc'] is not None else 0.00
        new_review_count = agg_data['review_count_calc'] if agg_data['review_count_calc'] is not None else 0

        # Update the reviewed object
        update_fields = []
        if hasattr(reviewed_object, 'average_rating'):
            reviewed_object.average_rating = round(new_average_rating, 2)
            update_fields.append('average_rating')
        if hasattr(reviewed_object, 'review_count'):
            reviewed_object.review_count = new_review_count
            update_fields.append('review_count')

        if update_fields:
            # Use .update() for efficiency if possible, or .save() if signals on target model need to fire.
            # Using .save() is safer if the target models have their own save logic/signals.
            # Be careful with save() to avoid recursion if the target model's save also triggers signals.
            # reviewed_model_class.objects.filter(pk=instance_object_id).update(**{
            #    'average_rating': round(new_average_rating, 2),
            #    'review_count': new_review_count
            # })
            reviewed_object.save(update_fields=update_fields)
            # print(f"Updated rating for {reviewed_model_class.__name__} {instance_object_id}: Avg {new_average_rating}, Count {new_review_count}")

    except ContentType.DoesNotExist:
        print(f"ContentType not found for review.")
    except Exception as e:
        # Log the error appropriately in a real application
        print(f"Error updating average rating for {instance_content_type} {instance_object_id}: {e}")


@receiver(post_save, sender=Review)
def review_saved_handler(sender, instance, created, **kwargs):
    """
    Handles actions after a Review is saved (created or updated).
    Updates the average rating of the reviewed item.
    """
    # If a review's approval status changes, or a new approved review is added, or rating changes
    if instance.is_approved or (not created and 'is_approved' in (kwargs.get('update_fields') or [])):
        update_average_rating(instance.content_type, instance.object_id_str)
    elif not created and 'is_approved' in (kwargs.get('update_fields') or []) and not instance.is_approved:
        # If review is unapproved, recalculate
        update_average_rating(instance.content_type, instance.object_id_str)


@receiver(post_delete, sender=Review)
def review_deleted_handler(sender, instance, **kwargs):
    """
    Handles actions after a Review is deleted.
    Updates the average rating of the reviewed item.
    """
    # Only update if the deleted review was approved, as unapproved ones didn't count.
    if instance.is_approved:
        update_average_rating(instance.content_type, instance.object_id_str)