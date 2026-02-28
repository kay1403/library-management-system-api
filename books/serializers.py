from rest_framework import serializers
from .models import Book, Transaction, Waitlist
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer pour les livres
    """
    available_copies = serializers.IntegerField(source='copies_available', read_only=True)
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'published_date', 'copies_available', 'available_copies']

    def validate_copies_available(self, value):
        if value < 0:
            raise serializers.ValidationError("Le nombre de copies ne peut pas être négatif.")
        return value

    def validate_published_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("La date de publication ne peut pas être dans le futur.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les transactions - Version enrichie pour le front
    """
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    book_isbn = serializers.CharField(source='book.isbn', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    status = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'book', 'book_title', 'book_author', 'book_isbn',
            'user', 'username', 'checkout_date', 'due_date', 'return_date',
            'status', 'days_until_due', 'is_overdue'
        ]
        read_only_fields = ['checkout_date', 'due_date']

    def get_status(self, obj):
        """Retourne le statut lisible de la transaction"""
        if obj.return_date:
            return "returned"
        if obj.due_date and obj.due_date < timezone.now():
            return "overdue"
        return "active"

    def get_days_until_due(self, obj):
        """Calcule le nombre de jours restants avant la date de retour"""
        if obj.return_date or not obj.due_date:
            return None
        delta = obj.due_date - timezone.now()
        return delta.days

    def get_is_overdue(self, obj):
        """Indique si la transaction est en retard"""
        return bool(obj.due_date and obj.due_date < timezone.now() and not obj.return_date)


class TransactionCreateSerializer(serializers.Serializer):
    """
    Serializer pour la création d'un emprunt
    """
    book_id = serializers.IntegerField(required=True)

    def validate_book_id(self, value):
        try:
            book = Book.objects.get(id=value)
            if book.copies_available <= 0:
                raise serializers.ValidationError("Ce livre n'est pas disponible.")
            return value
        except Book.DoesNotExist:
            raise serializers.ValidationError("Livre non trouvé.")


class TransactionReturnSerializer(serializers.Serializer):
    """
    Serializer pour le retour d'un livre
    """
    transaction_id = serializers.IntegerField(required=True)


class WaitlistSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste d'attente
    """
    book_title = serializers.CharField(source='book.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    position = serializers.SerializerMethodField()

    class Meta:
        model = Waitlist
        fields = ['id', 'book', 'book_title', 'user', 'username', 'created_at', 'position']

    def get_position(self, obj):
        """Calcule la position dans la file d'attente"""
        waitlist = Waitlist.objects.filter(book=obj.book).order_by('created_at')
        for idx, item in enumerate(waitlist):
            if item.id == obj.id:
                return idx + 1
        return None


class WaitlistCreateSerializer(serializers.Serializer):
    """
    Serializer pour rejoindre la liste d'attente
    """
    book_id = serializers.IntegerField(required=True)

    def validate_book_id(self, value):
        try:
            Book.objects.get(id=value)
            return value
        except Book.DoesNotExist:
            raise serializers.ValidationError("Livre non trouvé.")