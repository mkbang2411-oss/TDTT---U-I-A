from django.contrib import admin
from .models import ChatConversation, ChatMessage # Import 2 model của bạn

# Đăng ký 2 model
admin.site.register(ChatConversation)
admin.site.register(ChatMessage)