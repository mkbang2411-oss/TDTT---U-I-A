from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from allauth.socialaccount.models import SocialAccount
from .models import ChatConversation, ChatMessage, EmailOTP
from django.shortcuts import render, redirect, get_object_or_404
from .models import UserProfile, FavoritePlace, PuzzleProgress
from django.conf import settings
import json, os
import pandas as pd
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from .utils import send_otp_email, send_welcome_email, send_password_reset_otp_email
from .models import PasswordResetOTP
from .models import FriendRequest, Friendship
from datetime import date, timedelta
from .nudenet_detector import check_nsfw_image_local
import requests 
from .gemini_utils import check_review_content
from .models import UserPreference
from .models import (
    FoodPlan, 
    SharedFoodPlan,
    PlanEditSuggestion
)
from .models import Notification
from .utils import (
    create_friend_request_notification,
    create_shared_plan_notification,
    create_suggestion_notification
)
import time
import queue
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .signals import sse_connections
from .utils import create_suggestion_approved_notification
# ------------------------SOCIAL ACCOUNT HANDLER--------------------------

def social_account_already_exists(request):
    """
    Trang thông báo khi email đã tồn tại trong hệ thống
    Hiển thị khi người dùng cố đăng nhập bằng Google với email đã được đăng ký
    """
    return render(request, 'account/already_linked.html', {
        'message': 'Email này đã được đăng ký trong hệ thống. Vui lòng đăng nhập bằng tài khoản hiện có.',
        'login_url': '/accounts/login/'  # ✅ Thêm URL đăng nhập
    })

# ------------------------OTP VERIFICATION PAGE--------------------------

def signup_email_page(request):
    """
    Trang nhập email để bắt đầu đăng ký
    Đây là bước đầu tiên trong quy trình đăng ký
    """
    return render(request, 'account/signup_email.html')

def verify_otp_page(request):
    """
    Hiển thị trang nhập OTP
    Email được lưu trong session từ bước gửi OTP
    """
    from datetime import timedelta
    from dateutil import parser
    
    email = request.session.get('otp_email')
    otp_sent_at = request.session.get('otp_sent_at')
    
    if not email or not otp_sent_at:
        # Nếu không có email trong session, quay lại trang signup
        return redirect('signup_email')
    
    # Kiểm tra timeout 30 phút
    try:
        sent_time = parser.parse(otp_sent_at)
        if timezone.now() - sent_time > timedelta(minutes=settings.OTP_SESSION_TIMEOUT_MINUTES):
            request.session.flush()
            messages.error(request, 'Phiên xác thực đã hết hạn. Vui lòng thử lại.')
            return redirect('signup_email')
    except Exception:
        pass
    
    return render(request, 'account/verify_otp.html', {
        'email': email
    })

def custom_signup_redirect(request):
    """
    Redirect trang /accounts/signup/ về trang nhập email
    Người dùng phải nhập email và verify OTP trước khi đến form đăng ký
    """
    # Nếu đã verify email rồi thì cho vào trang signup form
    if request.session.get('verified_email'):
        return redirect('signup_form')
    
    # Nếu chưa verify, redirect về trang nhập email
    return redirect('signup_email')

def signup_form_page(request):
    """
    Trang form đăng ký thật (sau khi đã verify OTP)
    Chỉ accessible khi đã có verified_email trong session
    """
    from datetime import timedelta
    from dateutil import parser
    
    verified_email = request.session.get('verified_email')
    verified_at = request.session.get('email_verified_at')
    
    if not verified_email or not verified_at:
        return redirect('signup_email')
    
    # Kiểm tra timeout 30 phút cho session verify
    try:
        verified_time = parser.parse(verified_at)
        if timezone.now() - verified_time > timedelta(minutes=settings.OTP_SESSION_TIMEOUT_MINUTES):
            request.session.flush()
            messages.error(request, 'Phiên xác thực đã hết hạn. Vui lòng xác thực lại email.')
            return redirect('signup_email')
    except Exception:
        pass
    
    # Import ở đây để tránh circular import
    from allauth.account.views import SignupView
    from django.contrib.auth import logout

    class SignupViewNoAutoLogin(SignupView):
        def form_valid(self, form):
            response = super().form_valid(form)
            try:
                # Đảm bảo KHÔNG đăng nhập ngay sau đăng ký
                logout(self.request)
            except Exception:
                pass
            # Chuyển hướng về trang đăng nhập lần đầu
            from django.urls import reverse
            return redirect(reverse('account_login'))

    return SignupViewNoAutoLogin.as_view()(request)

# ------------------------LẤY DỮ LIỆU REVIEW--------------------------

def load_user_reviews():
    try:
        # Thêm encoding='utf-8' vào đây
        with open('user_reviews.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError: 
        return {} # Trả về rỗng nếu tệp JSON bị hỏng

def save_user_reviews(data):
    # Thêm encoding='utf-8' và ensure_ascii=False
    with open('user_reviews.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@csrf_exempt
def reviews_api(request: HttpRequest, place_id: str):
    
    # === 1. GET REVIEW ===
    if request.method == 'GET':
        all_reviews = load_user_reviews()
        place_data = all_reviews.get(place_id)
        
        if place_data is None:
            review_content = {"google": [], "user": []}
        elif isinstance(place_data, list):
            review_content = {"google": place_data, "user": []}
        else:
            review_content = place_data

        # === LẤY THÔNG TIN USER ===
        user_info = {'is_logged_in': False}
        is_favorite = False
        if request.user.is_authenticated:
            avatar_url = get_user_avatar(request.user) 

            user_info = {
                'is_logged_in': True,
                'username': request.user.username,
                'avatar': avatar_url 
            }
        
            try:
                is_favorite = FavoritePlace.objects.filter(
                    user=request.user, 
                    place_id=str(place_id)
                ).exists()
            except Exception:
                pass
        
        return JsonResponse({
            'reviews': review_content,
            'user': user_info,
            'is_favorite': is_favorite
        })
    
    # === 2. XỬ LÝ VIỆC THÊM (POST) REVIEW ===
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({
                "success": False, 
                "message": "Bạn cần đăng nhập"
            }, status=403)
        
        avatar_nguoi_dung = get_user_avatar(request.user)

        try:
            data = json.loads(request.body)
            comment = data.get("comment", "").strip()
            rating = int(data.get("rating", 0))
            
            print(f"\n{'='*60}")
            print(f"📝 [NEW REVIEW] User: {request.user.username}")
            print(f"   Place ID: {place_id}")
            print(f"   Rating: {rating}/5")
            print(f"   Comment: {comment}")
            print(f"{'='*60}\n")
            
            if not comment or rating == 0:
                return JsonResponse({
                    "success": False, 
                    "message": "Thiếu thông tin"
                }, status=400)
            
            # 🔥 KIỂM TRA NỘI DUNG VỚI GEMINI
            print(f"🤖 [GEMINI] Bắt đầu kiểm tra nội dung...")
            
            try:
                validation = check_review_content(comment, rating)
                
                print(f"📊 [GEMINI] Kết quả kiểm tra:")
                print(f"   - is_valid: {validation.get('is_valid')}")
                print(f"   - reason: {validation.get('reason')}")
                print(f"   - severity: {validation.get('severity')}")
                print(f"   - suggested: {validation.get('suggested_content', 'N/A')[:50]}")
                
                if not validation['is_valid']:
                    print(f"❌ [GEMINI] CHẶN REVIEW - Lý do: {validation['reason']}\n")
                    
                    response_data = {
                        "success": False,
                        "message": f"❌ Nội dung không phù hợp: {validation['reason']}"
                    }
                    
                    # Nếu có gợi ý nội dung tốt hơn
                    if validation.get('suggested_content'):
                        response_data['suggested_content'] = validation['suggested_content']
                        response_data['message'] += f"\n\n💡 Gợi ý: {validation['suggested_content']}"
                    
                    return JsonResponse(response_data, status=400)
                
                print(f"✅ [GEMINI] CHO PHÉP GỬI REVIEW\n")
            
            except Exception as gemini_error:
                # Nếu Gemini lỗi, vẫn cho phép gửi review (fail-safe)
                print(f"⚠️ [GEMINI] LỖI KHI GỌI API:")
                print(f"   Error: {gemini_error}")
                import traceback
                traceback.print_exc()
                print(f"   → Cho phép gửi review (fail-safe mode)\n")
            
        except json.JSONDecodeError:
            print(f"❌ [ERROR] Lỗi parse JSON\n")
            return JsonResponse({
                "success": False, 
                "message": "Lỗi dữ liệu JSON"
            }, status=400)
        except ValueError as ve:
            print(f"❌ [ERROR] Rating không hợp lệ: {ve}\n")
            return JsonResponse({
                "success": False, 
                "message": "Rating không hợp lệ"
            }, status=400)
        except Exception as e:
            print(f"❌ [ERROR] Lỗi không xác định:")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            print()
            return JsonResponse({
                "success": False, 
                "message": "Có lỗi xảy ra khi xử lý đánh giá"
            }, status=500)

        # === 3. LƯU REVIEW VÀO JSON ===
        try:
            print(f"💾 [SAVE] Đang lưu review vào JSON...")
            
            all_reviews = load_user_reviews()
            
            if all_reviews.get(place_id) is None:
                all_reviews[place_id] = {"google": [], "user": []}
            
            # Đảm bảo cấu trúc dict
            if isinstance(all_reviews[place_id], list):
                all_reviews[place_id] = {"google": all_reviews[place_id], "user": []}

            new_review = {
                "ten": request.user.username,
                "avatar": avatar_nguoi_dung,
                "rating": rating,
                "comment": comment,
                "date": datetime.now().isoformat()
            }
            
            all_reviews[place_id]["user"].append(new_review)
            save_user_reviews(all_reviews)
            
            print(f"✅ [SAVE] Lưu thành công!")
            print(f"{'='*60}\n")
            
            return JsonResponse({
                "success": True, 
                "message": "✅ Đánh giá thành công!"
            })
        
        except Exception as save_error:
            print(f"❌ [SAVE] Lỗi khi lưu review:")
            print(f"   {save_error}")
            import traceback
            traceback.print_exc()
            print()
            return JsonResponse({
                "success": False, 
                "message": "Không thể lưu đánh giá"
            }, status=500)

    # === 4. METHOD NOT ALLOWED ===
    return JsonResponse({
        "success": False, 
        "message": "Method not allowed"
    }, status=405)
# ==========================================================
# 🗑️ API XÓA ĐÁNH GIÁ CỦA USER
# ==========================================================

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_review_api(request, place_id, review_index):
    """
    Xóa đánh giá của user
    DELETE /api/reviews/<place_id>/<review_index>/
    
    Params:
        - place_id: ID của quán
        - review_index: Index của review trong mảng user reviews
    """
    try:
        # 1. ĐỌC FILE JSON
        all_reviews = load_user_reviews()
        
        place_data = all_reviews.get(place_id)
        
        if not place_data:
            return JsonResponse({
                'success': False,
                'message': 'Không tìm thấy quán'
            }, status=404)
        
        # 2. ĐẢM BẢO CẤU TRÚC DICT
        if isinstance(place_data, list):
            place_data = {"google": place_data, "user": []}
            all_reviews[place_id] = place_data
        
        user_reviews = place_data.get('user', [])
        
        # 3. KIỂM TRA INDEX HỢP LỆ
        try:
            review_index = int(review_index)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Index không hợp lệ'
            }, status=400)
        
        if review_index < 0 or review_index >= len(user_reviews):
            return JsonResponse({
                'success': False,
                'message': 'Không tìm thấy đánh giá'
            }, status=404)
        
        # 4. KIỂM TRA QUYỀN SỞ HỮU
        review_to_delete = user_reviews[review_index]
        
        # So sánh username (case-insensitive)
        review_username = review_to_delete.get('ten', '').strip().lower()
        current_username = request.user.username.strip().lower()
        
        print(f"\n🔍 [DELETE REVIEW] Check ownership:")
        print(f"   Review username: '{review_username}'")
        print(f"   Current user: '{current_username}'")
        
        if review_username != current_username:
            return JsonResponse({
                'success': False,
                'message': 'Bạn chỉ có thể xóa đánh giá của chính mình'
            }, status=403)
        
        # 5. XÓA REVIEW
        deleted_review = user_reviews.pop(review_index)
        
        print(f"✅ [DELETE] Removed review:")
        print(f"   User: {deleted_review.get('ten')}")
        print(f"   Comment: {deleted_review.get('comment', '')[:50]}")
        
        # 6. LƯU LẠI FILE
        all_reviews[place_id]['user'] = user_reviews
        save_user_reviews(all_reviews)
        
        print(f"💾 [DELETE] Saved. Remaining reviews: {len(user_reviews)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa đánh giá',
            'remaining_count': len(user_reviews)
        })
        
    except Exception as e:
        print(f"❌ [DELETE ERROR]: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi xóa đánh giá'
        }, status=500)

