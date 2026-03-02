from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active_member', 'date_of_membership')
    list_filter = ('is_active_member', 'is_staff', 'is_superuser', 'date_of_membership')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Membership Information', {
            'fields': ('date_of_membership', 'is_active_member'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Membership Information', {
            'fields': ('date_of_membership', 'is_active_member'),
        }),
    )
    
    actions = ['activate_members', 'deactivate_members']
    
    def activate_members(self, request, queryset):
        updated = queryset.update(is_active_member=True)
        self.message_user(request, f'{updated} users activated.')
    activate_members.short_description = "Activate selected users"
    
    def deactivate_members(self, request, queryset):
        updated = queryset.update(is_active_member=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_members.short_description = "Deactivate selected users"