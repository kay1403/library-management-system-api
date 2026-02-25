from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.utils import timezone
from .models import Book, Loan
from .serializers import BookSerializer, LoanSerializer, CheckoutSerializer, ReturnSerializer
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

User = get_user_model()

# --------------------------
# BOOK VIEWSET
# --------------------------
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return []

# --------------------------
# USER VIEWSET
# --------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

# --------------------------
# LOANS
# --------------------------
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        if book.copies_available <= 0:
            return Response({'error': 'No copies available'}, status=status.HTTP_400_BAD_REQUEST)

        existing_loan = Loan.objects.filter(user=request.user, book=book, return_date__isnull=True).exists()
        if existing_loan:
            return Response({'error': 'You already have this book checked out'}, status=status.HTTP_400_BAD_REQUEST)

        Loan.objects.create(user=request.user, book=book)
        book.copies_available -= 1
        book.save()
        return Response({'success': 'Book checked out successfully'}, status=status.HTTP_200_OK)

class ReturnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book_id = serializer.validated_data['book_id']

        try:
            loan = Loan.objects.get(user=request.user, book_id=book_id, return_date__isnull=True)
        except Loan.DoesNotExist:
            return Response({'error': 'No active loan found for this book'}, status=status.HTTP_400_BAD_REQUEST)

        loan.return_date = timezone.now()
        loan.save()

        loan.book.copies_available += 1
        loan.book.save()

        return Response({'success': 'Book returned successfully'}, status=status.HTTP_200_OK)

# My Loans
class MyLoansView(generics.ListAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)