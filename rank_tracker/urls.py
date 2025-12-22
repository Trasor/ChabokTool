from django.urls import path
from . import views

app_name = 'rank_tracker'

urlpatterns = [
    # لیست و مدیریت پروژه‌ها
    path('', views.project_list, name='project_list'),
    path('project/create/', views.project_create, name='project_create'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/delete/', views.project_delete, name='project_delete'),

    # مدیریت کلمات کلیدی
    path('project/<int:project_id>/keywords/add/', views.keyword_add, name='keyword_add'),
    path('keyword/<int:keyword_id>/delete/', views.keyword_delete, name='keyword_delete'),

    # آپدیت رتبه‌ها
    path('project/<int:project_id>/update-ranks/', views.update_ranks, name='update_ranks'),

    # API برای Chart
    path('api/keyword-history/<int:keyword_id>/', views.keyword_history_api, name='keyword_history_api'),

    # دانلود فایل نمونه
    path('download-sample/', views.download_sample_excel, name='download_sample'),
]
