from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.models import SocialAccount
import json
from datetime import datetime

# ==========================================================
# ✏️ LOGIC API THÊM REVIEW (ĐÃ CHUYỂN TỪ FLASK SANG)
# ==========================================================


# from .utils import load_user_reviews, save_user_reviews


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
# -----------------------------------------------------------

@csrf_exempt
def reviews_api(request: HttpRequest, place_id: str):
    
    # === 1. XỬ LÝ VIỆC LẤY (GET) REVIEW ===
    if request.method == 'GET':
        all_reviews = load_user_reviews()
        place_data = all_reviews.get(place_id)
        
        # Tạo dữ liệu review chuẩn
        if place_data is None:
            review_content = {"google": [], "user": []}
        elif isinstance(place_data, list):
            review_content = {"google": place_data, "user": []}
        else:
            review_content = place_data

        # === LẤY THÔNG TIN USER ĐANG ĐĂNG NHẬP ===
        user_info = {'is_logged_in': False}
        if request.user.is_authenticated:
            avatar_url = 'https://cdn-icons-png.flaticon.com/512/847/847969.png' # Avatar mặc định
            try:
                # Thử lấy avatar từ tài khoản Google
                social_account = SocialAccount.objects.get(user=request.user, provider='google')
                avatar_url = social_account.get_avatar_url()
            except SocialAccount.DoesNotExist:
                pass # Nếu không có, dùng avatar mặc định

            user_info = {
                'is_logged_in': True,
                'username': request.user.username,
                'avatar': avatar_url
            }
        
        # === TRẢ VỀ JSON (gộp cả review và user) ===
        response_data = {
            'reviews': review_content, # Dữ liệu review
            'user': user_info          # Thông tin người dùng
        }
        return JsonResponse(response_data)
    
    # === 2. XỬ LÝ VIỆC THÊM (POST) REVIEW (Phải đăng nhập) ===
    if request.method == 'POST':
        # Kiểm tra đăng nhập thủ công 
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Bạn cần đăng nhập để đánh giá"}, status=403)
        
        user = request.user
        ten_nguoi_dung = user.username

        avatar_nguoi_dung = 'https://cdn-icons-png.flaticon.com/512/847/847969.png' # Avatar mặc định
        try:
            # Thử lấy avatar từ tài khoản Google
            social_account = SocialAccount.objects.get(user=user, provider='google')
            avatar_nguoi_dung = social_account.get_avatar_url()
        except SocialAccount.DoesNotExist:
            # Nếu user đăng nhập bằng tài khoản thường (không phải Google)
            # bạn có thể thêm logic lấy avatar từ Profile (nếu có) ở đây
            pass

        # Lấy dữ liệu từ body
        try:
            data = json.loads(request.body)
            comment = data.get("comment")
            rating = int(data.get("rating", 0))
            if not comment or rating == 0:
                return JsonResponse({"success": False, "message": "Vui lòng nhập comment và chọn sao"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Dữ liệu JSON không hợp lệ"}, status=400)

        # Logic lưu file (giữ nguyên)
        all_reviews = load_user_reviews()
        value = all_reviews.get(place_id)
        if value is None:
            all_reviews[place_id] = {"google": [], "user": []}
        elif isinstance(value, list):
            all_reviews[place_id] = {"google": value, "user": []}

        new_review = {
            "ten": ten_nguoi_dung,
            "avatar": avatar_nguoi_dung,
            "rating": rating,
            "comment": comment,
            "date": datetime.now().isoformat()
            
        }
        all_reviews[place_id]["user"].append(new_review)
        save_user_reviews(all_reviews)
        
        return JsonResponse({"success": True, "message": f"✅ {ten_nguoi_dung} đã thêm đánh giá!"})

    
    # === 3. Nếu là method khác (PUT, DELETE...) ===
    return JsonResponse({"success": False, "message": "Method không được hỗ trợ"}, status=405)