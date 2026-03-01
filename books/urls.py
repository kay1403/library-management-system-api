from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book-api')

urlpatterns = [
    # API endpoints (maintenant ils seront sous /api/)
    path('', include(router.urls)),  # ← /api/books/
    path('checkout/', views.CheckoutAPIView.as_view(), name='checkout-api'),  
    path('return/', views.ReturnAPIView.as_view(), name='return-api'),
    path('my-transactions/', views.MyTransactionsAPIView.as_view(), name='my-transactions-api'),
    path('overdue/', views.OverdueTransactionsAPIView.as_view(), name='overdue-api'),
    path('waitlist/', views.WaitlistAPIView.as_view(), name='waitlist-api'),
    path('waitlist/join/', views.JoinWaitlistAPIView.as_view(), name='join-waitlist-api'),
    path('waitlist/<int:waitlist_id>/cancel/', views.CancelWaitlistAPIView.as_view(), name='cancel-waitlist-api'),
    
    # Template endpoints (ceux-ci restent à la racine car ce sont des pages)
    path('borrow/<int:book_id>/', views.borrow_book_page, name='borrow-book'),
    path('return/<int:transaction_id>/', views.return_book_page, name='return-book'),
    # Note: 'waitlist/' est déjà défini dans les URLs principales
]