# ------------------------LƯU LỊCH SỬ CHATBOT AI--------------------------
# --- Helper để lấy Avatar ---
def get_user_avatar(user):
    default_avatar = 'https://cdn-icons-png.flaticon.com/512/847/847969.png'
    
    if not user.is_authenticated:
        return default_avatar

    try:
        if hasattr(user, 'profile') and user.profile.avatar:
            # ✅ TRẢ VỀ URL TƯƠNG ĐỐI (không hardcode domain/port)
            return user.profile.avatar.url
    except Exception as e:
        print(f"Error loading profile avatar: {e}")

    try:
        social_account = SocialAccount.objects.get(user=user, provider='google')
        return social_account.get_avatar_url()
    except SocialAccount.DoesNotExist:
        pass
        
    return default_avatar

# --- API 1: Lấy danh sách các đoạn chat (Sidebar) ---
#@login_required
def get_conversation_list(request):
    """API trả về danh sách các cuộc trò chuyện của user"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'success', 'conversations': []})
    try:
        # Lấy tất cả cuộc trò chuyện của user, sắp xếp mới nhất lên đầu
        conversations = ChatConversation.objects.filter(user=request.user).order_by('-created_at')
        
        data = []
        for conv in conversations:
            # Format ngày tháng
                date_str = conv.created_at.strftime("%d/%m/%Y %H:%M")
                # Nếu không có title thì lấy tạm nội dung tin nhắn đầu hoặc "Đoạn chat mới"
                title = conv.title if conv.title else "Đoạn chat mới"
                data.append({
                    'id': conv.id,
                    'title': conv.title or "Đoạn chat mới",
                    'date': conv.created_at.strftime("%d/%m/%Y")
                })
        
        return JsonResponse({'status': 'success', 'conversations': data})
    except Exception as e:
        print(f"Lỗi Server: {e}") # In lỗi ra terminal để dễ debug
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# --- API 2: Lấy chi tiết tin nhắn của 1 đoạn chat ---
@login_required
def load_chat_history(request):
    conversation_id = request.GET.get('conversation_id')
    
    # Nếu KHÔNG có conversation_id lập tức để tạo giao diện "Chat mới"
    if not conversation_id:
        return JsonResponse({
            'status': 'success', 
            'messages': [],         
            'conversation_id': None 
        })
    
    try:
        conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
        messages = conversation.messages.all().order_by('timestamp')
        
        user_avatar = get_user_avatar(request.user)
        ai_avatar = "🍜" 

        message_list = []
        for msg in messages:
            message_list.append({
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%H:%M'), 
                'avatar': user_avatar if msg.sender == 'user' else ai_avatar
            })
            
        return JsonResponse({
            'status': 'success', 
            'messages': message_list,
            'conversation_id': conversation.id
        })
            
    except ChatConversation.DoesNotExist:
        # Trường hợp ID gửi lên không tồn tại hoặc không phải của user này
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy cuộc trò chuyện'}, status=404)
# --- API 3: Lưu tin nhắn (Xử lý logic tạo mới) ---
@csrf_exempt
#@login_required
def save_chat_message(request):
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                # Nếu chưa đăng nhập -> Không lưu DB, trả về success để JS không báo lỗi
                return JsonResponse({'status': 'success', 'conversation_id': None})
            
            data = json.loads(request.body)
            content = data.get('content')
            sender = data.get('sender')
            conversation_id = data.get('conversation_id')

            if not content:
                return JsonResponse({'status': 'error'}, status=400)

            conversation = None

            # CASE A: Đã có ID đoạn chat -> Lấy đoạn chat đó
            if conversation_id:
                try:
                    conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
                    # Cập nhật thời gian để đoạn chat này nhảy lên đầu danh sách Sidebar
                    conversation.updated_at = timezone.now()
                    conversation.save()
                except ChatConversation.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Không tìm thấy đoạn chat'}, status=404)

            # CASE B: Chưa có ID (Chat mới) -> Tạo mới ngay tại thời điểm này
            else:
                if sender == 'user':
                    # ✅ Ưu tiên dùng custom_title nếu có, nếu không thì dùng content
                    custom_title = data.get('custom_title', None)

                    if custom_title:
                        title_text = custom_title[:100]  # Giới hạn 100 ký tự
                        print(f"[BACKEND] Dùng custom title: {title_text}")
                    else:
                        auto_title_source = data.get('content', 'New Chat')
                        title_text = auto_title_source[:50]  # Giới hạn 50 ký tự
                        print(f"[BACKEND] Dùng content làm title: {title_text}")

                    conversation = ChatConversation.objects.create(
                        user=request.user,
                        title=title_text
                    )
                else:
                    # Nếu sender là 'ai' mà không có ID -> Lỗi logic frontend
                    return JsonResponse({'status': 'error', 'message': 'AI không thể bắt đầu đoạn chat mới'}, status=400)

            # Lưu tin nhắn
            ChatMessage.objects.create(
                conversation=conversation,
                sender=sender,
                content=content
            )

            # Trả về ID để JS cập nhật (nếu là đoạn chat mới tạo)
            return JsonResponse({
                'status': 'success', 
                'conversation_id': conversation.id,
                'title': conversation.title
            })

        except Exception as e:
            print(f"Lỗi Save Chat: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

# --- API 4: Đổi tên đoạn chat ---
@csrf_exempt
@login_required
@require_POST # Chỉ cho phép method POST
def rename_chat(request):
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        new_title = data.get('new_title')

        if not conversation_id or not new_title:
            return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin'}, status=400)

        # Tìm và cập nhật (Chỉ sửa được chat của chính user đó)
        conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
        conversation.title = new_title
        conversation.save()

        return JsonResponse({'status': 'success', 'message': 'Đổi tên thành công'})

    except ChatConversation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy đoạn chat'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# --- API 5: Xóa đoạn chat ---
@csrf_exempt
@login_required
@require_POST
def delete_chat(request):
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')

        if not conversation_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu ID'}, status=400)

        # Tìm và xóa
        conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete() # Xóa khỏi database

        return JsonResponse({'status': 'success', 'message': 'Xóa thành công'})

    except ChatConversation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy đoạn chat'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
def check_auth_status(request):
    """
    Một API view để kiểm tra trạng thái đăng nhập.
    """
    if request.user.is_authenticated:
        # Nếu đã đăng nhập
        return JsonResponse({
            'is_authenticated': True,
            'is_logged_in': True,  # ← THÊM dòng này cho script.js
            'username': request.user.username
        })
    else:
        # Nếu chưa đăng nhập
        return JsonResponse({
            'is_authenticated': False,
            'is_logged_in': False  # ← THÊM dòng này
        })
    
@login_required
def update_avatar(request):
    if request.method == 'POST':
        # Kiểm tra xem có file được gửi lên không
        if 'avatar' in request.FILES:
            image_file = request.FILES['avatar']
            
            # Lấy hoặc tạo profile nếu chưa có
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Gán ảnh mới (Django tự xử lý việc lưu file và đặt tên)
            profile.avatar = image_file
            profile.save()
            
            return redirect('home') # Đổi xong quay về trang chủ

    return render(request, 'change_avatar.html')

# --- Lấy thông tin User & Avatar hiện tại ---
def get_user_info(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Chưa đăng nhập'}, status=401)
    
    # Gọi hàm helper ở trên để lấy ảnh chuẩn nhất
    avatar_url = get_user_avatar(request.user)

    is_social_login = False
    try:
        # Kiểm tra trong bảng SocialAccount xem user này có liên kết Google không
        if SocialAccount.objects.filter(user=request.user, provider='google').exists():
            is_social_login = True
    except Exception as e:
        print(f"Lỗi kiểm tra Social Account: {e}")
        pass

    return JsonResponse({
        'status': 'success',
        'username': request.user.username,
        'email': request.user.email,
        'avatar_url': avatar_url,
        'is_social_login': is_social_login
    })

# ---  Upload Avatar Mới ---
@csrf_exempt
def upload_avatar_api(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error', 
                'message': 'Chưa đăng nhập'
            }, status=401)
        
        image_file = request.FILES['avatar']
        
        # 🔍 KIỂM TRA NSFW BẰNG NUDENET
        print(f"\n{'='*60}")
        print(f"🔍 [AVATAR MODERATION]")
        print(f"   User: {request.user.username}")
        print(f"   File: {image_file.name}")
        print(f"   Size: {image_file.size/1024:.1f} KB")
        
        # ✅ DÙNG NUDENET
        check_result = check_nsfw_image_local(image_file)
        
        print(f"   Result: is_safe={check_result['is_safe']}, reason={check_result['reason']}")
        print(f"{'='*60}\n")
        
        if not check_result['is_safe']:
            return JsonResponse({
                'status': 'error',
                'message': f'❌ {check_result["reason"]}',
                'details': check_result.get('details', {})
            }, status=400)
        
        # ✅ ẢNH AN TOÀN → LƯU
        image_file.seek(0)
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.avatar = image_file
        profile.save()
        
        return JsonResponse({
            'status': 'success',
            'new_avatar_url': profile.avatar.url
        })
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Lỗi upload'
    }, status=400)

@csrf_exempt
def change_password_api(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Chưa đăng nhập'}, status=401)
        
        # Chặn Google User
        if SocialAccount.objects.filter(user=request.user, provider='google').exists():
             return JsonResponse({'status': 'error', 'message': 'Tài khoản Google không thể đổi mật khẩu'}, status=403)

        try:
            data = json.loads(request.body)
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            # 1. Kiểm tra dữ liệu đầu vào
            if not old_password or not new_password:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin'}, status=400)
            
            if new_password != confirm_password:
                return JsonResponse({'status': 'error', 'message': 'Mật khẩu xác nhận không khớp'}, status=400)

            if len(new_password) < 6:
                return JsonResponse({'status': 'error', 'message': 'Mật khẩu mới quá ngắn (>6 ký tự)'}, status=400)

            # 2. Kiểm tra mật khẩu cũ có đúng không
            if not request.user.check_password(old_password):
                return JsonResponse({'status': 'error', 'message': 'Mật khẩu cũ không chính xác'}, status=400)

            # 3. Đổi mật khẩu
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user) # Giữ đăng nhập
            
            return JsonResponse({'status': 'success', 'message': 'Đổi mật khẩu thành công'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

# --- API: THÍCH / BỎ THÍCH QUÁN YÊU THÍCH ---
@csrf_exempt
@require_POST
@login_required
def toggle_favorite(request, place_id):
    try:
        # 🔍 DEBUG
        print(f"\n🔍 [TOGGLE FAVORITE] User: {request.user.username}")
        print(f"📊 [TOGGLE] place_id type: {type(place_id)}")
        print(f"📊 [TOGGLE] place_id value: '{place_id}'")
        
        favorite, created = FavoritePlace.objects.get_or_create(
            user=request.user, 
            place_id=str(place_id)  # ✅ Đảm bảo luôn lưu dạng string
        )
        
        if not created:
            favorite.delete()
            print(f"❌ [TOGGLE] REMOVED from favorites\n")
            return JsonResponse({'status': 'removed', 'message': 'Đã xóa khỏi yêu thích'})
        else:
            print(f"✅ [TOGGLE] ADDED to favorites\n")
            return JsonResponse({'status': 'added', 'message': 'Đã thêm vào yêu thích'})
            
    except Exception as e:
        print(f"❌ [TOGGLE ERROR] {e}\n")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_user_favorites_api(request):
    user = request.user

    # ✅ LẤY DANH SÁCH ID TỪ DB
    favorite_ids = list(
        FavoritePlace.objects.filter(user=user).values_list('place_id', flat=True)
    )

    # 🔍 DEBUG: In ra console
    print(f"\n{'='*60}")
    print(f"🔍 [DEBUG] User: {user.username}")
    print(f"📊 [DEBUG] Favorite IDs from DB: {favorite_ids}")
    print(f"📊 [DEBUG] Count: {len(favorite_ids)}")
    print(f"{'='*60}\n")

    # ĐỌC CSV
    csv_path = os.path.join(settings.BASE_DIR, '..', 'backend', 'Data_with_flavor.csv')
    csv_path = os.path.abspath(csv_path)

    favorite_places = []
    try:
        df = pd.read_csv(csv_path)
        df['data_id'] = df['data_id'].astype(str)  # ✅ Ép kiểu string

        # 🔍 DEBUG: Kiểm tra CSV
        print(f"📄 [DEBUG] CSV total rows: {len(df)}")
        print(f"📄 [DEBUG] CSV data_id sample: {df['data_id'].head().tolist()}")

        # LỌC QUÁN
        filtered_df = df[df['data_id'].isin(favorite_ids)]

        # 🔍 DEBUG: Kiểm tra kết quả filter
        print(f"✅ [DEBUG] Filtered rows: {len(filtered_df)}")
        print(f"✅ [DEBUG] Filtered IDs: {filtered_df['data_id'].tolist()}")
        
        # ❌ KIỂM TRA TRÙNG LẶP
        if len(filtered_df) > len(favorite_ids):
            print(f"⚠️ [WARNING] CSV has DUPLICATES!")
            print(f"   Expected: {len(favorite_ids)} rows")
            print(f"   Got: {len(filtered_df)} rows")
            
            # Tìm các ID bị trùng
            duplicates = filtered_df[filtered_df.duplicated(subset=['data_id'], keep=False)]
            if not duplicates.empty:
                print(f"🔴 [DUPLICATES]:")
                print(duplicates[['data_id', 'ten_quan', 'dia_chi']])

        favorite_places = filtered_df.fillna('').to_dict('records')
        
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ [ERROR] {e}")

    return JsonResponse({'favorites': favorite_places})
# ==========================================================
# ✏️ LOGIC API KẾT BẠN
# ==========================================================

@csrf_exempt
@require_http_methods(["POST"])
def send_friend_request(request):
    """Gửi lời mời kết bạn"""
    try:
        data = json.loads(request.body)
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')
        
        sender = get_object_or_404(User, id=sender_id)
        receiver = get_object_or_404(User, id=receiver_id)
        
        # Kiểm tra không tự gửi cho chính mình
        if sender == receiver:
            return JsonResponse({'error': 'Không thể kết bạn với chính mình'}, status=400)
        
        # Kiểm tra đã là bạn chưa
        if Friendship.objects.filter(user1=sender, user2=receiver).exists() or \
           Friendship.objects.filter(user1=receiver, user2=sender).exists():
            return JsonResponse({'error': 'Đã là bạn bè rồi'}, status=400)
        
        # ✅ FIX: Kiểm tra và xử lý lời mời cũ
        existing_request = FriendRequest.objects.filter(
            sender=sender, 
            receiver=receiver
        ).first()
        
        if existing_request:
            if existing_request.status == 'pending':
                # Nếu đang pending → báo lỗi
                return JsonResponse({'error': 'Đã gửi lời mời rồi'}, status=400)
            else:
                # Nếu đã rejected/accepted → XÓA và tạo mới
                existing_request.delete()
        
        # Tạo lời mời kết bạn MỚI
        friend_request = FriendRequest.objects.create(sender=sender, receiver=receiver)
        
        # ✅ TẠO THÔNG BÁO
        create_friend_request_notification(receiver, sender, friend_request.id)
        
        return JsonResponse({
            'success': True,
            'message': 'Đã gửi lời mời kết bạn',
            'request_id': friend_request.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def accept_friend_request(request):
    """Chấp nhận lời mời kết bạn"""
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
        
        friend_request = get_object_or_404(FriendRequest, id=request_id, status='pending')
        
        # Cập nhật trạng thái
        friend_request.status = 'accepted'
        friend_request.save()
        
        # Tạo quan hệ bạn bè
        Friendship.objects.create(user1=friend_request.sender, user2=friend_request.receiver)
        
        # ✅ THÊM ĐOẠN NÀY - Tạo notification cho người gửi lời mời
        Notification.objects.create(
            user=friend_request.sender,  # Người nhận thông báo
            notification_type='friend_accepted',  # 🔥 Type mới
            title='Lời mời kết bạn được chấp nhận 🎉',
            message=f'{friend_request.receiver.username} đã chấp nhận lời mời kết bạn của bạn',
            related_id=friend_request.receiver.id  # ID của người chấp nhận
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Đã chấp nhận lời mời kết bạn'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reject_friend_request(request):
    """Từ chối lời mời kết bạn"""
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
        
        friend_request = get_object_or_404(FriendRequest, id=request_id, status='pending')
        friend_request.status = 'rejected'
        friend_request.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã từ chối lời mời kết bạn'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_friends_list(request, user_id):
    """Lấy danh sách bạn bè"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Lấy bạn bè
        friends_as_user1 = Friendship.objects.filter(user1=user).values_list('user2', flat=True)
        friends_as_user2 = Friendship.objects.filter(user2=user).values_list('user1', flat=True)
        
        friend_ids = list(friends_as_user1) + list(friends_as_user2)
        friends = User.objects.filter(id__in=friend_ids)
        
        friends_data = [
            {
                'id': friend.id,
                'username': friend.username,
                'email': friend.email
            }
            for friend in friends
        ]
        
        return JsonResponse({'friends': friends_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_friend_requests(request, user_id):
    """Lấy danh sách lời mời kết bạn"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Lời mời nhận được
        received_requests = FriendRequest.objects.filter(receiver=user, status='pending')
        
        requests_data = [
            {
                'id': req.id,
                'sender_id': req.sender.id,
                'sender_username': req.sender.username,
                'created_at': req.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for req in received_requests
        ]
        
        return JsonResponse({'requests': requests_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def search_user(request):
    """Tìm kiếm user theo email"""
    try:
        query = request.GET.get('q', '')
        
        if not query:
            return JsonResponse({'error': 'Cần nhập email để tìm kiếm'}, status=400)
        
        # Tìm theo email
        users = User.objects.filter(email__icontains=query)[:10]
        
        users_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            for user in users
        ]
        
        return JsonResponse({'users': users_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
@require_http_methods(["GET"])
def get_current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Chưa đăng nhập'}, status=401)
    
    try:
        user = request.user
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'email': user.email
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# ===============================
# 📍 GỢI Ý QUÁN THEO QUẬN CHO ALBUM
# ===============================
from django.http import JsonResponse

@login_required
def get_district_places(request):
    """
    GET /api/food/suggestions/?district=Quận%201,%203,%205&food=Phở
    
    Trả về danh sách quán theo:
    1. Địa chỉ chứa quận
    2. Tên quán chứa món ăn (nếu có tham số food)
    """
    district = request.GET.get("district")
    food_keyword = request.GET.get("food", "").strip()  # 🆕 Thêm tham số food
    
    if not district:
        return JsonResponse(
            {"status": "error", "message": "Thiếu tham số district"},
            status=400
        )

    try:
        csv_path = os.path.join(
            settings.BASE_DIR, "..", "backend", "Data_with_flavor.csv"
        )
        csv_path = os.path.abspath(csv_path)

        df = pd.read_csv(csv_path)

        ADDRESS_COL = "dia_chi"
        NAME_COL = "ten_quan"  # 🆕 Thêm cột tên quán
        
        if ADDRESS_COL not in df.columns:
            return JsonResponse(
                {"status": "error", "message": f"Không tìm thấy cột '{ADDRESS_COL}'"},
                status=500,
            )

        df[ADDRESS_COL] = df[ADDRESS_COL].astype(str)
        df[NAME_COL] = df[NAME_COL].astype(str)

        # 🔍 TÁCH CÁC QUẬN
        district_list = [d.strip() for d in district.split(",")]
        normalized_districts = []
        for d in district_list:
            d_lower = d.lower()
            if "quận" not in d_lower:
                normalized_districts.append(f"quận {d}")
            else:
                normalized_districts.append(d_lower)

        def match_row(row):
            addr_lower = str(row[ADDRESS_COL]).lower()
            name_lower = str(row[NAME_COL]).lower()
            
            # ✅ Kiểm tra địa chỉ có chứa quận không
            has_district = any(district in addr_lower for district in normalized_districts)
            
            # 🆕 Nếu có tham số food → kiểm tra tên quán có chứa món ăn không
            if food_keyword:
                food_lower = food_keyword.lower()
                has_food = food_lower in name_lower
                return has_district and has_food
            
            return has_district

        filtered_df = df[df.apply(match_row, axis=1)]

        # 🔀 SHUFFLE để tránh lấy toàn quán đầu file
        filtered_df = filtered_df.sample(frac=1).reset_index(drop=True)
        
        places = filtered_df.fillna("").to_dict("records")[:15]

        return JsonResponse(
            {
                "status": "success",
                "district": district,
                "food": food_keyword if food_keyword else "Tất cả",
                "count": len(places),
                "places": places,
            }
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    # ==========================================================
# 🧩 PUZZLE GAME - LƯU TIẾN ĐỘ
# ==========================================================

@login_required
@require_http_methods(["GET"])
def get_puzzle_progress(request):
    """
    Lấy tiến độ hoàn thành puzzle của user
    GET /api/puzzle/progress/
    """
    try:
        user = request.user
        progress_list = PuzzleProgress.objects.filter(user=user)
        
        progress_data = {}
        for progress in progress_list:
            progress_data[progress.map_name] = {
                'completed': progress.completed,
                'completion_time': progress.completion_time,
                'moves_count': progress.moves_count,
                'completed_at': progress.completed_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return JsonResponse({
            'status': 'success',
            'progress': progress_data
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
@login_required
def save_puzzle_completion(request):
    """
    Lưu tiến độ hoàn thành puzzle
    POST /api/puzzle/complete/
    Body: {
        "map_name": "banh_mi",
        "completion_time": 120,  // giây
        "moves_count": 45
    }
    """
    try:
        data = json.loads(request.body)
        map_name = data.get('map_name')
        completion_time = data.get('completion_time')
        moves_count = data.get('moves_count')
        
        if not map_name:
            return JsonResponse({
                'status': 'error', 
                'message': 'Thiếu thông tin map_name'
            }, status=400)
        
        # Tạo hoặc cập nhật progress
        progress, created = PuzzleProgress.objects.update_or_create(
            user=request.user,
            map_name=map_name,
            defaults={
                'completed': True,
                'completion_time': completion_time,
                'moves_count': moves_count
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã lưu tiến độ thành công',
            'is_new_record': created
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
@login_required
def reset_puzzle_progress(request, map_name):
    """
    Reset tiến độ puzzle về chưa hoàn thành
    POST /api/puzzle/reset/<map_name>/
    """
    try:
        progress = PuzzleProgress.objects.filter(
            user=request.user,
            map_name=map_name
        ).first()
        
        if progress:
            progress.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'Đã reset tiến độ {map_name}'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'Chưa có tiến độ để reset'
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ===============================
# 🔥 STREAK SYSTEM APIs
# ===============================

@login_required
@require_http_methods(["GET", "POST"])
@csrf_exempt  # ✅ THÊM DECORATOR NÀY

def streak_handler(request):
    user = request.user
    
    if request.method == 'GET':
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            today = date.today()
            
            print(f"🔍 GET Streak - User: {user.username}")
            print(f"   Current streak: {profile.current_streak}")
            print(f"   Last update: {profile.last_streak_date}")
            print(f"   Today: {today}")
            
            if profile.last_streak_date:
                days_diff = (today - profile.last_streak_date).days
                print(f"   Days diff: {days_diff}")
                
                if days_diff > 1:
                    profile.current_streak = 0
                    profile.streak_frozen = True
                    profile.save()
                    print("   ❄️ STREAK FROZEN")
            
            # ✅ KIỂM TRA ĐÃ HIỆN POPUP FROZEN HÔM NAY CHƯA
            from .models import StreakPopupLog
            
            # 🔥 SỬA: Kiểm tra CẢ frozen VÀ milestone popup
            has_shown_frozen_today = StreakPopupLog.objects.filter(
                user=user,
                popup_type='frozen',
                shown_at__date=today
            ).exists()
            
            has_shown_milestone_today = StreakPopupLog.objects.filter(
                user=user,
                popup_type='milestone',
                shown_at__date=today
            ).exists()
            
            print(f"   Has shown frozen popup today: {has_shown_frozen_today}")
            print(f"   Has shown milestone popup today: {has_shown_milestone_today}")
            
            return JsonResponse({
                'status': 'success',
                'streak': profile.current_streak,
                'longest_streak': profile.longest_streak,
                'is_frozen': profile.streak_frozen,
                'last_update': profile.last_streak_date.isoformat() if profile.last_streak_date else None,
                'has_shown_frozen_popup': has_shown_frozen_today,  # ✅ Trả về cho frontend
                'has_shown_milestone_popup': has_shown_milestone_today  # ✅ THÊM field mới
            })
            
        except Exception as e:
            print(f"❌ Error GET streak: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    elif request.method == 'POST':
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            today = date.today()
            
            print(f"\n🔥 POST Streak - User: {user.username}")
            print(f"   Current streak: {profile.current_streak}")
            print(f"   Last update: {profile.last_streak_date}")
            print(f"   Today: {today}")
            
            # Nếu đã update hôm nay rồi thì không tăng nữa
            if profile.last_streak_date == today:
                print("   ⭐ Already updated today - SKIP")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Already updated today',
                    'streak': profile.current_streak,
                    'longest_streak': profile.longest_streak,
                    'increased': False
                })
            
            # Kiểm tra liên tiếp
            if profile.last_streak_date:
                days_diff = (today - profile.last_streak_date).days
                print(f"   Days diff: {days_diff}")
                
                if days_diff == 1:
                    # Tăng streak
                    profile.current_streak += 1
                    profile.streak_frozen = False
                    print(f"   ✅ INCREASED to {profile.current_streak}")
                elif days_diff > 1:
                    # Mất streak, reset về 1
                    profile.current_streak = 1
                    profile.streak_frozen = False
                    print(f"   🔄 RESET to 1 (gap of {days_diff} days)")
            else:
                # Lần đầu tiên
                profile.current_streak = 1
                profile.streak_frozen = False
                print("   🆕 FIRST TIME - Set to 1")
            
            # Cập nhật longest streak
            if profile.current_streak > profile.longest_streak:
                profile.longest_streak = profile.current_streak
            
            profile.last_streak_date = today
            profile.save()
            
            print(f"   💾 SAVED: streak={profile.current_streak}, date={profile.last_streak_date}")
            
            # Kiểm tra milestone
            milestone = None
            if profile.current_streak in [3, 7, 14, 30, 50, 100, 365]:
                milestone = profile.current_streak
                print(f"   🎉 MILESTONE: {milestone} days!")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Streak updated',
                'streak': profile.current_streak,
                'longest_streak': profile.longest_streak,
                'increased': True,
                'milestone': milestone
            })
            
        except Exception as e:
            print(f"❌ Error POST streak: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
# ==========================================================
# 🗑️ API HỦY KẾT BẠN
# ==========================================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def unfriend(request):
    """Hủy kết bạn - XÓA CẢ FRIENDSHIP VÀ FRIEND REQUEST"""
    try:
        data = json.loads(request.body)
        friend_id = data.get('friend_id')
        
        if not friend_id:
            return JsonResponse({'error': 'Thiếu friend_id'}, status=400)
        
        user = request.user
        friend = get_object_or_404(User, id=friend_id)
        
        # ✅ 1. Tìm và xóa quan hệ bạn bè
        friendship = Friendship.objects.filter(
            user1=user, user2=friend
        ).first() or Friendship.objects.filter(
            user1=friend, user2=user
        ).first()
        
        if not friendship:
            return JsonResponse({'error': 'Không phải bạn bè'}, status=400)
        
        friendship.delete()
        
        # ✅ 2. XÓA TẤT CẢ FRIEND REQUEST (cả 2 chiều)
        FriendRequest.objects.filter(
            sender=user, receiver=friend
        ).delete()
        
        FriendRequest.objects.filter(
            sender=friend, receiver=user
        ).delete()
        
        print(f"✅ [UNFRIEND] {user.username} <-> {friend.username}")
        print(f"   - Deleted Friendship")
        print(f"   - Deleted all FriendRequests")
        
        return JsonResponse({
            'success': True,
            'message': 'Đã hủy kết bạn'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

# ==========================================================
# 👥 API XEM QUÁN YÊU THÍCH CỦA BẠN BÈ
# ==========================================================

@login_required
@require_http_methods(["GET"])
def get_friend_favorites(request, friend_id):
    """Lấy danh sách quán yêu thích của một bạn bè"""
    try:
        user = request.user
        friend = get_object_or_404(User, id=friend_id)
        
        # Kiểm tra có phải bạn bè không
        is_friend = Friendship.objects.filter(
            user1=user, user2=friend
        ).exists() or Friendship.objects.filter(
            user1=friend, user2=user
        ).exists()
        
        if not is_friend:
            return JsonResponse({
                'error': 'Bạn phải là bạn bè mới xem được danh sách yêu thích'
            }, status=403)
        
        # Lấy danh sách ID quán yêu thích
        favorite_ids = list(
            FavoritePlace.objects.filter(user=friend).values_list('place_id', flat=True)
        )
        
        if not favorite_ids:
            return JsonResponse({
                'status': 'success',
                'friend_username': friend.username,
                'favorites': []
            })
        
        # Đọc CSV để lấy thông tin chi tiết
        csv_path = os.path.join(settings.BASE_DIR, '..', 'backend', 'Data_with_flavor.csv')
        csv_path = os.path.abspath(csv_path)
        
        favorite_places = []
        try:
            df = pd.read_csv(csv_path)
            df['data_id'] = df['data_id'].astype(str)
            
            filtered_df = df[df['data_id'].isin(favorite_ids)]
            favorite_places = filtered_df.fillna('').to_dict('records')
        except Exception as e:
            print(f"Lỗi đọc CSV: {e}")
        
        return JsonResponse({
            'status': 'success',
            'friend_username': friend.username,
            'favorites': favorite_places
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    # ==========================================================
# 📖 FOOD STORY APIs
# ==========================================================

from .models import FoodStory, UnlockedStory

@login_required
@require_http_methods(["GET"])
def get_food_story(request, map_name):
    """
    Lấy thông tin Food Story của một món ăn
    GET /api/food-story/<map_name>/
    """
    try:
        story = FoodStory.objects.get(map_name=map_name)
        
        # Kiểm tra user đã unlock chưa
        is_unlocked = UnlockedStory.objects.filter(
            user=request.user,
            story=story
        ).exists()
        
        # Nếu chưa unlock -> chỉ trả về thông tin cơ bản
        if not is_unlocked:
            return JsonResponse({
                'status': 'locked',
                'message': 'Hoàn thành puzzle để mở khóa câu chuyện này!',
                'title': story.title,
                'description': story.description,
                'image_url': story.image_url
            })
        
        # Nếu đã unlock -> trả về đầy đủ thông tin
        return JsonResponse({
            'status': 'unlocked',
            'story': {
                'map_name': story.map_name,
                'title': story.title,
                'description': story.description,
                'history': story.history,
                'fun_facts': story.fun_facts,
                'variants': story.variants,
                'origin_region': story.origin_region,
                'image_url': story.image_url,
                'video_url': story.video_url,
                'unesco_recognized': story.unesco_recognized,
                'recognition_text': story.recognition_text
            }
        })
        
    except FoodStory.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy thông tin món ăn'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def unlock_food_story(request, map_name):
    """
    Unlock Food Story khi user hoàn thành puzzle
    POST /api/food-story/unlock/<map_name>/
    """
    try:
        story = FoodStory.objects.get(map_name=map_name)
        
        # Tạo record unlock (hoặc bỏ qua nếu đã unlock)
        unlocked, created = UnlockedStory.objects.get_or_create(
            user=request.user,
            story=story
        )
        
        if created:
            return JsonResponse({
                'status': 'success',
                'message': f'🎉 Đã mở khóa câu chuyện: {story.title}',
                'is_new': True,
                'story_preview': {
                    'title': story.title,
                    'description': story.description,
                    'fun_facts_count': len(story.fun_facts),
                    'variants_count': len(story.variants)
                }
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'Bạn đã mở khóa câu chuyện này rồi',
                'is_new': False
            })
            
    except FoodStory.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy thông tin món ăn'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_all_unlocked_stories(request):
    """
    Lấy danh sách tất cả story user đã unlock
    GET /api/food-stories/unlocked/
    """
    try:
        unlocked = UnlockedStory.objects.filter(user=request.user).select_related('story')
        
        stories_data = []
        for unlock in unlocked:
            stories_data.append({
                'map_name': unlock.story.map_name,
                'title': unlock.story.title,
                'description': unlock.story.description,  # ✅ Đã có sẵn
                'image_url': unlock.story.image_url,
                'unlocked_at': unlock.unlocked_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(stories_data),
            'stories': stories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@require_http_methods(["GET"])
def geocode_proxy(request):
    address = request.GET.get('address', '')
    
    if not address:
        return JsonResponse({'error': 'Thiếu địa chỉ'}, status=400)
    
    url = f'https://nominatim.openstreetmap.org/search?format=json&q={address}&limit=1'
    
    try:
        response = requests.get(
            url, 
            headers={'User-Agent': 'UIA-Food-Finder/1.0'},
            timeout=5
        )
        data = response.json()
        
        if data and len(data) > 0:
            return JsonResponse({
                'lat': data[0]['lat'],
                'lon': data[0]['lon'],
                'display_name': data[0].get('display_name', '')
            })
        else:
            return JsonResponse({'error': 'Không tìm thấy địa điểm'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

# ===============================
# 📧 OTP APIs - SIGNUP FLOW
# ===============================

@csrf_exempt
@require_POST
def send_otp_api(request):
    """
    API gửi OTP đến email khi đăng ký
    POST /api/send-otp/
    Body: {"email": "example@email.com"}
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Vui lòng nhập email'
            }, status=400)
        
        # Kiểm tra email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Email này đã được đăng ký. Vui lòng đăng nhập.'
            }, status=400)
        
        # Tạo OTP mới (method generate_otp sẽ tự động xóa OTP cũ)
        otp = EmailOTP.generate_otp(email)
        
        # Gửi email
        if send_otp_email(email, otp.otp_code):
            # Lưu email vào session để dùng cho bước verify
            request.session['otp_email'] = email
            request.session['otp_sent_at'] = timezone.now().isoformat()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Mã OTP đã được gửi đến email của bạn'
            })
        else:
            otp.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Không thể gửi email. Vui lòng thử lại sau.'
            }, status=500)
            
    except Exception as e:
        print(f"Error in send_otp_api: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Có lỗi xảy ra. Vui lòng thử lại.'
        }, status=500)


