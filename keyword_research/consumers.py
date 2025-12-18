"""
WebSocket Consumer for Real-time Updates
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TaskStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket برای دریافت وضعیت Task
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"✅ WebSocket connected: User {self.user.id}")
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            print(f"❌ WebSocket disconnected: User {self.user.id}")
    
    async def task_status(self, event):
        """
        دریافت پیام از Signal و ارسال به Frontend
        """
        await self.send(text_data=json.dumps({
            'type': 'task_completed',
            'data': event['data']
        }))