from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
from accounts import views as account_views

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

]
