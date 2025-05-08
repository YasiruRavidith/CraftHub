# apps/accounts/serializers.py
from rest_framework import serializers
from .models import CustomUser, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('user_type', 'company_name', 'contact_number', 'address') # Adjust as needed
        # Consider making 'user_type' write_once or part of initial setup

class CustomUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False) # Make profile optional during user creation (can be updated later)
    # The UserProfileSerializer needs `required=False` because we are handling its creation
    # (or lack thereof) in the .create() method or via signals.
    # If the signal automatically creates it, then this profile field here would be for READ operations only.

    class Meta:
        model = CustomUser
        # For READ, fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
        # For WRITE (registration), typically 'username', 'email', 'password'
        # We should use separate serializers for read and write if complexity grows.
        # For initial setup:
        fields = ('id','username', 'email', 'password', 'profile')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'email': {'required': True},
             'username': {'required': True} # Or make false if you use email only login.
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None) # Use pop correctly
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()

        # Handle profile creation or update. Our signal handles creation automatically
        # so this part might be for updating if profile_data is provided.
        if profile_data:
             # If signal creates a blank profile, retrieve and update it
            UserProfile.objects.filter(user=user).update(**profile_data)
            # Or if signal doesn't auto-create and 'required=True' on profile serializer:
            # UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        instance = super().update(instance, validated_data)

        # Handle password update carefully
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)
            instance.save()

        if profile_data:
            profile_instance = instance.profile # Assumes profile exists due to signal or previous creation
            for attr, value in profile_data.items():
                setattr(profile_instance, attr, value)
            profile_instance.save()
        return instance