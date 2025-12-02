from django.urls import path
from . import views

urlpatterns = [
    # API kết bạn
    path('friend-request/send/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/accept/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/', views.reject_friend_request, name='reject_friend_request'),
    path('friends/<int:user_id>/', views.get_friends_list, name='get_friends_list'),
    path('friend-requests/<int:user_id>/', views.get_friend_requests, name='get_friend_requests'),
    path('users/search/', views.search_user, name='search_user'),
    path('current-user/', views.get_current_user, name='get_current_user'),
    path('api/streak/', views.streak_handler, name='streak_handler'),
    path('friend/unfriend/', views.unfriend, name='unfriend'),
    path('friend/<int:friend_id>/favorites/', views.get_friend_favorites, name='get_friend_favorites'),
    path('geocode/', views.geocode_proxy, name='geocode'),

    # 🗂️ Food Plan APIs
    path('food-plan/save/', views.save_food_plan_api, name='save_food_plan'),
    path('food-plan/list/', views.get_food_plans_api, name='get_food_plans'),
    path('food-plan/delete/<int:plan_id>/', views.delete_food_plan_api, name='delete_food_plan'),
]