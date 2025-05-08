from django.shortcuts import render

# apps/accounts/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import CustomUser, UserProfile
from .serializers import CustomUserSerializer, UserProfileSerializer # UserProfileSerializer (if separate views)
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = CustomUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Get profile from user (it's created by the signal)
        # You can allow profile data to be sent with registration and update here
        profile_data = request.data.get('profile', None)
        if profile_data and hasattr(user, 'profile'):
            profile_serializer = UserProfileSerializer(user.profile, data=profile_data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                # Optional: clean up user if profile update fails and profile is crucial for this step
                # user.delete()
                # return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                pass # Or just log errors if profile is optional/later update

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": CustomUserSerializer(user, context=self.get_serializer_context()).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Return the currently authenticated user
        return self.request.user