from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.module_list, name='module_list'),
    path('detail/<uuid:module_id>/', views.module_detail, name='module_detail'),
    path('categories/', views.categories_list, name='categories_list'),
    path('user-modules/', views.user_modules, name='user_modules'),
]
