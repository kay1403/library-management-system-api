from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, CheckoutView, ReturnView, MyLoansView

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='books')

urlpatterns = router.urls + [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('return/<int:loan_id>/', ReturnView.as_view(), name='return'),
    path('my-loans/', MyLoansView.as_view(), name='my-loans'),
]