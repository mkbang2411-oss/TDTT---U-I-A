from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
import threading

# ✅ GLOBAL DICT để lưu SSE connections
# Key: user_id, Value: queue để gửi notification
sse_connections = {}

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """
    Signal được trigger mỗi khi có Notification mới được tạo
    """
    if created:  # Chỉ xử lý khi TẠO MỚI notification
        user_id = instance.user.id
        
        print(f"🔔 [SIGNAL] New notification created for user_id={user_id}")
        print(f"   Type: {instance.notification_type}")
        print(f"   Title: {instance.title}")
        
        # ✅ Gửi notification qua SSE nếu user đang connected
        if user_id in sse_connections:
            queue = sse_connections[user_id]
            
            notification_data = {
                'id': instance.id,
                'type': instance.notification_type,
                'title': instance.title,
                'message': instance.message,
                'is_read': instance.is_read,
                'created_at': instance.created_at.isoformat(),
                'related_id': instance.related_id,
                'metadata': instance.metadata
            }
            
            # Đưa vào queue để SSE stream gửi đi
            queue.put(notification_data)
            print(f"✅ [SIGNAL] Pushed to SSE queue for user_id={user_id}")
        else:
            print(f"⚠️  [SIGNAL] User {user_id} không có SSE connection active")