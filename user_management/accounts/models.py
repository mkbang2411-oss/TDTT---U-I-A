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
    
class EmailOTP(models.Model):
    """
    Model lưu mã OTP gửi về email
    """
    MAX_ATTEMPTS = 5  # Số lần thử tối đa
    
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)  # Số lần thử sai
    is_locked = models.BooleanField(default=False)  # Khóa sau nhiều lần thử sai
    
    class Meta:
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.otp_code}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_verified and not self.is_locked and self.expires_at > timezone.now()
    
    def mark_as_verified(self):
        self.is_verified = True
        self.save()
    
    def increment_attempts(self):
        """Tăng số lần thử và khóa nếu vượt quá giới hạn"""
        self.attempts += 1
        if self.attempts >= self.MAX_ATTEMPTS:
            self.is_locked = True
        self.save()
        return self.attempts
    
    @staticmethod
    def cleanup_expired():
        from django.utils import timezone
        EmailOTP.objects.filter(expires_at__lt=timezone.now()).delete()
    
    @classmethod
    def generate_otp(cls, email):
        import random
        from datetime import timedelta
        from django.utils import timezone
        
        # Xóa OTP cũ của email này
        cls.objects.filter(email=email).delete()
        
        # Tạo OTP 6 số
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Thời gian hết hạn: 5 phút
        expires_at = timezone.now() + timedelta(minutes=5)
        
        # Tạo record mới
        otp = cls.objects.create(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        return otp


class PasswordResetOTP(models.Model):
    """
    Model lưu mã OTP cho reset password
    """
    MAX_ATTEMPTS = 5
    
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Password Reset OTP"
        verbose_name_plural = "Password Reset OTPs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - Reset OTP - {self.otp_code}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_verified and not self.is_locked and self.expires_at > timezone.now()
    
    def mark_as_verified(self):
        self.is_verified = True
        self.save()
    
    def increment_attempts(self):
        self.attempts += 1
        if self.attempts >= self.MAX_ATTEMPTS:
            self.is_locked = True
        self.save()
        return self.attempts
    
    @classmethod
    def generate_otp(cls, email):
        import random
        from datetime import timedelta
        from django.utils import timezone
        
        # Xóa OTP cũ của email này
        cls.objects.filter(email=email).delete()
        
        # Tạo OTP 6 số
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Thời gian hết hạn: 5 phút
        expires_at = timezone.now() + timedelta(minutes=5)
        
        # Tạo record mới
        otp = cls.objects.create(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        return otp
    
class FoodPlan(models.Model):
    """
    Model để lưu lịch trình ăn uống của user
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default="Lịch trình ăn uống")
    plan_data = models.JSONField()  # Lưu toàn bộ danh sách quán ăn dưới dạng JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"