@csrf_exempt
@require_POST
def verify_otp_api(request):
    """
    API xác thực OTP
    POST /api/verify-otp/
    Body: {"email": "example@email.com", "otp": "123456"}
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        
        if not email or not otp_code:
            return JsonResponse({
                'status': 'error',
                'message': 'Thiếu thông tin email hoặc OTP'
            }, status=400)
        
        # Tìm OTP
        try:
            otp_obj = EmailOTP.objects.get(email=email, otp_code=otp_code)
        except EmailOTP.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Mã OTP không chính xác'
            }, status=400)
        
        # Kiểm tra OTP đã hết hạn chưa
        if not otp_obj.is_valid():
            otp_obj.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Mã OTP đã hết hạn. Vui lòng gửi lại mã mới.'
            }, status=400)
        
        # Kiểm tra số lần thử
        if otp_obj.attempts >= 5:
            otp_obj.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn đã nhập sai quá nhiều lần. Vui lòng gửi lại mã mới.'
            }, status=400)
        
        # Tăng số lần thử (dù đúng hay sai)
        otp_obj.attempts += 1
        otp_obj.save()
        
        # Xác thực thành công
        otp_obj.delete()
        
        # Lưu vào session để biết email đã được verify
        request.session['verified_email'] = email
        request.session['email_verified_at'] = timezone.now().isoformat()
        
        # Gửi email chào mừng (tạm thời, vì user chưa có username)
        # send_welcome_email(email, email.split('@')[0])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Xác thực thành công! Vui lòng hoàn tất đăng ký.'
        })
        
    except Exception as e:
        print(f"Error in verify_otp_api: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Có lỗi xảy ra. Vui lòng thử lại.'
        }, status=500)


@csrf_exempt
@require_POST
def resend_otp_api(request):
    """
    API gửi lại OTP
    POST /api/resend-otp/
    Body: {"email": "example@email.com"}
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Vui lòng nhập email'
            }, status=400)
        
        # Kiểm tra OTP cũ
        try:
            old_otp = EmailOTP.objects.get(email=email)
            
            # Kiểm tra rate limiting (không cho gửi lại quá nhanh)
            time_since_created = timezone.now() - old_otp.created_at
            if time_since_created.total_seconds() < 60:  # Phải đợi ít nhất 60s
                wait_time = 60 - int(time_since_created.total_seconds())
                return JsonResponse({
                    'status': 'error',
                    'message': f'Vui lòng đợi {wait_time}s trước khi gửi lại',
                    'wait_time': wait_time
                }, status=429)
            
            # Xóa OTP cũ
            old_otp.delete()
        except EmailOTP.DoesNotExist:
            pass
        
        # Tạo OTP mới (method generate_otp sẽ tự động xóa OTP cũ)
        otp = EmailOTP.generate_otp(email)
        
        # Gửi email
        if send_otp_email(email, otp.otp_code):
            # Cập nhật session
            request.session['otp_sent_at'] = timezone.now().isoformat()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Mã OTP mới đã được gửi'
            })
        else:
            otp.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Không thể gửi email. Vui lòng thử lại sau.'
            }, status=500)
            
    except Exception as e:
        print(f"Error in resend_otp_api: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Có lỗi xảy ra. Vui lòng thử lại.'
        }, status=500)


