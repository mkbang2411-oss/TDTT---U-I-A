from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


# ✅ Danh sách ký tự đặc biệt được phép (10 ký tự)
ALLOWED_SPECIAL_CHARS = r'.?_@*&$#!~'
SPECIAL_CHARS_DISPLAY = '. ? _ @ * & $ # ! ~'

# ✅ Regex pattern cho mật khẩu hợp lệ
# Chỉ cho phép: chữ cái (a-z, A-Z), chữ số (0-9), và các ký tự đặc biệt được liệt kê
PASSWORD_PATTERN = re.compile(r'^[a-zA-Z0-9.?_@*&$#!~]+$')

# ✅ Giới hạn độ dài
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 32


def validate_password_format(password):
    """
    Hàm helper để validate mật khẩu
    Trả về tuple (is_valid, error_message)
    
    Quy tắc:
    - Độ dài: 6-32 ký tự
    - Phải chứa ít nhất 1 chữ cái thường (a-z)
    - Phải chứa ít nhất 1 chữ cái in hoa (A-Z)
    - Phải chứa ít nhất 1 chữ số (0-9)
    - Phải chứa ít nhất 1 ký tự đặc biệt
    - Không được chứa dấu cách
    - Chỉ được chứa các ký tự cho phép
    """
    # 1. Kiểm tra độ dài tối thiểu
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f'Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự'
    
    # 2. Kiểm tra độ dài tối đa
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f'Mật khẩu không được vượt quá {MAX_PASSWORD_LENGTH} ký tự'
    
    # 3. Kiểm tra không chứa dấu cách
    if ' ' in password:
        return False, 'Mật khẩu không được chứa dấu cách'
    
    # 4. Kiểm tra chỉ chứa ký tự được phép
    if not PASSWORD_PATTERN.match(password):
        return False, f'Mật khẩu chỉ được chứa chữ cái, chữ số và các ký tự đặc biệt: {SPECIAL_CHARS_DISPLAY}'
    
    # 5. Kiểm tra phải có ít nhất 1 chữ cái thường
    if not re.search(r'[a-z]', password):
        return False, 'Mật khẩu phải chứa ít nhất 1 chữ cái thường (a-z)'
    
    # 6. Kiểm tra phải có ít nhất 1 chữ cái in hoa
    if not re.search(r'[A-Z]', password):
        return False, 'Mật khẩu phải chứa ít nhất 1 chữ cái in hoa (A-Z)'
    
    # 7. Kiểm tra phải có ít nhất 1 chữ số
    if not re.search(r'[0-9]', password):
        return False, 'Mật khẩu phải chứa ít nhất 1 chữ số (0-9)'
    
    # 8. Kiểm tra phải có ít nhất 1 ký tự đặc biệt
    special_chars_pattern = r'[.?_@*&$#!~]'
    if not re.search(special_chars_pattern, password):
        return False, f'Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt: {SPECIAL_CHARS_DISPLAY}'
    
    return True, None


class NoSpacePasswordValidator:
    """
    Validator kiểm tra mật khẩu không chứa dấu cách
    """
    
    def validate(self, password, user=None):
        if ' ' in password:
            raise ValidationError(
                _("Mật khẩu không được chứa dấu cách."),
                code='password_contains_space',
            )
    
    def get_help_text(self):
        return _("Mật khẩu của bạn không được chứa dấu cách.")


class MaxLengthPasswordValidator:
    """
    Validator kiểm tra độ dài tối đa của mật khẩu
    """
    
    def __init__(self, max_length=MAX_PASSWORD_LENGTH):
        self.max_length = max_length
    
    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _(f"Mật khẩu không được vượt quá {self.max_length} ký tự."),
                code='password_too_long',
            )
    
    def get_help_text(self):
        return _(f"Mật khẩu của bạn không được vượt quá {self.max_length} ký tự.")


class AllowedCharactersPasswordValidator:
    """
    Validator kiểm tra mật khẩu chỉ chứa các ký tự được phép:
    - Chữ cái (a-z, A-Z)
    - Chữ số (0-9)
    - Ký tự đặc biệt: , . / [ ] \ = - < > ? { } | + _ ( ) * & ^ % $ # @ ! ~
    """
    
    def validate(self, password, user=None):
        if not PASSWORD_PATTERN.match(password):
            raise ValidationError(
                _(f"Mật khẩu chỉ được chứa chữ cái, chữ số và các ký tự đặc biệt: {SPECIAL_CHARS_DISPLAY}"),
                code='password_invalid_characters',
            )
    
    def get_help_text(self):
        return _(f"Mật khẩu chỉ được chứa chữ cái, chữ số và các ký tự đặc biệt: {SPECIAL_CHARS_DISPLAY}")


class LowercasePasswordValidator:
    """
    Validator kiểm tra mật khẩu phải chứa ít nhất 1 chữ cái thường
    """
    
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Mật khẩu phải chứa ít nhất 1 chữ cái thường (a-z)."),
                code='password_no_lowercase',
            )
    
    def get_help_text(self):
        return _("Mật khẩu của bạn phải chứa ít nhất 1 chữ cái thường (a-z).")


class UppercasePasswordValidator:
    """
    Validator kiểm tra mật khẩu phải chứa ít nhất 1 chữ cái in hoa
    """
    
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Mật khẩu phải chứa ít nhất 1 chữ cái in hoa (A-Z)."),
                code='password_no_uppercase',
            )
    
    def get_help_text(self):
        return _("Mật khẩu của bạn phải chứa ít nhất 1 chữ cái in hoa (A-Z).")


class DigitPasswordValidator:
    """
    Validator kiểm tra mật khẩu phải chứa ít nhất 1 chữ số
    """
    
    def validate(self, password, user=None):
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("Mật khẩu phải chứa ít nhất 1 chữ số (0-9)."),
                code='password_no_digit',
            )
    
    def get_help_text(self):
        return _("Mật khẩu của bạn phải chứa ít nhất 1 chữ số (0-9).")


class SpecialCharacterPasswordValidator:
    """
    Validator kiểm tra mật khẩu phải chứa ít nhất 1 ký tự đặc biệt
    Ký tự được phép: . ? _ @ * & $ # ! ~
    """
    
    def validate(self, password, user=None):
        special_chars_pattern = r'[.?_@*&$#!~]'
        if not re.search(special_chars_pattern, password):
            raise ValidationError(
                _(f"Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt: {SPECIAL_CHARS_DISPLAY}"),
                code='password_no_special',
            )
    
    def get_help_text(self):
        return _(f"Mật khẩu của bạn phải chứa ít nhất 1 ký tự đặc biệt: {SPECIAL_CHARS_DISPLAY}")

