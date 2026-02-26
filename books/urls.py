from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, CheckoutView, ReturnView, MyTransactionsView, JoinWaitlistView, OverdueTransactionsView
from . import views

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='books')

urlpatterns = router.urls + [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('return/<int:transaction_id>/', ReturnView.as_view(), name='return'),
    path('my-transactions/', MyTransactionsView.as_view(), name='my-transactions'),
    path('waitlist/', JoinWaitlistView.as_view(), name='join-waitlist'),
    path('overdue/', OverdueTransactionsView.as_view(), name='overdue-transactions'),
    path('browse/', views.book_list_view, name='book-list'),
    path('book/<int:pk>/', views.book_detail_view, name='book-detail'),
    path('my-transactions/', views.my_transactions_view, name='my-transactions'),

]