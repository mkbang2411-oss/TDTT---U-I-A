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
        return redirect('/accounts/login/')

# Danh sách URL của project
urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    
    # Custom signup flow với OTP: Email → OTP → Password Form
    path('accounts/signup/', account_views.signup_email_page, name='account_signup'),  # Step 1: Email input page
    path('accounts/signup-email/', account_views.signup_email_page, name='signup_email'),  # Email input page (alias)
    path('accounts/verify-otp/', account_views.verify_otp_page, name='verify_otp'),  # Step 2: OTP verification page
    path('accounts/signup-form/', account_views.signup_form_page, name='signup_form'),  # Step 3: Password form (after OTP verified)
    
    # Include allauth URLs (login, logout, password reset, social auth, etc.)
    path('accounts/', include('allauth.urls')),
    
    path('api/accounts/', include('accounts.urls')),
    
    path('api/reviews/<str:place_id>/', account_views.reviews_api, name='reviews_api'),
    path('api/reviews/<str:place_id>/<int:review_index>/', account_views.delete_review_api,  name='delete_review'),
    path('api/streak/', account_views.streak_handler, name='streak_handler_direct'),
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
    
    # 📖 Food Story APIs
    path('api/food-story/<str:map_name>/', account_views.get_food_story, name='get_food_story'),
    path('api/food-story/unlock/<str:map_name>/', account_views.unlock_food_story, name='unlock_food_story'),
    path('api/food-stories/unlocked/', account_views.get_all_unlocked_stories, name='get_all_unlocked_stories'),

    # 📧 OTP VERIFICATION APIs
    path('api/send-otp/', account_views.send_otp_api, name='send_otp'),
    path('api/verify-otp/', account_views.verify_otp_api, name='verify_otp'),
    path('api/resend-otp/', account_views.resend_otp_api, name='resend_otp'),

    # 🔑 PASSWORD RESET (OTP-based)
    path('accounts/password-reset/request/', account_views.password_reset_request_page, name='password_reset_request'),
    path('accounts/password-reset/verify-otp/', account_views.password_reset_verify_otp_page, name='password_reset_verify_otp'),
    path('accounts/password-reset/new-password/', account_views.password_reset_form_page, name='password_reset_form'),
    path('api/password-reset/send-otp/', account_views.send_password_reset_otp_api, name='send_password_reset_otp'),
    path('api/password-reset/verify-otp/', account_views.verify_password_reset_otp_api, name='verify_password_reset_otp'),
    path('api/password-reset/reset/', account_views.reset_password_api, name='reset_password'),

    path('api/', include('accounts.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)