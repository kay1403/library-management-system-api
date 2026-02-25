from rest_framework import serializers
from .models import Book, Transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'published_date', 'copies_available']

    def validate(self, data):
        if data['copies_available'] < 0:
            raise serializers.ValidationError("Copies cannot be negative.")
        if data['published_date'] > timezone.now().date():
            raise serializers.ValidationError("Published date cannot be in the future.")
        return data


class TransactionSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'book', 'checkout_date', 'return_date', 'status']

    def get_status(self, obj):
        return "returned" if obj.return_date else "active"


class CheckoutSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()


class ReturnSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()


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