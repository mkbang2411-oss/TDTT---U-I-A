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
    # Share Food Plan
    path('food-plan/share/<int:plan_id>/', views.share_food_plan_api, name='share_food_plan'),
    path('food-plan/shared/', views.get_shared_plans_api, name='get_shared_plans'),
    
    # 🍽️ User Preferences APIs
    path('preferences/', views.get_user_preferences, name='get_preferences'),
    path('preferences/save/', views.save_user_preference, name='save_preference'),
    path('preferences/delete/', views.delete_user_preference, name='delete_preference'),
    
    # Suggestions
    path('food-plan/suggest/<int:plan_id>/', views.submit_plan_suggestion_api, name='submit_plan_suggestion'),
    path('food-plan/suggestions/<int:plan_id>/', views.get_plan_suggestions_api, name='get_plan_suggestions'),
    path('food-plan/suggestion/review/<int:suggestion_id>/', views.review_suggestion_api, name='review_suggestion'),
    path('my-friends/', views.get_current_user_friends, name='get_current_user_friends'),
    path('food-plan/suggestions/<int:plan_id>/', views.get_plan_suggestions_api, name='get_plan_suggestions'),
    path('food-plan/suggestion-detail/<int:suggestion_id>/', views.get_suggestion_detail_api, name='get_suggestion_detail'),
    path('food-plan/suggestion-approve/<int:suggestion_id>/', views.approve_suggestion_api, name='approve_suggestion'),
    path('food-plan/suggestion-reject/<int:suggestion_id>/', views.reject_suggestion_api, name='reject_suggestion'),
    path('food-plan/leave-shared/<int:plan_id>/', views.leave_shared_plan_api, name='leave_shared_plan'),
     path('food-plan/suggestion-approve-single/', views.suggestion_approve_single, name='suggestion_approve_single'),
]
