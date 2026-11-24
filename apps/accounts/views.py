from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.accounts.serializers import UserRegisterSerializer, UserProfileSerializer
from apps.profiles.models import UserProfile


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            profile = user.profile
            return Response({
                "status": "success",
                "message": "User registered and logged in successfully.",
                "user": {
                    "id": str(profile.id),
                    "username": user.username,
                    "email": user.email,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Ensure profile exists
            profile, _ = UserProfile.objects.get_or_create(user=user)
            return Response({
                "status": "success",
                "message": "Logged in successfully.",
                "user": {
                    "id": str(profile.id),
                    "username": user.username,
                    "email": user.email,
                    "headline": profile.headline,
                }
            })
        return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"status": "success", "message": "Logged out successfully."})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
