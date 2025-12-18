from django.db import models
from django.conf import settings 
from django.contrib.auth.models import User
from django.utils import timezone

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
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
class SharedFoodPlan(models.Model):
    """
    Model theo dõi việc share plan giữa các user
    """
    PERMISSION_CHOICES = [
        ('view', 'Chỉ xem'),
        ('edit', 'Xem và chỉnh sửa'),
    ]
    
    food_plan = models.ForeignKey('FoodPlan', on_delete=models.CASCADE, related_name='shares')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_plans_as_owner')
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_shared_plans')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='edit')
    shared_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Có thể revoke share
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('food_plan', 'shared_with')
        ordering = ['-shared_at']
    
    def __str__(self):
        return f"{self.owner.username} shared '{self.food_plan.name}' with {self.shared_with.username}"


class PlanEditSuggestion(models.Model):
    """
    Model lưu các thay đổi mà bạn bè đề xuất
    """
    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('accepted', 'Đã chấp nhận'),
        ('rejected', 'Đã từ chối'),
    ]
    
    shared_plan = models.ForeignKey('SharedFoodPlan', on_delete=models.CASCADE, related_name='suggestions')
    suggested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Lưu dữ liệu plan cũ và mới
    original_data = models.JSONField()  # Plan gốc trước khi edit
    suggested_data = models.JSONField()  # Plan sau khi edit
    
    # 🔥 THÊM DÒNG NÀY
    pending_changes = models.JSONField(default=dict, blank=True)  # Lưu trạng thái các thay đổi đã chọn
    
    # Metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)  # Lời nhắn kèm theo suggestion
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Suggestion by {self.suggested_by.username} - {self.status}"           
    
class UserPreference(models.Model):
    """
    Lưu sở thích ăn uống của user (likes/dislikes/allergies)
    """
    PREFERENCE_TYPES = [
        ('like', 'Thích'),
        ('dislike', 'Không thích'),
        ('allergy', 'Dị ứng'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='food_preferences')
    preference_type = models.CharField(max_length=20, choices=PREFERENCE_TYPES)
    item = models.CharField(max_length=200)  # Tên món/nguyên liệu
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'preference_type', 'item')  # Tránh trùng lặp
        ordering = ['-created_at']
    
    def __str__(self):
        type_icon = {'like': '❤️', 'dislike': '❌', 'allergy': '⚠️'}
        return f"{type_icon.get(self.preference_type, '')} {self.user.username} - {self.item}"

# ==========================================================
# 🔔 NOTIFICATION SYSTEM
# ==========================================================

class Notification(models.Model):
    """
    Model lưu trữ thông báo cho user
    """
    NOTIFICATION_TYPES = (
        ('friend_request', 'Lời mời kết bạn'),
        ('shared_plan', 'Plan được chia sẻ'),
        ('suggestion', 'Đề xuất mới'),
    )
    
    # User nhận thông báo
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # Loại thông báo
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES
    )
    
    # Nội dung thông báo
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Trạng thái đã đọc
    is_read = models.BooleanField(default=False)
    
    # Thời gian
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Link tới đối tượng liên quan (tùy chọn)
    related_id = models.IntegerField(null=True, blank=True)  # ID của plan, friend request, etc.
    
    # Metadata JSON (lưu thêm thông tin nếu cần)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']  # Mới nhất lên đầu
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title} - {'Đã đọc' if self.is_read else 'Chưa đọc'}"
    
    def mark_as_read(self):
        """Đánh dấu đã đọc"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class StreakPopupLog(models.Model):
    """
    Lưu lịch sử hiển thị popup streak frozen
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streak_popups')
    popup_type = models.CharField(max_length=20, default='frozen')  # frozen/milestone
    shown_at = models.DateTimeField(auto_now_add=True)
    streak_value = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-shown_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.popup_type} popup at {self.shown_at}"

class ReviewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place_id = models.CharField(max_length=255)
    review_date = models.DateTimeField(default=timezone.now)
    rating = models.IntegerField()
    comment = models.TextField()
    
    class Meta:
        db_table = 'review_history'
        indexes = [
            models.Index(fields=['user', 'place_id']),
            models.Index(fields=['user', 'review_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.place_id} - {self.review_date}"    
    
class NotificationDelayMetric(models.Model):
    """Lưu thời gian delay của notifications"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delay_metrics')
    sent_at = models.DateTimeField()
    received_at = models.DateTimeField()
    delay_ms = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_session = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']

class FriendRequestDelayMetric(models.Model):
    """Lưu metrics delay cho các thao tác kết bạn"""
    ACTION_CHOICES = [
        ('send', 'Send Friend Request'),
        ('cancel', 'Cancel Request'),
        ('accept', 'Accept Request'),
        ('reject', 'Reject Request'),
        ('unfriend', 'Unfriend'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_request_metrics')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_request_targets')
    
    sent_at = models.DateTimeField()
    received_at = models.DateTimeField()
    delay_ms = models.IntegerField()
    
    test_session = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'test_session']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.delay_ms}ms"