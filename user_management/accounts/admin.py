from django.contrib import admin
from .models import (
    ChatConversation, 
    ChatMessage,
    UserProfile,
    FavoritePlace,
    EmailOTP
)

# Đăng ký các model
admin.site.register(ChatConversation)
admin.site.register(ChatMessage)
admin.site.register(UserProfile)
admin.site.register(FavoritePlace)

# ==========================================
# 📧 ĐĂNG KÝ MODEL EMAIL OTP
# ==========================================
@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp_code', 'created_at', 'expires_at', 'is_verified', 'attempts']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email', 'otp_code']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """Không cho phép thêm OTP thủ công từ admin"""
        return False