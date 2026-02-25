from rest_framework import serializers
from .models import Book, Loan
from django.contrib.auth import get_user_model

User = get_user_model()

# Book Serializer
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'published_date', 'copies_available']

# Loan Serializer
class LoanSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['id', 'book', 'checkout_date', 'return_date', 'status']

    def get_status(self, obj):
        return "returned" if obj.return_date else "active"

class CheckoutSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()

class ReturnSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
# User Serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'date_of_membership', 'is_active_member']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user