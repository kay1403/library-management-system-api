from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction as db_transaction
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Book, Transaction, Waitlist
from .serializers import (
    BookSerializer, TransactionSerializer, TransactionCreateSerializer,
    TransactionReturnSerializer, WaitlistSerializer, WaitlistCreateSerializer
)

User = get_user_model()


# ====================== API VIEWS (pour frontend dynamique) ======================

class BookViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les livres
    - GET : accessible à tous (authentifié ou non)
    - POST/PUT/DELETE : réservé aux admins
    """
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'isbn']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'published_date', 'copies_available']
    ordering = ['title']

    def get_permissions(self):
        """
        Permissions différenciées selon l'action
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]  # Tout le monde peut voir les livres

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtre par disponibilité
        available = self.request.query_params.get('available')
        if available and available.lower() == 'true':
            queryset = queryset.filter(copies_available__gt=0)
        return queryset


class CheckoutAPIView(APIView):
    """
    API pour emprunter un livre
    POST /api/checkout/ {book_id: 1}
    """
    permission_classes = [IsAuthenticated]
    MAX_ACTIVE_TRANSACTIONS = 5

    def post(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book_id = serializer.validated_data['book_id']
        user = request.user

        # Vérifier si l'utilisateur est un membre actif
        if hasattr(user, 'is_active_member') and not user.is_active_member:
            return Response(
                {'error': 'Votre compte est inactif. Contactez l\'administrateur.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Vérifier la limite d'emprunts
        active_count = Transaction.objects.filter(
            user=user,
            return_date__isnull=True
        ).count()

        if active_count >= self.MAX_ACTIVE_TRANSACTIONS:
            return Response(
                {'error': f'Limite d\'emprunts atteinte ({self.MAX_ACTIVE_TRANSACTIONS} maximum).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with db_transaction.atomic():
                book = Book.objects.select_for_update().get(id=book_id)

                # Vérifier la disponibilité
                if book.copies_available <= 0:
                    return Response(
                        {'error': 'Ce livre n\'est pas disponible actuellement.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Vérifier si déjà emprunté
                if Transaction.objects.filter(
                    user=user,
                    book=book,
                    return_date__isnull=True
                ).exists():
                    return Response(
                        {'error': 'Vous avez déjà emprunté ce livre.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Créer la transaction
                transaction = Transaction.objects.create(user=user, book=book)
                book.copies_available -= 1
                book.save()

                # Retourner la transaction créée
                response_serializer = TransactionSerializer(transaction)
                return Response(
                    {
                        'success': 'Livre emprunté avec succès!',
                        'transaction': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

        except Book.DoesNotExist:
            return Response(
                {'error': 'Livre non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReturnAPIView(APIView):
    """
    API pour retourner un livre
    POST /api/return/ {transaction_id: 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionReturnSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        transaction_id = serializer.validated_data['transaction_id']

        try:
            with db_transaction.atomic():
                # Récupérer la transaction active
                transaction = Transaction.objects.select_for_update().get(
                    id=transaction_id,
                    user=request.user,
                    return_date__isnull=True
                )

                # Marquer comme retourné
                transaction.return_date = timezone.now()
                transaction.save()

                # Remettre le livre en stock
                book = transaction.book
                book.copies_available += 1
                book.save()

                # Vérifier la liste d'attente
                waitlist_entries = Waitlist.objects.filter(book=book).order_by('created_at')
                if waitlist_entries.exists():
                    next_entry = waitlist_entries.first()
                    try:
                        send_mail(
                            subject=f'Livre disponible : {book.title}',
                            message=(
                                f'Bonjour {next_entry.user.username},\n\n'
                                f'Le livre "{book.title}" est maintenant disponible.\n'
                                f'Connectez-vous pour l\'emprunter !'
                            ),
                            from_email=None,
                            recipient_list=[next_entry.user.email],
                            fail_silently=True,  # Ne pas bloquer si l'email échoue
                        )
                    except Exception as e:
                        # Log l'erreur mais ne pas bloquer le retour
                        print(f"Erreur d'envoi d'email: {e}")

                response_serializer = TransactionSerializer(transaction)
                return Response(
                    {
                        'success': 'Livre retourné avec succès!',
                        'transaction': response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )

        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction active non trouvée.'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyTransactionsAPIView(generics.ListAPIView):
    """
    API pour lister les transactions de l'utilisateur connecté
    GET /api/my-transactions/?status=active|returned|overdue
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)

        # Filtre par statut
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(return_date__isnull=True)
        elif status_filter == 'returned':
            queryset = queryset.filter(return_date__isnull=False)
        elif status_filter == 'overdue':
            queryset = queryset.filter(
                return_date__isnull=True,
                due_date__lt=timezone.now()
            )

        return queryset.order_by('-checkout_date')


class OverdueTransactionsAPIView(generics.ListAPIView):
    """
    API pour lister les transactions en retard
    GET /api/overdue/
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user,
            return_date__isnull=True,
            due_date__lt=timezone.now()
        ).order_by('due_date')


class JoinWaitlistAPIView(APIView):
    """
    API pour rejoindre la liste d'attente d'un livre
    POST /api/waitlist/ {book_id: 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WaitlistCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book_id = serializer.validated_data['book_id']
        book = get_object_or_404(Book, id=book_id)

        # Vérifier si déjà dans la liste d'attente
        if Waitlist.objects.filter(user=request.user, book=book).exists():
            return Response(
                {'error': 'Vous êtes déjà dans la liste d\'attente pour ce livre.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier si le livre est disponible (pas besoin d'attente)
        if book.copies_available > 0:
            return Response(
                {'warning': 'Ce livre est disponible, vous pouvez l\'emprunter directement !'},
                status=status.HTTP_200_OK
            )

        # Ajouter à la liste d'attente
        waitlist = Waitlist.objects.create(user=request.user, book=book)

        response_serializer = WaitlistSerializer(waitlist)
        return Response(
            {
                'success': 'Ajouté à la liste d\'attente avec succès!',
                'waitlist': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class WaitlistAPIView(generics.ListAPIView):
    """
    API pour voir la liste d'attente d'un livre
    GET /api/waitlist/?book_id=1
    """
    serializer_class = WaitlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        book_id = self.request.query_params.get('book_id')
        if book_id:
            return Waitlist.objects.filter(book_id=book_id).order_by('created_at')
        return Waitlist.objects.filter(user=self.request.user).order_by('-created_at')


class CancelWaitlistAPIView(APIView):
    """
    API pour quitter la liste d'attente
    DELETE /api/waitlist/{id}/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, waitlist_id):
        waitlist = get_object_or_404(Waitlist, id=waitlist_id, user=request.user)
        waitlist.delete()
        return Response(
            {'success': 'Retiré de la liste d\'attente.'},
            status=status.HTTP_200_OK
        )


# ====================== TEMPLATE VIEWS (pour rendu HTML) ======================

def book_list_page(request):
    """Page liste des livres (HTML)"""
    books = Book.objects.all()
    return render(request, "books/book_list.html", {"books": books})


@login_required
def book_detail_page(request, book_id):
    """Page détail d'un livre (HTML)"""
    book = get_object_or_404(Book, id=book_id)
    # Vérifier si l'utilisateur a déjà emprunté ce livre
    user_has_borrowed = Transaction.objects.filter(
        user=request.user,
        book=book,
        return_date__isnull=True
    ).exists()
    
    # Vérifier si l'utilisateur est dans la liste d'attente
    user_in_waitlist = Waitlist.objects.filter(
        user=request.user,
        book=book
    ).exists()
    
    context = {
        "book": book,
        "user_has_borrowed": user_has_borrowed,
        "user_in_waitlist": user_in_waitlist
    }
    return render(request, "books/book_detail.html", context)


@login_required
def my_transactions_page(request):
    """Page mes transactions (HTML)"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-checkout_date')
    return render(request, "books/my_transactions.html", {"transactions": transactions})


@login_required
def overdue_books_page(request):
    """Page livres en retard (HTML)"""
    transactions = Transaction.objects.filter(
        user=request.user,
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).order_by('due_date')
    return render(request, "books/overdue.html", {"transactions": transactions})


@login_required
def borrow_book_page(request, book_id):
    """
    Vue template pour emprunter un livre (redirige vers l'API)
    """
    if request.method == "POST":
        # Utiliser l'API en interne
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        api_request = factory.post('/api/checkout/', {'book_id': book_id}, format='json')
        api_request.user = request.user
        
        response = CheckoutAPIView.as_view()(api_request)
        
        if response.status_code == 201:
            messages.success(request, "Livre emprunté avec succès!")
        else:
            error_msg = response.data.get('error', 'Erreur lors de l\'emprunt')
            messages.error(request, error_msg)
        
        return redirect('book-detail', book_id=book_id)
    
    return redirect('book-detail', book_id=book_id)


@login_required
def return_book_page(request, transaction_id):
    """
    Vue template pour retourner un livre
    """
    if request.method == "POST":
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        api_request = factory.post('/api/return/', {'transaction_id': transaction_id}, format='json')
        api_request.user = request.user
        
        response = ReturnAPIView.as_view()(api_request)
        
        if response.status_code == 200:
            messages.success(request, "Livre retourné avec succès!")
        else:
            error_msg = response.data.get('error', 'Erreur lors du retour')
            messages.error(request, error_msg)
        
        return redirect('my-transactions')
    
    return redirect('my-transactions')@login_required
def my_transactions_page(request):
    """Page mes transactions (HTML)"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-checkout_date')
    
    # Calculer les stats
    transactions_active = transactions.filter(return_date__isnull=True).count()
    transactions_overdue = transactions.filter(
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).count()
    
    # Ajouter l'attribut is_overdue à chaque transaction
    for transaction in transactions:
        transaction.is_overdue = transaction.due_date and transaction.due_date < timezone.now() and not transaction.return_date
        if transaction.due_date and not transaction.return_date:
            delta = transaction.due_date - timezone.now()
            transaction.days_until_due = delta.days
        else:
            transaction.days_until_due = None
    
    context = {
        "transactions": transactions,
        "transactions_active": transactions_active,
        "transactions_overdue": transactions_overdue
    }
    return render(request, "books/my_transactions.html", context)

@login_required
def overdue_books_page(request):
    """Page livres en retard (HTML)"""
    transactions = Transaction.objects.filter(
        user=request.user,
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).order_by('due_date')
    
    # Calculer les jours de retard
    for transaction in transactions:
        delta = timezone.now() - transaction.due_date
        transaction.days_overdue = delta.days
    
    return render(request, "books/overdue.html", {"transactions": transactions})

