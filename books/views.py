from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Book, Loan
from .serializers import BookSerializer, LoanSerializer, CheckoutSerializer, ReturnSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# --------------------------
# BOOK VIEWSET
# --------------------------
class BookViewSet(viewsets.ModelViewSet):
    """
    Book CRUD API with:
    - Admin-only create/update/delete
    - Filtering by author, ISBN
    - Search by title, author, ISBN
    - Pagination
    - Filter only available books
    - Ordering
    """
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'isbn']           # exact matches
    search_fields = ['title', 'author', 'isbn']    # partial search
    ordering_fields = ['title', 'published_date']  # allow ordering
    ordering = ['title']                            # default ordering

    def get_queryset(self):
        """
        Optionally filter by availability (?available=true)
        """
        queryset = super().get_queryset()
        available = self.request.query_params.get('available')
        if available and available.lower() == 'true':
            queryset = queryset.filter(copies_available__gt=0)
        return queryset

    def get_permissions(self):
        """
        Admin-only for create/update/delete, read-only for everyone else
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]




# --------------------------
# Checkout Endpoint
# --------------------------
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        # Check if book exists
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check available copies
        if book.copies_available <= 0:
            return Response({'error': 'No copies available'}, status=status.HTTP_400_BAD_REQUEST)

        # Check duplicate active loan
        if Loan.objects.filter(user=request.user, book=book, return_date__isnull=True).exists():
            return Response({'error': 'You already have this book checked out'}, status=status.HTTP_400_BAD_REQUEST)

        # Create loan
        Loan.objects.create(user=request.user, book=book)
        book.copies_available -= 1
        book.save()
        return Response({'success': 'Book checked out successfully'}, status=status.HTTP_200_OK)

# --------------------------
# Return Endpoint
# --------------------------
class ReturnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        # Find active loan
        try:
            loan = Loan.objects.get(user=request.user, book_id=book_id, return_date__isnull=True)
        except Loan.DoesNotExist:
            return Response({'error': 'No active loan found for this book'}, status=status.HTTP_400_BAD_REQUEST)

        # Return book
        loan.return_date = timezone.now()
        loan.save()
        loan.book.copies_available += 1
        loan.book.save()
        return Response({'success': 'Book returned successfully'}, status=status.HTTP_200_OK)

# --------------------------
# My Loans Endpoint
# --------------------------
class MyLoansView(generics.ListAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return all loans of the user, optionally filter only active loans with ?active=true
        """
        queryset = Loan.objects.filter(user=self.request.user)
        active = self.request.query_params.get('active', None)
        if active and active.lower() == 'true':
            queryset = queryset.filter(return_date__isnull=True)
        return queryset.order_by('-checkout_date')