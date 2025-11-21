from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
from .models import ChatConversation, ChatMessage
from django.shortcuts import render, redirect, get_object_or_404
from .models import UserProfile, FavoritePlace
from django.conf import settings
import json, os
import pandas as pd
from datetime import datetime

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
    
    # === GET REVIEW ===
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
            return JsonResponse({"success": False, "message": "Bạn cần đăng nhập"}, status=403)
        
        # 👇 GỌI HÀM HELPER (Logic lấy avatar tự động chuẩn xác)
        # Dù user dùng Google hay ảnh tự up, hàm này đều lấy đúng cái mới nhất
        avatar_nguoi_dung = get_user_avatar(request.user)

        try:
            data = json.loads(request.body)
            comment = data.get("comment")
            rating = int(data.get("rating", 0))
            if not comment or rating == 0:
                return JsonResponse({"success": False, "message": "Thiếu thông tin"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Lỗi dữ liệu"}, status=400)

        # Logic lưu file (giữ nguyên)
        all_reviews = load_user_reviews()
        if all_reviews.get(place_id) is None:
            all_reviews[place_id] = {"google": [], "user": []}
        
        # Đảm bảo cấu trúc dict
        if isinstance(all_reviews[place_id], list):
             all_reviews[place_id] = {"google": all_reviews[place_id], "user": []}

        new_review = {
            "ten": request.user.username,
            "avatar": avatar_nguoi_dung, # ✅ Lưu URL avatar chuẩn vào JSON
            "rating": rating,
            "comment": comment,
            "date": datetime.now().isoformat()
        }
        
        all_reviews[place_id]["user"].append(new_review)
        save_user_reviews(all_reviews)
        
        return JsonResponse({"success": True, "message": "Đánh giá thành công!"})

    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


# ------------------------LƯU LỊCH SỬ CHATBOT AI--------------------------
# --- Helper để lấy Avatar ---
def get_user_avatar(user):
    # 1. Ảnh mặc định
    default_avatar = 'https://cdn-icons-png.flaticon.com/512/847/847969.png'
    
    if not user.is_authenticated:
        return default_avatar

    # 2. Kiểm tra UserProfile
    try:
        # hasattr kiểm tra xem user có quan hệ với profile không
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar_url = user.profile.avatar.url
            # user.profile.avatar.url sẽ trả về đường dẫn file media
            if avatar_url.startswith('/'):
                return 'http://127.0.0.1:8000' + avatar_url
            return avatar_url
    except Exception:
        pass

    # 3. Kiểm tra tài khoản Google 
    try:
        social_account = SocialAccount.objects.get(user=user, provider='google')
        return social_account.get_avatar_url()
    except SocialAccount.DoesNotExist:
        pass
        
    # 4. Nếu không có gì hết thì trả về mặc định
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
                    title_text = content[:40] + "..." if len(content) > 40 else content
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
            'username': request.user.username  # Gửi kèm tên user nếu muốn
        })
    else:
        # Nếu chưa đăng nhập
        return JsonResponse({'is_authenticated': False})
    
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
             return JsonResponse({'status': 'error', 'message': 'Chưa đăng nhập'}, status=401)

        # Tìm hoặc tạo profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Lưu ảnh mới
        profile.avatar = request.FILES['avatar']
        profile.save()
        
        # Trả về URL mới ngay lập tức để giao diện cập nhật
        return JsonResponse({
            'status': 'success', 
            'new_avatar_url': 'http://127.0.0.1:8000' + profile.avatar.url
        })
    
    return JsonResponse({'status': 'error', 'message': 'Lỗi upload'}, status=400)

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
        favorite, created = FavoritePlace.objects.get_or_create(
            user=request.user, 
            place_id=str(place_id)
        )
        
        if not created:
            favorite.delete()
            return JsonResponse({'status': 'removed', 'message': 'Đã xóa khỏi yêu thích'})
        else:
            return JsonResponse({'status': 'added', 'message': 'Đã thêm vào yêu thích'})
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_user_favorites_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Chưa đăng nhập', 'favorites': []}, status=403)

    user = request.user
    
    # Lấy danh sách ID từ DB
    favorite_ids = list(FavoritePlace.objects.filter(user=user).values_list('place_id', flat=True))
    
    # Đọc CSV
    csv_path = os.path.join(settings.BASE_DIR, '..', 'backend', 'Data_with_flavor.csv')
    csv_path = os.path.abspath(csv_path)

    favorite_places = []
    try:
        df = pd.read_csv(csv_path)
        df['data_id'] = df['data_id'].astype(str) # Ép kiểu string để so sánh
        
        # Lọc những quán có id nằm trong danh sách favorite
        filtered_df = df[df['data_id'].isin(favorite_ids)]
        
        # Chuyển dữ liệu thành List of Dictionaries
        # fillna('') để tránh lỗi null khi chuyển sang JSON
        favorite_places = filtered_df.fillna('').to_dict('records')
        
    except Exception as e:
        print(f"Lỗi đọc CSV: {e}")
    
    # Trả về JSON 
    return JsonResponse({'favorites': favorite_places})