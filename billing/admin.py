from django.contrib import admin
from .models import UserCredit, Transaction


@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'last_updated']
    search_fields = ['user__username', 'user__email']
    list_filter = ['last_updated']
    readonly_fields = ['last_updated']
    
    # امکان ویرایش مستقیم balance
    fields = ['user', 'balance', 'last_updated']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'credit_amount', 'price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'authority', 'ref_id']
    readonly_fields = ['created_at', 'paid_at']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'credit_amount', 'price')
        }),
        ('وضعیت', {
            'fields': ('status', 'authority', 'ref_id')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'paid_at')
        }),
    )