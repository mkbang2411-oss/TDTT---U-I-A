from django.core.mail import send_mail
from django.conf import settings


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

    # Lưu ý:
    # - Với email HTML, ảnh nền phải là URL public (http/https), KHÔNG dùng đường dẫn ổ đĩa kiểu D:\...
    # - Hãy upload file mail.png (A4) lên static/server và thay URL bên dưới cho đúng.
    background_url = 'https://res.cloudinary.com/dbmq2hme4/image/upload/v1764926423/disc_covers/mail.png'

    # Template HTML cho email OTP (nền A4, font Poppins, màu #fff4bf)
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
            }}

            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 500;
            }}

            /* Nền A4 */
            .email-bg {{
                width: 100%;
                min-height: 100vh;
                background-image: url('{background_url}');
                background-repeat: no-repeat;
                background-position: center top;
                background-size: cover;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0;
            }}

            /* Block chữ nằm giữa, padding đều 4 phía */
            .content-wrapper {{
                max-width: 800px;
                width: 100%;
                padding: 64px;
                color: #fff4bf;
                display: flex;
                justify-content: center;
            }}

            .content {{
                max-width: 520px;
                margin: 0 auto;
                color: #fff4bf;
                line-height: 1.7;
                text-align: left;
            }}

            .content p {{
                margin: 0 0 12px 0;
            }}

            .content p:last-child {{
                margin-bottom: 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-bg">
            <div class="content-wrapper">
                <div class="content">
                    <p>Kính gửi Quý khách,</p>

                    <p>
                        Hệ thống <strong>UIA Food</strong> xin thông báo mã OTP xác minh tài khoản của Quý khách là:
                        <strong>{otp_code}</strong>.
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
    </body>
    </html>
    """

    # Plain text version (fallback)
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
                    <h3>⭐ Đánh giá &amp; Chia sẻ</h3>
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

    # Dùng cùng layout nền A4 như mail OTP đăng ký
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
            }}

            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 500;
            }}

            .email-bg {{
                width: 100%;
                min-height: 100vh;
                background-image: url('{background_url}');
                background-repeat: no-repeat;
                background-position: center top;
                background-size: cover;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0;
            }}

            .content-wrapper {{
                max-width: 800px;
                width: 100%;
                padding: 64px;
                color: #fff4bf;
                display: flex;
                justify-content: center;
            }}

            .content {{
                max-width: 520px;
                margin: 0 auto;
                color: #fff4bf;
                line-height: 1.7;
                text-align: left;
            }}

            .content p {{
                margin: 0 0 12px 0;
            }}

            .content p:last-child {{
                margin-bottom: 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-bg">
            <div class="content-wrapper">
                <div class="content">
                    <p>Kính gửi Quý khách,</p>

                    <p>
                        Hệ thống <strong>UIA Food</strong> nhận được yêu cầu khôi phục mật khẩu cho tài khoản của Quý khách.
                        Mã OTP khôi phục mật khẩu của Quý khách là: <strong>{otp_code}</strong>.
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
