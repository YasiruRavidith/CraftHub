# apps/listings/models.py
from django.db import models
from django.conf import settings # To get CustomUser model
from apps.accounts.models import UserProfile # To link listings to sellers/designers through profiles
                                             # or directly link to settings.AUTH_USER_MODEL


class Material(models.Model):
    FABRIC_TYPE_CHOICES = [
        ('COTTON', 'Cotton'),
        ('SILK', 'Silk'),
        ('WOOL', 'Wool'),
        ('LINEN', 'Linen'),
        ('POLYESTER', 'Polyester'),
        ('RAYON', 'Rayon'),
        ('DENIM', 'Denim'),
        # ... Add more choices
        ('OTHER', 'Other'),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Best to link directly to the User model
        on_delete=models.CASCADE,
        related_name='materials_listed',
        # Optional: limit_choices_to={'profile__user_type': UserProfile.USER_TYPE_CHOICES[0][0]} # 'SELLER'
        # The limit_choices_to in ForeignKey is tricky with dynamic model attributes
        # It's often better to enforce this logic in forms/serializers/views
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    fabric_type = models.CharField(max_length=50, choices=FABRIC_TYPE_CHOICES, default='OTHER')
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2) # e.g., in meters or kg
    unit_of_measurement = models.CharField(max_length=20, default='meters') # meters, yards, kg, pieces
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    region_available = models.CharField(max_length=100, blank=True)
    # Certifications (Consider a separate ManyToMany model for certifications later for complexity)
    certifications = models.CharField(max_length=255, blank=True, help_text="e.g., GOTS, Oeko-Tex, comma-separated")
    image = models.ImageField(upload_to='materials_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True) # To allow sellers to temporarily delist
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.seller.username}"

    # Basic permission check idea - implement thoroughly in views/serializers
    def can_be_modified_by(self, user):
        return self.seller == user or user.is_staff


class Design(models.Model):
    designer = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Link directly to the User model
        on_delete=models.CASCADE,
        related_name='designs_created',
        # Optional: limit_choices_to={'profile__user_type': UserProfile.USER_TYPE_CHOICES[1][0]} # 'DESIGNER'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # Tags (Consider using django-taggit or a ManyToManyField to a Tag model for more advanced tagging)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated styles, themes (e.g., floral, abstract, modern)")
    # For 3D, Tech Packs consider FileFields. For this example, main design image and details.
    design_image = models.ImageField(upload_to='designs_images/', blank=True, null=True)
    # tech_pack_file = models.FileField(upload_to='tech_packs/', blank=True, null=True)
    customization_preferences = models.TextField(blank=True, help_text="e.g., Colors can be changed, open to size variations.")
    licensing_options = models.CharField(max_length=50, default='EXCLUSIVE', choices=[('EXCLUSIVE', 'Exclusive'), ('NON_EXCLUSIVE', 'Non-Exclusive'), ('ROYALTY', 'Royalty-based')])
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="One-time purchase price or license fee base.")
    is_active = models.BooleanField(default=True) # To allow designers to temporarily delist
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.designer.username}"

    def can_be_modified_by(self, user):
        return self.designer == user or user.is_staff

# Advanced Tip (For Later):
# class Certification(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True)
# Then Material model: certifications = models.ManyToManyField(Certification, blank=True)

# class Tag(models.Model):
#     name = models.CharField(max_length=50, unique=True)
# Then Design model: tags = models.ManyToManyField(Tag, blank=True)