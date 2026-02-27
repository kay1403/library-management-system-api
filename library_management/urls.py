from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from books.views import book_list_page, my_transactions_page
from users.views import login_page, register_page
from django.contrib.auth import views as auth_views
from books.views import (
     book_detail_page,
     overdue_books_page)
from users.views import login_page, register_page


def home_page(request):
    return render(request, "home.html")


urlpatterns = [
    path('', home_page, name='home_page'),
    path('books/', book_list_page, name='books-list'),
    path('my-transactions/', my_transactions_page, name='my-transactions'),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),


    path('api/', include('books.urls')),
    path('api/users/', include('users.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),


    path('books/<int:book_id>/', book_detail_page, name='book-detail'),
    path('overdue/', overdue_books_page, name='overdue-books'),
]

