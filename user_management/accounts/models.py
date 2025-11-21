from django.db import models
from django.conf import settings 
from django.contrib.auth.models import User

class ChatConversation(models.Model):
    """
    Model này đại diện cho một phiên/cuộc trò chuyện hoàn chỉnh.
    Nó liên kết với một người dùng.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True) # Tiêu đề cho cuộc chat (tùy chọn)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id} của {self.user.username}"

class ChatMessage(models.Model):
    """
    Model này lưu trữ một tin nhắn cụ thể trong một cuộc trò chuyện.
    """
    # Định nghĩa các lựa chọn cho người gửi
    SENDER_CHOICES = (
        ('user', 'User'),
        ('ai', 'AI'),
    )

    conversation = models.ForeignKey(ChatConversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField() # Nội dung tin nhắn
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp'] # Sắp xếp tin nhắn theo thời gian

    def __str__(self):
        return f"{self.get_sender_display()}: {self.content[:30]}..."
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # upload_to='avatars/' nghĩa là ảnh sẽ chui vào thư mục media/avatars/
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True)

    def __str__(self):
        return self.user.username
    
class FavoritePlace(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    # Lưu ID của quán từ file CSV (nếu file CSV dùng cột data_id, hãy đảm bảo khớp kiểu dữ liệu)
    place_id = models.CharField(max_length=100) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'place_id') # Một người không thể like 1 quán 2 lần

    def __str__(self):
        return f"{self.user.username} - {self.place_id}"