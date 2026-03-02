from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from books.models import Transaction

class Command(BaseCommand):
    help = 'Send overdue book notifications to users'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        overdue_transactions = Transaction.objects.filter(return_date__isnull=True, due_date__lt=now)

        for transaction in overdue_transactions:
            user = transaction.user
            book = transaction.book
            send_mail(
                subject=f'Overdue Book Reminder: {book.title}',
                message=f'Dear {user.username},\n\nThe book "{book.title}" is overdue. Please return it as soon as possible.',
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Notification sent to {user.email} for {book.title}'))