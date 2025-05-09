from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import AbstractBaseModel # Assuming you'll create this in core/models.py


# It's good practice to have a generic base model for timestamps, etc.
# If core.models.AbstractBaseModel doesn't exist yet, you can define created_at/updated_at directly
# or define AbstractBaseModel in this file temporarily.
# For now, let's assume AbstractBaseModel will have created_at and updated_at.
# If not using core.AbstractBaseModel, add:
# created_at = models.DateTimeField(auto_now_add=True)
# updated_at = models.DateTimeField(auto_now=True)
# to each model.

class Category(AbstractBaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    # Add image for category if needed
    # image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(AbstractBaseModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Certification(AbstractBaseModel):
    name = models.CharField(max_length=200)
    issuing_body = models.CharField(max_length=200)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(upload_to='certifications/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.issuing_body})"

class BaseListing(AbstractBaseModel):
    """
    Abstract base model for common fields in Material and Design.
    """
    name = models.CharField(max_length=255) # For Material name or Design title
    slug = models.SlugField(max_length=270, unique=True, blank=True, editable=False)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_listings")
    tags = models.ManyToManyField(Tag, blank=True, related_name="%(class)s_listings")
    is_active = models.BooleanField(default=True) # Whether the listing is visible
    is_verified = models.BooleanField(default=False) # Admin verified (optional)
    main_image = models.ImageField(upload_to='listings/%(class)s_main_images/', blank=True, null=True)
    # Consider a separate model for multiple images if needed:
    # additional_images = models.JSONField(blank=True, null=True) # Store list of image paths or use a related model
    certifications = models.ManyToManyField(Certification, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            # Ensure slug is unique
            slug = base_slug
            counter = 1
            while type(self).objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Material(BaseListing):
    UNIT_CHOICES = (
        ('m', 'Meter'),
        ('kg', 'Kilogram'),
        ('sqm', 'Square Meter'),
        ('pcs', 'Pieces'),
        ('yard', 'Yard'),
        ('lb', 'Pound'),
    )
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='materials_listed', limit_choices_to={'user_type__in': ['seller', 'manufacturer']})
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='m')
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    stock_quantity = models.PositiveIntegerField(null=True, blank=True) # Null if made-to-order
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True) # Stock Keeping Unit

    # Material-specific attributes
    composition = models.CharField(max_length=255, blank=True, null=True) # e.g., "100% Cotton", "70% Polyester, 30% Viscose"
    weight_gsm = models.PositiveIntegerField(null=True, blank=True) # Grams per Square Meter
    width_cm = models.PositiveIntegerField(null=True, blank=True) # Width in centimeters
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated lead time in days for production/sourcing if not in stock.")
    additional_images = models.JSONField(blank=True, null=True, default=list) # For multiple images

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0, null=True, blank=True)


    def __str__(self):
        return f"{self.name} (by {self.seller.username})"


class Design(BaseListing):
    # Renaming 'name' field from BaseListing to 'title' for clarity in Design context
    title = models.CharField(max_length=255)
    designer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='designs_listed', limit_choices_to={'user_type__in': ['designer']})
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price for the design or license.")
    licensing_terms = models.TextField(blank=True, null=True, help_text="Details about licensing, e.g., exclusive, non-exclusive, usage rights.")
    # design_files = models.FileField(upload_to='designs/files/', blank=True, null=True, help_text="Main design file (e.g., AI, PSD, CAD). Consider security.")
    # Using thumbnail_image instead of main_image from BaseListing if semantically better
    thumbnail_image = models.ImageField(upload_to='designs/thumbnails/', blank=True, null=True)
    design_files_link = models.URLField(blank=True, null=True, help_text="Link to secure storage for design files (e.g., for after purchase)")

    # Override name from BaseListing to use title
    @property
    def name(self):
        return self.title

    @name.setter
    def name(self, value):
        self.title = value

    def save(self, *args, **kwargs):
        if not self.slug: # Ensure slug is based on title
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Check Design model for slug uniqueness
            while Design.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super(Design, self).save(*args, **kwargs) # Call Design's super, not BaseListing's directly here

    def __str__(self):
        return f"{self.title} (by {self.designer.username})"

class TechPack(AbstractBaseModel):
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='tech_packs')
    file = models.FileField(upload_to='designs/tech_packs/')
    version = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True) # Overriding from AbstractBaseModel if needed, or remove if it's already there.

    def __str__(self):
        return f"Tech Pack for {self.design.title} (v: {self.version or 'N/A'})"