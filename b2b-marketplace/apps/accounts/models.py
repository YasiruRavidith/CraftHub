from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'), # Can list materials
        ('designer', 'Designer'), # Can list designs
        ('manufacturer', 'Manufacturer'), # Can take orders, provide quotes
        ('admin', 'Administrator'), # Platform admin
    )
    email = models.EmailField(unique=True) # Make email the unique identifier
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='buyer')

    # USERNAME_FIELD = 'email' # If you want to login with email
    # REQUIRED_FIELDS = ['username'] # Adjust if email is USERNAME_FIELD

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    # Seller specific fields (can be moved to a SellerProfile model if it grows complex)
    seller_verified = models.BooleanField(default=False)
    # Designer specific fields
    design_portfolio_url = models.URLField(blank=True, null=True)
    # Manufacturer specific fields
    manufacturing_capabilities = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# If you need more distinct profile types, you could do:
# class SellerProfile(models.Model):
#     profile = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
#     # seller specific fields
#
# class DesignerProfile(models.Model):
#     profile = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
#     # designer specific fields