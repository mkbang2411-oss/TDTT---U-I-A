from django.db import models
from django.conf import settings # Dùng để liên kết tới User model

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