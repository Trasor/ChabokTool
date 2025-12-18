from django.contrib import admin
from .models import GapRequest, GapKeyword


@admin.register(GapRequest)
class GapRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'created_date', 'duration')
    list_filter = ('status', 'created_date')
    search_fields = ('name', 'user__username')


@admin.register(GapKeyword)
class GapKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'competitor', 'link', 'user')
    list_filter = ('competitor', 'user')
    search_fields = ('keyword', 'competitor')