import os
import datetime # For date-based upload paths
import uuid     # For unique filenames
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import AbstractBaseModel # Corrected import path assuming core is top-level

# --- Upload Path Helper Functions ---
def get_listing_image_upload_path(instance, filename):
    """
    Generates a unique upload path for BaseListing main_images.
    Example: listings/material_main_images/2025/05/10/uuid_filename.ext
    """
    ext = filename.split('.')[-1]
    # Generate a unique filename using UUID to prevent collisions
    new_filename = f"{uuid.uuid4()}.{ext}"
    # Get the lowercase model name (e.g., 'material', 'design')
    model_class_name = instance.__class__.__name__.lower()
    date_path = datetime.datetime.now().strftime('%Y/%m/%d')
    return os.path.join('listings', f'{model_class_name}_main_images', date_path, new_filename)

def get_design_thumbnail_upload_path(instance, filename):
    """
    Generates a unique upload path for Design thumbnail_images.
    Example: designs/thumbnails/2025/05/10/uuid_filename.ext
    """
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    date_path = datetime.datetime.now().strftime('%Y/%m/%d')
    return os.path.join('designs', 'thumbnails', date_path, new_filename)

def get_tech_pack_upload_path(instance, filename):
    """
    Generates a unique upload path for TechPack files.
    Example: designs/tech_packs/design_slug_or_id/uuid_filename.ext
    """
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    # Using design's slug or ID for subfolder if desired for organization
    design_identifier = instance.design.slug if instance.design and instance.design.slug else str(instance.design.id)
    date_path = datetime.datetime.now().strftime('%Y/%m/%d') # Optional: add date path too
    return os.path.join('designs', 'tech_packs', design_identifier, date_path, new_filename)

def get_certification_file_upload_path(instance, filename):
    """
    Generates a unique upload path for Certification files.
    Example: certifications/uuid_filename.ext
    """
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    date_path = datetime.datetime.now().strftime('%Y/%m/%d')
    return os.path.join('certifications', date_path, new_filename)


# --- Models ---

class Category(AbstractBaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    # image = models.ImageField(upload_to='category_images/', blank=True, null=True) # Define upload_to if used

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness if just slugify(self.name) might not be unique enough
            original_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(AbstractBaseModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Tag.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Certification(AbstractBaseModel):
    name = models.CharField(max_length=200)
    issuing_body = models.CharField(max_length=200)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(upload_to=get_certification_file_upload_path, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.issuing_body})"

class BaseListing(AbstractBaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=270, unique=True, blank=True, editable=False)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_listings")
    tags = models.ManyToManyField(Tag, blank=True, related_name="%(class)s_listings")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    main_image = models.ImageField(upload_to=get_listing_image_upload_path, blank=True, null=True)
    certifications = models.ManyToManyField(Certification, blank=True)

    # Fields for average rating and review count
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def _generate_unique_slug(self, source_string_value):
        """Helper to generate a unique slug for the instance's class."""
        if not source_string_value: # Handle empty or None source
            base_slug = f"{self.__class__.__name__.lower()}-{uuid.uuid4().hex[:8]}"
        else:
            base_slug = slugify(source_string_value)

        # Ensure slug length constraints, reserving space for potential counter
        # Max length of slug field is 270. Let's reserve 10 for "-counter".
        max_base_len = 270 - 10 
        if len(base_slug) > max_base_len:
            base_slug = base_slug[:max_base_len]

        slug = base_slug
        counter = 1
        # Use self.__class__ to refer to the concrete model (Material or Design)
        while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            # If slug with counter exceeds max_length, this needs more sophisticated truncation logic
            # or rely on the SlugField's max_length to truncate if database supports it.
            # For simplicity, we assume this loop doesn't generate overly long slugs often.
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            # The source for the slug ('name' or 'title') will be handled by concrete class if overridden
            # For BaseListing, it defaults to self.name
            slug_source = getattr(self, 'name', None) # Default to 'name'
            if hasattr(self, 'title') and isinstance(self, Design): # Special case for Design using 'title'
                 slug_source = self.title
            self.slug = self._generate_unique_slug(slug_source)
        super().save(*args, **kwargs)

    def __str__(self):
        # Use self.name which might be a property in subclasses like Design
        return self.name if self.name else f"Unnamed {self.__class__.__name__}"


class Material(BaseListing):
    UNIT_CHOICES = (
        ('m', 'Meter'), ('kg', 'Kilogram'), ('sqm', 'Square Meter'),
        ('pcs', 'Pieces'), ('yard', 'Yard'), ('lb', 'Pound'),
    )
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='materials_listed', limit_choices_to={'user_type__in': ['seller', 'manufacturer']})
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='m')
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    stock_quantity = models.PositiveIntegerField(null=True, blank=True)
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True) # Consider unique=True based on needs

    composition = models.CharField(max_length=255, blank=True, null=True)
    weight_gsm = models.PositiveIntegerField(null=True, blank=True)
    width_cm = models.PositiveIntegerField(null=True, blank=True)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated lead time in days for production/sourcing if not in stock.")
    additional_images = models.JSONField(blank=True, null=True, default=list) # For multiple images URLs or paths

    # average_rating and review_count are inherited from BaseListing

    def __str__(self):
        return f"{self.name} (by {self.seller.username})"
    
    # No need to override save() for slug if BaseListing's save correctly uses self.name


class Design(BaseListing):
    title = models.CharField(max_length=255) # This effectively becomes the 'name' for Design
    designer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='designs_listed', limit_choices_to={'user_type__in': ['designer']})
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price for the design or license.")
    licensing_terms = models.TextField(blank=True, null=True, help_text="Details about licensing...")
    thumbnail_image = models.ImageField(upload_to=get_design_thumbnail_upload_path, blank=True, null=True)
    design_files_link = models.URLField(blank=True, null=True, help_text="Link to secure storage for design files...")

    # average_rating and review_count are inherited from BaseListing

    # Override 'name' property to always point to 'title' for this model
    @property
    def name(self):
        return self.title

    @name.setter
    def name(self, value):
        self.title = value

    # The BaseListing.save() method will use self.name for slug generation.
    # Since self.name is a property pointing to self.title, it should work correctly.
    # No need to override save() here if BaseListing's logic is sufficient.
    # However, if BaseListing.save() directly uses self.name without going through property getter for some reason
    # (which shouldn't be the case for direct attribute access in Python), then overriding save is safer.
    # Let's keep the BaseListing.save() generic and ensure it refers to self.name correctly.
    # The logic in BaseListing.save() now correctly checks for Design's title via getattr.

    def __str__(self):
        return f"{self.title} (by {self.designer.username})"


class TechPack(AbstractBaseModel):
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='tech_packs')
    file = models.FileField(upload_to=get_tech_pack_upload_path) # Use the callable
    version = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    # uploaded_at is inherited from AbstractBaseModel as created_at, or can be specific if needed
    # If you need a distinct 'uploaded_at' different from 'created_at':
    # uploaded_at_specific = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Tech Pack for {self.design.title} (v: {self.version or 'N/A'})"