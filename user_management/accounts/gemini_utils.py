"""
Gemini AI utilities cho việc kiểm duyệt nội dung review
"""
import os
import json
import google.generativeai as genai
from django.conf import settings

# Cấu hình Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def check_review_content(comment, rating):
    """
    Kiểm tra nội dung review có phù hợp không
    
    Args:
        comment (str): Nội dung đánh giá
        rating (int): Số sao (1-5)
    
    Returns:
        dict: {
            'is_valid': bool,
            'reason': str,
            'suggested_content': str (optional)
        }
    """
    
    if not GEMINI_API_KEY:
        print("⚠️ Gemini API key không được cấu hình")
        return {
            'is_valid': True,
            'reason': 'API key not configured'
        }
    
    try:
        # ✅ SỬA MODEL NAME
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
Bạn là một hệ thống kiểm duyệt nội dung đánh giá nhà hàng/quán ăn.

NHIỆM VỤ:
Phân tích đánh giá sau và xác định xem nội dung có phù hợp không.

ĐÁNH GIÁ:
- Số sao: {rating}/5
- Nội dung: "{comment}"

TIÊU CHÍ KHÔNG PHÙ HỢP:
1. Chứa từ ngữ thô tục, chửi thề, tục tĩu
2. Spam (lặp lại nhiều lần cùng nội dung)
3. Quảng cáo sản phẩm/dịch vụ khác
4. Nội dung không liên quan đến món ăn/dịch vụ
5. Phân biệt chủng tộc, tôn giáo, giới tính
6. Thông tin cá nhân nhạy cảm
7. Nội dung quá ngắn hoặc vô nghĩa (ví dụ: "abc", "123")

TRẢ VỀ JSON:
{{
    "is_valid": true/false,
    "reason": "lý do ngắn gọn nếu không hợp lệ",
    "severity": "low/medium/high",
    "suggested_content": "nội dung gợi ý tốt hơn (nếu có)"
}}

CHỈ TRẢ VỀ JSON, KHÔNG KÈM MARKDOWN.
"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Xử lý trường hợp Gemini trả về markdown
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        return {
            'is_valid': result.get('is_valid', True),
            'reason': result.get('reason', ''),
            'severity': result.get('severity', 'low'),
            'suggested_content': result.get('suggested_content', '')
        }
        
    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API: {e}")
        # Nếu lỗi, cho phép review đi qua (fail-safe)
        return {
            'is_valid': True,
            'reason': f'Error: {str(e)}'
        }


def analyze_review_sentiment(comment, rating):
    """
    Phân tích cảm xúc của review (optional - dùng sau)
    """
    if not GEMINI_API_KEY:
        return {'sentiment': 'neutral'}
    
    try:
        # ✅ SỬA MODEL NAME
        model = genai.GenerativeModel('gemini-flash-latest')
        
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
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        return json.loads(result_text)
        
    except Exception as e:
        print(f"❌ Lỗi sentiment analysis: {e}")
        return {'sentiment': 'neutral'}