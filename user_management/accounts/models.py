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


# CHÚ Ý: 2 CLASS NÀY PHẢI Ở NGOÀI, KHÔNG THỤT LỀ
class FriendRequest(models.Model):
    """
    Model lưu trữ yêu cầu kết bạn giữa các user
    """
    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('accepted', 'Đã chấp nhận'),
        ('rejected', 'Đã từ chối'),
    ]
    

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"


class Friendship(models.Model):
    """
    Model lưu trữ quan hệ bạn bè giữa 2 user
    """
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friendships_as_user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friendships_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user1.username} <-> {self.user2.username}"

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
    


# 🎮 
class GameProgress(models.Model):
    """
    Model lưu tiến độ chơi game của từng user
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='game_progress')
    current_level = models.IntegerField(default=0)  # Level hiện tại đang chơi
    completed_levels = models.JSONField(default=list)  # Danh sách các level đã hoàn thành [0, 1, 2...]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    level_stars = models.JSONField(default=dict)  # {"0": 3, "1": 2, "2": 1}
    deaths = models.IntegerField(default=0)  # Số lần chết
    best_times = models.JSONField(default=dict)  # {"0": 45.5, "1": 60.2}
    
    class Meta:
        verbose_name = "Game Progress"
        verbose_name_plural = "Game Progresses"
    
    def __str__(self):
        return f"{self.user.username} - Level {self.current_level}"
    
    def unlock_level(self, level_index):
        """Mở khóa level mới khi hoàn thành"""
        if level_index not in self.completed_levels:
            self.completed_levels.append(level_index)
            self.completed_levels.sort()  # Sắp xếp để dễ quản lý
            self.save()
    
    def get_max_unlocked_level(self):
        """Trả về level cao nhất có thể chơi (level tiếp theo sau level đã hoàn thành)"""
        if not self.completed_levels:
            return 0  # Nếu chưa hoàn thành level nào thì chỉ được chơi level 0
        return max(self.completed_levels) + 1
    
    def is_level_unlocked(self, level_index):
        """Kiểm tra xem level có được mở khóa chưa"""
        if level_index == 0:
            return True  # Level đầu tiên luôn mở
        return level_index in self.completed_levels or level_index <= self.get_max_unlocked_level()


class FoodCard(models.Model):
    """
    Thẻ món ăn dùng cho album Food Map Journey.
    Mỗi card gắn với 1 level trong mini game.
    """
    level_index = models.IntegerField(unique=True)  # level tương ứng (0,1,2,3,...)
    district = models.CharField(max_length=100)     # VD: "Quận 1"
    food_name = models.CharField(max_length=100)    # VD: "Phở"
    icon = models.CharField(max_length=10, blank=True, null=True)  # emoji: 🍜, 🥖,...
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Level {self.level_index} - {self.district} - {self.food_name}"
