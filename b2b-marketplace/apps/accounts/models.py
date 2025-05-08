# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    # You can add common fields here if needed for all users
    # For example, a default phone number field if all users have one
    email = models.EmailField(_('email address'), unique=True) # Make email unique for login

    # Remove username field requirements if you login with email
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = [] # 'username' will not be required then

    def __str__(self):
        return self.email # Or self.username if you keep it


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('SELLER', 'Material Seller'),
        ('DESIGNER', 'Cloth Designer'),
        ('MANUFACTURER', 'Garment Manufacturer'),
        ('BUYER', 'Cloth Shop/Buyer'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    # Add fields specific to different user profiles later, or use Proxy models / Multi-table inheritance
    # For now, this distinguishes roles. Example:
    company_name = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.get_user_type_display()}"

# Consider adding signals to automatically create a UserProfile when a CustomUser is created
# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # For existing users, instance.profile already exists and can be accessed.
    # If you need to update, you'd access instance.profile.save() after changes.

# And update apps/accounts/apps.py to load signals
# class AccountsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'apps.accounts'
#
#     def ready(self):
#         import apps.accounts.signals # novermin