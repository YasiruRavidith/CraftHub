from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.core.models import AbstractBaseModel # For created_at, updated_at
# from apps.listings.models import Material, Design # To link directly if not using GFK fully

# If AbstractBaseModel is not defined:
# class AbstractBaseModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         abstract = True

class Review(AbstractBaseModel):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)] # 1 to 5 stars

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True, help_text="Admin can unapprove problematic reviews")
    is_edited = models.BooleanField(default=False)

    # Generic Foreign Key to allow reviews on different models
    # (e.g., Seller (CustomUser), Manufacturer (CustomUser), Design, Material)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField() # Assuming target objects use UUIDs. If mixed, use CharField or PositiveIntegerField.
                                   # For CustomUser, object_id would be CustomUser.id (which is int by default)
                                   # For Material/Design, object_id would be their UUIDs.
                                   # To handle this mix, object_id might need to be CharField if CustomUser.id is not UUID.
                                   # Let's assume CustomUser.id is an integer and others are UUID.
                                   # A simpler approach is separate FKs or ensuring all target IDs are compatible.
                                   # For now, let's assume UUID for all reviewable objects for consistency,
                                   # meaning CustomUser.id would need to be changed to UUIDField if not already.
                                   # OR, have separate review models (ReviewUser, ReviewMaterial, etc.)
                                   # OR, adjust object_id field type. Let's use CharField for flexibility for now.
    # object_id = models.CharField(max_length=36) # More flexible for mixed ID types
    # For simplicity if all reviewed items (User, Material, Design) have UUID PKs:
    # object_id = models.UUIDField()
    # If CustomUser has an int PK and Material/Design have UUID PKs, this is tricky for GFK.
    # Let's stick to UUID for `object_id` and assume CustomUser will also have a UUID pk,
    # or we handle the type conversion in serializers/views.
    # A common pattern is that the User model (CustomUser) has an INT primary key by default.
    # If so, `object_id` here cannot be `models.UUIDField()` if it's to store user IDs.
    # Let's use CharField for `object_id` to accommodate different PK types (int for User, UUID for others).
    object_id_str = models.CharField(max_length=36, db_index=True) # String representation of the target object's ID
    content_object = GenericForeignKey('content_type', 'object_id_str')


    # Optional: Direct foreign keys if you primarily review specific types and GFK is for extension
    # reviewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews_received')
    # reviewed_material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    # reviewed_design = models.ForeignKey(Design, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')

    class Meta:
        ordering = ['-created_at']
        # Ensure a user can review a specific item only once
        unique_together = ('author', 'content_type', 'object_id_str')
        indexes = [
            models.Index(fields=["content_type", "object_id_str"]),
        ]

    def __str__(self):
        return f"Review by {self.author.username} for {self.content_object} ({self.rating} stars)"

    def save(self, *args, **kwargs):
        if self.pk: # if object is being updated
            self.is_edited = True
        super().save(*args, **kwargs)

# We'll also need a way to store average ratings. This could be on the reviewed models themselves
# or in a separate model. For now, let's assume we'll add fields to CustomUser (Profile), Material, Design.
# Example fields to add to other models (e.g., Profile or Material/Design):
# average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
# review_count = models.PositiveIntegerField(default=0)


class ReviewReply(AbstractBaseModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey( # Usually the owner of the reviewed item
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_replies'
    )
    comment = models.TextField()
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Review Replies"

    def __str__(self):
        return f"Reply by {self.author.username} to review {self.review.id}"

    def save(self, *args, **kwargs):
        if self.pk:
            self.is_edited = True
        super().save(*args, **kwargs)