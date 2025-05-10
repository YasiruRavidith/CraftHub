from rest_framework import generics, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model
from django.http import Http404 # Import Http404 for get_object
from rest_framework import serializers # Import serializers for ValidationError

from .models import Profile
from .serializers import UserSerializer, RegisterSerializer, ProfileSerializer, UserProfileSerializer
from .permissions import IsOwnerOrReadOnlyProfile
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser # Correctly imported

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user, context={'request': request}).data # Pass request to context for UserSerializer if it builds URLs
        return Response({
            "user": user_data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)


class CustomAuthTokenLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user, context={'request': request}).data # Pass request to context
        return Response({
            'token': token.key,
            'user': user_data
        })

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users' profiles to be viewed or edited.
    Use 'me/' for the current user's profile.
    """
    queryset = Profile.objects.select_related('user').all()
    # serializer_class = ProfileSerializer # Default, will be overridden by get_serializer_class
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnlyProfile] # Changed to IsAuthenticated for base
    parser_classes = [MultiPartParser, FormParser, JSONParser] # <<< --- THIS IS THE CRITICAL ADDITION ---

    def get_serializer_class(self):
        # For 'retrieve' of 'me' or owned profile, or 'list' (if admin), use general ProfileSerializer
        # For 'update' or 'partial_update' of 'me' or owned profile, use UserProfileSerializer
        if self.action in ['update', 'partial_update']:
            # Ensure the object being updated belongs to the request.user or user is admin
            # get_object() will enforce IsOwnerOrReadOnlyProfile for object-level actions
            return UserProfileSerializer
        return ProfileSerializer # Default for list, retrieve, create

    def get_object(self):
        # Handle 'me' for the current user's profile
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if self.kwargs.get(lookup_url_kwarg) == 'me':
            if self.request.user.is_authenticated:
                profile, created = Profile.objects.get_or_create(user=self.request.user)
                # Manually check object permissions because IsOwnerOrReadOnlyProfile.has_permission might not be enough
                # if the action is 'retrieve' and we want to allow any authenticated user to see their own profile.
                # However, for update/partial_update, the default permission check after get_object will apply.
                return profile
            else:
                # This should ideally be caught by IsAuthenticated permission class first
                raise Http404("User not authenticated or profile not found for 'me'.")
        return super().get_object()

    def perform_create(self, serializer):
        # Creating a profile directly via API. Usually done by signal.
        if self.request.user.is_authenticated:
            if Profile.objects.filter(user=self.request.user).exists():
                 # Use DRF's ValidationError for consistency in API responses
                 raise serializers.ValidationError({"detail": "Profile already exists for this user."})
            serializer.save(user=self.request.user)
        else:
            # This should be caught by IsAuthenticated permission class
            raise permissions.NotAuthenticated("User must be authenticated to create a profile.")

    # For PATCH and PUT, DRF's ModelViewSet.update and .partial_update
    # will call get_object() (which applies IsOwnerOrReadOnlyProfile for 'me')
    # and then use the serializer from get_serializer_class() (which is UserProfileSerializer).
    # The UserProfileSerializer is designed for updates and doesn't include 'user' field as writable.

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for current authenticated user's details (CustomUser model).
    Access via /api/v1/accounts/users/me/
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    # get_queryset is not strictly needed if get_object is overridden this way
    # but good for clarity or if you have other list actions.
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)