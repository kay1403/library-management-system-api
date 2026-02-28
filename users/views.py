from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import generics
from rest_framework.permissions import AllowAny

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth import get_user_model

from .serializers import UserSerializer

User = get_user_model()

# Formulaire d'inscription personnalisé
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

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
            return [IsAdminUser()]
        return [IsAuthenticated()]

def login_page(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("/")
    return render(request, "users/login.html", {"form": form})

def register_page(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
        else:
            # Ajoutez ceci pour voir les erreurs dans la console
            print("Erreurs du formulaire:", form.errors)
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})