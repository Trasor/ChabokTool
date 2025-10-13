from django.urls import path
from . import views

urlpatterns = [
    path('', views.keyword_research, name='keyword_research'),
    path('requests/', views.requests_list, name='requests_list'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
]