from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from .signals import sse_connections
import queue
import json

def send_otp_email(email, otp_code):
    """
    Gửi mã OTP qua email xác thực tài khoản

    Args:
        email (str): Email người nhận
        otp_code (str): Mã OTP 6 số

    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    subject = '🔐 Mã OTP xác thực tài khoản UIA Food'

    background_url = 'https://res.cloudinary.com/dbmq2hme4/image/upload/v1764926423/disc_covers/mail.png'

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Mã OTP xác thực tài khoản UIA Food</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                margin: 0;
                padding: 0;
                background-color: #e5e5e5;
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 500;
                min-height: 100% !important;
                height: 100% !important;
            }}

            .email-container {{
                max-width: 850px;
                margin: 0 auto;
                background-color: #f5f5f5;
                padding: 40px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}

            .email-bg {{
                width: 100%;
                max-width: 595px;
                margin: 0 auto;
                background-image: url('{background_url}');
                background-repeat: no-repeat;
                background-position: center center;
                background-size: 100% 100%;
                position: relative;
                min-height: 842px;
                display: flex;
                align-items: flex-start;
                justify-content: center;
            }}

            .content-wrapper {{
                width: 100%;
                height: 100%;
                padding: 200px 60px 80px 60px;
                display: flex;
                justify-content: center;
                align-items: flex-start;
            }}

            .content {{
                max-width: 100%;
                width: 100%;
                color: #fff4bf;
                line-height: 1.9;
                text-align: justify;
                text-justify: inter-word;
                font-size: 15px;
                white-space: normal;
                word-wrap: break-word;
                display: block !important;
                max-height: none !important;
                overflow: visible !important;
            }}

            .content p {{
                margin: 0 0 16px 0;
                font-size: 15px;
                display: block !important;
                max-height: none !important;
                overflow: visible !important;
            }}

            .content p:last-child {{
                margin-bottom: 0;
            }}

            .content strong {{
                font-weight: 600;
            }}

            .otp-code {{
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 2px;
            }}

            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 0;
                }}
                
                .email-container {{
                    padding: 20px;
                }}

                .email-bg {{
                    min-height: 600px;
                }}
                
                .content-wrapper {{
                    padding: 160px 40px 60px 40px;
                }}
                
                .content {{
                    font-size: 13px;
                }}
                
                .content p {{
                    font-size: 13px;
                    margin-bottom: 14px;
                }}
                
                .otp-code {{
                    font-size: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-bg">
                <div class="content-wrapper">
                    <div class="content">
                        <p>Kính gửi Quý khách,</p>

                        <p>
                            Hệ thống <strong>UIA Food</strong> xin thông báo mã OTP xác minh tài khoản của Quý khách là: 
                            <span class="otp-code">{otp_code}</span>.
                        </p>

                        <p>
                            Vui lòng sử dụng mã này để hoàn tất quy trình xác thực. Mã OTP sẽ hết hạn sau 
                            <strong>5 phút</strong>.
                        </p>

                        <p>
                            Quý khách vui lòng không cung cấp mã OTP cho bất kỳ ai nhằm đảm bảo an toàn thông tin.
                        </p>

                        <p>
                            Nếu Quý khách không yêu cầu mã OTP, vui lòng bỏ qua thông điệp này hoặc liên hệ với bộ phận 
                            hỗ trợ của chúng tôi để được trợ giúp.
                        </p>

                        <p style="margin-top: 24px;">
                            Trân trọng,<br/>
                            Đội ngũ UIA Food
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
    Kính gửi Quý khách,

    Hệ thống UIA Food xin thông báo mã OTP xác minh tài khoản của Quý khách là: {otp_code}.

    Mã có hiệu lực trong 5 phút.
    Vui lòng không chia sẻ mã này với bất kỳ ai.

    Nếu Quý khách không yêu cầu mã OTP, vui lòng bỏ qua email này.

    Trân trọng,
    Đội ngũ UIA Food
    """

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False


