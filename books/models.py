from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    copies_available = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

    def clean(self):
        """
        Business validations
        """
        if self.copies_available < 0:
            raise ValidationError("Copies available cannot be negative.")

        if self.published_date > timezone.now().date():
            raise ValidationError("Published date cannot be in the future.")

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
        ]



class Loan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    checkout_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.book}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=Q(return_date__isnull=True),
                name='unique_active_loan'
            )
        ]