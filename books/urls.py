from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, CheckoutView, ReturnView, MyLoansView

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='books')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('return/', ReturnView.as_view(), name='return'),
    path('my-loans/', MyLoansView.as_view(), name='my-loans'),
]