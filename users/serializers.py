from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'date_of_membership', 'is_active_member']

    def create(self, validated_data):
        """
        Hash password on creation
        """
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update user safely, handle password hashing
        """
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_active_member = validated_data.get('is_active_member', instance.is_active_member)
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)
        instance.save()
        return instance