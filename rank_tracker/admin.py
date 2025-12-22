from django.contrib import admin
from .models import RankProject, RankKeyword, RankHistory


@admin.register(RankProject)
class RankProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'target_domain', 'user', 'keyword_capacity',
                    'keywords_count', 'update_count_current_month', 'last_update_at', 'is_active')
    list_filter = ('is_active', 'created_date')
    search_fields = ('project_name', 'target_domain', 'user__username')
    readonly_fields = ('created_date', 'last_update_at')

    def keywords_count(self, obj):
        return obj.keywords_count
    keywords_count.short_description = 'تعداد کلمات'


@admin.register(RankKeyword)
class RankKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'project', 'current_rank', 'previous_rank',
                    'highest_rank', 'page_number', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('keyword', 'project__project_name')
    readonly_fields = ('created_at',)


@admin.register(RankHistory)
class RankHistoryAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'rank', 'checked_at')
    list_filter = ('checked_at',)
    search_fields = ('keyword__keyword',)
    readonly_fields = ('checked_at',)
    date_hierarchy = 'checked_at'
