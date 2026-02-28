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


# ====================== API VIEWS (for dynamic frontend) ======================

class BookViewSet(viewsets.ModelViewSet):
    """
    CRUD API for books
    - GET: accessible to everyone (authenticated or not)
    - POST/PUT/DELETE: reserved for admins
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
        Differentiated permissions based on action
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]  # Everyone can view books

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by availability
        available = self.request.query_params.get('available')
        if available and available.lower() == 'true':
            queryset = queryset.filter(copies_available__gt=0)
        return queryset


class CheckoutAPIView(APIView):
    """
    API to borrow a book
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

        # Check if the user is an active member
        if hasattr(user, 'is_active_member') and not user.is_active_member:
            return Response(
                {'error': 'Your account is inactive. Please contact the administrator.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check loan limit
        active_count = Transaction.objects.filter(
            user=user,
            return_date__isnull=True
        ).count()

        if active_count >= self.MAX_ACTIVE_TRANSACTIONS:
            return Response(
                {'error': f'Loan limit reached ({self.MAX_ACTIVE_TRANSACTIONS} maximum).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with db_transaction.atomic():
                book = Book.objects.select_for_update().get(id=book_id)

                # Check availability
                if book.copies_available <= 0:
                    return Response(
                        {'error': 'This book is not currently available.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Check if already borrowed
                if Transaction.objects.filter(
                    user=user,
                    book=book,
                    return_date__isnull=True
                ).exists():
                    return Response(
                        {'error': 'You have already borrowed this book.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Create transaction
                transaction = Transaction.objects.create(user=user, book=book)
                book.copies_available -= 1
                book.save()

                # Return the created transaction
                response_serializer = TransactionSerializer(transaction)
                return Response(
                    {
                        'success': 'Book borrowed successfully!',
                        'transaction': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

        except Book.DoesNotExist:
            return Response(
                {'error': 'Book not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReturnAPIView(APIView):
    """
    API to return a book
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
                # Retrieve the active transaction
                transaction = Transaction.objects.select_for_update().get(
                    id=transaction_id,
                    user=request.user,
                    return_date__isnull=True
                )

                # Mark as returned
                transaction.return_date = timezone.now()
                transaction.save()

                # Put the book back in stock
                book = transaction.book
                book.copies_available += 1
                book.save()

                # Check the waitlist
                waitlist_entries = Waitlist.objects.filter(book=book).order_by('created_at')
                if waitlist_entries.exists():
                    next_entry = waitlist_entries.first()
                    try:
                        send_mail(
                            subject=f'Book available: {book.title}',
                            message=(
                                f'Hello {next_entry.user.username},\n\n'
                                f'The book "{book.title}" is now available.\n'
                                f'Log in to borrow it!'
                            ),
                            from_email=None,
                            recipient_list=[next_entry.user.email],
                            fail_silently=True,  # Do not block if email fails
                        )
                    except Exception as e:
                        # Log the error but do not block the return process
                        print(f"Email sending error: {e}")

                response_serializer = TransactionSerializer(transaction)
                return Response(
                    {
                        'success': 'Book returned successfully!',
                        'transaction': response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )

        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Active transaction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyTransactionsAPIView(generics.ListAPIView):
    """
    API to list transactions of the logged-in user
    GET /api/my-transactions/?status=active|returned|overdue
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)

        # Filter by status
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
    API to list overdue transactions
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
    API to join the waitlist for a book
    POST /api/waitlist/ {book_id: 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WaitlistCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book_id = serializer.validated_data['book_id']
        book = get_object_or_404(Book, id=book_id)

        # Check if already in waitlist
        if Waitlist.objects.filter(user=request.user, book=book).exists():
            return Response(
                {'error': 'You are already on the waitlist for this book.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if book is available (no need for waitlist)
        if book.copies_available > 0:
            return Response(
                {'warning': 'This book is available, you can borrow it directly!'},
                status=status.HTTP_200_OK
            )

        # Add to waitlist
        waitlist = Waitlist.objects.create(user=request.user, book=book)

        response_serializer = WaitlistSerializer(waitlist)
        return Response(
            {
                'success': 'Successfully added to the waitlist!',
                'waitlist': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class WaitlistAPIView(generics.ListAPIView):
    """
    API to view the waitlist for a book
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
    API to leave the waitlist
    DELETE /api/waitlist/{id}/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, waitlist_id):
        waitlist = get_object_or_404(Waitlist, id=waitlist_id, user=request.user)
        waitlist.delete()
        return Response(
            {'success': 'Removed from the waitlist.'},
            status=status.HTTP_200_OK
        )


# ====================== TEMPLATE VIEWS (for HTML rendering) ======================

def book_list_page(request):
    """Book list page (HTML)"""
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
    user_waitlist_entry = Waitlist.objects.filter(
        user=request.user,
        book=book
    ).first()
    
    user_in_waitlist = user_waitlist_entry is not None
    user_waitlist_id = user_waitlist_entry.id if user_waitlist_entry else None  # AJOUTE ÇA
    
    # Calculer la position dans la file d'attente
    waitlist_position = None
    if user_in_waitlist:
        waitlist_position = Waitlist.objects.filter(
            book=book,
            created_at__lt=user_waitlist_entry.created_at
        ).count() + 1
    
    context = {
        "book": book,
        "user_has_borrowed": user_has_borrowed,
        "user_in_waitlist": user_in_waitlist,
        "user_waitlist_id": user_waitlist_id,  # AJOUTE ÇA
        "waitlist_position": waitlist_position
    }
    return render(request, "books/book_detail.html", context)


@login_required
def borrow_book_page(request, book_id):
    """
    Template view to borrow a book (redirects to the API)
    """
    if request.method == "POST":
        # Use the API internally
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        api_request = factory.post('/api/checkout/', {'book_id': book_id}, format='json')
        api_request.user = request.user
        
        response = CheckoutAPIView.as_view()(api_request)
        
        if response.status_code == 201:
            messages.success(request, "Book borrowed successfully!")
        else:
            error_msg = response.data.get('error', 'Error while borrowing')
            messages.error(request, error_msg)
        
        return redirect('book-detail', book_id=book_id)
    
    return redirect('book-detail', book_id=book_id)


@login_required
def return_book_page(request, transaction_id):
    """
    Template view to return a book
    """
    if request.method == "POST":
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        api_request = factory.post('/api/return/', {'transaction_id': transaction_id}, format='json')
        api_request.user = request.user
        
        response = ReturnAPIView.as_view()(api_request)
        
        if response.status_code == 200:
            messages.success(request, "Book returned successfully!")
        else:
            error_msg = response.data.get('error', 'Error while returning')
            messages.error(request, error_msg)
        
        return redirect('my-transactions')
    
    return redirect('my-transactions')


@login_required
def my_transactions_page(request):
    """My transactions page (HTML)"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-checkout_date')
    
    # Calculate stats
    transactions_active = transactions.filter(return_date__isnull=True).count()
    transactions_overdue = transactions.filter(
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).count()
    
    # Add is_overdue attribute to each transaction
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
    """Overdue books page (HTML)"""
    transactions = Transaction.objects.filter(
        user=request.user,
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).order_by('due_date')
    
    # Calculate days overdue
    for transaction in transactions:
        delta = timezone.now() - transaction.due_date
        transaction.days_overdue = delta.days
    
    return render(request, "books/overdue.html", {"transactions": transactions})

@login_required
def waitlist_page(request):
    """Page liste d'attente de l'utilisateur"""
    from .models import Waitlist
    
    waitlist_items = Waitlist.objects.filter(user=request.user).select_related('book').order_by('created_at')
    
    # Calculer la position pour chaque élément
    for item in waitlist_items:
        # Compter combien de personnes sont devant dans la file d'attente pour ce livre
        position = Waitlist.objects.filter(
            book=item.book,
            created_at__lt=item.created_at
        ).count() + 1
        item.position = position
    
    return render(request, "books/waitlist.html", {"waitlist_items": waitlist_items})