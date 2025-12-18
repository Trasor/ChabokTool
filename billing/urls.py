from django.urls import path
from . import views

urlpatterns = [
    path('buy-credit/', views.buy_credit, name='buy_credit'),
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('verify/', views.verify_payment, name='verify_payment'),  # ✅ جدید
    path('pay/<int:transaction_id>/', views.pay_transaction, name='pay_transaction'),  # ✅ جدید
]