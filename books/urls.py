from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book-api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/checkout/', views.CheckoutView.as_view(), name='checkout-api'),
    path('api/return/<int:transaction_id>/', views.ReturnView.as_view(), name='return-api'),
    path('api/waitlist/', views.JoinWaitlistView.as_view(), name='join-waitlist-api'),
    path('api/overdue/', views.OverdueTransactionsView.as_view(), name='overdue-transactions-api'),
    path('borrow/<int:book_id>/', views.borrow_book_page, name='borrow-book'),
]