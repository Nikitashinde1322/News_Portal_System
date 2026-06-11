from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_approved']
    list_filter = ['is_approved']
    actions = ['approve_news', 'reject_news']

    def approve_news(self, request, queryset):
        queryset.update(is_approved=True)
    approve_news.short_description = "Approve selected news"

    def reject_news(self, request, queryset):
        queryset.update(is_approved=False)
    reject_news.short_description = "Reject selected news"