from django.urls import path
from . import views

urlpatterns = [
    path('', views.gap_analysis, name='gap_analysis'),
    path('requests/', views.gap_requests_list, name='gap_requests_list'),
    path('request/<int:pk>/', views.gap_request_detail, name='gap_request_detail'),
    path('delete/<int:request_id>/', views.delete_gap_request, name='delete_gap_request'),
]