def send_welcome_email(email, username):
    """
    Gửi email chào mừng sau khi xác thực thành công

    Args:
        email (str): Email người nhận
        username (str): Tên người dùng

    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    subject = '🎉 Chào mừng bạn đến với UIA Food!'

    background_url = 'https://res.cloudinary.com/dbmq2hme4/image/upload/v1764926423/disc_covers/mail.png'

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Chào mừng bạn đến với UIA Food</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                margin: 0;
                padding: 0;
                background-color: #e5e5e5;
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 500;
                min-height: 100% !important;
                height: 100% !important;
            }}

            .email-container {{
                max-width: 850px;
                margin: 0 auto;
                background-color: #f5f5f5;
                padding: 40px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}

            .email-bg {{
                width: 100%;
                max-width: 595px;
                margin: 0 auto;
                background-image: url('{background_url}');
                background-repeat: no-repeat;
                background-position: center center;
                background-size: 100% 100%;
                position: relative;
                min-height: 842px;
                display: flex;
                align-items: flex-start;
                justify-content: center;
            }}

            .content-wrapper {{
                width: 100%;
                height: 100%;
                padding: 200px 60px 80px 60px;
                display: flex;
                justify-content: center;
                align-items: flex-start;
            }}

            .content {{
                max-width: 100%;
                width: 100%;
                color: #fff4bf;
                line-height: 1.9;
                text-align: justify;
                text-justify: inter-word;
                font-size: 15px;
                white-space: normal;
                word-wrap: break-word;
                display: block !important;
                max-height: none !important;
                overflow: visible !important;
            }}

            .content p {{
                margin: 0 0 16px 0;
                font-size: 15px;
                display: block !important;
                max-height: none !important;
                overflow: visible !important;
            }}

            .content p:last-child {{
                margin-bottom: 0;
            }}

            .content strong {{
                font-weight: 600;
            }}

            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 0;
                }}
                
                .email-container {{
                    padding: 20px;
                }}

                .email-bg {{
                    min-height: 600px;
                }}
                
                .content-wrapper {{
                    padding: 160px 40px 60px 40px;
                }}
                
                .content {{
                    font-size: 13px;
                }}
                
                .content p {{
                    font-size: 13px;
                    margin-bottom: 14px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-bg">
                <div class="content-wrapper">
                    <div class="content">
                        <p>Xin chào <strong>{username}</strong>!</p>

                        <p>
                            Chúc mừng bạn đã tạo tài khoản thành công tại <strong>UIA Food</strong> - nền tảng tìm kiếm và khám phá ẩm thực hàng đầu!
                        </p>

                        <p>
                            <strong>UIA Food</strong> là hệ thống hỗ trợ tìm kiếm quán ăn thông minh, được thiết kế đặc biệt để giúp bạn khám phá hàng ngàn quán ăn.
                        </p>

                        <p>
                            Hệ thống <strong>Chatbot AI</strong> của chúng tôi hoạt động 24/24, luôn sẵn sàng hỗ trợ bạn tìm kiếm quán ăn phù hợp với khẩu vị, ngân sách và nhu cầu của bạn.
                        </p>

                        <p>
                            Hãy bắt đầu hành trình khám phá ẩm thực của bạn cùng <strong>UIA Food</strong> ngay hôm nay!
                        </p>

                        <p style="margin-top: 24px;">
                            Trân trọng,<br/>
                            Đội ngũ UIA Food
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
    Xin chào {username}!

    Chúc mừng bạn đã tạo tài khoản thành công tại UIA Food!

    Khám phá ngay:
    - Bản đồ địa điểm ăn uống
    - Chatbot AI thông minh
    - Đánh giá & Lưu quán yêu thích

    Truy cập: http://127.0.0.1:8000/

    Trân trọng,
    Đội ngũ UIA Food
    """

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Lỗi gửi email chào mừng: {e}")
        return False


