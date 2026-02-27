from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import UserViewSet, RegisterView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('token/', obtain_auth_token, name='api-token-auth'),
    path('api-register/', RegisterView.as_view(), name='api-register'),
    path('', include(router.urls)),
]