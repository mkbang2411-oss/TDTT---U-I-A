"""
Gemini AI utilities cho việc kiểm duyệt nội dung review
Hỗ trợ nhiều API keys với cơ chế fallback tự động
"""
import os
import json
import google.generativeai as genai
from django.conf import settings

# ==================== QUẢN LÝ NHIỀU API KEYS ====================

class GeminiAPIManager:
    """
    Quản lý nhiều Gemini API keys với cơ chế fallback
    """
    
    def __init__(self):
        # Đọc danh sách API keys từ env (cách nhau bởi dấu phẩy)
        keys_string = os.getenv('GEMINI_API_KEYS', '')
        
        # Tách thành list và loại bỏ khoảng trắng
        self.api_keys = [key.strip() for key in keys_string.split(',') if key.strip()]
        
        # Index hiện tại (bắt đầu từ 0)
        self.current_index = 0
        
        # Log số lượng keys
        if self.api_keys:
            print(f"🔑 [GEMINI] Tải {len(self.api_keys)} API keys")
        else:
            print("⚠️ [GEMINI] CẢNH BÁO: Không có API key nào được cấu hình!")
    
    def get_current_key(self):
        """Lấy API key hiện tại"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_index]
    
    def rotate_key(self):
        """
        Chuyển sang API key tiếp theo
        Returns: bool - True nếu còn key khả dụng, False nếu đã hết
        """
        if not self.api_keys:
            return False
        
        # Chuyển sang key tiếp theo
        self.current_index += 1
        
        # Nếu đã hết keys
        if self.current_index >= len(self.api_keys):
            print(f"❌ [GEMINI] Đã thử hết {len(self.api_keys)} API keys!")
            self.current_index = 0  # Reset về đầu
            return False
        
        print(f"🔄 [GEMINI] Chuyển sang API key #{self.current_index + 1}/{len(self.api_keys)}")
        return True
    
    def reset(self):
        """Reset về key đầu tiên"""
        self.current_index = 0


# Khởi tạo manager toàn cục
api_manager = GeminiAPIManager()

# Giữ nguyên biến cũ để tương thích
GEMINI_API_KEY = api_manager.get_current_key()


# ==================== HÀM CHECK_REVIEW_CONTENT (GIỮ NGUYÊN LOGIC) ====================

def check_review_content(comment, rating):
    """
    Kiểm tra nội dung review có phù hợp không
    
    Args:
        comment (str): Nội dung đánh giá
        rating (int): Số sao (1-5)
    
    Returns:
        dict: {
            'is_valid': bool,
            'reason': str
        }
    """
    
    if not api_manager.api_keys:
        print("⚠️ Gemini API key không được cấu hình")
        return {
            'is_valid': True,
            'reason': 'API key not configured'
        }
    
    # Reset về key đầu tiên
    api_manager.reset()
    
    # Thử với từng API key
    max_attempts = len(api_manager.api_keys)
    
    for attempt in range(max_attempts):
        current_key = api_manager.get_current_key()
        
        try:
            # Cấu hình API key hiện tại
            genai.configure(api_key=current_key)
            
            # GIỮ NGUYÊN: model gemini-flash-latest
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # GIỮ NGUYÊN: prompt của bạn
            prompt = f"""
Bạn là một hệ thống kiểm duyệt nội dung đánh giá nhà hàng/quán ăn.

NHIỆM VỤ:
Phân tích đánh giá sau và xác định xem nội dung có phù hợp không.

ĐÁNH GIÁ:
- Số sao: {rating}/5
- Nội dung: "{comment}"

TIÊU CHÍ KHÔNG PHÙ HỢP:
1. Chứa từ ngữ thô tục, chửi thề, tục tĩu
2. Quảng cáo sản phẩm/dịch vụ khác
3. Nội dung không liên quan đến món ăn/dịch vụ
4. Phân biệt chủng tộc, tôn giáo, giới tính
5. Thông tin cá nhân nhạy cảm
6. Nội dung quá ngắn hoặc vô nghĩa (ví dụ: "abc", "123")

TRẢ VỀ JSON:
{{
    "is_valid": true/false,
    "reason": "lý do ngắn gọn nếu không hợp lệ",
    "severity": "low/medium/high"
}}

CHỈ TRẢ VỀ JSON, KHÔNG KÈM MARKDOWN.
"""
            
            # GIỮ NGUYÊN: cách gọi API
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # GIỮ NGUYÊN: xử lý markdown
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # GIỮ NGUYÊN: parse JSON
            result = json.loads(result_text)
            
            # GIỮ NGUYÊN: format trả về
            return {
                'is_valid': result.get('is_valid', True),
                'reason': result.get('reason', ''),
                'severity': result.get('severity', 'low')
            }
        
        except Exception as e:
            error_message = str(e).lower()
            
            # Kiểm tra lỗi quota/rate limit
            if 'quota' in error_message or 'rate limit' in error_message or '429' in error_message:
                print(f"⚠️ [GEMINI] API key #{api_manager.current_index + 1} hết quota: {e}")
                
                # Thử chuyển sang key tiếp theo
                if api_manager.rotate_key():
                    continue  # Thử lại với key mới
                else:
                    break  # Đã hết keys
            else:
                # GIỮ NGUYÊN: xử lý lỗi khác
                print(f"❌ Lỗi khi gọi Gemini API: {e}")
                
                # Thử key tiếp theo
                if api_manager.rotate_key():
                    continue
                else:
                    break
    
    # GIỮ NGUYÊN: fail-safe
    return {
        'is_valid': True,
        'reason': f'Error: All API keys exhausted'
    }


# ==================== HÀM ANALYZE_REVIEW_SENTIMENT (GIỮ NGUYÊN LOGIC) ====================

def analyze_review_sentiment(comment, rating):
    """
    Phân tích cảm xúc của review (optional - dùng sau)
    """
    if not api_manager.api_keys:
        return {'sentiment': 'neutral'}
    
    # Reset về key đầu tiên
    api_manager.reset()
    
    # Thử với từng API key
    max_attempts = len(api_manager.api_keys)
    
    for attempt in range(max_attempts):
        current_key = api_manager.get_current_key()
        
        try:
            # Cấu hình API key hiện tại
            genai.configure(api_key=current_key)
            
            # GIỮ NGUYÊN: model gemini-flash-latest
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # GIỮ NGUYÊN: prompt của bạn
            prompt = f"""
Phân tích cảm xúc của đánh giá này:

Số sao: {rating}/5
Nội dung: "{comment}"

Trả về JSON:
{{
    "sentiment": "positive/negative/neutral",
    "confidence": 0.0-1.0,
    "keywords": ["từ", "khóa", "chính"]
}}
"""
            
            # GIỮ NGUYÊN: cách gọi API
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # GIỮ NGUYÊN: xử lý markdown
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # GIỮ NGUYÊN: parse JSON
            return json.loads(result_text)
        
        except Exception as e:
            error_message = str(e).lower()
            
            # Kiểm tra lỗi quota
            if 'quota' in error_message or 'rate limit' in error_message or '429' in error_message:
                print(f"⚠️ [GEMINI] Sentiment API key #{api_manager.current_index + 1} hết quota")
                
                if api_manager.rotate_key():
                    continue
                else:
                    break
            else:
                # GIỮ NGUYÊN: xử lý lỗi
                print(f"❌ Lỗi sentiment analysis: {e}")
                
                if api_manager.rotate_key():
                    continue
                else:
                    break
    
    # GIỮ NGUYÊN: fail-safe
    return {'sentiment': 'neutral'}