# ===============================
# 🔑 PASSWORD RESET OTP APIs
# ===============================

@csrf_exempt
@require_POST
def send_password_reset_otp_api(request):
    """
    API gửi OTP để reset mật khẩu
    POST /api/password-reset/send-otp/
    Body: {"email": "example@email.com"}
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Vui lòng nhập email'
            }, status=400)
        
        # Kiểm tra email có tồn tại không
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Email này chưa được đăng ký'
            }, status=404)
        
        # Kiểm tra có phải tài khoản Google không
        if SocialAccount.objects.filter(user=user, provider='google').exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Tài khoản Google không thể đặt lại mật khẩu'
            }, status=400)
        
        # Tạo OTP mới (tự động xóa OTP cũ)
        otp = PasswordResetOTP.generate_otp(email)
        
        # Gửi email
        if send_password_reset_otp_email(email, otp.otp_code):
            request.session['password_reset_email'] = email
            request.session['password_reset_sent_at'] = timezone.now().isoformat()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Mã OTP đã được gửi đến email của bạn'
            })
        else:
            otp.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Không thể gửi email. Vui lòng thử lại sau.'
            }, status=500)
            
    except Exception as e:
        print(f"Error in send_password_reset_otp_api: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Có lỗi xảy ra. Vui lòng thử lại.'
        }, status=500)


@csrf_exempt
@require_POST
def verify_password_reset_otp_api(request):
    """
    API xác thực OTP reset mật khẩu
    POST /api/password-reset/verify-otp/
    Body: {"email": "example@email.com", "otp": "123456"}
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        
        if not email or not otp_code:
            return JsonResponse({
                'status': 'error',
                'message': 'Thiếu thông tin email hoặc OTP'
            }, status=400)
        
        # Tìm OTP
        try:
            otp_obj = PasswordResetOTP.objects.get(email=email, otp_code=otp_code)
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Mã OTP không chính xác'
            }, status=400)
        
        # Kiểm tra hết hạn
        if not otp_obj.is_valid():
            otp_obj.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Mã OTP đã hết hạn'
            }, status=400)
        
        # Kiểm tra đã bị khóa
        if otp_obj.is_locked:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn đã nhập sai quá nhiều lần'
            }, status=400)
        
        # Xác thực thành công - đánh dấu và xóa
        otp_obj.mark_as_verified()
        otp_obj.delete()
        
        # Lưu session
        request.session['password_reset_verified'] = email
        request.session['password_reset_verified_at'] = timezone.now().isoformat()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Xác thực thành công'
        })
        
    except Exception as e:
        print(f"Error in verify_password_reset_otp_api: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Có lỗi xảy ra'
        }, status=500)


