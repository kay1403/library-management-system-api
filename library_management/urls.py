from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from books.views import book_list_page, my_transactions_page, book_detail_page, overdue_books_page, waitlist_page
from users.views import login_page, register_page
from django.contrib.auth import views as auth_views

def home_page(request):
    return render(request, "home.html")

urlpatterns = [
    # Pages principales
    path('', home_page, name='home_page'),
    path('books/', book_list_page, name='books-list'),
    path('books/<int:book_id>/', book_detail_page, name='book-detail'),
    path('my-transactions/', my_transactions_page, name='my-transactions'),
    path('overdue/', overdue_books_page, name='overdue-books'),
    path('waitlist/', waitlist_page, name='waitlist'),
    
    # Authentification
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API - Note: on inclut books.urls qui contient toutes les routes API
    path('', include('books.urls')),
    path('api/users/', include('users.urls')),
    
    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]