def send_password_reset_otp_email(email, otp_code):
    """
    Gửi mã OTP để reset password qua email

    Args:
        email (str): Email người nhận
        otp_code (str): Mã OTP 6 số

    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    subject = '🔑 Mã OTP khôi phục mật khẩu - UIA Food'

    background_url = 'https://res.cloudinary.com/dbmq2hme4/image/upload/v1764926423/disc_covers/mail.png'

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Mã OTP khôi phục mật khẩu - UIA Food</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                margin: 0;
                padding: 0;
                background-color: #e5e5e5;
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 500;
                min-height: 100% !important;
                height: 100% !important;
            }}

            .email-container {{
                max-width: 850px;
                margin: 0 auto;
                background-color: #f5f5f5;
                padding: 40px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}

            .email-bg {{
                width: 100%;
                max-width: 595px;
                margin: 0 auto;
                background-image: url('{background_url}');
                background-repeat: no-repeat;
                background-position: center center;
                background-size: 100% 100%;
                position: relative;
                min-height: 842px;
                display: flex;
                align-items: flex-start;
                justify-content: center;
            }}

            .content-wrapper {{
                width: 100%;
                height: 100%;
                padding: 200px 60px 80px 60px;
                display: flex;
                justify-content: center;
                align-items: flex-start;
            }}

            .content {{
                max-width: 100%;
                width: 100%;
                color: #fff4bf;
                line-height: 1.9;
                text-align: justify;
                text-justify: inter-word;
                font-size: 15px;
                white-space: normal;
                word-wrap: break-word;
                display: block !important;
                max-height: none !important;
                overflow: visible !important;
            }}

            .content p {{
                margin: 0 0 16px 0;
                font-size: 15px;
                display: block !important;
                max-height: none !important;
                overflow: visible !important;
            }}

            .content p:last-child {{
                margin-bottom: 0;
            }}

            .content strong {{
                font-weight: 600;
            }}

            .otp-code {{
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 2px;
            }}

            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 0;
                }}
                
                .email-container {{
                    padding: 20px;
                }}

                .email-bg {{
                    min-height: 600px;
                }}
                
                .content-wrapper {{
                    padding: 160px 40px 60px 40px;
                }}
                
                .content {{
                    font-size: 13px;
                }}
                
                .content p {{
                    font-size: 13px;
                    margin-bottom: 14px;
                }}
                
                .otp-code {{
                    font-size: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-bg">
                <div class="content-wrapper">
                    <div class="content">
                        <p>Kính gửi Quý khách,</p>

                        <p>
                            Hệ thống <strong>UIA Food</strong> nhận được yêu cầu khôi phục mật khẩu cho tài khoản của Quý khách. 
                            Mã OTP khôi phục mật khẩu của Quý khách là: <span class="otp-code">{otp_code}</span>.
                        </p>

                        <p>
                            Vui lòng sử dụng mã này để tiếp tục quy trình khôi phục mật khẩu. Mã OTP sẽ hết hạn sau 
                            <strong>5 phút</strong>.
                        </p>

                        <p>
                            Quý khách vui lòng không cung cấp mã OTP cho bất kỳ ai nhằm đảm bảo an toàn thông tin.
                        </p>

                        <p>
                            Nếu Quý khách không thực hiện yêu cầu khôi phục mật khẩu, vui lòng bỏ qua thông điệp này.
                        </p>

                        <p style="margin-top: 24px;">
                            Trân trọng,<br/>
                            Đội ngũ UIA Food
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
    Kính gửi Quý khách,

    Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản UIA Food của Quý khách.

    Mã OTP khôi phục mật khẩu của Quý khách là: {otp_code}.

    Mã có hiệu lực trong 5 phút.
    Vui lòng không chia sẻ mã này với bất kỳ ai.

    Nếu Quý khách không thực hiện yêu cầu này, vui lòng bỏ qua email.

    Trân trọng,
    Đội ngũ UIA Food
    """

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Lỗi gửi email reset password: {e}")
        return False
    
def create_friend_request_notification(receiver_user, sender_user, request_id):
    """
    Tạo thông báo lời mời kết bạn
    """
    return Notification.objects.create(
        user=receiver_user,
        notification_type='friend_request',
        title='Lời mời kết bạn',
        message=f'{sender_user.username} đã gửi lời mời kết bạn cho bạn',
        related_id=request_id,
        metadata={
            'sender_id': sender_user.id,
            'sender_username': sender_user.username,
            'request_id': request_id
        }
    )


