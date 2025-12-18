from django.urls import path
from . import views

urlpatterns = [
    path('', views.keyword_research, name='keyword_research'),
    path('requests/', views.requests_list, name='requests_list'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/<int:request_id>/delete/', views.delete_request, name='delete_request'),
    path('download-sample/', views.download_sample_file, name='download_sample_file'),
    path('check-status/', views.check_task_status, name='check_task_status'),  # ✅ جدید
]