from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book-api')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/checkout/', views.CheckoutAPIView.as_view(), name='checkout-api'),
    path('api/return/', views.ReturnAPIView.as_view(), name='return-api'),
    path('api/my-transactions/', views.MyTransactionsAPIView.as_view(), name='my-transactions-api'),
    path('api/overdue/', views.OverdueTransactionsAPIView.as_view(), name='overdue-api'),
    path('api/waitlist/', views.WaitlistAPIView.as_view(), name='waitlist-api'),
    path('api/waitlist/join/', views.JoinWaitlistAPIView.as_view(), name='join-waitlist-api'),
    path('api/waitlist/<int:waitlist_id>/cancel/', views.CancelWaitlistAPIView.as_view(), name='cancel-waitlist-api'),
    
    # Template endpoints (pour rendu HTML)
    path('borrow/<int:book_id>/', views.borrow_book_page, name='borrow-book'),
    path('return/<int:transaction_id>/', views.return_book_page, name='return-book'),
]