import uuid
from django.db import models

class AbstractBaseModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_at` and `updated_at` fields.
    And an optional UUID primary key.
    """
    # If you want UUIDs as primary keys for all models inheriting this:
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ['-created_at'] # Default ordering for models inheriting this

# Example of another utility model or mixin
class SlugMixin(models.Model):
    """
    A mixin for models that need a slug field auto-generated from a name/title.
    Requires the inheriting model to have a 'get_slug_source_string()' method.
    """
    slug = models.SlugField(max_length=255, unique=True, blank=True, editable=False)

    class Meta:
        abstract = True

    def get_slug_source_string(self):
        """
        This method must be implemented by the inheriting model.
        It should return the string that will be used to generate the slug.
        e.g., return self.title or self.name
        """
        raise NotImplementedError("Models inheriting SlugMixin must implement get_slug_source_string()")

    def _generate_unique_slug(self):
        from django.utils.text import slugify
        base_slug = slugify(self.get_slug_source_string())
        slug = base_slug
        counter = 1
        # Suffix with counter until slug is unique
        while type(self).objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug: # Generate slug only if it's not already set or on creation
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

# You can add other base models or mixins here, for example:
# - SoftDeleteMixin
# - SeoTagsMixin
# - AddressModel (if addresses are reused across many models)