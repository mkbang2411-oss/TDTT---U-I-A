from django.contrib.auth import get_user_model
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.core.exceptions import ImmediateHttpResponse
import logging

# Thiết lập logger cho file này
logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter tùy chỉnh để kiểm tra email đã verify OTP chưa 
    trước khi cho phép đăng ký tài khoản (dùng session 'verified_email').
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Override hàm save_user của allauth.
        Kiểm tra email đã verify chưa trước khi tạo tài khoản, 
        và gửi email chào mừng sau khi tạo.
        """
        from django.core.exceptions import ValidationError
        from .utils import send_welcome_email
        from datetime import timedelta
        from dateutil import parser
        from django.conf import settings
        
        # Lấy email đã verify từ session
        verified_email = request.session.get('verified_email')
        verified_at = request.session.get('email_verified_at')
        
        # Lấy email từ form đăng ký và chuẩn hóa
        form_email = form.cleaned_data.get('email', '').strip().lower()
        
        # --- BƯỚC 1: KIỂM TRA XÁC THỰC OTP ---
        # Kiểm tra email trong form có khớp với email đã verify không
        if not verified_email or form_email != verified_email:
            logger.warning(
                f"Đăng ký thất bại: Email '{form_email}' không khớp với email đã verify trong session: '{verified_email}'"
            )
            # Clear session và raise ValidationError
            request.session.flush()
            raise ValidationError(
                '⚠️ Email chưa được xác thực OTP. Vui lòng xác thực email trước khi đăng ký!'
            )
        
        # Kiểm tra timeout verification
        if verified_at:
            try:
                from django.utils import timezone
                verified_time = parser.parse(verified_at)
                if timezone.now() - verified_time > timedelta(minutes=getattr(settings, 'OTP_SESSION_TIMEOUT_MINUTES', 30)):
                    request.session.flush()
                    raise ValidationError(
                        '⚠️ Phiên xác thực đã hết hạn. Vui lòng xác thực lại email.'
                    )
            except Exception as e:
                logger.error(f"Error checking verification timeout: {e}")
        
        # --- BƯỚC 2: TẠO TÀI KHOẢN GỐC ---
        # Gọi hàm save_user gốc của DefaultAccountAdapter
        user = super().save_user(request, user, form, commit=False)
        
        if commit:
            user.save()
            
            # --- BƯỚC 3: GỬI EMAIL CHÀO MỪNG ---
            try:
                send_welcome_email(user.email, user.username)
                logger.info(f"Đã gửi email chào mừng thành công cho user: {user.email}")
            except Exception as e:
                # Log lỗi chi tiết thay vì chỉ in ra console
                logger.error(f"⚠️ Không gửi được email chào mừng cho {user.email}: {e}")
            
            # --- BƯỚC 4: THÊM THÔNG BÁO THÀNH CÔNG ---
            messages.success(
                request,
                '🎉 Đăng ký thành công! Chào mừng bạn đến với UIA Food. Vui lòng đăng nhập để tiếp tục.'
            )
            
            # --- BƯỚC 5: XÓA TOÀN BỘ SESSION ĐỂ TRÁNH VÒNG LẶP ---
            # Xóa TẤT CẢ session data liên quan đến signup
            request.session.pop('verified_email', None)
            request.session.pop('email_verified_at', None)
            request.session.pop('otp_email', None)
            request.session.pop('otp_sent_at', None)
            # Force save session
            request.session.modified = True
            logger.info(f"Đã xóa toàn bộ session verify cho user: {user.email}")

        return user
    
    def get_signup_redirect_url(self, request):
        """
        Sau khi đăng ký thành công, redirect về trang đăng nhập
        """
        return reverse('account_login')
    
    def is_open_for_signup(self, request):
        """
        Kiểm tra có cho phép đăng ký không. 
        Mặc định là True, logic kiểm tra OTP đã được chuyển vào save_user.
        """
        # Trả về True vì logic kiểm tra email đã được đưa vào save_user.
        return True
    
    def authentication_failed(self, request, **credentials):
        """
        Override để custom thông báo lỗi khi đăng nhập thất bại
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Lấy email/username từ credentials
        login = credentials.get('username') or credentials.get('email')
        
        if login:
            # Kiểm tra xem user có tồn tại không
            try:
                User.objects.get(email__iexact=login)
                # User tồn tại -> lỗi là mật khẩu sai
                from django.core.exceptions import ValidationError
                raise ValidationError('Mật khẩu không chính xác')
            except User.DoesNotExist:
                # User không tồn tại
                from django.core.exceptions import ValidationError
                raise ValidationError('Không tìm thấy người dùng với email này')
        
        # Fallback về message mặc định
        super().authentication_failed(request, **credentials)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    # Bỏ qua form signup trung gian, tự động tạo tài khoản
    def is_auto_signup(self, request, sociallogin):
        return True

    # Xử lý trường hợp email đã có user trong hệ thống
    def pre_social_login(self, request, sociallogin):
        email = (sociallogin.user.email or "").strip()
        if not email:
            return  # Không có email thì để allauth xử lý bình thường

        User = get_user_model()
        try:
            existing_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return  # Không có user trùng email -> cho qua để auto signup

        # Nếu social account đã liên kết với user này rồi -> cho đăng nhập bình thường
        if SocialAccount.objects.filter(user=existing_user, provider=sociallogin.account.provider).exists():
            return

        # Nếu email đã tồn tại nhưng chưa liên kết Google -> hiển thị trang thông báo thân thiện
        url = reverse('social_account_already_exists')
        raise ImmediateHttpResponse(redirect(url))