@csrf_exempt
@require_POST
def reset_password_api(request):
    """
    API đặt lại mật khẩu mới
    POST /api/password-reset/reset/
    Body: {"new_password": "newpass123"}
    """
    try:
        data = json.loads(request.body)
        new_password = data.get('new_password', '').strip()
        
        # Lấy email từ session (đã verify OTP)
        email = request.session.get('password_reset_verified')
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Phiên xác thực không hợp lệ. Vui lòng thực hiện lại từ đầu.'
            }, status=403)
        
        if not new_password:
            return JsonResponse({
                'status': 'error',
                'message': 'Thiếu thông tin'
            }, status=400)
        
        # Kiểm tra độ dài mật khẩu
        if len(new_password) < 6:
            return JsonResponse({
                'status': 'error',
                'message': 'Mật khẩu phải có ít nhất 6 ký tự'
            }, status=400)
        
        # Đặt lại mật khẩu
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Xóa session
            request.session.pop('password_reset_verified', None)
            request.session.pop('password_reset_verified_at', None)
            request.session.pop('password_reset_email', None)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Đặt lại mật khẩu thành công'
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Không tìm thấy người dùng'
            }, status=404)
            
    except Exception as e:
        print(f"Error in reset_password_api: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Có lỗi xảy ra'
        }, status=500)


def password_reset_request_page(request):
    """Trang nhập email để reset mật khẩu"""
    return render(request, 'account/password_reset_request.html')


def password_reset_verify_otp_page(request):
    """Trang nhập OTP reset mật khẩu"""
    email = request.session.get('password_reset_email')
    if not email:
        return redirect('password_reset_request')
    
    return render(request, 'account/password_reset_verify_otp.html', {
        'reset_email': email
    })


def password_reset_form_page(request):
    """Trang nhập mật khẩu mới"""
    email = request.session.get('password_reset_verified')
    if not email:
        return redirect('password_reset_request')
    
    return render(request, 'account/password_reset_form.html', {
        'email': email
    })

