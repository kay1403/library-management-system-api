from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer

User = get_user_model()



class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserViewSet(viewsets.ModelViewSet):
    """
    User CRUD API
    - Admin can list, update, delete users
    - Users can retrieve/update their own data
    """
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            # Only admin can list or delete
            return [IsAdminUser()]
        # Authenticated users can retrieve/update themselves
        return [IsAuthenticated()]