from rest_framework import generics, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model
from .models import Profile
from .serializers import UserSerializer, RegisterSerializer, ProfileSerializer, UserProfileSerializer
from .permissions import IsOwnerOrReadOnlyProfile

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
        user_data = UserSerializer(user).data
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
        user_data = UserSerializer(user).data
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
    serializer_class = ProfileSerializer # General profile serializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnlyProfile]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'create'] and self.request.user.is_authenticated and getattr(self.get_object(), 'user', None) == self.request.user:
            return UserProfileSerializer # Specific serializer for owner updates
        return ProfileSerializer

    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            if self.request.user.is_authenticated:
                profile, created = Profile.objects.get_or_create(user=self.request.user)
                return profile
            else:
                raise permissions.NotAuthenticated("User is not authenticated.")
        return super().get_object()

    def perform_create(self, serializer):
        # This might not be the typical way to create a profile via API,
        # as it's usually created via signal.
        # But if direct creation is allowed, associate with current user.
        if self.request.user.is_authenticated:
            # Check if profile already exists to prevent duplicates
            if Profile.objects.filter(user=self.request.user).exists():
                 raise serializers.ValidationError("Profile already exists for this user.")
            serializer.save(user=self.request.user)
        else:
            raise permissions.NotAuthenticated("User must be authenticated to create a profile.")

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for current authenticated user's details.
    Access via /api/v1/accounts/users/me/
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)