@csrf_exempt
@require_POST
@login_required
def unlock_food_story(request, map_name):
    """
    Unlock Food Story khi user hoàn thành puzzle
    POST /api/food-story/unlock/<map_name>/
    """
    try:
        story = FoodStory.objects.get(map_name=map_name)
        
        # Tạo record unlock (hoặc bỏ qua nếu đã unlock)
        unlocked, created = UnlockedStory.objects.get_or_create(
            user=request.user,
            story=story
        )
        
        if created:
            return JsonResponse({
                'status': 'success',
                'message': f'🎉 Đã mở khóa câu chuyện: {story.title}',
                'is_new': True,
                'story_preview': {
                    'title': story.title,
                    'description': story.description,
                    'fun_facts_count': len(story.fun_facts),
                    'variants_count': len(story.variants)
                }
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'Bạn đã mở khóa câu chuyện này rồi',
                'is_new': False
            })
            
    except FoodStory.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy thông tin món ăn'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_all_unlocked_stories(request):
    """
    Lấy danh sách tất cả story user đã unlock
    GET /api/food-stories/unlocked/
    """
    try:
        unlocked = UnlockedStory.objects.filter(user=request.user).select_related('story')
        
        stories_data = []
        for unlock in unlocked:
            stories_data.append({
                'map_name': unlock.story.map_name,
                'title': unlock.story.title,
                'description': unlock.story.description,  # ✅ Đã có sẵn
                'image_url': unlock.story.image_url,
                'unlocked_at': unlock.unlocked_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(stories_data),
            'stories': stories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# ==========================================================
# 🗂️ FOOD PLAN APIs - LƯU THEO ACCOUNT
# ==========================================================

from .models import FoodPlan

@csrf_exempt
@require_POST
@login_required
def save_food_plan_api(request):
    """
    Lưu lịch trình ăn uống vào database
    POST /api/food-plan/save/
    Body: {
        "name": "Lịch trình ngày 15/12",
        "plan_data": {...}  // Toàn bộ dữ liệu plan
    }
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', 'Lịch trình ăn uống')
        plan_data = data.get('plan_data')
        
        if not plan_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Thiếu dữ liệu plan'
            }, status=400)
        
        # Tạo plan mới
        food_plan = FoodPlan.objects.create(
            user=request.user,
            name=name,
            plan_data=plan_data
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã lưu lịch trình',
            'plan_id': food_plan.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_food_plans_api(request):
    """
    Lấy danh sách lịch trình (bao gồm cả plan của mình và plan được share)
    GET /api/accounts/food-plan/list/
    """
    try:
        # 1️⃣ Plans của chính user (KHÔNG bị share)
        own_plans = FoodPlan.objects.filter(user=request.user).order_by('-created_at')
        
        plans_data = []
        
        # Thêm own plans
        for plan in own_plans:
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'plan_data': plan.plan_data,
                'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_shared': False,  # Plan của mình
                'owner_username': request.user.username,
                'owner_id': request.user.id
            })
        
        # 2️⃣ Plans được share CHO user (từ người khác)
        shared_plans = SharedFoodPlan.objects.filter(
            shared_with=request.user,
            is_active=True
        ).select_related('food_plan', 'owner').order_by('-shared_at')
        
        for share in shared_plans:
            # ✅ KIỂM TRA: Chỉ thêm nếu KHÔNG phải plan của chính mình
            if share.food_plan.user != request.user:
                plans_data.append({
                    'id': share.food_plan.id,
                    'name': share.food_plan.name,
                    'plan_data': share.food_plan.plan_data,
                    'created_at': share.shared_at.strftime('%Y-%m-%d %H:%M:%S'),  # ✅ Dùng shared_at
                    'is_shared': True,  # Plan được share
                    'owner_username': share.owner.username,
                    'owner_id': share.owner.id,
                    'permission': share.permission
                })
        
        return JsonResponse({
            'status': 'success',
            'plans': plans_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def delete_food_plan_api(request, plan_id):
    """
    Xóa lịch trình
    POST /api/food-plan/delete/<plan_id>/
    """
    try:
        plan = FoodPlan.objects.get(id=plan_id, user=request.user)
        plan.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã xóa lịch trình'
        })
        
    except FoodPlan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy lịch trình'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
@csrf_exempt
@require_POST
@login_required
def leave_shared_plan_api(request, plan_id):
    """
    User rời khỏi shared plan (ngừng xem)
    POST /api/accounts/food-plan/leave-shared/<plan_id>/
    """
    try:
        # Tìm shared plan
        shared_plan = SharedFoodPlan.objects.filter(
            food_plan_id=plan_id,
            shared_with=request.user,
            is_active=True
        ).first()
        
        if not shared_plan:
            return JsonResponse({
                'status': 'error',
                'message': 'Không tìm thấy lịch trình được chia sẻ'
            }, status=404)
        
        # Đánh dấu là không active (không xóa hẳn)
        shared_plan.is_active = False
        shared_plan.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã ngừng xem lịch trình'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)    
# ==========================================================
# 📤 SHARE FOOD PLAN APIs
# ==========================================================

@csrf_exempt
@require_POST
@login_required
def share_food_plan_api(request, plan_id):
    """
    Share plan cho bạn bè
    POST /api/food-plan/share/<plan_id>/
    Body: {
        "friend_ids": [1, 2, 3],
        "permission": "edit"  // "view" hoặc "edit"
    }
    """
    try:
        data = json.loads(request.body)
        friend_ids = data.get('friend_ids', [])
        permission = data.get('permission', 'edit')
        
        # Lấy plan (chỉ owner mới share được)
        plan = FoodPlan.objects.get(id=plan_id, user=request.user)
        
        # Kiểm tra danh sách bạn bè
        if not friend_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'Vui lòng chọn ít nhất 1 bạn bè'
            }, status=400)
        
        shared_count = 0
        already_shared = []
        
        for friend_id in friend_ids:
            try:
                friend = User.objects.get(id=friend_id)
                
                # Kiểm tra có phải bạn bè không
                is_friend = Friendship.objects.filter(
                    user1=request.user, user2=friend
                ).exists() or Friendship.objects.filter(
                    user1=friend, user2=request.user
                ).exists()
                
                if not is_friend:
                    continue
                
                # Tạo share (hoặc cập nhật nếu đã share trước đó)
                share, created = SharedFoodPlan.objects.get_or_create(
                    food_plan=plan,
                    owner=request.user,
                    shared_with=friend,
                    defaults={'permission': permission}
                )
                
                if created:
                    shared_count += 1
                    create_shared_plan_notification(friend, request.user, plan.id, plan.name)
                else:
                    # Nếu đã share rồi thì cập nhật permission
                    share.permission = permission
                    share.is_active = True
                    share.save()
                    already_shared.append(friend.username)
                    
            except User.DoesNotExist:
                continue
        
        message = f"Đã chia sẻ cho {shared_count} người"
        if already_shared:
            message += f" ({', '.join(already_shared)} đã được chia sẻ trước đó)"
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'shared_count': shared_count
        })
        
    except FoodPlan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy lịch trình'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@login_required
@require_http_methods(["GET"])
def get_current_user_friends(request):
    """
    Lấy danh sách bạn bè của user hiện tại
    GET /api/accounts/my-friends/
    """
    try:
        user = request.user
        
        # Lấy bạn bè
        friends_as_user1 = Friendship.objects.filter(user1=user).values_list('user2', flat=True)
        friends_as_user2 = Friendship.objects.filter(user2=user).values_list('user1', flat=True)
        
        friend_ids = list(friends_as_user1) + list(friends_as_user2)
        friends = User.objects.filter(id__in=friend_ids)
        
        friends_data = [
            {
                'id': friend.id,
                'username': friend.username,
                'email': friend.email
            }
            for friend in friends
        ]
        
        return JsonResponse({'friends': friends_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_shared_plans_api(request):
    """
    Lấy danh sách plan được share cho user
    GET /api/food-plan/shared/
    """
    try:
        # Lấy các plan được share cho user này
        shared_plans = SharedFoodPlan.objects.filter(
            shared_with=request.user,
            is_active=True
        ).select_related('food_plan', 'owner')
        
        plans_data = []
        for share in shared_plans:
            # Kiểm tra xem có suggestion pending không
            pending_suggestion = PlanEditSuggestion.objects.filter(
                shared_plan=share,
                status='pending'
            ).first()
            
            plans_data.append({
                'id': share.food_plan.id,
                'name': share.food_plan.name,
                'owner_username': share.owner.username,
                'owner_id': share.owner.id,
                'permission': share.permission,
                'shared_at': share.shared_at.strftime('%Y-%m-%d %H:%M:%S'),
                'has_pending_suggestion': pending_suggestion is not None,
                'is_shared': True  # Flag để frontend biết đây là shared plan
            })
        
        return JsonResponse({
            'status': 'success',
            'shared_plans': plans_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def submit_plan_suggestion_api(request, plan_id):
    """
    Bạn bè submit suggestion cho plan
    POST /api/accounts/food-plan/suggest/<plan_id>/
    Body: {
        "suggested_data": {...},
        "message": "Tôi đã thêm quán X vào lịch trình"
    }
    """
    try:
        data = json.loads(request.body)
        suggested_data = data.get('suggested_data')
        message = data.get('message', '')
        
        # Kiểm tra user có quyền edit plan này không
        shared_plan = SharedFoodPlan.objects.get(
            food_plan_id=plan_id,
            shared_with=request.user,
            is_active=True,
            permission='edit'
        )
        
        # 🔥 THÊM: Kiểm tra xem đã có suggestion pending chưa
        existing_pending = PlanEditSuggestion.objects.filter(
            shared_plan=shared_plan,
            suggested_by=request.user,
            status='pending'
        ).exists()
        
        if existing_pending:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn đã có 1 đề xuất đang chờ duyệt. Vui lòng đợi chủ sở hữu xử lý trước khi gửi đề xuất mới.'
            }, status=400)
        
        # Lấy dữ liệu gốc
        original_data = shared_plan.food_plan.plan_data
        
        # Tạo suggestion
        suggestion = PlanEditSuggestion.objects.create(
            shared_plan=shared_plan,
            suggested_by=request.user,
            original_data=original_data,
            suggested_data=suggested_data,
            message=message,
            pending_changes={}
        )

        create_suggestion_notification(
            shared_plan.owner,
            request.user,
            plan_id,
            shared_plan.food_plan.name
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã gửi đề xuất chỉnh sửa',
            'suggestion_id': suggestion.id
        })
        
    except SharedFoodPlan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Bạn không có quyền chỉnh sửa lịch trình này'
        }, status=403)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_plan_suggestions_api(request, plan_id):
    """
    Owner xem các suggestion cho plan của mình
    GET /api/accounts/food-plan/suggestions/<plan_id>/
    """
    try:
        # Kiểm tra user có phải owner không
        plan = FoodPlan.objects.get(id=plan_id, user=request.user)
        
        # ✅ LẤY TẤT CẢ SUGGESTIONS (không chỉ pending)
        suggestions = PlanEditSuggestion.objects.filter(
            shared_plan__food_plan=plan
        ).select_related('suggested_by', 'shared_plan').order_by('-created_at')
        
        suggestions_data = []
        for suggestion in suggestions:
            suggestions_data.append({
                'id': suggestion.id,
                'suggested_by_username': suggestion.suggested_by.username,  # ✅ FIX: thêm _username
                'suggested_by_id': suggestion.suggested_by.id,
                'message': suggestion.message,
                'status': suggestion.status,  # ✅ THÊM status
                'created_at': suggestion.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'status': 'success',
            'suggestions': suggestions_data
        })
        
    except FoodPlan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy lịch trình'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@login_required
@require_http_methods(["GET"])
def get_suggestion_detail_api(request, suggestion_id):
    """
    Lấy chi tiết 1 suggestion để so sánh
    GET /api/accounts/food-plan/suggestion-detail/<suggestion_id>/
    """
    try:
        # Lấy suggestion
        suggestion = PlanEditSuggestion.objects.select_related(
            'shared_plan__food_plan',
            'suggested_by'
        ).get(id=suggestion_id)
        
        # Kiểm tra quyền: phải là owner của plan
        if suggestion.shared_plan.food_plan.user != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền xem suggestion này'
            }, status=403)
        
        return JsonResponse({
            'status': 'success',
            'suggestion': {
                'id': suggestion.id,
                'suggested_by_username': suggestion.suggested_by.username,
                'suggested_by_id': suggestion.suggested_by.id,
                'message': suggestion.message,
                'status': suggestion.status,
                'created_at': suggestion.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'current_data': suggestion.original_data,     # ✅ Dữ liệu gốc
                'suggested_data': suggestion.suggested_data   # ✅ Dữ liệu đề xuất
            }
        })
        
    except PlanEditSuggestion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy suggestion'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@login_required
def approve_suggestion_api(request, suggestion_id):
    """
    Owner chấp nhận suggestion
    POST /api/accounts/food-plan/suggestion-approve/<suggestion_id>/
    
    🔥 KHI CHẤP NHẬN 1 ĐỀ XUẤT → TỰ ĐỘNG TỪ CHỐI TẤT CẢ ĐỀ XUẤT PENDING KHÁC
    """
    try:
        # Lấy suggestion
        suggestion = PlanEditSuggestion.objects.select_related(
            'shared_plan__food_plan'
        ).get(id=suggestion_id)
        
        # Kiểm tra quyền
        if suggestion.shared_plan.food_plan.user != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền duyệt suggestion này'
            }, status=403)
        
        # Kiểm tra status
        if suggestion.status != 'pending':
            return JsonResponse({
                'status': 'error',
                'message': f'Suggestion này đã được xử lý ({suggestion.status})'
            }, status=400)
        
        # ✅ CẬP NHẬT PLAN
        plan = suggestion.shared_plan.food_plan
        plan.plan_data = suggestion.suggested_data
        plan.save()
        
        # ✅ CẬP NHẬT STATUS CỦA ĐỀ XUẤT ĐƯỢC CHẤP NHẬN
        suggestion.status = 'accepted'
        suggestion.reviewed_at = timezone.now()
        suggestion.save()

        create_suggestion_approved_notification(
            user=suggestion.suggested_by,  # Người nhận thông báo
            owner_username=request.user.username,  # Chủ sở hữu
            plan_id=plan.id,
            plan_name=plan.name,
            suggestion_id=suggestion.id
        )
        
        # 🔥 MỚI: TỰ ĐỘNG TỪ CHỐI TẤT CẢ ĐỀ XUẤT PENDING KHÁC CHO CÙNG PLAN
        other_pending_suggestions = PlanEditSuggestion.objects.filter(
            shared_plan__food_plan=plan,
            status='pending'
        ).exclude(id=suggestion_id)
        
        rejected_count = 0
        for other_sug in other_pending_suggestions:
            other_sug.status = 'rejected'
            other_sug.reviewed_at = timezone.now()
            other_sug.save()
            rejected_count += 1
        
        message = 'Đã chấp nhận đề xuất thành công'
        if rejected_count > 0:
            message += f' (Đã tự động từ chối {rejected_count} đề xuất khác)'
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'rejected_count': rejected_count
        })
        
    except PlanEditSuggestion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy suggestion'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@csrf_exempt
@require_POST
@login_required
def reject_suggestion_api(request, suggestion_id):
    """
    Owner từ chối suggestion
    POST /api/accounts/food-plan/suggestion-reject/<suggestion_id>/
    """
    try:
        # Lấy suggestion
        suggestion = PlanEditSuggestion.objects.select_related(
            'shared_plan__food_plan'
        ).get(id=suggestion_id)
        
        # Kiểm tra quyền
        if suggestion.shared_plan.food_plan.user != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền xử lý suggestion này'
            }, status=403)
        
        # Kiểm tra status
        if suggestion.status != 'pending':
            return JsonResponse({
                'status': 'error',
                'message': f'Suggestion này đã được xử lý ({suggestion.status})'
            }, status=400)
        
        # ✅ CẬP NHẬT STATUS
        suggestion.status = 'rejected'
        suggestion.reviewed_at = timezone.now()
        suggestion.save()
        
        # 🔥 THÊM: Tạo thông báo cho người đề xuất
        from .utils import create_suggestion_rejected_notification
        
        create_suggestion_rejected_notification(
            user=suggestion.suggested_by,  # Người nhận thông báo
            owner_username=request.user.username,  # Chủ sở hữu
            plan_id=suggestion.shared_plan.food_plan.id,
            plan_name=suggestion.shared_plan.food_plan.name,
            suggestion_id=suggestion.id
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã từ chối đề xuất'
        })
        
    except PlanEditSuggestion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy suggestion'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@login_required
def review_suggestion_api(request, suggestion_id):
    """
    Owner accept/reject suggestion
    POST /api/food-plan/suggestion/review/<suggestion_id>/
    Body: {
        "action": "accept" / "reject"
    }
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        if action not in ['accept', 'reject']:
            return JsonResponse({
                'status': 'error',
                'message': 'Action không hợp lệ'
            }, status=400)
        
        # Lấy suggestion
        suggestion = PlanEditSuggestion.objects.get(id=suggestion_id)
        
        # Kiểm tra user có phải owner không
        if suggestion.shared_plan.owner != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền review suggestion này'
            }, status=403)
        
        if action == 'accept':
            # Cập nhật plan với dữ liệu mới
            plan = suggestion.shared_plan.food_plan
            plan.plan_data = suggestion.suggested_data
            plan.save()
            
            suggestion.status = 'accepted'
            message = 'Đã chấp nhận thay đổi'
        else:
            suggestion.status = 'rejected'
            message = 'Đã từ chối thay đổi'
        
        suggestion.reviewed_at = timezone.now()
        suggestion.save()
        
        return JsonResponse({
            'status': 'success',
            'message': message
        })
        
    except PlanEditSuggestion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy suggestion'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)     

