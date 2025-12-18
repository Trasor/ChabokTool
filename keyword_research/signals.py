"""
Signals for Task Completion
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ResearchRequest


@receiver(post_save, sender=ResearchRequest)
def notify_task_completion(sender, instance, **kwargs):
    """
    وقتی Task تکمیل شد، به Frontend اطلاع بده
    """
    if instance.status in ['completed', 'failed']:
        channel_layer = get_channel_layer()
        
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f"user_{instance.user.id}",
                    {
                        'type': 'task_status',
                        'data': {
                            'request_id': instance.id,
                            'status': instance.status,
                            'message': 'درخواست شما تکمیل شد!' if instance.status == 'completed' else 'خطا در پردازش',
                        }
                    }
                )
            except Exception as e:
                print(f"❌ Signal error: {str(e)}")