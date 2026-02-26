from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from books.views import book_list_page, my_transactions_page
from django.shortcuts import render
from users.views import login_page, register_page





def home_page(request):
    return render(request, "home.html")


urlpatterns = [
    path('', home_page),
    path('admin/', admin.site.urls),
    path('api/', include('books.urls')),
    path('api/', include('users.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('books/', book_list_page),
    path('my-transactions/', my_transactions_page),
    path("login/", login_page),
    path("register/", register_page),
]