@login_required
@require_http_methods(["GET"])
def get_my_suggestions_api(request, plan_id):
    """
    Lấy danh sách suggestion của user cho 1 plan cụ thể
    GET /api/accounts/food-plan/my-suggestions/<plan_id>/
    """
    try:
        # Kiểm tra user có được share plan này không
        shared_plan = SharedFoodPlan.objects.filter(
            food_plan_id=plan_id,
            shared_with=request.user,
            is_active=True
        ).first()
        
        if not shared_plan:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền xem lịch trình này'
            }, status=403)
        
        # Lấy tất cả suggestions của user này cho plan này
        suggestions = PlanEditSuggestion.objects.filter(
            shared_plan=shared_plan,
            suggested_by=request.user
        ).order_by('-created_at')
        
        suggestions_data = []
        for suggestion in suggestions:
            # 🔥 FIX TIMEZONE: Format datetime với timezone
            created_at = suggestion.created_at
            reviewed_at = suggestion.reviewed_at
            
            # Đảm bảo có timezone info
            if created_at and created_at.tzinfo is None:
                from django.utils import timezone
                created_at = timezone.make_aware(created_at)
            
            if reviewed_at and reviewed_at.tzinfo is None:
                from django.utils import timezone
                reviewed_at = timezone.make_aware(reviewed_at)
            
            suggestions_data.append({
                'id': suggestion.id,
                'message': suggestion.message,
                'status': suggestion.status,
                # 🔥 THAY ĐỔI: Trả về ISO format với timezone (giữ nguyên UTC)
                'created_at': created_at.isoformat() if created_at else None,
                'reviewed_at': reviewed_at.isoformat() if reviewed_at else None
            })
        
        return JsonResponse({
            'status': 'success',
            'suggestions': suggestions_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@login_required
def suggestion_approve_single(request):
    """
    Chấp nhận từng thay đổi riêng lẻ
    POST /api/accounts/food-plan/suggestion-approve-single/
    Body: {
        "suggestion_id": 123,
        "change_type": "added",  // added/removed/modified
        "change_key": "custom_1234567890"
    }
    """
    try:
        data = json.loads(request.body)
        suggestion_id = data.get('suggestion_id')
        change_type = data.get('change_type')
        change_key = data.get('change_key')
        
        # ✅ SỬA: Dùng đúng model PlanEditSuggestion
        suggestion = PlanEditSuggestion.objects.select_related(
            'shared_plan__food_plan'
        ).get(id=suggestion_id)
        
        # ✅ Kiểm tra quyền: phải là owner
        if suggestion.shared_plan.food_plan.user != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền duyệt suggestion này'
            }, status=403)
        
        # ✅ Kiểm tra status
        if suggestion.status != 'pending':
            return JsonResponse({
                'status': 'error',
                'message': f'Suggestion đã được xử lý ({suggestion.status})'
            }, status=400)
        
        # ✅ Lấy dữ liệu
        plan = suggestion.shared_plan.food_plan
        current_data = list(plan.plan_data)  # Copy để tránh modify trực tiếp
        suggested_data = suggestion.suggested_data
        
        print(f"\n🔍 [SINGLE APPROVE] Type: {change_type}, Key: {change_key}")
        print(f"   Current data length: {len(current_data)}")
        print(f"   Suggested data length: {len(suggested_data)}")
        
        # ✅ ÁP DỤNG THAY ĐỔI
        if change_type == 'added':
            # Thêm quán mới
            new_item = next((item for item in suggested_data if item['key'] == change_key), None)
            if new_item:
                # Kiểm tra xem đã tồn tại chưa
                if not any(item['key'] == change_key for item in current_data):
                    current_data.append(new_item)
                    print(f"   ✅ ADDED: {change_key}")
                else:
                    print(f"   ⚠️ SKIP: {change_key} already exists")
            else:
                print(f"   ❌ NOT FOUND in suggested_data")
                
        elif change_type == 'removed':
            # Xóa quán
            original_length = len(current_data)
            current_data = [item for item in current_data if item['key'] != change_key]
            if len(current_data) < original_length:
                print(f"   ✅ REMOVED: {change_key}")
            else:
                print(f"   ⚠️ NOT FOUND to remove: {change_key}")
                
        elif change_type == 'modified':
            # Sửa quán
            new_item = next((item for item in suggested_data if item['key'] == change_key), None)
            if new_item:
                for i, item in enumerate(current_data):
                    if item['key'] == change_key:
                        current_data[i] = new_item
                        print(f"   ✅ MODIFIED: {change_key}")
                        break
            else:
                print(f"   ❌ NOT FOUND in suggested_data")
        
        # ✅ LƯU LẠI
        plan.plan_data = current_data
        plan.save()
        
        print(f"   💾 SAVED - New length: {len(current_data)}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã áp dụng thay đổi',
            'new_count': len(current_data)
        })
        
    except PlanEditSuggestion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy suggestion'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
@csrf_exempt
@require_POST
@login_required
def approve_all_changes_api(request):
    """
    Chấp nhận tất cả thay đổi đã đánh dấu
    POST /api/accounts/food-plan/approve-all-changes/
    """
    try:
        data = json.loads(request.body)
        suggestion_id = data.get('suggestion_id')
        approved_changes = data.get('approved_changes', [])
        
        # Lấy suggestion
        suggestion = PlanEditSuggestion.objects.select_related(
            'shared_plan__food_plan'
        ).get(id=suggestion_id)
        
        # Kiểm tra quyền
        if suggestion.shared_plan.food_plan.user != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền duyệt suggestion này'
            }, status=403)
        
        # Kiểm tra status
        if suggestion.status != 'pending':
            return JsonResponse({
                'status': 'error',
                'message': f'Suggestion đã được xử lý ({suggestion.status})'
            }, status=400)
        
        # Áp dụng các thay đổi
        plan = suggestion.shared_plan.food_plan
        current_data = list(plan.plan_data)
        suggested_data = suggestion.suggested_data
        
        success_count = 0
        
        for change in approved_changes:
            change_type = change['changeType']
            change_key = change['changeKey']
            
            if change_type == 'added':
                new_item = next((item for item in suggested_data if item['key'] == change_key), None)
                if new_item and not any(item['key'] == change_key for item in current_data):
                    current_data.append(new_item)
                    success_count += 1
                    
            elif change_type == 'removed':
                original_length = len(current_data)
                current_data = [item for item in current_data if item['key'] != change_key]
                if len(current_data) < original_length:
                    success_count += 1
                    
            elif change_type == 'modified':
                new_item = next((item for item in suggested_data if item['key'] == change_key), None)
                if new_item:
                    for i, item in enumerate(current_data):
                        if item['key'] == change_key:
                            current_data[i] = new_item
                            success_count += 1
                            break
        
        # ✅ LƯU PLAN
        plan.plan_data = current_data
        plan.save()
        
        # 🔥 QUAN TRỌNG: CẬP NHẬT STATUS SUGGESTION
        suggestion.status = 'accepted'
        suggestion.reviewed_at = timezone.now()
        suggestion.save()
        
        # 🔥 MỚI: TỰ ĐỘNG TỪ CHỐI TẤT CẢ ĐỀ XUẤT PENDING KHÁC
        other_pending_suggestions = PlanEditSuggestion.objects.filter(
            shared_plan__food_plan=plan,
            status='pending'
        ).exclude(id=suggestion_id)
        
        rejected_count = 0
        for other_sug in other_pending_suggestions:
            other_sug.status = 'rejected'
            other_sug.reviewed_at = timezone.now()
            other_sug.save()
            rejected_count += 1
        
        print(f"✅ [APPROVE ALL] Updated suggestion {suggestion_id} to 'accepted'")
        print(f"🔥 Auto-rejected {rejected_count} other pending suggestions")
        
        message = f'Đã áp dụng {success_count} thay đổi'
        if rejected_count > 0:
            message += f' (Đã tự động từ chối {rejected_count} đề xuất khác)'
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'applied_count': success_count,
            'rejected_count': rejected_count
        })
        
    except PlanEditSuggestion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy suggestion'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)    

