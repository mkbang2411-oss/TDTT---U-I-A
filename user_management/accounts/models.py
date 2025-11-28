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

    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)
    streak_frozen = models.BooleanField(default=False)

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
    
class PuzzleProgress(models.Model):
    """
    Lưu tiến độ hoàn thành puzzle của user
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='puzzle_progress')
    map_name = models.CharField(max_length=50)  # 'banh_mi', 'com_tam', 'bun_bo_hue'
    completed = models.BooleanField(default=False)
    completion_time = models.IntegerField(null=True, blank=True)  # Thời gian hoàn thành (giây)
    moves_count = models.IntegerField(null=True, blank=True)  # Số bước di chuyển
    completed_at = models.DateTimeField(auto_now=True)  # Lần hoàn thành gần nhất

    class Meta:
        unique_together = ('user', 'map_name')
        ordering = ['-completed_at']

    def __str__(self):
        status = "✅" if self.completed else "⏳"
        return f"{status} {self.user.username} - {self.map_name}"

class FoodStory(models.Model):
    """
    Lưu thông tin câu chuyện/lịch sử của món ăn
    """
    map_name = models.CharField(max_length=50, unique=True)  # 'banh_mi', 'com_tam', 'bun_bo_hue'
    title = models.CharField(max_length=200)  # "Bánh Mì - Hương Vị Đặc Trưng Việt Nam"
    description = models.TextField()  # Mô tả ngắn
    
    # Nội dung chính
    history = models.TextField()  # Lịch sử hình thành
    fun_facts = models.JSONField(default=list)  # List các fun facts ['fact1', 'fact2']
    variants = models.JSONField(default=list)  # Các biến thể ['Bánh mì pate', 'Bánh mì thit nuong']
    origin_region = models.CharField(max_length=100)  # "Miền Nam" / "Huế"
    
    # Media
    image_url = models.CharField(max_length=500, blank=True)
    video_url = models.CharField(max_length=500, blank=True)
    
    # UNESCO Recognition (optional)
    unesco_recognized = models.BooleanField(default=False)
    recognition_text = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"📖 {self.title}"


class UnlockedStory(models.Model):
    """
    Theo dõi story nào user đã unlock
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_stories')
    story = models.ForeignKey(FoodStory, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'story')
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"✅ {self.user.username} - {self.story.title}"