from django.contrib import admin
from .models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Админ-панель для модели Post"""
    list_display = ['id', 'author', 'text_preview', 'created_at', 'get_likes_count', 'get_comments_count']
    list_filter = ['created_at', 'author']
    search_fields = ['text', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('author', 'text', 'image')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Превью текста поста"""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'
    
    def get_likes_count(self, obj):
        """Количество лайков"""
        return obj.get_likes_count()
    get_likes_count.short_description = 'Лайки'
    
    def get_comments_count(self, obj):
        """Количество комментариев"""
        return obj.get_comments_count()
    get_comments_count.short_description = 'Комментарии'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Админ-панель для модели Like"""
    list_display = ['id', 'user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__text']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Админ-панель для модели Comment"""
    list_display = ['id', 'post', 'author', 'text_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['text', 'author__username', 'post__text']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        """Превью текста комментария"""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'
