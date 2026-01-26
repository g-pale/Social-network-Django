from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('recipient', 'actor', 'notification_type', 'is_read')
        }),
        ('Связанные объекты', {
            'fields': ('post', 'comment', 'conversation')
        }),
        ('Дата', {
            'fields': ('created_at',)
        }),
    )
