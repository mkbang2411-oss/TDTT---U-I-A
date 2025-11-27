from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
from accounts import views as account_views
from django.conf import settings
from django.conf.urls.static import static

# Trang chủ (home)
def home(request):
    if request.user.is_authenticated:
        return HttpResponse("Chào mừng bạn, bạn đã đăng nhập!")
    else:
        # Tự động điều hướng đến URL login của allauth
        return redirect('/accounts/login/')

# Danh sách URL của project
urlpatterns = [
    path('', home, name='home'),  # Trang chủ
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Dùng django-allauth
    path('api/accounts/', include('accounts.urls')),  # ← QUAN TRỌNG!
    path('api/reviews/<str:place_id>', account_views.reviews_api, name='reviews_api'),

    path('api/check-auth/', account_views.check_auth_status, name='check_auth_status'),
    path('api/save-chat/', account_views.save_chat_message, name='save_chat_message'),
    path('api/load-chat/', account_views.load_chat_history, name='load_chat_history'),
    path('api/conversations/', account_views.get_conversation_list, name='get_conversation_list'),
    path('api/rename-chat/', account_views.rename_chat, name='rename_chat'),
    path('api/delete-chat/', account_views.delete_chat, name='delete_chat'),
    path('update-avatar/', account_views.update_avatar, name='update_avatar'),
    path('api/user-info/', account_views.get_user_info, name='get_user_info'),
    path('api/upload-avatar/', account_views.upload_avatar_api, name='upload_avatar_api'),
    path('api/change-password/', account_views.change_password_api, name='change_password_api'),
    path('api/favorite/<str:place_id>/', account_views.toggle_favorite, name='toggle_favorite'),
    path('api/get-favorites/', account_views.get_user_favorites_api, name='get_user_favorites_api'),
    path('api/puzzle/progress/', account_views.get_puzzle_progress, name='get_puzzle_progress'),
    path('api/puzzle/complete/', account_views.save_puzzle_completion, name='save_puzzle_completion'),
    path('api/puzzle/reset/<str:map_name>/', account_views.reset_puzzle_progress, name='reset_puzzle_progress'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
