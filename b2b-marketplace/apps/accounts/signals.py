from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    try:
        instance.profile.save()
    except Profile.DoesNotExist: # Should not happen if signal works correctly
        Profile.objects.create(user=instance)
    except Exception as e: # Catch other potential errors during profile save
        print(f"Error saving profile for user {instance.username}: {e}")


# If you have specific profiles like SellerProfile, DesignerProfile etc.
# you might want to create them based on user_type
# @receiver(post_save, sender=User)
# def create_specific_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.user_type == 'seller':
#             SellerProfile.objects.create(profile=instance.profile) # Assuming Profile is already created
#         elif instance.user_type == 'designer':
#             DesignerProfile.objects.create(profile=instance.profile)
        # ... and so on