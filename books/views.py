from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book, Transaction, Waitlist
from .serializers import BookSerializer, TransactionSerializer, CheckoutSerializer, ReturnSerializer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q



User = get_user_model()


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'isbn']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'published_date']
    ordering = ['title']

    def get_queryset(self):
        queryset = super().get_queryset()
        available = self.request.query_params.get('available')
        if available and available.lower() == 'true':
            queryset = queryset.filter(copies_available__gt=0)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    MAX_ACTIVE_TRANSACTIONS = 5

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        active_count = Transaction.objects.filter(
            user=request.user,
            return_date__isnull=True
        ).count()

        if active_count >= self.MAX_ACTIVE_TRANSACTIONS:
            return Response(
                {'error': f'Transaction limit reached (max {self.MAX_ACTIVE_TRANSACTIONS} active).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                book = Book.objects.select_for_update().get(id=book_id)

                if book.copies_available <= 0:
                    return Response(
                        {'error': 'No copies available'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if Transaction.objects.filter(
                    user=request.user,
                    book=book,
                    return_date__isnull=True
                ).exists():
                    return Response(
                        {'error': 'You already have this book checked out'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                Transaction.objects.create(user=request.user, book=book)
                book.copies_available -= 1
                book.save()

            return Response(
                {'success': 'Book checked out successfully'},
                status=status.HTTP_200_OK
            )

        except Book.DoesNotExist:
            return Response(
                {'error': 'Book not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyTransactionsView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        active = self.request.query_params.get('active', None)
        if active and active.lower() == 'true':
            queryset = queryset.filter(return_date__isnull=True)
        return queryset.order_by('-checkout_date')


class ReturnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id):
        try:
            with transaction.atomic():
                transaction_obj = Transaction.objects.select_for_update().get(
                    id=transaction_id,
                    user=request.user,
                    return_date__isnull=True
                )

                transaction_obj.return_date = timezone.now()
                transaction_obj.save()

                book = transaction_obj.book
                book.copies_available += 1
                book.save()

                if book.copies_available > 0:
                    waitlist_entries = Waitlist.objects.filter(
                        book=book
                    ).order_by('created_at')

                    if waitlist_entries.exists():
                        next_entry = waitlist_entries.first()
                        next_user = next_entry.user

                        send_mail(
                            subject=f'Book Available: {book.title}',
                            message=(
                                f'Dear {next_user.username},\n\n'
                                f'The book "{book.title}" is now available for checkout.'
                            ),
                            from_email=None,
                            recipient_list=[next_user.email],
                            fail_silently=False,
                        )

                        next_entry.delete()

            return Response(
                {"success": "Book returned successfully"},
                status=status.HTTP_200_OK
            )

        except Transaction.DoesNotExist:
            return Response(
                {"error": "Active transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class JoinWaitlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        book_id = request.data.get('book_id')
        book = get_object_or_404(Book, id=book_id)


        from .models import Waitlist
        if Waitlist.objects.filter(user=request.user, book=book).exists():
            return Response({'error': 'You are already on the waitlist'}, status=400)

        Waitlist.objects.create(user=request.user, book=book)
        return Response({'success': 'Added to waitlist'}, status=200)

class OverdueTransactionsView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user,
            return_date__isnull=True,
            due_date__lt=timezone.now()
        ).order_by('due_date')



def book_list_view(request):
    books = Book.objects.all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        books = books.filter(
            Q(title__icontains=search) |
            Q(author__icontains=search) |
            Q(isbn__icontains=search)
        )
    
    # Filters
    author = request.GET.get('author', '')
    if author:
        books = books.filter(author__icontains=author)
    
    isbn = request.GET.get('isbn', '')
    if isbn:
        books = books.filter(isbn__icontains=isbn)
    
    available = request.GET.get('available', '')
    if available == 'true':
        books = books.filter(copies_available__gt=0)
    
    # Ordering
    ordering = request.GET.get('ordering', 'title')
    books = books.order_by(ordering)
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'books': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'books/book_list.html', context)

def book_detail_view(request, pk):
    book = Book.objects.get(pk=pk)
    return render(request, 'books/book_detail.html', {'book': book})

@login_required
def my_transactions_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    
    active = request.GET.get('active', '')
    if active == 'true':
        transactions = transactions.filter(return_date__isnull=True)
    elif active == 'false':
        transactions = transactions.filter(return_date__isnull=False)
    
    context = {'transactions': transactions}
    return render(request, 'books/my_transactions.html', context)