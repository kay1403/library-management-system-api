from django.contrib import admin
from .models import Book, Transaction, Waitlist

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'copies_available', 'published_date')
    list_filter = ('author', 'published_date')
    search_fields = ('title', 'author', 'isbn')
    ordering = ('title',)
    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'author', 'isbn', 'published_date')
        }),
        ('Availability', {
            'fields': ('copies_available',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'checkout_date', 'due_date', 'return_date', 'status')
    list_filter = ('checkout_date', 'due_date', 'return_date')
    search_fields = ('book__title', 'user__username')
    date_hierarchy = 'checkout_date'
    actions = ['mark_as_returned']
    
    def mark_as_returned(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(return_date=timezone.now())
        self.message_user(request, f'{updated} transactions marked as returned.')
    mark_as_returned.short_description = "Mark selected as returned"
    
    def status(self, obj):
        if obj.return_date:
            return '<span style="color: green; font-weight: bold;">✓ Returned</span>'
        elif obj.due_date and obj.due_date < timezone.now():
            return '<span style="color: red; font-weight: bold;">⚠ Overdue</span>'
        else:
            return '<span style="color: blue; font-weight: bold;">📖 Active</span>'
    status.allow_tags = True
    status.short_description = 'Status'


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'created_at', 'position')
    list_filter = ('created_at', 'book')
    search_fields = ('book__title', 'user__username')
    ordering = ('book', 'created_at')
    
    def position(self, obj):
        # Calculate position in queue for this book
        position = Waitlist.objects.filter(
            book=obj.book,
            created_at__lt=obj.created_at
        ).count() + 1
        return f"#{position}"
    position.short_description = 'Queue Position'