def create_shared_plan_notification(receiver_user, owner_user, plan_id, plan_name):
    """
    Tạo thông báo plan được share
    """
    return Notification.objects.create(
        user=receiver_user,
        notification_type='shared_plan',
        title='Plan được chia sẻ',
        message=f'{owner_user.username} đã share plan "{plan_name}" cho bạn',
        related_id=plan_id,
        metadata={
            'owner_id': owner_user.id,
            'owner_username': owner_user.username,
            'plan_id': plan_id,
            'plan_name': plan_name
        }
    )


def create_suggestion_notification(receiver_user, suggester_user, plan_id, plan_name):
    """
    Tạo thông báo đề xuất mới
    """
    return Notification.objects.create(
        user=receiver_user,
        notification_type='suggestion',
        title='Đề xuất mới',
        message=f'{suggester_user.username} đã đề xuất chỉnh sửa plan "{plan_name}"',
        related_id=plan_id,
        metadata={
            'suggester_id': suggester_user.id,
            'suggester_username': suggester_user.username,
            'plan_id': plan_id,
            'plan_name': plan_name
        }
    )


def mark_notifications_as_read(user, notification_type=None, related_id=None):
    """
    Đánh dấu thông báo đã đọc
    """
    queryset = Notification.objects.filter(user=user, is_read=False)
    
    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    
    if related_id:
        queryset = queryset.filter(related_id=related_id)
    
    return queryset.update(is_read=True)

def create_suggestion_approved_notification(user, owner_username, plan_id, plan_name, suggestion_id):
    """
    Tạo thông báo khi owner chấp nhận đề xuất
    
    Args:
        user: User nhận thông báo (người đã đề xuất)
        owner_username: Tên chủ sở hữu plan
        plan_id: ID của plan
        plan_name: Tên plan
        suggestion_id: ID của suggestion (để link tới)
    """
    
    notification = Notification.objects.create(
        user=user,
        notification_type='suggestion_approved',
        title='Đề xuất được chấp nhận',
        message=f'{owner_username} đã chấp nhận đề xuất của bạn cho plan "{plan_name}"',
        related_id=plan_id,
        metadata={
            'suggestion_id': suggestion_id,
            'owner_username': owner_username
        }
    )
    
    # Push SSE
    if user.id in sse_connections:
        try:
            notification_data = {
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'related_id': notification.related_id,
                'metadata': notification.metadata
            }
            sse_connections[user.id].put(notification_data)
            print(f"✅ Pushed suggestion_approved notification to user {user.username}")
        except queue.Full:
            print(f"⚠️ Queue full for user {user.id}")
    
    return notification

def create_suggestion_rejected_notification(user, owner_username, plan_id, plan_name, suggestion_id):
    """
    Tạo thông báo khi owner từ chối đề xuất
    
    Args:
        user: User nhận thông báo (người đã đề xuất)
        owner_username: Tên chủ sở hữu plan
        plan_id: ID của plan
        plan_name: Tên plan
        suggestion_id: ID của suggestion (để link tới)
    """
    
    notification = Notification.objects.create(
        user=user,
        notification_type='suggestion_rejected',
        title='Đề xuất bị từ chối',
        message=f'{owner_username} đã từ chối đề xuất của bạn cho plan "{plan_name}"',
        related_id=plan_id,
        metadata={
            'suggestion_id': suggestion_id,
            'owner_username': owner_username
        }
    )
    
    # Push SSE
    if user.id in sse_connections:
        try:
            notification_data = {
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'related_id': notification.related_id,
                'metadata': notification.metadata
            }
            sse_connections[user.id].put(notification_data)
            print(f"✅ Pushed suggestion_rejected notification to user {user.username}")
        except queue.Full:
            print(f"⚠️ Queue full for user {user.id}")
    
    return notification