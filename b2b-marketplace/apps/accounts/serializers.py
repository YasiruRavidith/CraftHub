from rest_framework import serializers
from .models import CustomUser, Profile
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ('user',) # Exclude user to avoid circular dependency or redundant data

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True) # Nested serializer for profile
    # Use PrimaryKeyRelatedField if you want to update profile via user endpoint
    # profile_id = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), source='profile', write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type', 'profile', 'password')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}, # Password is not sent back, required only for creation
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        # profile_data = validated_data.pop('profile', None) # If handling profile update here

        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()

        # if profile_data:
        #     profile_serializer = ProfileSerializer(instance.profile, data=profile_data, partial=True)
        #     if profile_serializer.is_valid(raise_exception=True):
        #         profile_serializer.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")
    profile = ProfileSerializer(required=False) # Allow optional profile data during registration

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'user_type', 'profile')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'buyer')
        )
        # Profile is created by signal, but if you want to pass initial data:
        if profile_data:
            profile_serializer = ProfileSerializer(instance=user.profile, data=profile_data, partial=True)
            if profile_serializer.is_valid(): # Profile already exists due to signal
                profile_serializer.save()
            else:
                print("Profile serializer errors:", profile_serializer.errors) # For debugging
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating a user's own profile."""
    class Meta:
        model = Profile
        fields = [
            'company_name', 'bio', 'profile_picture', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country', 'website', 'seller_verified',
            'design_portfolio_url', 'manufacturing_capabilities'
        ]
        read_only_fields = ('seller_verified',) # Only admin should verify