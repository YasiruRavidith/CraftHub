import random
import string
from django.utils.text import slugify

def generate_random_string(length=10, chars=string.ascii_lowercase + string.digits):
    """Generates a random string of specified length."""
    return ''.join(random.choice(chars) for _ in range(length))

def generate_unique_slug(instance, source_field_name, slug_field_name='slug', max_length=255):
    """
    Generates a unique slug for a model instance.
    :param instance: The model instance.
    :param source_field_name: The name of the field to use as the source for the slug (e.g., 'title', 'name').
    :param slug_field_name: The name of the slug field on the model.
    :param max_length: Maximum length of the slug.
    :return: A unique slug string.
    """
    if hasattr(instance, slug_field_name) and getattr(instance, slug_field_name):
        return getattr(instance, slug_field_name) # Return existing slug if it's already set

    source_string = getattr(instance, source_field_name)
    if not source_string:
        # Fallback if source string is empty, generate a random one or raise error
        base_slug = slugify(generate_random_string(12))
    else:
        base_slug = slugify(source_string)

    # Truncate base_slug if it's too long before adding counter suffix
    # Max length of suffix is approx log10(num_existing_items) + 1 (for hyphen)
    # Let's reserve ~10 chars for suffix and counter for safety, can be adjusted
    suffix_space = 10
    truncated_slug_length = max_length - suffix_space
    if len(base_slug) > truncated_slug_length:
        base_slug = base_slug[:truncated_slug_length]

    slug = base_slug
    counter = 1
    model_class = instance.__class__

    while model_class.objects.filter(**{slug_field_name: slug}).exclude(pk=instance.pk).exists():
        # Ensure the new slug with counter doesn't exceed max_length
        potential_slug = f"{base_slug}-{counter}"
        if len(potential_slug) > max_length:
            # If too long even with counter, truncate base_slug further and restart counter
            # This part can get complex to perfectly guarantee uniqueness within length.
            # A simpler approach is to ensure source_field_name + counter is usually within limits.
            # Or use a shorter random suffix if truncation is needed.
            # For now, we'll assume base_slug is reasonably sized or rely on DB constraints for length.
            # This is a known difficult problem if max_length is very restrictive.
            # A common strategy is to truncate and add a short hash.
            base_slug_trimmed = base_slug[:max_length - len(str(counter)) - 1 - 2] # -2 for safety margin
            slug = f"{base_slug_trimmed}-{counter}"
            if not base_slug_trimmed: # Edge case: max_length is too small
                 slug = generate_random_string(max_length)[:max_length] # Fallback to random if trimming is too aggressive
                 # And then check uniqueness again (this could loop if max_length is tiny and many items exist)
        else:
            slug = potential_slug
        counter += 1
    return slug


# Example utility for API responses (you might use DRF's built-in responses more often)
class ApiResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        response = {"status": "success", "message": message}
        if data is not None:
            response["data"] = data
        # In DRF, you'd just return Response(response, status=status_code) from a view
        return response # This structure is for conceptual understanding

    @staticmethod
    def error(message="An error occurred", errors=None, status_code=400):
        response = {"status": "error", "message": message}
        if errors is not None:
            response["errors"] = errors
        return response


# Add other utilities:
# - Email sending helpers (though Django has built-in mail functions)
# - Date/time manipulation utilities
# - File handling utilities (e.g., custom storage backends, file validators)
# - Third-party API integration helpers (if generic enough)