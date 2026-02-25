from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Book, Transaction
from .serializers import BookSerializer, TransactionSerializer, CheckoutSerializer, ReturnSerializer
from django.contrib.auth import get_user_model
from django.db import transaction

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

                transaction_obj.book.copies_available += 1
                transaction_obj.book.save()

            return Response(
                {"success": "Book returned successfully"},
                status=status.HTTP_200_OK
            )

        except Transaction.DoesNotExist:
            return Response(
                {"error": "Active transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )