from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, otp_code):
    """
    Gửi mã OTP qua email
    
    Args:
        email (str): Email người nhận
        otp_code (str): Mã OTP 6 số
    
    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    subject = '🔐 Mã OTP xác thực tài khoản UIA Food'
    
    # Template HTML cho email
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #BC2A12 0%, #E63B21 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .otp-box {{
                background: #f9f9f9;
                border: 2px dashed #BC2A12;
                border-radius: 10px;
                padding: 25px;
                margin: 30px 0;
            }}
            .otp-code {{
                font-size: 42px;
                font-weight: bold;
                color: #BC2A12;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .warning {{
                background: #FFF3CD;
                border-left: 4px solid #FFC107;
                padding: 15px;
                margin: 20px 0;
                text-align: left;
            }}
            .footer {{
                background: #f9f9f9;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🍜 UIA Food - Find Food Find Us</h1>
                <p>Xác thực tài khoản của bạn</p>
            </div>
            
            <div class="content">
                <h2>Xin chào!</h2>
                <p>Cảm ơn bạn đã đăng ký tài khoản tại <strong>UIA Food</strong>.</p>
                <p>Để hoàn tất quá trình đăng ký, vui lòng nhập mã OTP bên dưới:</p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #666;">Mã OTP của bạn</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Lưu ý quan trọng:</strong>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>Mã OTP có hiệu lực trong <strong>5 phút</strong></li>
                        <li>Không chia sẻ mã này với bất kỳ ai</li>
                        <li>Nếu bạn không thực hiện đăng ký, vui lòng bỏ qua email này</li>
                    </ul>
                </div>
                
                <p style="color: #999; font-size: 14px; margin-top: 30px;">
                    Nếu bạn gặp vấn đề, vui lòng liên hệ bộ phận hỗ trợ.
                </p>
            </div>
            
            <div class="footer">
                <p>© 2025 UIA Food - Find Food Find Us</p>
                <p>Email này được gửi tự động, vui lòng không trả lời.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version (fallback)
    plain_message = f"""
    Xin chào!
    
    Cảm ơn bạn đã đăng ký tài khoản tại UIA Food.
    
    Mã OTP của bạn là: {otp_code}
    
    Mã này có hiệu lực trong 5 phút.
    Vui lòng không chia sẻ mã này với bất kỳ ai.
    
    Nếu bạn không thực hiện đăng ký, vui lòng bỏ qua email này.
    
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
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #BC2A12 0%, #E63B21 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .feature-box {{
                background: #f9f9f9;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }}
            .feature-box h3 {{
                color: #BC2A12;
                margin-top: 0;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #BC2A12 0%, #E63B21 100%);
                color: white;
                padding: 15px 40px;
                border-radius: 25px;
                text-decoration: none;
                font-weight: bold;
                margin: 20px 0;
            }}
            .footer {{
                background: #f9f9f9;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Chào mừng đến với UIA Food!</h1>
                <p style="font-size: 18px; margin: 10px 0 0 0;">Find Food Find Us</p>
            </div>
            
            <div class="content">
                <h2>Xin chào {username}!</h2>
                <p>Chúc mừng bạn đã tạo tài khoản thành công tại <strong>UIA Food</strong>!</p>
                
                <div class="feature-box">
                    <h3>🗺️ Khám phá địa điểm ăn uống</h3>
                    <p>Tìm kiếm hàng ngàn quán ăn ngon khắp thành phố với bản đồ tương tác.</p>
                </div>
                
                <div class="feature-box">
                    <h3>🤖 Chatbot AI thông minh</h3>
                    <p>Trò chuyện với AI để nhận gợi ý món ăn phù hợp với sở thích của bạn.</p>
                </div>
                
                <div class="feature-box">
                    <h3>⭐ Đánh giá & Chia sẻ</h3>
                    <p>Lưu quán yêu thích, viết review và chia sẻ trải nghiệm ăn uống.</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="http://127.0.0.1:8000/" class="cta-button">Bắt đầu khám phá ngay!</a>
                </div>
                
                <p style="color: #999; font-size: 14px; margin-top: 40px;">
                    Nếu bạn cần hỗ trợ, đừng ngần ngại liên hệ với chúng tôi!
                </p>
            </div>
            
            <div class="footer">
                <p>© 2025 UIA Food - Find Food Find Us</p>
                <p>Email này được gửi tự động, vui lòng không trả lời.</p>
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
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #BC2A12 0%, #E63B21 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .otp-box {{
                background: #f9f9f9;
                border: 2px dashed #BC2A12;
                border-radius: 10px;
                padding: 25px;
                margin: 30px 0;
            }}
            .otp-code {{
                font-size: 42px;
                font-weight: bold;
                color: #BC2A12;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .warning {{
                background: #FFF3CD;
                border-left: 4px solid #FFC107;
                padding: 15px;
                margin: 20px 0;
                text-align: left;
            }}
            .footer {{
                background: #f9f9f9;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔑 Khôi phục mật khẩu</h1>
                <p>UIA Food - Find Food Find Us</p>
            </div>
            
            <div class="content">
                <h2>Yêu cầu khôi phục mật khẩu</h2>
                <p>Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản của bạn.</p>
                <p>Để tiếp tục, vui lòng nhập mã OTP bên dưới:</p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #666;">Mã OTP của bạn</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Lưu ý quan trọng:</strong>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>Mã OTP có hiệu lực trong <strong>5 phút</strong></li>
                        <li>Không chia sẻ mã này với bất kỳ ai</li>
                        <li>Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email</li>
                        <li>Vì lý do bảo mật, hãy đổi mật khẩu ngay nếu bạn nghi ngờ tài khoản bị xâm nhập</li>
                    </ul>
                </div>
                
                <p style="color: #999; font-size: 14px; margin-top: 30px;">
                    Nếu bạn gặp vấn đề, vui lòng liên hệ bộ phận hỗ trợ.
                </p>
            </div>
            
            <div class="footer">
                <p>© 2025 UIA Food - Find Food Find Us</p>
                <p>Email này được gửi tự động, vui lòng không trả lời.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Yêu cầu khôi phục mật khẩu
    
    Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản của bạn.
    
    Mã OTP của bạn là: {otp_code}
    
    Mã này có hiệu lực trong 5 phút.
    Vui lòng không chia sẻ mã này với bất kỳ ai.
    
    Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.
    
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