@login_required
@require_http_methods(["GET"])
def check_pending_suggestion_api(request, plan_id):
    """
    Kiểm tra xem user có suggestion pending cho plan này không
    GET /api/accounts/food-plan/check-pending/<plan_id>/
    """
    try:
        # Kiểm tra user có được share plan này không
        shared_plan = SharedFoodPlan.objects.filter(
            food_plan_id=plan_id,
            shared_with=request.user,
            is_active=True
        ).first()
        
        if not shared_plan:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn không có quyền xem lịch trình này'
            }, status=403)
        
        # Kiểm tra pending suggestion
        has_pending = PlanEditSuggestion.objects.filter(
            shared_plan=shared_plan,
            suggested_by=request.user,
            status='pending'
        ).exists()
        
        return JsonResponse({
            'status': 'success',
            'has_pending': has_pending
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)    
# ==========================================================
# 🍽️ USER PREFERENCES APIs
# ==========================================================

@login_required
@require_http_methods(["GET"])
def get_user_preferences(request):
    """
    Lấy toàn bộ sở thích của user
    GET /api/preferences/
    """
    try:
        preferences = UserPreference.objects.filter(user=request.user)
        
        # Phân loại theo type
        data = {
            'likes': [p.item for p in preferences.filter(preference_type='like')],
            'dislikes': [p.item for p in preferences.filter(preference_type='dislike')],
            'allergies': [p.item for p in preferences.filter(preference_type='allergy')],
            'medicalconditions': [p.item for p in preferences.filter(preference_type='medicalcondition')]
        }
        
        return JsonResponse({
            'status': 'success',
            'preferences': data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required  # ✅ ĐẢM BẢO USER ĐÃ LOGIN
def save_user_preference(request):
    try:
        data = json.loads(request.body)
        pref_type = data.get('type')  # like/dislike/allergy/medicalcondition
        item = data.get('item', '').strip()
        
        print(f"[SAVE PREF] User: {request.user.username}")
        print(f"[SAVE PREF] Type: {pref_type}")
        print(f"[SAVE PREF] Item: {item}")
        
        if not pref_type or not item:
            return JsonResponse({
                'status': 'error',
                'message': 'Thiếu thông tin type hoặc item'
            }, status=400)
        
        # ✅ BƯỚC 1: XÓA TẤT CẢ CONFLICT CŨ (trừ type hiện tại)
        conflict_types = ['like', 'dislike', 'allergy', 'medicalcondition']
        conflict_types.remove(pref_type)  # Loại bỏ type đang thêm
        
        deleted_count = 0
        for conflict_type in conflict_types:
            deleted, _ = UserPreference.objects.filter(
                user=request.user,
                preference_type=conflict_type,
                item=item
            ).delete()
            
            if deleted > 0:
                print(f"[CONFLICT] Deleted {deleted} '{conflict_type}' for item: {item}")
                deleted_count += deleted
        
        # ✅ BƯỚC 2: TẠO HOẶC BỎ QUA NẾU ĐÃ TỒN TẠI
        preference, created = UserPreference.objects.get_or_create(
            user=request.user,
            preference_type=pref_type,
            item=item
        )
        
        print(f"[SAVE PREF] Created: {created}")
        
        message = f'Đã lưu: {item}'
        if deleted_count > 0:
            message += f' (đã xóa {deleted_count} preference cũ xung đột)'
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'is_new': created,
            'conflicts_removed': deleted_count
        })
            
    except Exception as e:
        print(f"[SAVE PREF ERROR] {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def delete_user_preference(request):
    """
    Xóa 1 preference
    POST /api/preferences/delete/
    Body: {
        "type": "like",
        "item": "Phở bò"
    }
    """
    try:
        data = json.loads(request.body)
        pref_type = data.get('type')
        item = data.get('item', '').strip()
        
        if not pref_type or not item:
            return JsonResponse({
                'status': 'error',
                'message': 'Thiếu thông tin'
            }, status=400)
        
        # Tìm và xóa
        deleted_count, _ = UserPreference.objects.filter(
            user=request.user,
            preference_type=pref_type,
            item=item
        ).delete()
        
        if deleted_count > 0:
            return JsonResponse({
                'status': 'success',
                'message': f'Đã xóa: {item}'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Không tìm thấy'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# ==========================================================
# 🔔 NOTIFICATION APIs
# ==========================================================

@login_required
@require_http_methods(["GET"])
def get_notifications_api(request):
    """
    Lấy danh sách thông báo của user
    GET /api/accounts/notifications/
    Query params:
        - unread_only=true: chỉ lấy thông báo chưa đọc
        - limit=20: giới hạn số lượng
    """
    try:
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        limit = int(request.GET.get('limit', 50))
        
        # Query notifications
        notifications = Notification.objects.filter(user=request.user)
        
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        notifications = notifications[:limit]
        
        # Serialize data
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'type': notif.notification_type,
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'read_at': notif.read_at.isoformat() if notif.read_at else None,
                'related_id': notif.related_id,
                'metadata': notif.metadata
            })
        
        # Đếm số thông báo chưa đọc
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({
            'status': 'success',
            'notifications': notifications_data,
            'unread_count': unread_count
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def mark_notification_read_api(request, notification_id):
    """
    Đánh dấu 1 thông báo đã đọc
    POST /api/accounts/notifications/<id>/read/
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        notification.mark_as_read()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã đánh dấu đã đọc'
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy thông báo'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def mark_all_notifications_read_api(request):
    """
    Đánh dấu TẤT CẢ thông báo đã đọc
    POST /api/accounts/notifications/read-all/
    """
    try:
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({
            'status': 'success',
            'message': f'Đã đánh dấu {updated_count} thông báo',
            'count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def delete_notification_api(request, notification_id):
    """
    Xóa 1 thông báo
    POST /api/accounts/notifications/<id>/delete/
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        notification.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã xóa thông báo'
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy thông báo'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def clear_all_notifications_api(request):
    """
    Xóa TẤT CẢ thông báo đã đọc
    POST /api/accounts/notifications/clear-all/
    """
    try:
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Đã xóa {deleted_count} thông báo',
            'count': deleted_count
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@login_required
def notification_stream(request):
    """SSE endpoint để push thông báo real-time"""
    
    user_id = request.user.id
    
    def event_stream():
        # ✅ TẠO QUEUE cho user này
        notification_queue = queue.Queue()
        sse_connections[user_id] = notification_queue
        
        print(f"✅ SSE Connected: {request.user.username} (user_id={user_id})")
        
        # ✅ GỬI INITIAL MESSAGE (với padding để force flush)
        initial_msg = f"data: {json.dumps({'type': 'connected', 'message': 'Connected', 'user': request.user.username})}\n\n"
        initial_msg += ": " + " " * 2048 + "\n\n"  # 🔥 PADDING để force browser flush
        yield initial_msg
        
        last_check = timezone.now()
        
        try:
            while True:
                # ✅ 1. CHECK QUEUE (non-blocking, timeout 5s)
                try:
                    # 🔥 TĂNG TIMEOUT lên 5s để ổn định hơn
                    notification_data = notification_queue.get(timeout=5)
                    
                    print(f"📤 [SSE] Sending real-time notification to {request.user.username}")
                    
                    # Đếm unread
                    unread_count = Notification.objects.filter(
                        user=request.user,
                        is_read=False
                    ).count()
                    
                    event_data = {
                        'type': 'new_notifications',
                        'notifications': [notification_data],
                        'unread_count': unread_count
                    }
                    
                    # 🔥 FORMAT CHUẨN SSE + PADDING
                    message = f"data: {json.dumps(event_data)}\n\n"
                    message += ": " + " " * 2048 + "\n\n"  # Force flush
                    yield message
                    
                except queue.Empty:
                    # 🔥 GỬI HEARTBEAT để giữ connection sống
                    heartbeat_msg = f": heartbeat {timezone.now().isoformat()}\n\n"
                    yield heartbeat_msg
                    
                    # ✅ 2. FALLBACK: Poll database (mỗi 5s)
                    new_notifications = Notification.objects.filter(
                        user=request.user,
                        created_at__gt=last_check,
                        is_read=False
                    ).order_by('-created_at')
                    
                    if new_notifications.exists():
                        last_check = timezone.now()
                        
                        notifications_data = []
                        for notif in new_notifications:
                            notifications_data.append({
                                'id': notif.id,
                                'type': notif.notification_type,
                                'title': notif.title,
                                'message': notif.message,
                                'is_read': notif.is_read,
                                'created_at': notif.created_at.isoformat(),
                                'related_id': notif.related_id,
                                'metadata': notif.metadata
                            })
                        
                        unread_count = Notification.objects.filter(
                            user=request.user,
                            is_read=False
                        ).count()
                        
                        event_data = {
                            'type': 'new_notifications',
                            'notifications': notifications_data,
                            'unread_count': unread_count
                        }
                        
                        message = f"data: {json.dumps(event_data)}\n\n"
                        message += ": " + " " * 2048 + "\n\n"
                        yield message
                        
                        print(f"📤 [POLL] Sent {len(notifications_data)} notifications to {request.user.username}")
                    
        except GeneratorExit:
            # ✅ CLEANUP khi client disconnect
            if user_id in sse_connections:
                del sse_connections[user_id]
            print(f"🔌 Client disconnected: {request.user.username} (user_id={user_id})")
            
        except Exception as e:
            print(f"❌ SSE Error for {request.user.username}: {e}")
            import traceback
            traceback.print_exc()
            
            # Cleanup
            if user_id in sse_connections:
                del sse_connections[user_id]
            
            error_msg = f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            yield error_msg
    
    # ✅ TẠO RESPONSE
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream; charset=utf-8'
    )
    
    # 🔥 QUAN TRỌNG: Headers để KHÔNG buffer
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Credentials'] = 'true'
    
    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_favorite_view(request, user_id):
    try:
        viewed_user = User.objects.get(id=user_id)
        viewer = request.user

        if viewer.id == viewed_user.id:
            return Response({
                'status': 'ignored',
                'message': 'Không tạo thông báo cho chính mình'
            })

        notification = Notification.objects.create(
            user=viewed_user,  # Người nhận thông báo
            notification_type='favorite_viewed',  # 🔴 SỬA CHỖ NÀY
            title='Có người xem quán yêu thích của bạn 👀',
            message=f'{viewer.username} đã xem danh sách quán yêu thích của bạn',
            related_id=viewer.id
        )

        return Response({
            'status': 'success',
            'message': 'Đã ghi nhận lượt xem',
            'notification_id': notification.id
        })

    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Không tìm thấy user'
        }, status=404)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@csrf_exempt
@require_POST
@login_required
def log_streak_popup_api(request):
    """
    Log rằng popup đã được hiện
    POST /api/accounts/streak/log-popup/
    Body: {
        "popup_type": "frozen",  // frozen/milestone
        "streak_value": 0
    }
    """
    try:
        from .models import StreakPopupLog
        
        data = json.loads(request.body)
        popup_type = data.get('popup_type', 'frozen')
        streak_value = data.get('streak_value', 0)
        
        # Tạo log
        StreakPopupLog.objects.create(
            user=request.user,
            popup_type=popup_type,
            streak_value=streak_value
        )
        
        print(f"✅ [LOG POPUP] User: {request.user.username}, Type: {popup_type}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã log popup'
        })
        
    except Exception as e:
        print(f"❌ [LOG POPUP ERROR] {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)