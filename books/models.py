from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from datetime import timedelta



class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    copies_available = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

    def clean(self):
        if self.copies_available < 0:
            raise ValidationError("Copies available cannot be negative.")

        if self.published_date > timezone.now().date():
            raise ValidationError("Published date cannot be in the future.")

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
        ]


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    checkout_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)  

    def __str__(self):
        return f"{self.user} - {self.book}"


    def save(self, *args, **kwargs):
        if not self.checkout_date:
            self.checkout_date = timezone.now()

        if not self.due_date and not self.return_date:
            self.due_date = timezone.now() + timedelta(days=14)

        super().save(*args, **kwargs)

    @property
    def status(self):
        if self.return_date:
            return "returned"
        elif self.due_date and self.due_date < timezone.now():
            return "overdue"
        return "active"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=Q(return_date__isnull=True),
                name='unique_active_transaction'
            )
        ]


class Waitlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'book']