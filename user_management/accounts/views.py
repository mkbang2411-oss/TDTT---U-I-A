from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
from .models import ChatConversation, ChatMessage
from django.shortcuts import render, redirect, get_object_or_404
from .models import UserProfile, FavoritePlace, PuzzleProgress
from django.conf import settings
import json, os
import pandas as pd
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from .models import FriendRequest, Friendship
from datetime import date, timedelta
from django.views.decorators.csrf import csrf_exempt

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

@login_required
@require_http_methods(["GET"])
def get_user_favorites_api(request):
    user = request.user

    # Lấy danh sách ID từ DB
    favorite_ids = list(
        FavoritePlace.objects.filter(user=user).values_list('place_id', flat=True)
    )

    # Đọc CSV
    csv_path = os.path.join(settings.BASE_DIR, '..', 'backend', 'Data_with_flavor.csv')
    csv_path = os.path.abspath(csv_path)

    favorite_places = []
    try:
        df = pd.read_csv(csv_path)
        df['data_id'] = df['data_id'].astype(str)  # Ép kiểu string để so sánh

        # Lọc những quán có id nằm trong danh sách favorite
        filtered_df = df[df['data_id'].isin(favorite_ids)]

        # Chuyển dữ liệu thành List of Dict
        favorite_places = filtered_df.fillna('').to_dict('records')
    except Exception as e:
        print(f"Lỗi đọc CSV: {e}")

    # Trả về JSON
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
        
        # Kiểm tra đã gửi lời mời chưa
        if FriendRequest.objects.filter(sender=sender, receiver=receiver, status='pending').exists():
            return JsonResponse({'error': 'Đã gửi lời mời rồi'}, status=400)
        
        # Tạo lời mời kết bạn
        friend_request = FriendRequest.objects.create(sender=sender, receiver=receiver)
        
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
from django.contrib.auth.decorators import login_required
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
            
            return JsonResponse({
                'status': 'success',
                'streak': profile.current_streak,
                'longest_streak': profile.longest_streak,
                'is_frozen': profile.streak_frozen,
                'last_update': profile.last_streak_date.isoformat() if profile.last_streak_date else None
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
    """Hủy kết bạn"""
    try:
        data = json.loads(request.body)
        friend_id = data.get('friend_id')
        
        if not friend_id:
            return JsonResponse({'error': 'Thiếu friend_id'}, status=400)
        
        user = request.user
        friend = get_object_or_404(User, id=friend_id)
        
        # Tìm và xóa quan hệ bạn bè (có thể user1 hoặc user2)
        friendship = Friendship.objects.filter(
            user1=user, user2=friend
        ).first() or Friendship.objects.filter(
            user1=friend, user2=user
        ).first()
        
        if not friendship:
            return JsonResponse({'error': 'Không phải bạn bè'}, status=400)
        
        friendship.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã hủy kết bạn'
        })
        
    except Exception as e:
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