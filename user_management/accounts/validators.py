from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


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
