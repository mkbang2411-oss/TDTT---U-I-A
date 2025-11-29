# -*- coding: utf-8 -*-
import json
import pandas as pd
import math
import random
from datetime import datetime, timedelta
import unicodedata

# ==================== UTILITY FUNCTIONS ====================

def calculate_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách giữa 2 điểm GPS (km)"""
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def estimate_travel_time(distance_km):
    """Ước tính thời gian di chuyển (phút)"""
    avg_speed = 25
    return int((distance_km / avg_speed) * 60)

def normalize_text(text):
    """Chuẩn hóa text để tìm kiếm"""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    return text

def clean_value(value):
    """Chuyển đổi các giá trị NaN/None thành giá trị hợp lệ"""
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0
        return value
    return value

def is_open_now(opening_hours_str, check_time=None, min_hours_before_close=2, place_name=None):
    """
    Kiểm tra quán có đang mở cửa không VÀ còn đủ thời gian hoạt động
    
    Args:
        opening_hours_str: Chuỗi giờ mở cửa từ CSV (VD: "Mở cửa vào 4:30 · Đóng cửa vào 12:00")
        check_time: Thời gian cần kiểm tra (HH:MM hoặc time object)
        min_hours_before_close: Số giờ tối thiểu trước khi đóng cửa (mặc định 2 giờ)
        place_name: Tên quán (dùng để debug)
    
    Returns:
        True nếu quán đang mở và còn đủ thời gian, False nếu không
    """
    # Nếu không có thông tin giờ mở cửa → CHẶN LUÔN
    if not opening_hours_str or pd.isna(opening_hours_str):
        return False
    
    try:
        import re
        
        # Xử lý check_time
        if check_time is None:
            current_time = datetime.now().time()
        elif isinstance(check_time, str):
            current_time = datetime.strptime(check_time, '%H:%M').time()
        else:
            current_time = check_time
        
        # Chuẩn hóa: bỏ dấu, lowercase
        hours_str = normalize_text(str(opening_hours_str))
        
        
        # CHẶN các quán "Không rõ giờ mở cửa"
        if 'khong ro' in hours_str or 'khong biet' in hours_str or 'chua ro' in hours_str:
            return False
        
        # Kiểm tra quán mở 24/7
        if any(keyword in hours_str for keyword in ['always', '24', 'ca ngay', 'mo ca ngay']):
            return True
        
        # Parse giờ mở cửa - hỗ trợ cả "Mở cửa vào" và "Mở cửa lúc"
        open_time = None
        open_match = re.search(r'mo\s*cua\s*(?:vao|luc)?\s*(\d{1,2}):?(\d{2})?', hours_str)
        if open_match:
            hour = int(open_match.group(1))
            minute = int(open_match.group(2)) if open_match.group(2) else 0
            open_time = datetime.strptime(f'{hour:02d}:{minute:02d}', '%H:%M').time()
        
        # Parse giờ đóng cửa
        close_time = None
        close_match = re.search(r'(?:d)?ong\s*cua\s*(?:vao|luc)?\s*(\d{1,2}):?(\d{2})?', hours_str)
        if close_match:
            hour = int(close_match.group(1))
            minute = int(close_match.group(2)) if close_match.group(2) else 0
            close_time = datetime.strptime(f'{hour:02d}:{minute:02d}', '%H:%M').time()
        
        # Nếu không parse được giờ → CHẶN LUÔN (không cho qua như trước)
        if open_time is None or close_time is None:
            return False
        
        # Chuyển đổi tất cả sang phút để dễ so sánh
        current_minutes = current_time.hour * 60 + current_time.minute
        open_minutes = open_time.hour * 60 + open_time.minute
        close_minutes = close_time.hour * 60 + close_time.minute
        
        # Xử lý trường hợp quán mở qua đêm (VD: 22:00 - 02:00)
        if close_minutes < open_minutes:
            # Cộng 24 giờ cho giờ đóng cửa
            close_minutes += 24 * 60
            
            # Nếu giờ check < giờ mở → Coi như sáng hôm sau
            if current_minutes < open_minutes:
                current_minutes += 24 * 60
        
        # Tính thời gian tối thiểu cần có trước khi đóng cửa (đổi từ giờ sang phút)
        min_minutes_before_close = min_hours_before_close * 60
        
        # 3 điều kiện để quán hợp lệ:
        # 1. Đã đến giờ mở cửa
        is_open = (current_minutes >= open_minutes)

        # 2. Chưa đến giờ đóng cửa
        is_before_close = (current_minutes < close_minutes)

        # 3. Còn đủ thời gian hoạt động (ít nhất 2 giờ trước khi đóng)
        has_enough_time = ((close_minutes - current_minutes) >= min_minutes_before_close)

        # 🔥 CHẶN CHẶT: Nếu KHÔNG thỏa mãn cả 3 điều kiện → CHẶN LUÔN
        if not (is_open and is_before_close and has_enough_time):
            return False

        # ✅ Nếu đến đây → CẢ 3 ĐIỀU KIỆN ĐỀU ĐÚNG
        result = True
        
        return result
            
    except Exception as e:
        print(f"⚠️ Lỗi parse giờ: {opening_hours_str} -> {e}")
        # Khi có lỗi → CHẶN LUÔN (không cho qua như trước)
        return False

# ==================== CẬP NHẬT HÀM LỌC - GIỮ NGUYÊN DẤU ====================

def normalize_text_with_accent(text):
    """Chuẩn hóa text NHƯNG GIỮ NGUYÊN DẤU tiếng Việt"""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    # Chỉ chuẩn hóa khoảng trắng, KHÔNG loại bỏ dấu
    text = ' '.join(text.split())
    return text

# ==================== TỪ ĐIỂN CHỦ ĐỀ MỞ RỘNG - CÓ DẤU ĐẦY ĐỦ ====================

THEME_CATEGORIES = {
    'street_food': {
        'name': 'Ẩm thực đường phố',
        'keywords': [
            # Món ăn
            'bánh mì', 'bánh mỳ', 'banh mi',
            'phở', 'pho',
            'bún', 'bún bò', 'bún chả', 'bún riêu', 'bún đậu', 'bún mắm',
            'bún thịt nướng', 'bún ốc',
            'cơm tấm', 'cơm sườn', 'cơm gà', 'cơm chiên',
            'xôi', 'xôi gà', 'xôi thịt',
            'chè', 'chè khúc', 'chè thái',
            'street', 'vỉa hè', 'quán vỉa hè', 'đường phố',
            'hủ tiếu', 'hủ tíu', 'mì quảng',
            'cao lầu', 'bánh xèo', 'bánh căn',
            'gỏi cuốn', 'nem', 'chả giò', 'nem rán',
            'bánh cuốn', 'bánh bèo', 'bánh bột lọc',
            'cháo', 'cháo lòng', 'cháo vịt'
            # KHÔNG CÓ thương hiệu vì tên quán đã có keyword rồi
        ],
        'icon': '🍜'
    },
    'seafood': {
        'name': 'Hải sản',
        'keywords': [
            'hải sản', 'seafood',
            'fish', 'cá',
            'cua', 'ghẹ',
            'tôm', 'shrimp',
            'ốc', 'snail',
            'ngao', 'sò', 'nghêu',
            'mực', 'squid',
            'cá hồi', 'salmon',
            'hàu', 'oyster',
            'tôm hùm', 'lobster',
            'cá thu', 'cá ngừ', 'cá basa',
            'lẩu hải sản', 'nướng hải sản',
            'buffet hải sản'
        ],
        'icon': '🦞'
    },
    'coffee_chill': {
        'name': 'Giải khát',
        'keywords': [
            # Món uống
            'cà phê', 'cafe', 'coffee', 'ca phe',
            'cà phê sữa', 'cà phê đá', 'cà phê phin',
            'cà phê sữa đá', 'cà phê đen',
            'bạc xỉu', 'nâu đá', 'Akafe',
            'espresso', 'cappuccino', 'latte', 'americano',
            'mocha', 'macchiato', 'flat white','tea',
            'trà sữa', 'milk tea',
            'trà đào', 'trà chanh', 'trà atiso',
            'trà sen', 'trà hoa', 'trà ô long',
            'trà xanh', 'trà đen', 'trà gừng',
            'sinh tố', 'smoothie', 'juice',
            'nước ép', 'nước trái cây',
            'soda', 'soda cream', 'limonada',
            'matcha', 'chocolate', 'frappe',
            # Không gian
            'acoustic', 'chill', 'cozy',
            'book cafe', 'quán sách',
            # Thương hiệu KHÔNG có keyword trong tên
            'highlands', 'starbucks',
            'phúc long', 'trung nguyên',
            'gong cha', 'royaltea', 'ding tea',
            'tocotoco', 'koi thé', 'koi the',
            'bobapop', 'alley', 'tiger sugar',
            'passio', 'phindi',
            'angfarm', 'runam',
            'effoc', 'vinacafe'
        ],
        'icon': '☕'
    },
    'luxury_dining': {
        'name': 'Nhà hàng sang trọng',
        'keywords': [
            'nhà hàng', 'restaurant', 'nha hang',
            'fine dining', 'luxury', 'sang trọng', 'sang trong',
            'buffet','resort', 'rooftop',
            'steakhouse', 'bít tết', 'beefsteak', 'bit tet',
            'sky bar', 'lounge',
            'five star', 'cao cấp', 'cao cap',
            # Thương hiệu khách sạn/nhà hàng cao cấp
            'marriott', 'sheraton', 'hilton',
            'intercontinental', 'hyatt', 'sofitel',
            'pullman', 'novotel', 'renaissance',
            'reverie', 'vinpearl',
            'bistro', 'grill', 'prime',
            'dining', 'banquet', 'yen tiec', 'yến tiệc'
        ],
        'icon': '🍽️'
    },
    'asian_fusion': {
        'name': 'Ẩm thực châu Á',
        'keywords': [
            # Nhật - Món ăn
            'sushi', 'ramen', 'nhật bản',
            'japanese', 'tempura', 'takoyaki',
            'udon', 'soba', 'teriyaki',
            'sashimi', 'donburi', 'bento',
            'yakiniku', 'okonomiyaki',
            'katsu', 'tonkatsu', 'gyoza',
            'miso', 'wasabi', 'edamame',
            # Nhật - Thương hiệu KHÔNG có keyword
            'omakase', 'ichiban',
            'tokyo', 'osaka', 'hokkaido',
            'izakaya',
            # Hàn - Món ăn
            'hàn quốc', 'korean',
            'kimchi', 'bibimbap', 'bulgogi',
            'gimbap', 'tteokbokki', 'samgyeopsal',
            'bbq hàn', 'korean bbq',
            'jjigae', 'ramyeon',
            'kimbap', 'japchae', 'galbi',
            # Hàn - Thương hiệu
            'gogi', 'king bbq', 'sumo bbq',
            'seoul', 'busan', 'gangnam',
            # Thái
            'thái', 'thai', 'thailand',
            'tom yum', 'pad thai', 'somtum',
            'tom kha', 'green curry',
            'massaman', 'panang', 'bangkok',
            # Trung
            'trung hoa', 'trung quốc', 'chinese',
            'dimsum', 'dim sum', 'lẩu tứ xuyên',
            'mì vằn thắn', 'hủ tiếu xào',
            'há cảo', 'xíu mại', 'sủi cảo',
            'bắc kinh', 'quảng đông', 'thượng hải',
            'hongkong', 'canton'
        ],
        'icon': '🍱'
    },
    'vegetarian': {
        'name': 'Món chay',
        'keywords': [
            'chay', 'vegetarian', 'vegan',
            'healthy', 'organic', 'sạch',
            'salad', 'rau củ', 'rau sạch',
            'cơm chay', 'bún chay', 'phở chay',
            'đậu hũ', 'tofu',
            'nấm', 'mushroom',
            'chay thanh tịnh', 'an lạc',
            'chay tịnh', 'món chay',
            'thực dưỡng', 'thuần chay'
        ],
        'icon': '🥗'
    },
    'dessert_bakery': {
        'name': 'Tráng miệng & Bánh ngọt',
        'keywords': [
            # Bánh
            'bánh', 'cake', 'bakery',
            'bánh kem', 'bánh sinh nhật',
            'bánh ngọt', 'bánh ngon',
            'bánh mì ngọt', 'croissant', 'tiramisu',
            'macaron', 'cupcake', 'donut',
            'bánh bông lan', 'bánh flan',
            'bánh su kem', 'eclair',
            'mousse', 'cheesecake',
            'bánh tart', 'bánh pie',
            'bánh cookie', 'bánh quy',
            'mochi', 'bánh trung thu',
            # Kem
            'kem', 'ice cream', 'gelato',
            'kem tươi', 'kem que', 'kem ly',
            'kem ý', 'kem trang trí',
            'frosty', 'sundae', 'smoothie bowl',
            # Thương hiệu
            'abc bakery', 'tous les jours',
            'breadtalk', 'givral', 'kinh đô',
            'paris gateaux', 'brodard',
            'baskin robbins', 'swensen',
            'dairy queen'
        ],
        'icon': '🍰'
    },
    'spicy_food': {
        'name': 'Đồ cay',
        'keywords': [
        'cay', 'spicy', 'hot',
        'lẩu cay', 'lau cay', 'hot pot cay', 'hotpot cay',  # 🔥 BỎ "lẩu" đơn thuần
        'lẩu thái', 'lau thai',  # Lẩu Thái thường cay
        'lẩu tứ xuyên', 'lau tu xuyen', 'tứ xuyên', 'tu xuyen',  # Tứ Xuyên = cay
        # 🔥 XÓA: 'lẩu ếch', 'lẩu gà' (không chắc cay)
        'mì cay', 'mi cay', 'mì cay hàn quốc', 'mi cay han quoc',
        'tokbokki', 'tteokbokki',
        'gà cay', 'ga cay', 'gà rán cay', 'ga ran cay',
        'ớt', 'chili',
        'bún bò huế',  # Bún bò Huế thường cay
        'mực xào cay', 'muc xao cay',
        'đồ cay hàn', 'do cay han', 'đồ cay thái', 'do cay thai',
        'kim chi', 'kimchi',
        'sườn cay', 'suon cay',
        'phá lấu', 'pha lau'  # Phá lấu thường cay
        ],
        'icon': '🌶️'
    },
    # 🔥 THÊM KEY MỚI CHO "KHU ẨM THỰC"
    'food_street': {
        'name': 'Khu ẩm thực',
        'keywords': [],  # Không cần keywords vì xét trực tiếp cột mo_ta
        'icon': '🏪'
    },
    
    # 🔥 THÊM LUÔN CHO MICHELIN (nếu chưa có)
    'michelin': {
        'name': 'Michelin',
        'keywords': [],  # Xét trực tiếp cột mo_ta
        'icon': '⭐'
    }
}

# ==================== TỪ ĐIỂN KEYWORD CHO TỪNG BỮA ĂN ====================
MEAL_TYPE_KEYWORDS = {
    'breakfast': [
        # Món Việt sáng
        'phở', 'bún', 'bánh mì', 'cháo', 'xôi', 'hủ tiếu', 'bánh cuốn', 
        'bánh bèo', 'cơm tấm', 'mì quảng'
    ],
    
    'morning_drink': [
        # Đồ uống
        'cafe', 'coffee', 'cà phê', 'trà', 'tea', 'sinh tố', 'juice', 
        'nước', 'nước ép', 'smoothie', 'sữa', 'milk', 'trà sữa',
        'matcha', 'latte', 'cappuccino', 'espresso',
        # Từ theme coffee_chill
        'highlands', 'starbucks', 'phúc long', 'trung nguyên',
        'gong cha', 'royaltea', 'ding tea', 'tocotoco', 'koi thé',
        'bobapop', 'alley', 'tiger sugar', 'passio', 'phindi'
    ],
    
    'lunch': [
        # Món chính
        'cơm', 'bún', 'mì', 'phở', 'hủ tiếu', 'cơm tấm', 'miến',
        'bánh mì', 'bánh xèo', 'cao lầu', 'mì quảng'
    ],
    
    'afternoon_drink': [
        # Đồ uống
        'cafe', 'coffee', 'cà phê', 'trà', 'tea', 'trà sữa', 'milk tea', 
        'sinh tố', 'nước', 'juice', 'smoothie', 'soda',
        'matcha', 'chocolate', 'frappe',
        # Bánh nhẹ
        'bánh', 'cake', 'tiramisu', 'macaron', 'cupcake', 'donut',
        # Từ theme
        'highlands', 'starbucks', 'phúc long', 'trung nguyên',
        'gong cha', 'royaltea', 'tocotoco', 'koi thé', 'passio'
    ],
    
    'dinner': [
        # Món tối đa dạng
        'cơm', 'lẩu', 'nướng', 'hải sản', 'bún', 'mì', 'phở',
        'cơm tấm', 'nem', 'gỏi', 'cháo', 'hotpot', 'bbq',
        'sushi', 'ramen', 'dimsum', 'steak', 'bò', 'gà', 'cá', 'tôm', 'buffet'
    ],
    
    'dessert': [
        # Tráng miệng
        'bánh', 'kem', 'chè', 'cake', 'ice cream', 'dessert',
        'bánh ngọt', 'bánh kem', 'tiramisu', 'macaron', 'cupcake',
        'gelato', 'frosty', 'sundae', 'mousse', 'cheesecake',
        'donut', 'cookie', 'brownie', 'tart', 'pie', 'mochi',
        # 🔥 Bakery Tiếng Anh
        'bakery', 'patisserie', 'confectionery', 'pastry'
    ],
    
    # 🔥 CHO KHOẢNG THỜI GIAN NGẮN
    'meal': [
        # Bữa chính đa dạng
        'cơm', 'bún', 'phở', 'mì', 'hủ tiếu', 'cơm tấm', 'bánh mì',
        'bánh xèo', 'nem', 'gỏi', 'cháo', 'xôi', 'cao lầu'
    ],
    
    'meal1': [
        # Bữa chính 1
        'cơm', 'bún', 'phở', 'mì', 'hủ tiếu', 'cơm tấm', 'bánh mì',
        'bánh xèo', 'miến', 'cao lầu', 'mì quảng'
    ],
    
    'meal2': [
        # Bữa phụ nhẹ hơn
        'cơm', 'bún', 'phở', 'mì', 'bánh mì', 'nem', 'gỏi cuốn',
        'bánh xèo', 'bánh', 'xôi', 'chè'
    ],
    
    'drink': [
        # Đồ uống tổng hợp
        'cafe', 'coffee', 'cà phê', 'trà', 'tea', 'nước', 'sinh tố',
        'juice', 'smoothie', 'trà sữa', 'milk tea', 'soda', 'nước ép',
        'matcha', 'chocolate', 'latte', 'cappuccino',
        # Từ theme
        'highlands', 'starbucks', 'phúc long', 'trung nguyên',
        'gong cha', 'royaltea', 'tocotoco', 'koi thé', 'passio'
    ]
}

# ==================== FIND PLACES WITH ADVANCED FILTERS ====================

def find_places_advanced(user_lat, user_lon, df, filters, excluded_ids=None, top_n=30):
    """Tìm quán với bộ lọc nâng cao - CHỈ LỌC THEO THEME"""
    if excluded_ids is None:
        excluded_ids = set()
    
    results = []
    radius_km = filters.get('radius_km', 5)
    theme = filters.get('theme')
    # 🔥 BỎ: user_tastes = filters.get('tastes', [])

    # XỬ LÝ THEME - CÓ THỂ LÀ STRING HOẶC LIST
    if theme:
        if isinstance(theme, str):
            theme_list = [theme]
        else:
            theme_list = theme if theme else []
    else:
        theme_list = []
    
    skipped_rows = 0
    
    for idx, row in df.iterrows():
        try:
            data_id = clean_value(row.get('data_id', ''))
            
            if data_id in excluded_ids:
                continue
            
            # Parse tọa độ
            lat_str = str(row.get('lat', '')).strip().strip('"').strip()
            lon_str = str(row.get('lon', '')).strip().strip('"').strip()
            
            if not lat_str or not lon_str or lat_str == 'nan' or lon_str == 'nan':
                continue
                
            place_lat = float(lat_str)
            place_lon = float(lon_str)
            
            distance = calculate_distance(user_lat, user_lon, place_lat, place_lon)
            
            # Lọc bán kính
            if distance > radius_km:
                continue
            
            # Lọc giờ mở cửa
            gio_mo_cua = row.get('gio_mo_cua', '')
            check_time_str = filters.get('meal_time')
            ten_quan = str(row.get('ten_quan', ''))
            name_normalized = normalize_text_with_accent(ten_quan)  # ← THÊM DÒNG NÀY

            if check_time_str:
                if not is_open_now(gio_mo_cua, check_time=check_time_str, min_hours_before_close=2, place_name=ten_quan):
                    continue
            else:
                if not is_open_now(gio_mo_cua, min_hours_before_close=2, place_name=ten_quan):
                    continue
            
            # LỌC THEO THEME
            if theme:
                match_found = False
                
                for single_theme in theme_list:
                    if single_theme == 'food_street':
                        mo_ta = str(row.get('mo_ta', '')).strip().lower()
                        # 🔥 SỬA: So sánh linh hoạt hơn, bỏ dấu tiếng Việt
                        mo_ta_no_accent = normalize_text(mo_ta)  # Bỏ dấu
                        if 'khu' in mo_ta and 'am thuc' in mo_ta_no_accent:
                            match_found = True
                            break
                    
                    elif single_theme == 'michelin':
                        mo_ta = str(row.get('mo_ta', '')).strip().lower()
                        # 🔥 SỬA: Kiểm tra chứa từ "michelin"
                        if 'michelin' in mo_ta:
                            match_found = True
                            break
                    
                    else:
                        # Xử lý theme bình thường
                        theme_keywords = THEME_CATEGORIES[single_theme]['keywords']
                        
                        for keyword in theme_keywords:
                            keyword_normalized = normalize_text_with_accent(keyword)
                            
                            search_text = ' ' + name_normalized + ' '
                            search_keyword = ' ' + keyword_normalized + ' '
                            
                            if search_keyword in search_text:
                                match_found = True
                                break
                        
                        if match_found:
                            break
                        
                        # XÉT cột khau_vi cho spicy_food & dessert_bakery
                        if not match_found and single_theme in ['spicy_food', 'dessert_bakery']:
                            khau_vi = str(row.get('khau_vi', '')).strip().lower()
                            
                            if khau_vi:
                                if single_theme == 'spicy_food' and 'cay' in khau_vi:
                                    match_found = True
                                    break
                                elif single_theme == 'dessert_bakery' and 'ngọt' in khau_vi:
                                    match_found = True
                                    break
                
                if not match_found:
                    continue

            # 🔥 THÊM ĐOẠN NÀY NGAY SAU PHẦN LỌC THEME (sau dòng "if not match_found: continue")
            # 🔥 LỌC QUÁN NƯỚC - CHỈ CHO PHÉP KHI CÓ THEME coffee_chill
            if theme and 'coffee_chill' not in theme_list:
                # Danh sách keyword QUÁN NƯỚC cần loại bỏ
                drink_keywords = [
                    'cafe', 'coffee', 'ca phe', 'cà phê',
                    'trà', 'tea', 'trà sữa', 'milk tea',
                    'sinh tố', 'smoothie', 'juice', 'nước ép',
                    'highlands', 'starbucks', 'phúc long', 'trung nguyên',
                    'gong cha', 'royaltea', 'ding tea', 'tocotoco', 
                    'koi thé', 'koi the', 'bobapop', 'alley', 
                    'tiger sugar', 'passio', 'phindi'
                ]
                
                # Kiểm tra tên quán có chứa keyword quán nước không
                is_drink_place = False
                for drink_kw in drink_keywords:
                    drink_kw_normalized = normalize_text_with_accent(drink_kw)
                    if drink_kw_normalized in name_normalized:
                        is_drink_place = True
                        break
                
                # Nếu là quán nước → BỎ QUA
                if is_drink_place:
                    continue

            # 🔥 Lọc BÁNH MÌ KHỎI THEME dessert_bakery
            if theme and 'dessert_bakery' in theme_list:
                # Bỏ dấu để kiểm tra
                name_for_check = normalize_text(str(row.get('ten_quan', '')))
                # Loại bỏ tất cả biến thể của bánh mì
                banh_mi_variants = ['banhmi', 'banh mi', 'banhmy', 'banh my']
                if any(variant in name_for_check for variant in banh_mi_variants):
                    continue
            
            # THÊM VÀO RESULTS (phần code cũ giữ nguyên)
            results.append({
                'ten_quan': clean_value(row.get('ten_quan', '')),
                'dia_chi': clean_value(row.get('dia_chi', '')),
                'so_dien_thoai': clean_value(row.get('so_dien_thoai', '')),
                'rating': float(clean_value(row.get('rating', 0))) if pd.notna(row.get('rating')) else 0,
                'gio_mo_cua': clean_value(row.get('gio_mo_cua', '')),
                'lat': place_lat,
                'lon': place_lon,
                'distance': distance,
                'data_id': data_id,
                'hinh_anh': clean_value(row.get('hinh_anh', '')),
                'gia_trung_binh': clean_value(row.get('gia_trung_binh', '')),
                'thuc_don': clean_value(row.get('thuc_don', '')),
                'khau_vi': clean_value(row.get('khau_vi', ''))
            })
            
        except Exception as e:
            skipped_rows += 1
            continue
    
    # Sắp xếp: Khoảng cách → Rating
    results.sort(key=lambda x: (x['distance'], -x['rating']))
    return results[:top_n]

# ==================== MEAL TO THEME MAPPING ====================

MEAL_THEME_MAP = {
    # BUỔI SÁNG - Ưu tiên đồ ăn sáng Việt Nam
    'breakfast': {
        'preferred': ['street_food'],  # Ưu tiên phở, bánh mì, bún
        'fallback': ['asian_fusion', 'luxury_dining']
    },
    
    # ĐỒ UỐNG SÁNG - Cafe/trà
    'morning_drink': {
        'preferred': ['coffee_chill'],
        'fallback': ['dessert_bakery']
    },
    
    # BỮA TRƯA - Cơm/bún/mì
    'lunch': {
        'preferred': ['street_food'],
        'fallback': ['asian_fusion', 'seafood', 'spicy_food', 'luxury_dining']
    },
    
    # ĐỒ UỐNG CHIỀU - Cafe/trà sữa
    'afternoon_drink': {
        'preferred': ['coffee_chill', 'dessert_bakery'],
        'fallback': ['coffee_chill']
    },
    
    # BỮA TỐI - Đa dạng hơn
    'dinner': {
        'preferred': ['seafood', 'asian_fusion', 'spicy_food', 'luxury_dining'],
        'fallback': ['street_food']
    },
    
    # TRÁNG MIỆNG - Bánh/kem
    'dessert': {
        'preferred': ['dessert_bakery', 'coffee_chill'],
        'fallback': ['street_food']
    },
    
    # BỮA PHỤ (cho plan ngắn)
    'meal': {
        'preferred': ['street_food'],
        'fallback': ['asian_fusion']
    },
    'meal1': {
        'preferred': ['street_food'],
        'fallback': ['asian_fusion']
    },
    'meal2': {
        'preferred': ['street_food', 'asian_fusion'],
        'fallback': ['coffee_chill']
    },
    'drink': {
        'preferred': ['coffee_chill'],
        'fallback': ['dessert_bakery']
    }
}

def get_theme_for_meal(meal_key, user_selected_themes):
    """
    Chọn theme phù hợp cho từng bữa ăn
    
    Logic:
    1. Nếu user CHỌN theme → DÙNG theme ưu tiên phù hợp với bữa
    2. Nếu KHÔNG → dùng theme mặc định theo bữa
    """
    # ⚡ DANH SÁCH THEME KHÔNG PHÙ HỢP CHO TỪNG BỮA
    MEAL_RESTRICTIONS = {
        'dessert': ['michelin', 'food_street', 'luxury_dining', 'seafood', 'spicy_food'],
        'morning_drink': ['michelin', 'food_street', 'luxury_dining', 'seafood', 'asian_fusion', 'spicy_food', 'vegetarian'],
        'afternoon_drink': ['michelin', 'food_street', 'luxury_dining', 'seafood', 'asian_fusion', 'spicy_food', 'vegetarian'],
        'drink': ['michelin', 'food_street', 'luxury_dining', 'seafood', 'asian_fusion', 'spicy_food', 'vegetarian']
    }
    
    # 🔥 NẾU USER ĐÃ CHỌN THEME
    if user_selected_themes:
        # Lọc bỏ theme không phù hợp với bữa này
        restricted = MEAL_RESTRICTIONS.get(meal_key, [])
        suitable_themes = [t for t in user_selected_themes if t not in restricted]
        
        # ⚡ NẾU LÀ BỮA DRINK → ƯU TIÊN coffee_chill
        if meal_key in ['morning_drink', 'afternoon_drink', 'drink']:
            if 'coffee_chill' in suitable_themes:
                return 'coffee_chill'
            elif 'dessert_bakery' in suitable_themes:
                return 'dessert_bakery'
            elif suitable_themes:
                return suitable_themes[0]
            else:
                return 'coffee_chill'
        
        # ⚡ NẾU LÀ TRÁNG MIỆNG → ƯU TIÊN dessert_bakery
        if meal_key == 'dessert':
            if 'dessert_bakery' in suitable_themes:
                return 'dessert_bakery'
            elif 'street_food' in suitable_themes:  # 🔥 ƯU TIÊN street_food TRƯỚC coffee_chill
                return 'street_food'
            elif 'asian_fusion' in suitable_themes:  # 🔥 ƯU TIÊN asian_fusion TRƯỚC coffee_chill
                return 'asian_fusion'
            elif 'coffee_chill' in suitable_themes:  # 🔥 coffee_chill cuối cùng (chỉ khi không có lựa chọn khác)
                return 'coffee_chill'
            elif suitable_themes:
                return suitable_themes[0]
            else:
                return 'dessert_bakery'
        
        # 🔥 CÁC BỮA ĂN CHÍNH → ƯU TIÊN THEME PHÙ HỢP NHẤT
        # Ưu tiên: street_food > asian_fusion > seafood > spicy_food > luxury_dining
        priority_order = ['street_food', 'asian_fusion', 'seafood', 'spicy_food', 'luxury_dining', 'vegetarian', 'food_street', 'michelin']
        
        for theme in priority_order:
            if theme in suitable_themes:
                return theme
        
        # Nếu không có theme nào trong priority → lấy theme đầu tiên
        if suitable_themes:
            return suitable_themes[0]
        else:
            # Không có theme phù hợp → dùng mặc định
            meal_map = MEAL_THEME_MAP.get(meal_key, {'preferred': ['street_food'], 'fallback': []})
            return meal_map['preferred'][0]
    
    # 🔥 NẾU USER KHÔNG CHỌN THEME → Tự động chọn theo bữa
    meal_map = MEAL_THEME_MAP.get(meal_key, {'preferred': ['street_food'], 'fallback': []})
    return meal_map['preferred'][0]

# ==================== GENERATE SMART PLAN ====================

def generate_meal_schedule(time_start_str, time_end_str, user_selected_themes):
    """
    Generate meal schedule dựa trên KHUNG GIỜ thực tế
    Hỗ trợ khung giờ qua đêm (vd: 7:00 → 6:00 sáng hôm sau)
    """
    time_start = datetime.strptime(time_start_str, '%H:%M')
    time_end = datetime.strptime(time_end_str, '%H:%M')
    
    # 🔥 NẾU GIỜ KẾT THÚC < GIỜ BẮT ĐẦU → COI LÀ NGÀY HÔM SAU
    if time_end <= time_start:
        time_end = time_end + timedelta(days=1)
    
    start_hour = time_start.hour + time_start.minute / 60.0
    end_hour = time_end.hour + time_end.minute / 60.0
    
    # 🔥 NẾU QUA ĐÊM → CỘNG 24 GIỜ CHO end_hour
    if time_end.day > time_start.day:
        end_hour += 24
    
    # 🔥 KIỂM TRA CÓ CHỌN THEME KHÔNG
    has_selected_themes = user_selected_themes and len(user_selected_themes) > 0
    
    if has_selected_themes:
        has_coffee_chill = 'coffee_chill' in user_selected_themes
        dessert_themes = {'street_food', 'asian_fusion', 'dessert_bakery', 'coffee_chill'}
        has_dessert_theme = any(theme in dessert_themes for theme in user_selected_themes)
    else:
        has_coffee_chill = True
        has_dessert_theme = True
    
    plan = {}
    
    # 🔥 HÀM HELPER: TÍNH GIỜ VÀ FORMAT
    def format_time(hour_float):
        """Chuyển số giờ (có thể > 24) thành HH:MM"""
        hour_float = hour_float % 24  # Quay vòng 24 giờ
        return f'{int(hour_float):02d}:{int((hour_float % 1) * 60):02d}'
    
    def is_in_range(target_hour, range_start, range_end):
        """Kiểm tra giờ có nằm trong khoảng không (hỗ trợ qua đêm)"""
        # Nếu target_hour < start_hour → coi như ngày hôm sau
        if target_hour < start_hour:
            target_hour += 24
        return range_start <= target_hour < range_end and start_hour <= target_hour < end_hour
    
    # 🔥 KHUNG GIỜ BỮA SÁNG (6:00 - 10:00)
    breakfast_time = max(start_hour, 7)
    if breakfast_time < start_hour:
        breakfast_time += 24
    if is_in_range(breakfast_time, 7, 10):
        plan['breakfast'] = {
            'time': format_time(breakfast_time),
            'title': 'Bữa sáng',
            'categories': ['pho', 'banh mi', 'bun'],
            'icon': '🍳'
        }
    
    # 🔥 ĐỒ UỐNG BUỔI SÁNG (9:30 - 11:30)
    if has_coffee_chill:
        morning_drink_time = max(start_hour + 1.5, 9.5)
        if morning_drink_time < start_hour:
            morning_drink_time += 24
        if is_in_range(morning_drink_time, 9.5, 11.5):
            if 'breakfast' not in plan or (morning_drink_time - start_hour >= 1.5):
                plan['morning_drink'] = {
                    'time': format_time(morning_drink_time),
                    'title': 'Giải khát buổi sáng',
                    'categories': ['tra sua', 'cafe', 'coffee'],
                    'icon': '🧋'
                }
    
    # 🔥 BỮA TRƯA (11:00 - 14:00)
    lunch_time = max(start_hour, 11.5)
    if lunch_time < start_hour:
        lunch_time += 24
    if 'breakfast' in plan:
        breakfast_hour = float(plan['breakfast']['time'].split(':')[0]) + float(plan['breakfast']['time'].split(':')[1]) / 60
        if breakfast_hour < start_hour:
            breakfast_hour += 24
        lunch_time = max(lunch_time, breakfast_hour + 3)
    
    if is_in_range(lunch_time, 11, 14):
        plan['lunch'] = {
            'time': format_time(lunch_time),
            'title': 'Bữa trưa',
            'categories': ['com tam', 'mi', 'bun'],
            'icon': '🍚'
        }
    
    # 🔥 ĐỒ UỐNG BUỔI CHIỀU (14:00 - 17:00)
    if has_coffee_chill:
        afternoon_drink_time = max(start_hour, 14.5)
        if afternoon_drink_time < start_hour:
            afternoon_drink_time += 24
        if 'lunch' in plan:
            lunch_hour = float(plan['lunch']['time'].split(':')[0]) + float(plan['lunch']['time'].split(':')[1]) / 60
            if lunch_hour < start_hour:
                lunch_hour += 24
            afternoon_drink_time = max(afternoon_drink_time, lunch_hour + 1.5)
        
        if is_in_range(afternoon_drink_time, 14, 17):
            plan['afternoon_drink'] = {
                'time': format_time(afternoon_drink_time),
                'title': 'Giải khát buổi chiều',
                'categories': ['tra sua', 'cafe', 'coffee'],
                'icon': '☕'
            }
    
    # 🔥 BỮA TỐI (17:00 - 21:00)
    dinner_time = max(start_hour, 18)
    if dinner_time < start_hour:
        dinner_time += 24
    if 'lunch' in plan:
        lunch_hour = float(plan['lunch']['time'].split(':')[0]) + float(plan['lunch']['time'].split(':')[1]) / 60
        if lunch_hour < start_hour:
            lunch_hour += 24
        dinner_time = max(dinner_time, lunch_hour + 4)
    elif 'breakfast' in plan:
        breakfast_hour = float(plan['breakfast']['time'].split(':')[0]) + float(plan['breakfast']['time'].split(':')[1]) / 60
        if breakfast_hour < start_hour:
            breakfast_hour += 24
        dinner_time = max(dinner_time, breakfast_hour + 6)
    
    if is_in_range(dinner_time, 17, 21):
        plan['dinner'] = {
            'time': format_time(dinner_time),
            'title': 'Bữa tối',
            'categories': ['com tam', 'mi cay', 'pho'],
            'icon': '🍽️'
        }
    
    # 🔥 TRÁNG MIỆNG (19:00 - 23:00)
    if has_dessert_theme:
        dessert_time = max(start_hour, 20)
        if dessert_time < start_hour:
            dessert_time += 24
        if 'dinner' in plan:
            dinner_hour = float(plan['dinner']['time'].split(':')[0]) + float(plan['dinner']['time'].split(':')[1]) / 60
            if dinner_hour < start_hour:
                dinner_hour += 24
            dessert_time = max(dessert_time, dinner_hour + 1.5)
        
        if is_in_range(dessert_time, 19, 24):  # 🔥 Đến 24h (0h)
            plan['dessert'] = {
                'time': format_time(dessert_time),
                'title': 'Tráng miệng',
                'categories': ['banh kem', 'kem', 'tra sua'],
                'icon': '🍰'
            }
    
    # 🔥 NẾU KHÔNG CÓ BỮA NÀO → TẠO BỮA MẶC ĐỊNH
    if len(plan) == 0:
        plan['meal'] = {
            'time': time_start_str,
            'title': 'Bữa ăn',
            'categories': ['pho', 'com tam', 'bun'],
            'icon': '🍜'
        }
        
        duration_hours = (time_end - time_start).seconds / 3600
        if has_coffee_chill and duration_hours >= 1.5:
            drink_time = time_start + timedelta(hours=duration_hours * 0.7)
            plan['drink'] = {
                'time': drink_time.strftime('%H:%M'),
                'title': 'Giải khát',
                'categories': ['tra sua', 'cafe'],
                'icon': '☕'
            }
    
    return plan

def generate_food_plan(user_lat, user_lon, csv_file='Data_with_flavor.csv', theme=None, user_tastes=None, start_time='07:00', end_time='21:00', radius_km=None):
    """Tạo kế hoạch ăn uống thông minh"""
    
    if radius_km is None or radius_km <= 0:
        return {
            'error': True,
            'message': 'Vui lòng chọn bán kính tìm kiếm'
        }
    
    df = pd.read_csv(csv_file)
    
    # 🔥 PARSE USER THEMES TRƯỚC
    user_selected_themes = []
    if theme:
        if isinstance(theme, str):
            user_selected_themes = [t.strip() for t in theme.split(',')]
        elif isinstance(theme, list):
            user_selected_themes = theme
    
    # 🔥 TRUYỀN user_selected_themes VÀO generate_meal_schedule
    plan = generate_meal_schedule(start_time, end_time, user_selected_themes)
    
    current_lat, current_lon = user_lat, user_lon
    used_place_ids = set()
    
    # 🔥 PARSE USER THEMES
    user_selected_themes = []
    if theme:
        if isinstance(theme, str):
            user_selected_themes = [t.strip() for t in theme.split(',')]
        elif isinstance(theme, list):
            user_selected_themes = theme
    
    places_found = 0
    keys_to_remove = []  # 🔥 THÊM LIST ĐỂ LƯU KEY CẦN XÓA
    
    for key, meal in plan.items():
        # 🔥 CHỌN THEME PHÙ HỢP CHO TỪNG BỮA
        meal_theme = get_theme_for_meal(key, user_selected_themes)
        
        filters = {
            'theme': meal_theme,
            'tastes': user_tastes if user_tastes else [],
            'radius_km': radius_km,
            'meal_time': meal['time']
        }
        
        places = find_places_advanced(
            current_lat, current_lon, df, 
            filters, excluded_ids=used_place_ids, top_n=20
        )
        
        # 🔥 LỌC ĐẶC BIỆT: Loại bánh mì khỏi bữa tráng miệng
        if key == 'dessert' and places:
            filtered_places = []
            for p in places:
                name_lower = normalize_text(p['ten_quan'])  # Dùng normalize_text (BỎ DẤU)
                # Loại bỏ tất cả quán có "banh mi" hoặc "banhmi"
                if 'banhmi' not in name_lower and 'banh mi' not in name_lower:
                    filtered_places.append(p)
            places = filtered_places
        
        # 🔥 Lọc CHẶT THEO KEYWORD - NHƯNG BỎ QUA CHO THEME ĐẶC BIỆT
        if places and key in MEAL_TYPE_KEYWORDS:
            # ⚡ KIỂM TRA XEM CÓ PHẢI THEME ĐẶC BIỆT KHÔNG
            skip_keyword_filter = False
            
            if meal_theme in ['food_street', 'michelin', 'luxury_dining']:
                skip_keyword_filter = True
                print(f"⚡ Theme đặc biệt '{meal_theme}' - BỎ QUA lọc keyword")
            
            # ⚡ CHỈ LỌC NẾU KHÔNG PHẢI THEME ĐẶC BIỆT
            if not skip_keyword_filter:
                meal_keywords = MEAL_TYPE_KEYWORDS[key]
                filtered_places = []
                
                for place in places:
                    name_normalized = normalize_text_with_accent(place['ten_quan'])
                    
                    for kw in meal_keywords:
                        kw_normalized = normalize_text_with_accent(kw)
                        search_text = ' ' + name_normalized + ' '
                        search_keyword = ' ' + kw_normalized + ' '
                        
                        if search_keyword in search_text:
                            filtered_places.append(place)
                            break
                
                places = filtered_places
                print(f"✅ Đã lọc keyword cho theme '{meal_theme}', còn {len(places)} quán")
            else:
                print(f"⚡ Giữ nguyên {len(places)} quán cho theme '{meal_theme}'")
        
        if places:
            places_found += 1
            weights = [1.0 / (i + 1) for i in range(len(places))]
            best_place = random.choices(places, weights=weights, k=1)[0]
            
            used_place_ids.add(best_place['data_id'])
            
            travel_time = estimate_travel_time(best_place['distance'])
            arrive_time = datetime.strptime(meal['time'], '%H:%M')
            suggest_leave = (arrive_time - timedelta(minutes=travel_time)).strftime('%H:%M')
            
            meal['place'] = {
                'ten_quan': best_place['ten_quan'],
                'dia_chi': best_place['dia_chi'],
                'rating': best_place['rating'],
                'lat': best_place['lat'],
                'lon': best_place['lon'],
                'distance': round(best_place['distance'], 2),
                'travel_time': travel_time,
                'suggest_leave': suggest_leave,
                'data_id': best_place['data_id'],
                'hinh_anh': best_place['hinh_anh'],
                'gia_trung_binh': best_place['gia_trung_binh'],
                'khau_vi': best_place['khau_vi'],
                'gio_mo_cua': best_place['gio_mo_cua'] 
            }
            
            current_lat = best_place['lat']
            current_lon = best_place['lon']
        else:
            # 🔥 KHÔNG CÓ QUÁN PHÙ HỢP → ĐÁNH DẤU XÓA
            print(f"⚠️ Không tìm được quán phù hợp cho {{key}} ({{meal['title']}}), bỏ bữa này")
            keys_to_remove.append(key)  # 🔥 THÊM VÀO LIST THAY VÌ XÓA NGAY
    
    # 🔥 XÓA CÁC BỮA KHÔNG TÌM ĐƯỢC QUÁN SAU KHI DUYỆT XONG
    for key in keys_to_remove:
        del plan[key]
    
    if places_found == 0:
        return {
            'error': True,
            'message': f'Không tìm thấy quán nào trong bán kính {{radius_km}} km'
        }
    
    return plan

# ==================== HTML INTERFACE ====================

def get_food_planner_html():
    """Trả về HTML cho Food Planner - Version 2"""
    return '''
<!-- Leaflet Polyline Offset Plugin -->
<script src="https://cdn.jsdelivr.net/npm/leaflet-polylineoffset@1.1.1/leaflet.polylineoffset.min.js"></script>
<style>
/* ========== FLOATING BUTTON ========== */
.food-planner-btn {
    position: fixed;
    bottom: 230px; /* đặt cao hơn nút 🍜 khoảng 80px */
    right: 30px;
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    border-radius: 50%;
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9998;
    transition: all 0.2s ease;
}

.food-planner-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(255, 107, 53, 0.4);
}

.food-planner-btn svg {
    width: 28px;
    height: 28px;
    fill: white;
}

/* ========== ROUTE TOOLTIP ========== */
.route-tooltip {
    background: rgba(0, 0, 0, 0.8) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

.route-tooltip::before {
    border-top-color: rgba(0, 0, 0, 0.8) !important;
}

.route-number-marker {
    background: none !important;
    border: none !important;
}

/* ========== SIDE PANEL ========== */
.food-planner-panel {
    position: fixed;
    top: 0;
    right: -550px;
    width: 550px;
    height: 100vh;
    background: white;
    z-index: 9999999999999 !important;
    transition: right 0.3s ease;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.food-planner-panel.active {
    right: 0;
}

/* ========== HEADER ========== */
.panel-header {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
    padding: 18px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

.panel-header h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}

.header-actions {
    display: flex;
    gap: 8px;
}

.header-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.header-btn:hover {
    background: rgba(255, 255, 255, 0.3);
}

.header-btn svg {
    width: 16px;
    height: 16px;
    fill: white;
}

/* ========== CONTENT AREA ========== */
.panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    padding-top: 10px;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* ========== NEW FILTERS DESIGN ========== */
.filters-wrapper-new {
    padding: 0;
    margin-bottom: 20px;
}

.filter-section-new {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
    border: 2px solid #E9ECEF;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
}

.filter-section-new:hover {
    border-color: #FF6B35;
    box-shadow: 0 6px 24px rgba(255, 107, 53, 0.12);
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid rgba(255, 107, 53, 0.1);
}

.section-icon {
    font-size: 28px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.section-title {
    font-size: 16px;
    font-weight: 700;
    color: #333;
    margin: 0;
}

/* ❤️ THEME GRID REDESIGN */
.theme-grid-new {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.theme-grid-new .theme-card {
    background: white;
    border: 2px solid #E9ECEF;
    border-radius: 12px;
    padding: 16px 12px;
    cursor: pointer;
    transition: all 0.25s ease;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.theme-grid-new .theme-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(255, 107, 53, 0.1) 0%, rgba(255, 142, 83, 0.1) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.theme-grid-new .theme-card:hover {
    border-color: #FF6B35;
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(255, 107, 53, 0.2);
}

.theme-grid-new .theme-card:hover::before {
    opacity: 1;
}

.theme-grid-new .theme-card.selected {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    border-color: #FF6B35;
    color: white;
    transform: scale(1.05);
    box-shadow: 0 8px 24px rgba(255, 107, 53, 0.4);
}

.theme-grid-new .theme-card.selected::before {
    opacity: 0;
}

.theme-grid-new .theme-icon {
    font-size: 32px;
    margin-bottom: 8px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
    transition: transform 0.3s ease;
}

.theme-grid-new .theme-card:hover .theme-icon {
    transform: scale(1.2) rotate(5deg);
}

.theme-grid-new .theme-card.selected .theme-icon {
    transform: scale(1.1);
}

.theme-grid-new .theme-name {
    font-size: 13px;
    font-weight: 600;
    line-height: 1.3;
}

/* ⏰ TIME PICKER REDESIGN */
.time-picker-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 2px solid #E9ECEF;
}

.time-picker-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.time-label {
    font-size: 13px;
    font-weight: 600;
    color: #666;
    text-align: center;
}

.time-input-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%);
    padding: 12px;
    border-radius: 12px;
    border: 2px solid #FFD699;
}

.time-input {
    width: 52px;
    height: 48px;
    padding: 0;
    border: 2px solid #FF6B35;
    border-radius: 10px;
    font-size: 20px;
    font-weight: 700;
    text-align: center;
    background: white;
    color: #FF6B35;
    outline: none;
    transition: all 0.2s ease;
}

.time-input:focus {
    border-color: #FF8E53;
    box-shadow: 0 0 0 4px rgba(255, 107, 53, 0.1);
    transform: scale(1.05);
}

.time-separator {
    font-size: 24px;
    font-weight: 700;
    color: #FF6B35;
}

.time-arrow {
    font-size: 24px;
    color: #FF6B35;
    font-weight: 700;
    flex-shrink: 0;
}

/* 🎯 BUTTON REDESIGN */
.generate-btn-new {
    width: 100%;
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
    border: none;
    padding: 18px 24px;
    border-radius: 16px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    box-shadow: 0 6px 20px rgba(255, 107, 53, 0.3);
    position: relative;
    overflow: hidden;
}

.generate-btn-new::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.5s ease;
}

.generate-btn-new:hover::before {
    left: 100%;
}

.generate-btn-new:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(255, 107, 53, 0.4);
}

.generate-btn-new:active {
    transform: translateY(0);
}

.btn-icon {
    font-size: 20px;
}

.btn-text {
    font-size: 16px;
}

.btn-arrow {
    font-size: 20px;
    transition: transform 0.3s ease;
}

.generate-btn-new:hover .btn-arrow {
    transform: translateX(4px);
}

/* 📱 RESPONSIVE */
@media (max-width: 768px) {
    .theme-grid-new {
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    
    .time-picker-container {
        flex-direction: column;
        gap: 12px;
    }
    
    .time-arrow {
        transform: rotate(90deg);
    }
    
    .time-picker-group {
        width: 100%;
    }
}


/* ========== SAVED PLANS SECTION ========== */
.saved-plans-section {
    background: linear-gradient(135deg, #FFF9F5 0%, #FFF5F0 100%);
    border: 2px solid #FFE5D9;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(255, 107, 53, 0.1);
}

.saved-plans-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 15px;
    padding: 10px;
    background: white;
    border-radius: 12px;
    transition: all 0.2s ease;
}

.saved-plans-header:hover {
    background: #FFF5F0;
    transform: translateY(-2px);
}

.saved-plans-header .filter-title {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #FF6B35 !important;
}

.saved-plans-list {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}

.saved-plans-list.open {
    max-height: 400px;
    overflow-y: auto;
}

.saved-plan-item {
    background: white;
    border: 2px solid #FFE5D9;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.saved-plan-item:hover {
    border-color: #FF6B35;
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(255, 107, 53, 0.15);
}

.saved-plan-info {
    flex: 1;
}

.saved-plan-name {
    font-weight: 700;
    color: #333;
    font-size: 15px;
    margin-bottom: 6px;
    max-width: 180px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.saved-plan-date {
    font-size: 13px;
    color: #999;
    font-weight: 500;
}

.delete-plan-btn {
    background: #e74c3c;
    color: white;
    border: none;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.delete-plan-btn:hover {
    background: #c0392b;
}

/* ========== STYLE TÊN PLAN KHI EDIT ========== */
.schedule-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 🔥 Icon emoji - cố định, KHÔNG di chuyển */
.schedule-title > span:first-child {
    flex-shrink: 0;
}

/* 🔥 Container cho text - có overflow */
.schedule-title > span:last-child {
    flex: 1;
    min-width: 0;
    max-width: 280px;
    overflow: hidden;
    position: relative;
}

/* 🔥 Text bên trong - MẶC ĐỊNH KHÔNG chạy */
.schedule-title > span:last-child > span {
    display: inline-block;
    white-space: nowrap;
    animation: none; /* 🔥 Mặc định tắt */
}

/* 🔥 CHỈ CHẠY khi có class "overflow" */
.schedule-title > span:last-child.overflow > span {
    animation: marquee 10s ease-in-out infinite;
}

/* 🔥 Animation chạy qua lại - mượt mà hơn */
@keyframes marquee {
    0% {
        transform: translateX(0);
    }
    40% {
        transform: translateX(calc(-100% + 100px)); /* Chạy sang trái */
    }
    50% {
        transform: translateX(calc(-100% + 100px)); /* Dừng lại lâu hơn */
    }
    60% {
        transform: translateX(calc(-100% + 100px)); /* Dừng tiếp */
    }
    100% {
        transform: translateX(0); /* Chạy về phải */
    }
}

/* ========== KHI Ở CHẾ ĐỘ EDIT - KHUNG VIỀN CAM GRADIENT CỐ ĐỊNH ========== */
.schedule-title > span[contenteditable="true"] {
    border: 3px solid transparent;
    background: linear-gradient(white, white) padding-box,
                linear-gradient(to right, #FF6B35, #FF8E53) border-box;
    border-radius: 8px;
    padding: 6px 10px;
    width: 100%;
    max-width: 180px; /* 🔥 THU NHỎ lại để tránh nút + */
    min-width: 150px;
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    display: block;
    outline: none;
    cursor: text;
    box-sizing: border-box;
    margin-right: 8px; /* 🔥 THÊM khoảng cách với nút bên phải */
}

/* 🔥 TẮT ANIMATION khi đang edit */
.schedule-title > span[contenteditable="true"] > span {
    animation: none !important;
    transform: none !important;
}

/* 🔥 Ẩn scrollbar nhưng vẫn scroll được */
.schedule-title > span[contenteditable="true"]::-webkit-scrollbar {
    height: 3px;
}

.schedule-title > span[contenteditable="true"]::-webkit-scrollbar-thumb {
    background: linear-gradient(to right, #FF6B35, #FF8E53);
    border-radius: 10px;
}

.schedule-title > span[contenteditable="true"]::-webkit-scrollbar-track {
    background: #FFE5D9;
}

/* ========== TIMELINE VERTICAL - REDESIGN ========== */
.timeline-container {
    position: relative;
    padding: 20px 0;
    margin-top: 20px;
}

.timeline-line {
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(to bottom, #FF6B35, #FF8E53);
    transform: translateX(-50%);
    z-index: 0;
}

.meal-item {
    position: relative;
    margin-bottom: 30px;
    padding: 0;
    z-index: 1;
}

.meal-item:last-child {
    margin-bottom: 0;
}

.meal-item.dragging {
    opacity: 0.5;
}

/* ========== TIME MARKER - TRÊN ĐẦU CARD ========== */
.time-marker {
    position: relative;
    text-align: center;
    margin-bottom: 12px;
    z-index: 2;
}

.time-badge {
    display: inline-block;
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
    padding: 10px 24px;
    border-radius: 25px;
    font-size: 16px;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
    white-space: nowrap;
    letter-spacing: 0.5px;
    border: 3px solid white;
}

/* ========== TIME DOT - ẨN ĐI ========== */
.time-dot {
    display: none;
}

.meal-card-vertical {
    background: linear-gradient(135deg, #FFF9F5 0%, #FFF5F0 100%);
    border: 2px solid #FFE5D9;
    border-radius: 16px;
    padding: 20px;
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
    overflow: visible;
    box-shadow: 0 4px 16px rgba(255, 107, 53, 0.1);
    width: 100%;
}

.meal-card-vertical::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 6px;
    height: 100%;
    background: linear-gradient(to bottom, #FF6B35, #FF8E53);
    border-radius: 16px 0 0 16px;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.meal-card-vertical:hover {
    border-color: #FF6B35;
    box-shadow: 0 8px 32px rgba(255, 107, 53, 0.2);
    transform: translateY(-4px);
}

.meal-card-vertical:hover::before {
    opacity: 1;
}

.meal-card-vertical.edit-mode {
    cursor: default;
    background: linear-gradient(135deg, #FAFBFC 0%, #F5F7FA 100%);
}

.meal-card-vertical.empty-slot {
    background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
    border: 2px dashed #4caf50;
    cursor: default;
}

.meal-card-vertical.empty-slot:hover {
    border-color: #45a049;
    background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
    transform: none;
}

/* ========== HIGHLIGHT EFFECT KHI SẮP XẾP LẠI ========== */
@keyframes repositionPulse {
    0%, 100% {
        background: #FFF5F0;
        border-color: #FFE5D9;
        box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
    }
    25% {
        background: #E8F5E9;
        border-color: #4caf50;
        box-shadow: 0 0 0 8px rgba(76, 175, 80, 0.3);
    }
    50% {
        background: #FFF5F0;
        border-color: #FFE5D9;
        box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
    }
    75% {
        background: #E8F5E9;
        border-color: #4caf50;
        box-shadow: 0 0 0 8px rgba(76, 175, 80, 0.3);
    }
}

/* ========== DRAG & DROP VISUAL FEEDBACK ========== */
.meal-item[draggable="true"] {
    cursor: move;
}

.meal-item[draggable="true"]:active {
    cursor: grabbing;
}

.meal-item.dragging {
    opacity: 0.5;
}

.meal-item.drag-over {
    transform: scale(1.02);
    transition: transform 0.2s ease;
}

.meal-card-vertical.drop-target {
    border: 2px dashed #4caf50 !important;
    background: #E8F5E9 !important;
}

.meal-card-vertical.just-dropped {
    animation: repositionPulse 1.5s ease-in-out;
}

.meal-card-vertical.repositioned {
    animation: repositionPulse 1.5s ease-in-out;
}

/* Icon di chuyển lên/xuống */
.reposition-indicator {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 24px;
    animation: slideIndicator 0.8s ease-out;
    pointer-events: none;
    z-index: 100;
}

@keyframes slideIndicator {
    0% {
        opacity: 0;
        transform: translateY(-50%) scale(0.5);
    }
    50% {
        opacity: 1;
        transform: translateY(-50%) scale(1.2);
    }
    100% {
        opacity: 0;
        transform: translateY(-50%) scale(0.8);
    }
}


.meal-title-vertical {
    font-size: 16px;
    font-weight: 700;
    color: #333;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 12px;
    border-bottom: 2px solid rgba(255, 107, 53, 0.1);
}

.meal-title-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.meal-title-left > span:first-child {
    font-size: 24px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.meal-title-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ========== MEAL ACTIONS - REDESIGN ========== */
.meal-actions {
    display: none;
    gap: 10px;
    flex-wrap: nowrap; /* ✅ BẮT BUỘC NGANG HÀNG */
    align-items: center; /* ✅ CĂNG GIỮA */
}

.meal-card-vertical.edit-mode .meal-actions {
    display: flex;
}

/* ✅ NÚT CƠ BẢN - TO HƠN, RÕ RÀNG HƠN */
.meal-action-btn {
    background: white;
    border: 2px solid #e9ecef;
    padding: 10px 16px;
    border-radius: 12px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    position: relative;
    overflow: hidden;
    white-space: nowrap;
    min-height: 44px;
    outline: none; /* ✅ XÓA VIỀN ĐEN */
}

/* ✅ XÓA OUTLINE KHI FOCUS/ACTIVE */
.meal-action-btn:focus,
.meal-action-btn:active {
    outline: none;
}

.meal-action-btn:hover::before {
    opacity: 1;
}

/* ✅ ĐẢM BẢO ICON + TEXT Ở TRÊN */
.meal-action-btn .btn-icon,
.meal-action-btn .btn-text {
    position: relative;
    z-index: 1;
}

.meal-action-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    background: #f8f9fa; /* ✅ THÊM DÒNG NÀY */
    border-color: inherit;
}

.meal-action-btn:active {
    transform: translateY(0);
}

/* ✅ ICON + TEXT TRONG NÚT */
.meal-action-btn .btn-icon {
    font-size: 18px;
    line-height: 1;
    z-index: 1;
}

.meal-action-btn .btn-text {
    font-size: 13px;
    font-weight: 700;
    z-index: 1;
}

/* ========== NÚT XÓA - ĐỎ RÕ RÀNG ========== */
.meal-action-btn.delete-meal {
    background: linear-gradient(135deg, #fee 0%, #fdd 100%);
    border-color: #e74c3c;
    color: #c0392b;
}

.meal-action-btn.delete-meal:hover {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    border-color: #c0392b;
    color: white;
    box-shadow: 0 4px 16px rgba(231, 76, 60, 0.4);
}

/* ========== NÚT CHỌN QUÁN - XANH LÁ NỔI BẬT ========== */
.meal-action-btn.select-meal {
    background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
    border: 2px solid #4caf50;
    color: #2e7d32;
    flex: 1; /* ✅ Chiếm nhiều không gian hơn */
    min-width: 140px; /* ✅ Đủ rộng để hiển thị text */
}

.meal-action-btn.select-meal:hover {
    background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
    border-color: #45a049;
    color: white;
    box-shadow: 0 4px 16px rgba(76, 175, 80, 0.4);
}

/* ✅ TRẠNG THÁI ACTIVE - ĐANG CHỜ CHỌN */
.meal-action-btn.select-meal.active {
    background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
    border-color: #2e7d32;
    color: white;
    animation: selectPulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.2);
}

@keyframes selectPulse {
    0%, 100% { 
        box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.2);
        transform: scale(1);
    }
    50% { 
        box-shadow: 0 0 0 8px rgba(76, 175, 80, 0.1);
        transform: scale(1.03);
    }
}

/* ✅ RESPONSIVE - MOBILE */
@media (max-width: 768px) {
    .meal-actions {
        width: 100%;
        flex-wrap: nowrap; /* ✅ VẪN NGANG TRÊN MOBILE */
    }
    
    .meal-action-btn {
        flex: 1;
        min-width: 0;
        padding: 8px 10px; /* ✅ THU NHỎ PADDING */
    }
    
    .meal-action-btn.select-meal {
        min-width: 0;
    }
    
    .meal-action-btn .btn-text {
        font-size: 11px; /* ✅ CHỮ NHỎ HƠN */
    }
    
    .meal-action-btn .btn-icon {
        font-size: 16px; /* ✅ ICON NHỎ HƠN */
    }
}

.place-info-vertical {
    background: white;
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(255, 107, 53, 0.1);
}

.place-name-vertical {
    font-weight: 700;
    color: #FF6B35;
    margin-bottom: 8px;
    font-size: 15px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.place-name-vertical::before {
    content: '🍽️';
    font-size: 18px;
}

.place-address-vertical {
    color: #666;
    font-size: 13px;
    margin-bottom: 12px;
    line-height: 1.5;
    padding-left: 20px;
    position: relative;
}

.place-name-vertical {
    font-weight: 600;
    color: #FF6B35;
    margin-bottom: 5px;
    font-size: 14px;
}

.place-address-vertical {
    color: #666;
    font-size: 12px;
    margin-bottom: 10px;
    line-height: 1.4;
}

.place-meta-vertical {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 13px;
    margin-bottom: 12px;
}

.meta-item-vertical {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%);
    border-radius: 20px;
    color: #8B6914;
    font-weight: 600;
    border: 1px solid #FFD699;
}

.meta-item-vertical span {
    font-size: 16px;
}

.meta-item-vertical {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #666;
}

.travel-info-vertical {
    background: #FFF5E6;
    border-left: 3px solid #FFB84D;
    padding: 8px 10px;
    margin-top: 10px;
    border-radius: 4px;
    font-size: 12px;
    color: #8B6914;
    line-height: 1.4;
}

.time-input-inline {
    padding: 6px 10px;
    border: 2px solid #FFE5D9;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    outline: none;
    width: 100px;
    text-align: center;
}

.time-input-inline:focus {
    border-color: #FF6B35;
}

.empty-slot-content {
    text-align: center;
    padding: 20px;
    color: #4caf50;
}

.empty-slot-content .icon {
    font-size: 32px;
    margin-bottom: 8px;
}

.empty-slot-content .text {
    font-size: 14px;
    font-weight: 600;
}

/* ========== ACTION BUTTONS ========== */
.action-btn {
    min-width: 52px;
    height: 52px;
    border-radius: 26px;
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
    font-size: 15px;
    font-weight: 700;
    position: relative;
    overflow: hidden;
}

.action-btn::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.action-btn:hover::before {
    width: 300px;
    height: 300px;
}

.action-btn:hover {
    transform: translateY(-4px) scale(1.05);
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}

.action-btn:active {
    transform: translateY(-2px) scale(1.02);
    transition: all 0.1s;
}

/* 🔥 NÚT EDIT (CAM) */
.action-btn.edit {
    background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%);
    color: white;
}

.action-btn.edit:hover {
    background: linear-gradient(135deg, #FFB84D 0%, #FFA500 100%);
    box-shadow: 0 8px 24px rgba(255, 165, 0, 0.4);
}

.action-btn.edit.active {
    background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
    animation: editPulse 2s infinite;
}

.action-btn.edit.active:hover {
    background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
    box-shadow: 0 8px 24px rgba(76, 175, 80, 0.4);
}

@keyframes editPulse {
    0%, 100% {
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    50% {
        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.6);
    }
}

/* 🔥 NÚT LƯU (ĐỎ CAM GRADIENT) */
.action-btn.primary {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
}

.action-btn.primary:hover {
    background: linear-gradient(135deg, #FF8E53 0%, #FFB84D 100%);
    box-shadow: 0 8px 24px rgba(255, 107, 53, 0.4);
}

.action-btn.add {
    background: #4caf50;
    color: white;
}

.action-btn.add:hover {
    background: #45a049;
}

.action-btn svg {
    width: 22px;
    height: 22px;
    fill: white;
    z-index: 1;
    flex-shrink: 0;
}

.btn-label {
    z-index: 1;
    white-space: nowrap;
    color: white;
    font-size: 15px;
    font-weight: 700;
}

/* 🔥 NÚT CHIA SẺ (XANH DƯƠNG) */
.action-btn.share {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    color: white;
}

.action-btn.share:hover {
    background: linear-gradient(135deg, #42A5F5 0%, #2196F3 100%);
    box-shadow: 0 8px 24px rgba(33, 150, 243, 0.4);
}

/* ========== SCHEDULE HEADER ========== */
.schedule-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    background: white;
    z-index: 10;
    padding: 8px 16px;
    border-bottom: 1px solid #eee;
}

.schedule-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    max-width: 280px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.action-buttons {
    display: flex;
    flex-direction: row-reverse;
    gap: 10px;
}

/* ========== STYLE INPUT TÊN CARD ========== */
.meal-title-input {
    padding: 4px 8px;
    border: 2px solid #FFE5D9;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    outline: none;
    width: 160px;
    background: white; /* 🔥 THÊM background */
}

.meal-title-input:focus {
    border-color: #FF6B35;
}

.meal-tick-btn:hover {
    transform: scale(1.15);
    opacity: 0.8;
}

/* ========== MOBILE RESPONSIVE ========== */
@media (max-width: 768px) {
    .food-planner-panel {
        width: 100%;
        right: -100%;
    }
    
    .timeline-container {
        padding: 20px 0;
    }
    
    .meal-item {
        padding: 0;
        margin-bottom: 30px;
    }
    
    .time-dot {
        width: 16px;
        height: 16px;
    }
    
    .food-planner-btn {
        right: 20px;
    }
    
    .time-badge {
        padding: 8px 20px;
        font-size: 14px;
    }
}

/* ========== AUTO-SCROLL ZONE INDICATOR ========== */
.panel-content.scrolling-up::before,
.panel-content.scrolling-down::after {
    content: '';
    position: fixed;
    left: 0;
    right: 0;
    height: 200px;
    pointer-events: none;
    z-index: 999;
    animation: scrollZonePulse 1s infinite;
}

.panel-content.scrolling-up::before {
    top: 60px; /* Dưới header */
    background: linear-gradient(to bottom, rgba(76, 175, 80, 0.1), transparent);
}

.panel-content.scrolling-down::after {
    bottom: 0;
    background: linear-gradient(to top, rgba(76, 175, 80, 0.1), transparent);
}

@keyframes scrollZonePulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 0.8; }
}

/* 🔥 CHẶN SCROLL KHI HOVER VÀO INPUT GIỜ/PHÚT */
.time-input-hour:hover,
.time-input-minute:hover {
    overscroll-behavior: contain;
}

/* 🔥 CHẶN SCROLL TOÀN BỘ PANEL KHI FOCUS VÀO INPUT */
.panel-content:has(.time-input-hour:focus),
.panel-content:has(.time-input-minute:focus) {
    overflow: hidden !important;
}

/* ========== TOOLTIP HƯỚNG DẪN ========== */
.meal-action-btn[title]:hover::after {
    content: attr(title);
    position: absolute;
    bottom: calc(100% + 10px);
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    pointer-events: none;
    animation: tooltipFadeIn 0.2s ease-out;
}

.meal-action-btn[title]:hover::before {
    content: '';
    position: absolute;
    bottom: calc(100% + 2px);
    left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-top-color: rgba(0, 0, 0, 0.9);
    z-index: 1000;
    pointer-events: none;
    animation: tooltipFadeIn 0.2s ease-out;
}

@keyframes tooltipFadeIn {
    from {
        opacity: 0;
        transform: translateX(-50%) translateY(5px);
    }
    to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
}

/* ✅ ẨN TOOLTIP MẶC ĐỊNH CỦA BROWSER */
.meal-action-btn {
    position: relative;
}

/* ========== NÚT ĐÓNG THU THEO PANEL ========== */
.close-panel-btn {
    position: fixed;
    top: 50%;
    right: -48px; /* ✅ MẶC ĐỊNH ẨN NGOÀI MÀN HÌNH */
    transform: translateY(-50%);
    width: 48px;
    height: 100px;
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    border: none;
    border-radius: 12px 0 0 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999999999;
    box-shadow: -6px 0 20px rgba(255, 107, 53, 0.4);
    transition: right 0.3s ease, transform 0.3s ease, width 0.3s ease, box-shadow 0.3s ease, background 0.3s ease; /* ✅ CHỈ GIỮ TRANSITION CẦN THIẾT */
    overflow: hidden;
}

.close-panel-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.6s ease;
}

.close-panel-btn:hover::before {
    left: 100%;
}

/* ✅ KHI PANEL MỞ → NÚT XUẤT HIỆN */
.food-planner-panel.active .close-panel-btn {
    right: 550px !important; /* ✅ LỒI RA BÊN TRÁI PANEL */
}

.close-panel-btn:hover {
    background: linear-gradient(135deg, #FF8E53 0%, #FFB84D 100%);
    box-shadow: -8px 0 28px rgba(255, 107, 53, 0.5);
    transform: translateY(-50%) translateX(20px);
    width: 56px;
}

.close-panel-btn:active {
    transform: translateY(-50%) translateX(4px) scale(0.95);
}

.close-panel-btn .arrow-icon {
    font-size: 28px;
    font-weight: 900;
    color: white;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    animation: arrowPulse 2s ease-in-out infinite;
}

@keyframes arrowPulse {
    0%, 100% {
        transform: translateX(0);
        opacity: 1;
    }
    50% {
        transform: translateX(4px);
        opacity: 0.8;
    }
}

.close-panel-btn:hover .arrow-icon {
    animation: arrowBounce 0.6s ease-in-out infinite;
}

@keyframes arrowBounce {
    0%, 100% {
        transform: translateX(0);
    }
    50% {
        transform: translateX(8px);
    }
}

/* ========== RESPONSIVE ========== */
@media (max-width: 768px) {
    .close-panel-btn {
        right: -48px; /* ✅ Mobile: ẨN mặc định */
    }
    
    .food-planner-panel.active ~ .close-panel-btn {
        right: 100%; /* ✅ Mobile: panel = 100% width */
        width: 36px;
        height: 70px;
    }
}

</style>

<!-- Food Planner Button -->
<div class="food-planner-btn" id="foodPlannerBtn" title="Lên kế hoạch ăn uống">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z"/>
    </svg>
</div>

<!-- Food Planner Panel -->
<div class="food-planner-panel" id="foodPlannerPanel">
    <div class="panel-header">
        <h2 style="font-size: 22px;">
            <span style="font-size: 26px;">📋</span> Lịch trình bữa ăn
        </h2>
    </div>
        
        <div class="panel-content">
            <!-- AUTO MODE -->
            <div class="tab-content active" id="autoTab">
                <div class="filters-wrapper-new">
                    <!-- ❤️ BẢNG CHỦ ĐỀ ĐẸP -->
                    <div class="filter-section-new theme-section">
                        <div class="section-header">
                            <span class="section-icon">❤️</span>
                            <h3 class="section-title">Chọn chủ đề yêu thích</h3>
                        </div>
                        <div class="theme-grid-new" id="themeGrid"></div>
                    </div>
                    
                    <!-- ⏰ KHUNG THỜI GIAN ĐẸP -->
                    <div class="filter-section-new time-section">
                        <div class="section-header">
                            <span class="section-icon">⏰</span>
                            <h3 class="section-title">Khoảng thời gian</h3>
                        </div>
                        <div class="time-picker-container">
                            <div class="time-picker-group">
                                <label class="time-label">Từ</label>
                                <div class="time-input-wrapper">
                                    <input type="number" id="startHour" min="0" max="23" value="07" class="time-input">
                                    <span class="time-separator">:</span>
                                    <input type="number" id="startMinute" min="0" max="59" value="00" class="time-input">
                                </div>
                            </div>
                            
                            <div class="time-arrow">→</div>
                            
                            <div class="time-picker-group">
                                <label class="time-label">Đến</label>
                                <div class="time-input-wrapper">
                                    <input type="number" id="endHour" min="0" max="23" value="21" class="time-input">
                                    <span class="time-separator">:</span>
                                    <input type="number" id="endMinute" min="0" max="59" value="00" class="time-input">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 🎯 NÚT TẠO KẾ HOẠCH ĐẸP -->
                    <button class="generate-btn-new" onclick="generateAutoPlan()">
                        <span class="btn-icon">✨</span>
                        <span class="btn-text">Tạo kế hoạch tự động</span>
                        <span class="btn-arrow">→</span>
                    </button>
                </div>
                
                <!-- Saved Plans Section -->
                <div class="saved-plans-section" id="savedPlansSection" style="display: block;">
                    <div class="saved-plans-header" onclick="toggleSavedPlans()">
                        <div class="filter-title" style="margin: 0; font-size: 16px; font-weight: 700; color: #FF6B35;">
                            <span style="font-size: 20px; margin-right: 8px;">📋</span>
                            Lịch trình đã lưu
                        </div>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width: 20px; height: 20px; transition: transform 0.3s ease; color: #FF6B35;" id="savedPlansArrow">
                            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                        </svg>
                    </div>
                    <div class="saved-plans-list" id="savedPlansList"></div>
                </div>
                
                <div id="planResult"></div>
            </div>  
        </div>
        <!-- ✅ NÚT ĐÓNG ĐẸP HƠN VỚI ICON >> -->
            <button class="close-panel-btn" onclick="closeFoodPlanner()" title="Đóng lịch trình">
                <span class="arrow-icon">»</span>
            </button>
    </div>
</div>

<script>
// ========== GLOBAL STATE ==========
let isPlannerOpen = false;
let selectedThemes = []; // Đổi từ selectedTheme thành selectedThemes (array)
let currentPlan = null;
let currentPlanId = null;
let suggestedFoodStreet = null;
let filtersCollapsed = false;
let isEditMode = false;
let draggedElement = null;
let selectedPlaceForReplacement = null;
let waitingForPlaceSelection = null;
let autoScrollInterval = null;
let lastDragY = 0;
let dragDirection = 0;
let lastTargetElement = null;
window.currentPlanName = null;

// Themes data
const themes = {
    'street_food': { name: 'Ẩm thực đường phố', icon: '🍜' },
    'seafood': { name: 'Hải sản', icon: '🦞' },
    'coffee_chill': { name: 'Giải khát', icon: '☕' },
    'luxury_dining': { name: 'Nhà hàng sang trọng', icon: '🍽️' },
    'asian_fusion': { name: 'Ẩm thực châu Á', icon: '🍱' },
    'vegetarian': { name: 'Món chay', icon: '🥗' },
    'dessert_bakery': { name: 'Tráng miệng & Bánh', icon: '🍰' },
    'spicy_food': { name: 'Đồ cay', icon: '🌶️' },
    'food_street': { name: 'Khu ẩm thực', icon: '🏪' },
    'michelin': { name: 'Michelin', icon: '⭐' }
};

// Meal icons
const mealIcons = {
    'breakfast': '🍳',
    'morning_drink': '🧋',
    'lunch': '🍚',
    'afternoon_drink': '☕',
    'dinner': '🍽️',
    'dessert': '🍰',
    'meal': '🍜',
    'meal1': '🍚',
    'meal2': '🥖',
    'drink': '☕'
};

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    initThemeGrid();
    loadSavedPlans();
});

function initThemeGrid() {
    const grid = document.getElementById('themeGrid');
    if (!grid) return;
    
    // 🔥 XÓA CLASS CŨ
    grid.className = '';
    
    // 🔥 CẤU TRÚC MỚI - CHIA THÀNH 3 SECTIONS
    const sections = [
        {
            title: 'Giải khát & Tráng miệng',
            icon: '🍹',
            themes: ['coffee_chill', 'dessert_bakery'],
            columns: 2
        },
        {
            title: 'Ẩm thực đa dạng',
            icon: '🍽️',
            themes: ['street_food', 'asian_fusion', 'seafood', 'luxury_dining', 'vegetarian', 'spicy_food'],
            columns: 2
        },
        {
            title: 'Khu du lịch',
            icon: '🏙️',
            themes: ['food_street', 'michelin'],
            columns: 2
        }
    ];
    
    sections.forEach(section => {
        // Tạo section container
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'theme-section-group';
        sectionDiv.style.marginBottom = '24px';
        
        // Tạo header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'theme-section-header';
        headerDiv.innerHTML = `
            <span style="font-size: 24px; margin-right: 8px;">${section.icon}</span>
            <span style="font-size: 14px; font-weight: 700; color: #333;">${section.title}</span>
        `;
        headerDiv.style.cssText = `
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            padding: 8px 12px;
            background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%);
            border-radius: 12px;
            border: 2px solid #FFD699;
        `;
        
        // Tạo grid cho themes
        const themeGrid = document.createElement('div');
        themeGrid.className = 'theme-grid-new';
        themeGrid.style.gridTemplateColumns = `repeat(${section.columns}, 1fr)`;
        
        section.themes.forEach(key => {
            const theme = themes[key];
            const card = document.createElement('div');
            card.className = 'theme-card';
            card.dataset.theme = key;
            card.innerHTML = `
                <div class="theme-icon">${theme.icon}</div>
                <div class="theme-name">${theme.name}</div>
            `;
            card.onclick = () => selectTheme(key);
            themeGrid.appendChild(card);
        });
        
        sectionDiv.appendChild(headerDiv);
        sectionDiv.appendChild(themeGrid);
        grid.appendChild(sectionDiv);
    });
}

// ========== THEME SELECTION ==========
function selectTheme(themeKey) {
    const card = document.querySelector(`[data-theme="${themeKey}"]`);
    
    if (selectedThemes.includes(themeKey)) {
        // Bỏ chọn
        selectedThemes = selectedThemes.filter(t => t !== themeKey);
        if (card) card.classList.remove('selected');
    } else {
        // Thêm vào chọn
        selectedThemes.push(themeKey);
        if (card) card.classList.add('selected');
    }
}

// ========== SAVED PLANS ==========
function displaySavedPlansList(plans) {
    const listDiv = document.getElementById('savedPlansList');

    // ✅ Bắt đầu với nút "Tạo mới"
    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
            <span style="font-size: 14px; font-weight: 600; color: #333;">📋 Danh sách lịch trình</span>
            <button onclick="createNewEmptyPlan()" style="background: #4caf50; color: white; border: none; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;" title="Tạo lịch trình mới">+</button>
        </div>
    `;

    // ✅ Nếu không có plans → chỉ thêm thông báo
    if (!plans || plans.length === 0) {
        html += '<p style="color: #999; font-size: 13px; padding: 15px; text-align: center;">Chưa có kế hoạch nào</p>';
        listDiv.innerHTML = html;
        return;
    }
    
    // ✅ Nếu có plans → thêm từng plan vào html (KHÔNG khai báo lại)
    plans.forEach((plan, index) => {
        const date = new Date(plan.savedAt);
        const dateStr = date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
        const timeStr = date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
        
        html += `
            <div class="saved-plan-item" onclick="loadSavedPlans('${plan.id}')">
                <div class="saved-plan-info">
                    <div class="saved-plan-name">${plan.name}</div>
                    <div class="saved-plan-date">📅 ${dateStr} • ⏰ ${timeStr}</div>
                </div>
                <button class="delete-plan-btn" onclick="event.stopPropagation(); deleteSavedPlan('${plan.id}')">×</button>
            </div>
        `;
    });
    
    listDiv.innerHTML = html;
}

function toggleSavedPlans() {
    const listDiv = document.getElementById('savedPlansList');
    const arrow = document.getElementById('savedPlansArrow');
    
    // 🔥 NẾU ĐANG MỞ "LỊCH TRÌNH ĐÃ LƯU" → ĐÓNG FILTERS
    if (!listDiv.classList.contains('open')) {
        const filtersWrapper = document.getElementById('filtersWrapper');
        if (filtersWrapper && !filtersWrapper.classList.contains('collapsed')) {
            toggleFilters(); // Đóng filters trước khi mở lịch trình
        }
    }
    
    if (listDiv.classList.contains('open')) {
        listDiv.classList.remove('open');
        arrow.style.transform = 'rotate(0deg)';
    } else {
        listDiv.classList.add('open');
        arrow.style.transform = 'rotate(180deg)';
    }
}

// ========== SAVE PLAN - Sử dụng ARRAY THAY VÌ OBJECT ==========
function savePlan() {
    if (!currentPlan) return;

    // 🔥 LƯỚI ĐÚNG THỨ TỰ VỀ DOM
    const mealItems = document.querySelectorAll('.meal-item');
    const planArray = [];
    
    // Lấy thứ tự từ DOM (user đã kéo thả)
    mealItems.forEach(item => {
        const mealKey = item.dataset.mealKey;
        if (mealKey && currentPlan[mealKey]) {
            // 🔥 CẬP NHẬT THỜI GIAN từ input giờ/phút
            const hourInput = item.querySelector('.time-input-hour[data-meal-key="' + mealKey + '"]');
            const minuteInput = item.querySelector('.time-input-minute[data-meal-key="' + mealKey + '"]');
            
            if (hourInput && minuteInput) {
                const hour = hourInput.value.padStart(2, '0');
                const minute = minuteInput.value.padStart(2, '0');
                currentPlan[mealKey].time = `${hour}:${minute}`;
            }
            
            // 🔥 CẬP NHẬT TITLE từ input (CHỈ GIỮ 1 LẦN)
            const titleInput = item.querySelector('input[onchange*="updateMealTitle"]');
            if (titleInput && titleInput.value) {
                currentPlan[mealKey].title = titleInput.value;
            }
            
            // Thêm vào array
            planArray.push({
                key: mealKey,
                data: JSON.parse(JSON.stringify(currentPlan[mealKey])) // Deep copy
            });
        }
    });

    // ✅ KIỂM TRA PLAN CÓ DỮ LIỆU KHÔNG
    if (planArray.length === 0) {
        alert('⚠️ Lịch trình trống! Hãy thêm ít nhất 1 quán trước khi lưu.');
        return;
    }

    // Cập nhật order
    currentPlan._order = planArray.map(x => x.key);
    // Xóa quán gợi ý trước khi lưu
    suggestedFoodStreet = null;

    // 🔥 LẤY TÊN TỪ DOM (nếu user đã edit inline)
    const titleElement = document.querySelector('.schedule-title span[contenteditable]');
    let currentDisplayName = titleElement ? titleElement.textContent.trim() : (window.currentPlanName || '');
    
    // ✅ XỬ LÝ TÊN PLAN
    if (!currentPlanId) {
        // 🔥 PLAN MỚI (chưa có ID) → BẮT BUỘC PHẢI HỎI TÊN
        currentDisplayName = prompt('Đặt tên cho kế hoạch:', currentDisplayName || `Kế hoạch ${new Date().toLocaleDateString('vi-VN')}`);
        if (!currentDisplayName || currentDisplayName.trim() === '') {
            alert('⚠️ Bạn phải đặt tên để lưu lịch trình!');
            return;
        }
        currentDisplayName = currentDisplayName.trim();
    } else {
        // 🔥 PLAN CŨ (đã có ID)
        if (!currentDisplayName || currentDisplayName === 'Lịch trình của bạn') {
            // Chưa có tên custom → hỏi
            currentDisplayName = prompt('Đặt tên cho kế hoạch:', `Kế hoạch ${new Date().toLocaleDateString('vi-VN')}`);
            if (!currentDisplayName) return;
        }
        // Đã có tên custom → giữ nguyên, không hỏi
    }
    
    // ✅ TẠO HOẶC CẬP NHẬT PLAN
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    
    const planRecord = {
        id: currentPlanId || Date.now().toString(), // 🔥 TẠO ID MỚI NẾU CHƯA CÓ
        name: currentDisplayName,
        plan: planArray,
        savedAt: new Date().toISOString(),
        radius: window.currentRadius || '10'  // 🔥 THÊM DÒNG NÀY
    };
    
    if (currentPlanId) {
        // 🔥 CẬP NHẬT PLAN CŨ
        const index = savedPlans.findIndex(p => p.id === currentPlanId);
        if (index !== -1) {
            savedPlans[index] = planRecord;
        } else {
            // Không tìm thấy ID cũ → thêm mới
            savedPlans.unshift(planRecord);
        }
    } else {
        // 🔥 THÊM PLAN MỚI
        savedPlans.unshift(planRecord);
        currentPlanId = planRecord.id; // ✅ GÁN ID CHO currentPlanId
    }
    
    // Giới hạn 20 plans
    if (savedPlans.length > 20) {
        savedPlans.length = 20;
    }
    
    localStorage.setItem('food_plans', JSON.stringify(savedPlans));
    
    // 🔥 CẬP NHẬT TÊN HIỂN THỊ
    window.currentPlanName = planRecord.name;
    
    alert('✅ Đã lưu kế hoạch thành công!');
    
    // ✅ CẬP NHẬT DANH SÁCH PLANS
    loadSavedPlans();
    
    // ✅ TẮT EDIT MODE SAU KHI LƯU
    if (isEditMode) {
        toggleEditMode();
    }
}

// ========== LOAD SAVED PLAN - RESTORE TỪARAY VỀ OBJECT ==========
function loadSavedPlans(planId) {
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    const section = document.getElementById('savedPlansSection');
    
    // ✅ LUÔN HIỂN THỊ SECTION
    section.style.display = 'block';
    
    displaySavedPlansList(savedPlans);
    
    // Nếu có planId, load plan đó
    if (planId) {
        const plan = savedPlans.find(p => p.id === planId);
        
        if (plan) {
            currentPlan = {};
            
            if (Array.isArray(plan.plan)) {
                const orderList = [];
                plan.plan.forEach(item => {
                    currentPlan[item.key] = JSON.parse(JSON.stringify(item.data));
                    orderList.push(item.key);
                });
                currentPlan._order = orderList;
            } else {
                Object.assign(currentPlan, plan.plan);
            }

            currentPlanId = planId;
            window.currentPlanName = plan.name;
            window.currentRadius = plan.radius || '10';  // 🔥 THÊM DÒNG NÀY
            isEditMode = false;
            suggestedFoodStreet = null; // Xóa gợi ý khi load plan cũ
            displayPlanVertical(currentPlan, false);

            setTimeout(() => drawRouteOnMap(currentPlan), 500);
            
            const savedPlansList = document.getElementById('savedPlansList');
            const savedPlansArrow = document.getElementById('savedPlansArrow');
            
            if (savedPlansList && savedPlansArrow) {
                savedPlansList.classList.remove('open');
                savedPlansArrow.style.transform = 'rotate(0deg)';
            }
            
            if (section) {
                section.style.display = 'block';
            }
        }
    }
}

function deleteSavedPlan(planId) {
    if (!confirm('Bạn có chắc muốn xóa kế hoạch này?')) return;
    
    let savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    savedPlans = savedPlans.filter(p => p.id !== planId);
    
    localStorage.setItem('food_plans', JSON.stringify(savedPlans));
    
    if (currentPlanId === planId) {
        currentPlanId = null;
        currentPlan = null;
        document.getElementById('planResult').innerHTML = '';
        isEditMode = false;
    }
    
    loadSavedPlans();
}

// ========== TẠO LỊCH TRÌNH TRỐNG MỚI ==========
function createNewEmptyPlan() {
    const now = new Date();
    const dateStr = now.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
    const planName = prompt('Đặt tên cho lịch trình:', `Lịch trình ngày ${dateStr}`);
    
    if (!planName) return; // User cancel
    
    const newPlanId = Date.now().toString();
    
    // ✅ TẠO LỊCH TRÌNH TRỐNG VỚI 1 SLOT MẶC ĐỊNH
    currentPlan = {
        'custom_1': {
            time: '07:00',
            title: 'Bữa sáng',
            icon: '🍳',
            place: null
        },
        _order: ['custom_1']
    };
    
    currentPlanId = newPlanId;
    window.currentPlanName = planName;
    isEditMode = true; // ✅ TỰ ĐỘNG BẬT EDIT MODE
    waitingForPlaceSelection = null;
    
    // ✅ HIỂN THỊ LỊCH TRÌNH MỚI
    displayPlanVertical(currentPlan, true);
    
    // ✅ ĐÓNG "LỊCH TRÌNH ĐÃ LƯU" SAU KHI TẠO
    const savedPlansList = document.getElementById('savedPlansList');
    const savedPlansArrow = document.getElementById('savedPlansArrow');
    if (savedPlansList && savedPlansArrow) {
        savedPlansList.classList.remove('open');
        savedPlansArrow.style.transform = 'rotate(0deg)';
    }
    
    // ✅ ĐÓNG FILTERS NẾU ĐANG MỞ
    const filtersWrapper = document.getElementById('filtersWrapper');
    if (filtersWrapper && !filtersWrapper.classList.contains('collapsed')) {
        toggleFilters();
    }
    
    // ✅ SCROLL LÊN TOP
    const panelContent = document.querySelector('.panel-content');
    if (panelContent) {
        panelContent.scrollTop = 0;
    }
}

// ========== EDIT MODE ==========
function toggleEditMode() {
    isEditMode = !isEditMode;
    const editBtn = document.getElementById('editPlanBtn');
    
    if (editBtn) {
        if (isEditMode) {
            editBtn.classList.add('active');
            editBtn.title = 'Thoát chỉnh sửa';
            clearRoutes(); // Xóa đường khi vào edit mode
        } else {
            editBtn.classList.remove('active');
            editBtn.title = 'Chỉnh sửa';
            selectedPlaceForReplacement = null;
            waitingForPlaceSelection = null;
        }
    }
    
    // 🔥 LƯU TITLE TỪ INPUT TRƯỚC KHI RENDER LẠI
    if (isEditMode && currentPlan) {
        const mealItems = document.querySelectorAll('.meal-item');
        mealItems.forEach(item => {
            const mealKey = item.dataset.mealKey;
            if (mealKey && currentPlan[mealKey]) {
                const titleInput = item.querySelector('input[onchange*="updateMealTitle"]');
                if (titleInput && titleInput.value) {
                    currentPlan[mealKey].title = titleInput.value;
                }
            }
        });
    }
    
    if (currentPlan) {
        displayPlanVertical(currentPlan, isEditMode);
    }
}

// ========== OPEN/CLOSE PLANNER ==========
document.getElementById('foodPlannerBtn').addEventListener('click', function() {
    if (isPlannerOpen) {
        closeFoodPlanner();
    } else {
        openFoodPlanner();
    }
});

function openFoodPlanner() {
    document.getElementById('foodPlannerPanel').classList.add('active');
    isPlannerOpen = true;
    loadSavedPlans();
    
    // ✅ TỰ ĐỘNG VẼ LẠI ĐƯỜNG ĐI NẾU CÓ LỊCH TRÌNH
    setTimeout(() => {
        if (currentPlan && !isEditMode) {
            const hasPlaces = Object.keys(currentPlan)
                .filter(k => k !== '_order')
                .some(k => currentPlan[k] && currentPlan[k].place);
            
            if (hasPlaces) {
                drawRouteOnMap(currentPlan);
            }
        }
    }, 300);
}

function closeFoodPlanner() {
    document.getElementById('foodPlannerPanel').classList.remove('active');
    isPlannerOpen = false;
    
    // ✅ Cleanup toàn bộ
    clearRoutes();
    stopAutoScroll();
    disableGlobalDragTracking();
    
    // ✅ Reset states
    draggedElement = null;
    window.draggedElement = null;
    lastTargetElement = null;
    lastDragY = 0;
}

// ========== GET SELECTED FLAVORS ==========
function getSelectedFlavors() {
    const selectedFlavors = [];
    const flavorInput = document.getElementById('flavor');
    
    if (flavorInput && flavorInput.value.trim()) {
        const flavors = flavorInput.value.trim().toLowerCase().split(',');
        flavors.forEach(flavor => {
            const normalized = flavor.trim();
            if (normalized) {
                selectedFlavors.push(normalized);
            }
        });
    }
    
    return selectedFlavors;
}

// ========== TÌM KHU ẨM THỰC GỢI Ý (18:00 - 02:00) ==========
async function findSuggestedFoodStreet() {
    try {
        let userLat, userLon;
        
        if (window.currentUserCoords) {
            userLat = window.currentUserCoords.lat;
            userLon = window.currentUserCoords.lon;
        } else {
            return null;
        }
        
        const radiusInput = document.getElementById('radius');
        const radius = radiusInput?.value || window.currentRadius || '10';
        
        
        const randomHour = Math.floor(Math.random() * 9) + 18; // 18-26 (26 = 2h sÃ¡ng)
        const actualHour = randomHour >= 24 ? randomHour - 24 : randomHour;
        const randomMinute = Math.floor(Math.random() * 60);
        const searchTime = `${actualHour.toString().padStart(2, '0')}:${randomMinute.toString().padStart(2, '0')}`;
        
        const randomSeed = Date.now();
        const url = `/api/food-plan?lat=${userLat}&lon=${userLon}&random=${randomSeed}&start_time=${searchTime}&end_time=${searchTime}&radius_km=${radius}&theme=food_street`;
        
        const response = await fetch(url);
        if (!response.ok) return null;
        
        const data = await response.json();
        if (data.error || !data) return null;
        
        
        for (const key in data) {
            if (key !== '_order' && data[key] && data[key].place) {
                return data[key].place;
            }
        }
        
        return null;
    } catch (error) {
        console.error('Lá»—i tÃ¬m khu áº©m thá»±c gá»£i Ã½:', error);
        return null;
    }
}

// ========== AUTO MODE: GENERATE PLAN ==========
async function generateAutoPlan() {
    const resultDiv = document.getElementById('planResult');
    
    resultDiv.innerHTML = `
        <div class="loading-planner">
            <div class="loading-spinner"></div>
            <p>Đang tạo kế hoạch...</p>
        </div>
    `;
    
    try {
        let userLat, userLon;
        
        if (window.currentUserCoords && window.currentUserCoords.lat && window.currentUserCoords.lon) {
            userLat = window.currentUserCoords.lat;
            userLon = window.currentUserCoords.lon;
        } else if (navigator.geolocation) {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject);
            });
            userLat = position.coords.latitude;
            userLon = position.coords.longitude;
            window.currentUserCoords = { lat: userLat, lon: userLon };
        } else {
            throw new Error('Trình duyệt không hỗ trợ GPS');
        }
        
        const startHour = document.getElementById('startHour').value.padStart(2, '0');
        const startMinute = document.getElementById('startMinute').value.padStart(2, '0');
        const startTime = `${startHour}:${startMinute}`;

        const endHour = document.getElementById('endHour').value.padStart(2, '0');
        const endMinute = document.getElementById('endMinute').value.padStart(2, '0');
        const endTime = `${endHour}:${endMinute}`;
        
        // 🔥 ĐỌC TỪ HIDDEN INPUT TRƯỚC, SAU ĐÓ MỚI DÙNG window.currentRadius
        const radiusInput = document.getElementById('radius');
        const radius = radiusInput?.value || window.currentRadius || '10';

        // 🔥 CẬP NHẬT LẠI window.currentRadius
        window.currentRadius = radius;

        console.log('🔍 Bán kính đang dùng:', radius + ' km');

        const selectedFlavors = getSelectedFlavors();
        const tastesParam = selectedFlavors.join(',');
        
        const randomSeed = Date.now();
        let url = `/api/food-plan?lat=${userLat}&lon=${userLon}&random=${randomSeed}&start_time=${startTime}&end_time=${endTime}&radius_km=${radius}`;
        
        if (selectedThemes.length > 0) {
            url += `&theme=${selectedThemes.join(',')}`;
        }
        
        if (tastesParam) {
            url += `&tastes=${tastesParam}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Không thể tạo kế hoạch');
        }
        
        const data = await response.json();

        // 🔥 LOG DEBUG - KIỂM TRA DATA TỪ API
        console.log('🔍 [API Response] Full data:', data);
        Object.keys(data).forEach(key => {
            if (key !== '_order' && data[key] && data[key].place) {
                console.log(`📍 [${key}] ${data[key].place.ten_quan}`);
                console.log(`   gio_mo_cua:`, data[key].place.gio_mo_cua);
            }
        });
        
        if (data.error) {
            resultDiv.innerHTML = `
                <div class="error-message">
                    <h3>😔 ${data.message || 'Không tìm thấy quán'}</h3>
                    <p>Hãy thử tăng bán kính tìm kiếm hoặc thay đổi bộ lọc</p>
                </div>
            `;
            return;
        }
        
        currentPlan = data;
        
        isEditMode = false;
        displayPlanVertical(currentPlan, false);
        // Tìm khu ẩm thực gợi ý (CHỈ KHI KHÔNG CHỌN THEME food_street)
        if (!selectedThemes.includes('food_street')) {
            suggestedFoodStreet = await findSuggestedFoodStreet();
            if (suggestedFoodStreet) {
                displayPlanVertical(currentPlan, false);
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        resultDiv.innerHTML = `
            <div class="error-message">
                <h3>⚠️ Không thể tạo kế hoạch</h3>
                <p>${error.message === 'User denied Geolocation' 
                    ? 'Vui lòng bật GPS và thử lại' 
                    : 'Đã có lỗi xảy ra. Vui lòng thử lại sau.'}</p>
            </div>
        `;
    }
}

// ========== TÍNH TỔNG KINH PHÍ ==========
function calculateTotalBudget(plan) {
    let total = 0;
    let unknownCount = 0;
    let hasOverPrice = false;
    
    Object.keys(plan).forEach(key => {
        if (key === '_order') return;
        
        const meal = plan[key];
        if (!meal || !meal.place || !meal.place.gia_trung_binh) {
            unknownCount++;
            return;
        }
        
        const priceStr = meal.place.gia_trung_binh.trim();
        
        // 🔥 XỬ LÝ "Trên X.XXX.XXX ₫"
        if (priceStr.includes('Trên')) {
            hasOverPrice = true;
            const match = priceStr.match(/[\d\.]+/);
            if (match) {
                const value = parseInt(match[0].replace(/\./g, ''));
                total += value;
            }
            return;
        }
        
        // 🔥 XỬ LÝ KHOẢNG GIÁ: "100-200 N ₫" hoặc "1-100.000 ₫"
        const parts = priceStr.split('-');
        if (parts.length === 2) {
            let maxPart = parts[1].trim();
            
            // 🔥 CHUẨN HÓA: Thay thế TẤT CẢ khoảng trắng (bao gồm \xa0) thành khoảng trắng thường
            maxPart = maxPart.replace(/\s+/g, ' ');
            
            // 🔥 KIỂM TRA CÓ CHỮ "N" (không phân biệt khoảng trắng)
            const hasN = /N\s*₫/i.test(maxPart) || /\s+N\s+/i.test(maxPart);
            
            // Xóa TẤT CẢ ký tự không phải số hoặc dấu chấm
            maxPart = maxPart.replace(/[^\d\.]/g, '');
            
            // Xóa dấu chấm phân cách hàng nghìn
            maxPart = maxPart.replace(/\./g, '');
            
            let max = parseInt(maxPart);
            
            // 🔥 NẾU CÓ CHỮ "N" → NHÂN 1000
            if (!isNaN(max) && max > 0) {
                if (hasN) {
                    max = max * 1000;
                }
                total += max;
            } else {
                unknownCount++;
            }
        } else {
            unknownCount++;
        }
    });
    
    return {
        total: total,
        unknown: unknownCount,
        hasOverPrice: hasOverPrice
    };
}

function formatMoney(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(1).replace('.0', '') + ' triệu ₫';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(0) + '.000 ₫';
    } else {
        return value + ' ₫';
    }
}

// ========== AUTO MODE: DISPLAY VERTICAL TIMELINE ==========
function displayPlanVertical(plan, editMode = false) {
    const resultDiv = document.getElementById('planResult');
    
    if (!plan || Object.keys(plan).length === 0) {
        resultDiv.innerHTML = `
            <div class="error-message">
                <h3>😔 Không tìm thấy quán</h3>
                <p>Không có quán nào phù hợp trong khu vực của bạn</p>
            </div>
        `;
        clearRoutes();
        return;
    }

    // 🔥 KIỂM TRA TRƯỜNG HỢP ĐÃ XÓA HẾT QUÁN TRONG EDIT MODE
    const allKeys = Object.keys(plan).filter(k => k !== '_order');
    if (allKeys.length === 0 && editMode) {
        resultDiv.innerHTML = `
            <div class="error-message">
                <h3>🗑️ Đã xóa hết lịch trình</h3>
                <p>Bạn đã xóa tất cả các quán trong lịch trình này</p>
                <button onclick="toggleEditMode(); generateAutoPlan();" 
                    style="margin-top: 15px; padding: 10px 20px; background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600;">
                    ✨ Tạo lại lịch trình
                </button>
            </div>
        `;
        clearRoutes();
        return;
    }

    // 🔥 TÍNH TỔNG KINH PHÍ
    const budget = calculateTotalBudget(plan);

    let html = `
    <div class="schedule-header">
        <h3 class="schedule-title">
            <span style="margin-right: 8px;">📅</span>
            <span ${editMode ? 'contenteditable="true" class="editable" onblur="updateAutoPlanName(this.textContent)"' : ''}><span>${window.currentPlanName || 'Lịch trình của bạn'}</span></span>
        </h3>
        <div class="action-buttons" id="actionButtons">
            <button class="action-btn edit ${editMode ? 'active' : ''}" id="editPlanBtn" onclick="toggleEditMode()" title="${editMode ? 'Thoát chỉnh sửa' : 'Chỉnh sửa'}">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                </svg>
                <span class="btn-label">${editMode ? 'Xong' : 'Sửa'}</span>
            </button>
            <button class="action-btn primary" onclick="savePlan()" title="Lưu kế hoạch">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
                </svg>
                <span class="btn-label">Lưu</span>
            </button>
            <button class="action-btn share" onclick="sharePlan()" title="Chia sẻ kế hoạch">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M15 8l4.39 4.39a1 1 0 010 1.42L15 18.2v-3.1c-4.38.04-7.43 1.4-9.88 4.3.94-4.67 3.78-8.36 9.88-8.4V8z"/>
                </svg>
                <span class="btn-label">Chia sẻ</span>
            </button>
        </div>
    </div>

    <!-- 📍 Bán Kính Tìm Kiếm -->
    <div style="
        background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
        border: 2px solid #FFB84D;
        border-radius: 16px;
        padding: 16px 20px;
        margin: 16px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(255, 184, 77, 0.2);
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 28px;">📍</span>
            <div>
                <div style="font-size: 13px; color: #8B6914; font-weight: 600; margin-bottom: 4px;">Bán kính tìm kiếm</div>
                <div style="font-size: 20px; font-weight: 700; color: #6B5410;">
                    ${window.currentRadius || '10'} km
                </div>
            </div>
        </div>
    </div>

    <!-- 💰 Tổng Kinh Phí -->
    <div style="
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border: 2px solid #4caf50;
        border-radius: 16px;
        padding: 16px 20px;
        margin: 16px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 28px;">💰</span>
            <div>
                <div style="font-size: 13px; color: #2e7d32; font-weight: 600; margin-bottom: 4px;">Tổng kinh phí dự kiến</div>
                <div style="font-size: 20px; font-weight: 700; color: #1b5e20;">
                        ${budget.hasOverPrice ? 'Trên ' : ''}${formatMoney(budget.total)}
                        ${budget.unknown > 0 ? `<span style="font-size: 13px; font-weight: 500; color: #666; margin-left: 8px;">(Không tính ${budget.unknown} quán)</span>` : ''}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="timeline-container"><div class="timeline-line"></div>
    `;
    
    const mealOrder = ['breakfast', 'morning_drink', 'lunch', 'afternoon_drink', 'dinner', 'dessert', 'meal', 'meal1', 'drink', 'meal2'];
    let hasPlaces = false;
    
    // 🔥 ƯU TIÊN THỨ TỰ ĐÃ KÉO THẢ (_order), CHỈ SORT KHI CHƯA CÓ _order
    let allMealKeys;

    if (plan._order && plan._order.length > 0) {
        // ✅ Nếu có _order (đã kéo thả) → GIỮ NGUYÊN thứ tự
        allMealKeys = plan._order.filter(k => plan[k] && plan[k].time);
    } else {
        // ✅ Nếu chưa có _order → Sắp xếp theo thời gian
        allMealKeys = Object.keys(plan)
            .filter(k => k !== '_order' && plan[k] && plan[k].time)
            .sort((a, b) => {
                const timeA = plan[a].time || '00:00';
                const timeB = plan[b].time || '00:00';
                return timeA.localeCompare(timeB);
            });
        
        // 🔥 LƯU vào _order để lần sau không bị sort lại
        plan._order = allMealKeys;
    }
    
    for (const key of allMealKeys) {
        const meal = plan[key];
        if (!meal) continue;
        
        const icon = meal.icon || mealIcons[key] || '🍽️';
        
        // Kiểm tra nếu là slot trống (chưa có place)
        if (!meal.place) {
            const isWaitingForSelection = waitingForPlaceSelection === key;
            
            html += `
                <div class="meal-item" draggable="${editMode}" data-meal-key="${key}">
                    <div class="time-marker">
                        ${editMode ? 
                            `<div style="display: inline-flex; gap: 5px; align-items: center; justify-content: center; background: white; padding: 6px 12px; border-radius: 25px; box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);">
                                <input type="number" min="0" max="23" value="${meal.time.split(':')[0]}" 
                                    class="time-input-hour" data-meal-key="${key}"
                                    style="width: 60px; padding: 8px 6px; border: 2px solid #FFE5D9; border-radius: 8px; font-size: 16px; text-align: center; font-weight: 700; background: white; line-height: 1;">
                                <span style="font-weight: bold; color: #FF6B35; font-size: 18px;">:</span>
                                <input type="number" min="0" max="59" value="${meal.time.split(':')[1]}" 
                                    class="time-input-minute" data-meal-key="${key}"
                                    style="width: 60px; padding: 8px 6px; border: 2px solid #FFE5D9; border-radius: 8px; font-size: 16px; text-align: center; font-weight: 700; background: white; line-height: 1;">
                            </div>` :
                            `<div class="time-badge">⏰ ${meal.time}</div>`
                        }
                    </div>
                    <div class="time-dot"></div>
                    <div class="meal-card-vertical empty-slot ${editMode ? 'edit-mode' : ''}">
                        <div class="meal-title-vertical">
                            <div class="meal-title-left">
                                ${editMode ? `
                                    <select onchange="updateMealIcon('${key}', this.value)" style="border: none; background: transparent; font-size: 22px; cursor: pointer; outline: none; padding: 0;" onclick="event.stopPropagation();">
                                        ${iconOptions.map(ico => `<option value="${ico}" ${ico === icon ? 'selected' : ''}>${ico}</option>`).join('')}
                                    </select>
                                ` : `<span style="font-size: 22px;">${icon}</span>`}
                                ${editMode 
                                    ? `<input type="text" value="${meal.title}" onchange="updateMealTitle('${key}', this.value)" 
                                        class="time-input-inline" onclick="event.stopPropagation();" placeholder="Nhập tên bữa ăn">`
                                    : `<span>${meal.title}</span>`
                                }
                            </div>
                            ${editMode ? `
                            <div class="meal-actions">
                                <button class="meal-action-btn select-meal ${isWaitingForSelection ? 'active' : ''}" 
                                        onclick="selectPlaceForMeal('${key}')" title="${isWaitingForSelection ? 'Đang chờ bạn chọn quán trên bản đồ...' : 'Nhấn để chọn quán ăn từ bản đồ'}">
                                    <span class="btn-icon">${isWaitingForSelection ? '⏳' : '✏️'}</span>
                                    <span class="btn-text">${isWaitingForSelection ? 'Đang chọn...' : 'Chọn quán'}</span>
                                </button>
                                <button class="meal-action-btn delete-meal" onclick="deleteMealSlot('${key}')" title="Xóa bữa ăn này">
                                    <span class="btn-icon">🗑️</span>
                                    <span class="btn-text">Xóa</span>
                                </button>
                            </div>
                            ` : ''}
                        </div>
                        <div class="empty-slot-content">
                            <div class="icon">🏪</div>
                            <div class="text">${isWaitingForSelection ? 'Đang chờ chọn quán...' : 'Chưa có quán'}</div>
                            ${!editMode ? '<div style="font-size: 12px; margin-top: 8px; color: #999;">Bật chế độ chỉnh sửa để thêm quán</div>' : ''}
                        </div>
                    </div>
                </div>
            `;
            continue;
        }
        
        hasPlaces = true;
        const place = meal.place;
        
        // ✅ CODE MỚI - TRUYỀN THÊM data_id VÀ ten_quan
        const cardClickEvent = `onclick="flyToPlace(${place.lat}, ${place.lon}, '${place.data_id}', '${place.ten_quan.replace(/'/g, "\\'")}')"`;
        const cardCursor = 'cursor: pointer;'; // ✅ LUÔN HIỆN CON TRỎ TAY
        
        const isWaitingForSelection = waitingForPlaceSelection === key;
        
        html += `
            <div class="meal-item" draggable="${editMode}" data-meal-key="${key}">
                <div class="time-marker">
                    ${editMode ? 
                        `<div style="display: inline-flex; gap: 5px; align-items: center; justify-content: center; background: white; padding: 6px 12px; border-radius: 25px; box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);">
                            <input type="number" min="0" max="23" value="${meal.time.split(':')[0]}" 
                                class="time-input-hour" data-meal-key="${key}"
                                style="width: 60px; padding: 8px 6px; border: 2px solid #FFE5D9; border-radius: 8px; font-size: 16px; text-align: center; font-weight: 700; background: white; line-height: 1;">
                            <span style="font-weight: bold; color: #FF6B35; font-size: 18px;">:</span>
                            <input type="number" min="0" max="59" value="${meal.time.split(':')[1]}" 
                                class="time-input-minute" data-meal-key="${key}"
                                style="width: 60px; padding: 8px 6px; border: 2px solid #FFE5D9; border-radius: 8px; font-size: 16px; text-align: center; font-weight: 700; background: white; line-height: 1;">
                        </div>` :
                        `<div class="time-badge">⏰ ${meal.time}</div>`
                    }
                </div>
                <div class="time-dot"></div>
                <div class="meal-card-vertical ${editMode ? 'edit-mode' : ''}" ${cardClickEvent} style="${cardCursor}">
                    <div class="meal-title-vertical">
                        <div class="meal-title-left">
                            ${editMode ? `
                                <select onchange="updateMealIcon('${key}', this.value)" style="border: none; background: transparent; font-size: 22px; cursor: pointer; outline: none; padding: 0;" onclick="event.stopPropagation();">
                                    ${iconOptions.map(ico => `<option value="${ico}" ${ico === icon ? 'selected' : ''}>${ico}</option>`).join('')}
                                </select>
                            ` : `<span style="font-size: 22px;">${icon}</span>`}
                            <div style="display: flex; flex-direction: column; gap: 2px;">
                                ${editMode ? 
                                    `<input type="text" value="${meal.title}" onchange="updateMealTitle('${key}', this.value)" 
                                        class="time-input-inline" onclick="event.stopPropagation();" placeholder="Nhập tên bữa ăn">`
                                    : `<span>${meal.title}</span>`
                                }
                                ${(() => {
                                    const gioMoCua = place.gio_mo_cua || '';
                                    let displayTime = '';
                                    
                                    if (!gioMoCua || gioMoCua.trim() === '') {
                                        displayTime = 'Không rõ thời gian';
                                    } else {
                                        const gioNormalized = gioMoCua.toLowerCase();
                                        
                                        if (gioNormalized.includes('always') || gioNormalized.includes('24') || 
                                            gioNormalized.includes('cả ngày') || gioNormalized.includes('mở cả ngày') ||
                                            gioNormalized.includes('ca ngay') || gioNormalized.includes('mo ca ngay')) {
                                            displayTime = 'Mở cả ngày';
                                        } else if (gioNormalized.includes('mở') || gioNormalized.includes('đóng') ||
                                                gioNormalized.includes('ong') || gioNormalized.includes('mo cua') || 
                                                gioNormalized.includes('dong cua') || gioNormalized.includes('mo') || 
                                                gioNormalized.includes('dong')) {
                                            displayTime = gioMoCua;
                                        } else {
                                            displayTime = 'Không rõ thời gian';
                                        }
                                    }
                                    
                                    return `<div style="font-size: 11px; color: #8B6914; font-weight: 500;">
                                        🕐 ${displayTime}
                                    </div>`;
                                })()}
                            </div>
                        </div>
                        ${editMode ? `
                        <div class="meal-actions">
                            <button class="meal-action-btn select-meal ${isWaitingForSelection ? 'active' : ''}" 
                                    onclick="selectPlaceForMeal('${key}')" title="${isWaitingForSelection ? 'Đang chờ bạn chọn quán khác trên bản đồ...' : 'Nhấn để đổi sang quán khác'}">
                                <span class="btn-icon">${isWaitingForSelection ? '⏳' : '✏️'}</span>
                                <span class="btn-text">${isWaitingForSelection ? 'Đang đổi...' : 'Đổi quán'}</span>
                            </button>
                            <button class="meal-action-btn delete-meal" onclick="deleteMealSlot('${key}')" title="Xóa bữa ăn này">
                                <span class="btn-icon">🗑️</span>
                                <span class="btn-text">Xóa</span>
                            </button>
                        </div>
                        ` : ''}
                    </div>
                    <div class="place-info-vertical">
                        <div class="place-name-vertical">${place.ten_quan}</div>
                        <div class="place-address-vertical">📍 ${place.dia_chi}</div>
                        <div class="place-meta-vertical">
                            <div class="meta-item-vertical">
                                <span>⭐</span>
                                <strong>${place.rating ? parseFloat(place.rating).toFixed(1) : 'N/A'}</strong>
                            </div>
                            ${place.gia_trung_binh && !['$', '$$', '$$$', '$$$$'].includes(place.gia_trung_binh.trim()) ? `
                                <div class="meta-item-vertical">
                                    <span>💰</span>
                                    <strong>${place.gia_trung_binh}</strong>
                                </div>
                            ` : ''}
                        </div>
                        ${place.khau_vi ? `
                            <div style="margin-top: 8px; padding: 6px 10px; background: #FFF5E6; border-left: 3px solid #FFB84D; border-radius: 6px; font-size: 12px; color: #8B6914;">
                                👅 Khẩu vị: ${place.khau_vi}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';

    // CARD GỢI Ý KHU ẨM THỰC (CHỈ KHI KHÔNG EDIT MODE VÀ KHÔNG CHỌN THEME food_street)
    const shouldShowSuggestion = !editMode && 
                                suggestedFoodStreet && 
                                !selectedThemes.includes('food_street');

    if (shouldShowSuggestion) {
        html += `
            <div style="margin-top: 40px; padding: 0 20px;">
                <div style="
                    background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
                    border: 3px dashed #FFB84D;
                    border-radius: 20px;
                    padding: 20px;
                    position: relative;
                    box-shadow: 0 6px 20px rgba(255, 184, 77, 0.25);
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onclick="flyToPlace(${suggestedFoodStreet.lat}, ${suggestedFoodStreet.lon}, '${suggestedFoodStreet.data_id}', '${suggestedFoodStreet.ten_quan.replace(/'/g, "\\'")}')"
                onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 28px rgba(255, 184, 77, 0.35)';"
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 20px rgba(255, 184, 77, 0.25)';">
                    
                    <!-- TAG Gợi ý -->
                    <div style="
                        position: absolute;
                        top: -12px;
                        left: 20px;
                        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
                        color: white;
                        padding: 6px 16px;
                        border-radius: 20px;
                        font-size: 13px;
                        font-weight: 700;
                        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    ">
                        <span style="font-size: 16px;">✨</span>
                        <span>Gợi ý cho bạn</span>
                    </div>
                    
                    <!-- HEADER -->
                    <div style="margin-top: 10px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">🪔</span>
                        <div>
                            <div style="font-size: 16px; font-weight: 700; color: #6B5410; margin-bottom: 4px;">
                                Khu ẩm thực đêm
                            </div>
                            ${(() => {
                                const gioMoCua = suggestedFoodStreet.gio_mo_cua || '';
                                let displayTime = '';
                                
                                if (!gioMoCua || gioMoCua.trim() === '') {
                                    displayTime = 'Không rõ thời gian';
                                } else {
                                    const gioNormalized = gioMoCua.toLowerCase();
                                    
                                    if (gioNormalized.includes('always') || gioNormalized.includes('24') || 
                                        gioNormalized.includes('cả ngày') || gioNormalized.includes('mở cả ngày') ||
                                        gioNormalized.includes('ca ngay') || gioNormalized.includes('mo ca ngay')) {
                                        displayTime = 'Mở cả ngày';
                                    } else if (gioNormalized.includes('mở') || gioNormalized.includes('đóng') ||
                                            gioNormalized.includes('ong') || gioNormalized.includes('mo cua') || 
                                            gioNormalized.includes('dong cua') || gioNormalized.includes('mo') || 
                                            gioNormalized.includes('dong')) {
                                        displayTime = gioMoCua;
                                    } else {
                                        displayTime = 'Không rõ thời gian';
                                    }
                                }
                                
                                return `<div style="font-size: 13px; color: #8B6914; font-weight: 500;">
                                    🕐 ${displayTime}
                                </div>`;
                            })()}
                        </div>
                    </div>
                    
                    <!-- NỘI DUNG -->
                    <div style="
                        background: white;
                        border-radius: 12px;
                        padding: 16px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                        border: 1px solid rgba(255, 184, 77, 0.2);
                    ">
                        <div style="font-weight: 700; color: #FF6B35; margin-bottom: 8px; font-size: 15px; display: flex; align-items: center; gap: 6px;">
                            <span>🍽️</span>
                            <span>${suggestedFoodStreet.ten_quan}</span>
                        </div>
                        <div style="color: #666; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                            📍 ${suggestedFoodStreet.dia_chi}
                        </div>
                        <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px;">
                            <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%); border-radius: 20px; color: #8B6914; font-weight: 600; border: 1px solid #FFD699;">
                                <span style="font-size: 16px;">⭐</span>
                                <strong>${suggestedFoodStreet.rating ? parseFloat(suggestedFoodStreet.rating).toFixed(1) : 'N/A'}</strong>
                            </div>
                            ${suggestedFoodStreet.gia_trung_binh && !['$', '$$', '$$$', '$$$$'].includes(suggestedFoodStreet.gia_trung_binh.trim()) ? `
                                <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%); border-radius: 20px; color: #8B6914; font-weight: 600; border: 1px solid #FFD699;">
                                    <span style="font-size: 16px;">💰</span>
                                    <strong>${suggestedFoodStreet.gia_trung_binh}</strong>
                                </div>
                            ` : ''}
                        </div>
                        ${suggestedFoodStreet.khau_vi ? `
                            <div style="margin-top: 12px; padding: 8px 12px; background: #FFF5E6; border-left: 3px solid #FFB84D; border-radius: 6px; font-size: 12px; color: #8B6914;">
                                👅 Khẩu vị: ${suggestedFoodStreet.khau_vi}
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- FOOTER -->
                    <div style="margin-top: 16px; text-align: center; font-size: 13px; color: #8B6914; font-weight: 600;">
                        👆 Nhấn để xem trên bản đồ
                    </div>
                </div>
            </div>
        `;
    }

    // 🔥 THÊM NÚT "+" Ở CUỐI TIMELINE (CHỈ KHI EDIT MODE)
    if (editMode) {
        html += `
            <div style="margin-top: 30px; padding: 20px; text-align: center; display: flex; justify-content: center; align-items: center; gap: 30px;">
                <!-- NÚT THÊM QUÁN MỚI -->
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <button onclick="addNewMealSlot()" style="
                        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                        color: white;
                        border: none;
                        width: 56px;
                        height: 56px;
                        border-radius: 50%;
                        cursor: pointer;
                        font-size: 28px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
                        transition: all 0.2s ease;
                    " onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 6px 16px rgba(76, 175, 80, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 12px rgba(76, 175, 80, 0.3)';" title="Thêm quán mới">
                        +
                    </button>
                    <div style="margin-top: 10px; font-size: 14px; color: #4caf50; font-weight: 600;">
                        Thêm quán mới
                    </div>
                </div>
                
                <!-- NÚT XÓA TẤT CẢ -->
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <button onclick="deleteAllMeals()" style="
                        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                        color: white;
                        border: none;
                        width: 56px;
                        height: 56px;
                        border-radius: 50%;
                        cursor: pointer;
                        font-size: 28px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
                        transition: all 0.2s ease;
                    " onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 6px 16px rgba(231, 76, 60, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 12px rgba(231, 76, 60, 0.3)';" title="Xóa tất cả quán">
                        🗑️
                    </button>
                    <div style="margin-top: 10px; font-size: 14px; color: #e74c3c; font-weight: 600;">
                        Xóa tất cả
                    </div>
                </div>
            </div>
        `;
    }

    if (!hasPlaces && !editMode) {
        resultDiv.innerHTML = `
            <div class="error-message">
                <h3>😔 Không tìm thấy quán</h3>
                <p>Không có quán nào phù hợp trong khu vực của bạn</p>
            </div>
        `;
        clearRoutes();
        return;
    }

    resultDiv.innerHTML = html;

    const actionBtns = document.getElementById('actionButtons');
    if (actionBtns) {
        actionBtns.classList.add('visible');
    }

    if (editMode) {
        setupDragAndDrop();
        setTimeout(() => setupEditModeTimeInputs(), 100);
    }
    
    // 🔥 VẼ ĐƯỜNG ĐI KHI HIỂN THỊ KẾ HOẠCH
    if (!editMode && hasPlaces) {
        setTimeout(() => drawRouteOnMap(plan), 500);
    } else {
        clearRoutes();
    }

    // 🔥 KIỂM TRA text có dài hơn khung không
    setTimeout(() => {
        const titleContainer = document.querySelector('.schedule-title > span:last-child');
        if (titleContainer && !titleContainer.hasAttribute('contenteditable')) {
            const textSpan = titleContainer.querySelector('span');
            if (textSpan && textSpan.scrollWidth > titleContainer.clientWidth) {
                titleContainer.classList.add('overflow'); // 🔥 Thêm class để bật animation
            } else {
                titleContainer.classList.remove('overflow');
            }
        }
    }, 100);
}

// ========== ADD NEW MEAL SLOT ==========
function addNewMealSlot() {
    if (!currentPlan) {
        currentPlan = {};
    }
    
    const newKey = 'custom_' + Date.now();
    const lastMealTime = getLastMealTime();
    const newTime = addMinutesToTime(lastMealTime, 60);
    
    currentPlan[newKey] = {
        time: newTime,
        title: 'Bữa mới',
        icon: '🍽️',
        place: null
    };

    if (!currentPlan._order) {
        currentPlan._order = [];
    }
    currentPlan._order.push(newKey);
    
    waitingForPlaceSelection = newKey;
    displayPlanVertical(currentPlan, isEditMode);
    
    // Scroll to bottom
    setTimeout(() => {
        const timeline = document.querySelector('.timeline-container');
        if (timeline) {
            timeline.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, 100);
}

function getLastMealTime() {
    let latestTime = '07:00';
    for (const key in currentPlan) {
        if (currentPlan[key] && currentPlan[key].time) {
            if (currentPlan[key].time > latestTime) {
                latestTime = currentPlan[key].time;
            }
        }
    }
    return latestTime;
}

function addMinutesToTime(timeStr, minutes) {
    const [hours, mins] = timeStr.split(':').map(Number);
    const totalMins = hours * 60 + mins + minutes;
    const newHours = Math.floor(totalMins / 60) % 24;
    const newMins = totalMins % 60;
    return `${String(newHours).padStart(2, '0')}:${String(newMins).padStart(2, '0')}`;
}

// ========== KIỂM TRA 2 ĐOẠN ĐƯỜNG CÓ TRÙNG KHÔNG ==========
function checkRouteOverlap(coords1, coords2, threshold = 0.0001) {
    // Giảm threshold để chính xác hơn
    let overlapCount = 0;
    const sampleStep = Math.max(1, Math.floor(coords1.length / 20)); // Lấy mẫu để tăng tốc
    
    for (let i = 0; i < coords1.length; i += sampleStep) {
        const point1 = coords1[i];
        
        for (let j = 0; j < coords2.length; j += sampleStep) {
            const point2 = coords2[j];
            
            const distance = Math.sqrt(
                Math.pow(point1[0] - point2[0], 2) + 
                Math.pow(point1[1] - point2[1], 2)
            );
            
            if (distance < threshold) {
                overlapCount++;
                break;
            }
        }
    }
    
    // Chỉ cần 15% điểm trùng là đủ
    const minOverlapPoints = Math.ceil(coords1.length / sampleStep * 0.15);
    return overlapCount >= minOverlapPoints;
}

// ========== DRAW ROUTE ON MAP ==========
let routeLayers = [];
let currentRouteAbortController = null;

function clearRoutes() {
    // 🔥 HỦY TẤT CẢ REQUESTS ĐANG CHẠY
    if (currentRouteAbortController) {
        currentRouteAbortController.abort();
        currentRouteAbortController = null;
        console.log('⚠️ Đã hủy tất cả requests vẽ đường cũ');
    }

    if (typeof map !== 'undefined' && routeLayers.length > 0) {
        routeLayers.forEach(layer => {
            map.removeLayer(layer);
        });
        routeLayers = [];
    }
}

function getRouteColor(index, total) {
    const colors = [
        '#FF6B35', // Cam
        '#FFA500', // Cam sáng
        '#32CD32', // Xanh lá
        '#00CED1', // Xanh da trời
        '#1E90FF', // Xanh dương
        '#FF1493', // Hồng đậm
        '#9370DB'  // Tím
    ];
    
    if (total <= 1) return colors[0];
    
    const colorIndex = Math.min(
        Math.floor((index / (total - 1)) * (colors.length - 1)),
        colors.length - 1
    );
    
    return colors[colorIndex];
}

// ========== HÀM DỊCH CHUYỂN POLYLINE THEO MÉT (CỐ ĐỊNH) ==========
function offsetPolylineByMeters(coords, offsetMeters) {
    const offsetCoords = [];
    
    for (let i = 0; i < coords.length; i++) {
        const lat = coords[i][0];
        const lon = coords[i][1];
        
        // Tính vector hướng đi (tangent)
        let tangentLat, tangentLon;
        
        if (i === 0) {
            tangentLat = coords[i + 1][0] - lat;
            tangentLon = coords[i + 1][1] - lon;
        } else if (i === coords.length - 1) {
            tangentLat = lat - coords[i - 1][0];
            tangentLon = lon - coords[i - 1][1];
        } else {
            tangentLat = coords[i + 1][0] - coords[i - 1][0];
            tangentLon = coords[i + 1][1] - coords[i - 1][1];
        }
        
        // Chuẩn hóa vector hướng đi
        const tangentLength = Math.sqrt(tangentLat * tangentLat + tangentLon * tangentLon);
        if (tangentLength > 0) {
            tangentLat /= tangentLength;
            tangentLon /= tangentLength;
        }
        
        // 🔥 Vector vuông góc BÊN PHẢI của hướng đi (xoay 90° theo chiều kim đồng hồ)
        const perpLat = tangentLon;  // Swap và đổi dấu để xoay đúng
        const perpLon = -tangentLat;
        
        // 🔥 TÍNH OFFSET BẰNG MÉT (không phụ thuộc zoom)
        const metersPerDegreeLat = 111320;
        const metersPerDegreeLon = 111320 * Math.cos(lat * Math.PI / 180);
        
        const offsetLat = (offsetMeters / metersPerDegreeLat) * perpLat;
        const offsetLon = (offsetMeters / metersPerDegreeLon) * perpLon;
        
        offsetCoords.push([lat + offsetLat, lon + offsetLon]);
    }
    
    return offsetCoords;
}

function drawRouteOnMap(plan) {
    if (typeof map === 'undefined' || typeof L === 'undefined') {
        console.log('Map chưa sẵn sàng');
        return;
    }
    
    // 🔥 HỦY REQUESTS CŨ VÀ TẠO MỚI
    clearRoutes(); // Xóa routes cũ + hủy requests cũ
    currentRouteAbortController = new AbortController();
    const signal = currentRouteAbortController.signal;
    
    const drawnSegments = [];
    const waypoints = [];
    
    // Thêm vị trí user
    if (window.currentUserCoords) {
        waypoints.push({
            lat: window.currentUserCoords.lat,
            lon: window.currentUserCoords.lon,
            name: 'Vị trí của bạn',
            isUser: true
        });
    }
    
    // Lấy tất cả meal keys và sắp xếp theo thời gian
    const allMealKeys = Object.keys(plan)
        .filter(k => k !== '_order' && plan[k] && plan[k].time && plan[k].place)
        .sort((a, b) => {
            const timeA = plan[a].time || '00:00';
            const timeB = plan[b].time || '00:00';
            return timeA.localeCompare(timeB);
        });
    
    // Thêm các quán theo thứ tự
    allMealKeys.forEach(key => {
        const meal = plan[key];
        if (meal && meal.place) {
            waypoints.push({
                lat: meal.place.lat,
                lon: meal.place.lon,
                name: meal.place.ten_quan,
                time: meal.time,
                isUser: false
            });
        }
    });
    
    if (waypoints.length < 2) {
        console.log('Không đủ điểm để vẽ đường');
        return;
    }
    
    const totalRoutes = waypoints.length - 1;
    
    // 🔥 PATTERN VÀ WEIGHT ĐỒNG NHẤT CHO TẤT CẢ CÁC ĐƯỜNG
    const routeWeight = 6;
    const routeDash = null; // Đường liền
    
    async function drawSingleRoute(startPoint, endPoint, index) {
        try {
            const url = `https://router.project-osrm.org/route/v1/driving/${startPoint.lon},${startPoint.lat};${endPoint.lon},${endPoint.lat}?overview=full&geometries=geojson`;
            
            // 🔥 THÊM: Truyền signal vào fetch
            const response = await fetch(url, { signal });

            const data = await response.json();
            
            if (data.code === 'Ok' && data.routes && data.routes[0]) {
                const route = data.routes[0];
                const coords = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
                
                const color = getRouteColor(index, totalRoutes);
                
                // 🔥 KIỂM TRA TRÙNG VÀ TÍNH OFFSET (pixels nhỏ)
                let offsetPixels = 0;
                
                for (let i = 0; i < drawnSegments.length; i++) {
                    if (checkRouteOverlap(coords, drawnSegments[i].coords)) {
                        const overlapCount = drawnSegments.filter(seg => 
                            checkRouteOverlap(coords, seg.coords)
                        ).length;
                        
                        // 🔥 Offset 3 pixels mỗi đường (luân phiên trái/phải)
                        offsetPixels = (overlapCount % 2 === 0) ? 8 : -8;
                        console.log(`⚠️ Đường ${index} trùng ${overlapCount} đường, offset = ${offsetPixels}px`);
                        break;
                    }
                }
                
                drawnSegments.push({ coords: coords, index: index });
                
                // 🔥 Vẽ VIỀN TRẮNG
                const outlinePolyline = L.polyline(coords, {
                    color: '#FFFFFF',
                    weight: routeWeight + 3,
                    opacity: 0.9,
                    smoothFactor: 1
                }).addTo(map);
                
                routeLayers.push(outlinePolyline);
                
                // 🔥 VẼ ĐƯỜNG MÀU CHÍNH
                const mainPolyline = L.polyline(coords, {
                    color: color,
                    weight: routeWeight,
                    opacity: 1,
                    smoothFactor: 1,
                    dashArray: null
                }).addTo(map);
                
                // ✅ ÁP DỤNG OFFSET SAU KHI ADD VÀO MAP (cho cả 2 layer)
                if (offsetPixels !== 0) {
                    if (typeof outlinePolyline.setOffset === 'function') {
                        outlinePolyline.setOffset(offsetPixels);
                    }
                    if (typeof mainPolyline.setOffset === 'function') {
                        mainPolyline.setOffset(offsetPixels);
                    }
                }
                
                const tooltipText = index === 0 
                    ? `🚗 Khởi hành → ${endPoint.name}`
                    : `${index}. ${startPoint.name} → ${endPoint.name}`;
                
                mainPolyline.bindTooltip(tooltipText, {
                    permanent: false,
                    direction: 'center',
                    className: 'route-tooltip'
                });
                
                routeLayers.push(mainPolyline);
                
                // ĐÁNH SỐ QUÁN
                if (!startPoint.isUser) {
                    const numberMarker = L.marker([startPoint.lat, startPoint.lon], {
                        icon: L.divIcon({
                            className: 'route-number-marker',
                            html: `<div style="
                                background: ${color};
                                color: white;
                                width: 40px;
                                height: 40px;
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-weight: bold;
                                font-size: 18px;
                                border: 4px solid white;
                                box-shadow: 0 3px 10px rgba(0,0,0,0.4);
                                z-index: 1000;
                            ">${index}</div>`,
                            iconSize: [40, 40],
                            iconAnchor: [20, 20]
                        }),
                        zIndexOffset: 1000
                    }).addTo(map);
                    
                    routeLayers.push(numberMarker);
                }
                
                // ĐÁNH SỐ QUÁN CUỐI
                if (index === totalRoutes - 1 && !endPoint.isUser) {
                    const lastColor = getRouteColor(totalRoutes - 1, totalRoutes);
                    const lastNumberMarker = L.marker([endPoint.lat, endPoint.lon], {
                        icon: L.divIcon({
                            className: 'route-number-marker',
                            html: `<div style="
                                background: ${lastColor};
                                color: white;
                                width: 40px;
                                height: 40px;
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-weight: bold;
                                font-size: 18px;
                                border: 4px solid white;
                                box-shadow: 0 3px 10px rgba(0,0,0,0.4);
                                z-index: 1000;
                            ">${totalRoutes}</div>`,
                            iconSize: [40, 40],
                            iconAnchor: [20, 20]
                        }),
                        zIndexOffset: 1000
                    }).addTo(map);
                    
                    routeLayers.push(lastNumberMarker);
                }
                
            } else {
                console.log('Không tìm thấy route, dùng đường thẳng');
                const color = getRouteColor(index, totalRoutes);
                
                const outlineLine = L.polyline(
                    [[startPoint.lat, startPoint.lon], [endPoint.lat, endPoint.lon]],
                    { color: '#FFFFFF', weight: routeWeight + 3, opacity: 0.9 }
                ).addTo(map);
                routeLayers.push(outlineLine);

                const mainStraightLine = L.polyline(
                    [[startPoint.lat, startPoint.lon], [endPoint.lat, endPoint.lon]],
                    { color: color, weight: routeWeight, opacity: 1 }
                ).addTo(map);
                routeLayers.push(mainStraightLine);
            }
            
        } catch (error) {
            // 🔥 BỎ QUA NẾU REQUEST BỊ HỦY
            if (error.name === 'AbortError') {
                console.log(`⚠️ Request vẽ đường ${index} đã bị hủy`);
                return;
            }
        
            console.error('Lỗi vẽ route:', error);
            const color = getRouteColor(index, totalRoutes);
            
            const outlineLine = L.polyline(
                [[startPoint.lat, startPoint.lon], [endPoint.lat, endPoint.lon]],
                { color: '#FFFFFF', weight: routeWeight + 3, opacity: 0.9 }
            ).addTo(map);
            routeLayers.push(outlineLine);

            const mainStraightLine = L.polyline(
                [[startPoint.lat, startPoint.lon], [endPoint.lat, endPoint.lon]],
                { color: color, weight: routeWeight, opacity: 1 }
            ).addTo(map);
            routeLayers.push(mainStraightLine);
        }
    }
    
    // Vẽ từng đoạn route
    (async function drawAllRoutes() {
        try {
            for (let i = 0; i < waypoints.length - 1; i++) {
                // 🔥 KIỂM TRA NẾU ĐÃ BỊ HỦY THÌ DỪNG NGAY
                if (signal.aborted) {
                    console.log('⚠️ Đã dừng vẽ tất cả routes do bị hủy');
                    return;
                }
                
                await drawSingleRoute(waypoints[i], waypoints[i + 1], i);
            }
            
            // 🔥 CHỈ FIT BOUNDS NẾU CHƯA BỊ HỦY
            if (!signal.aborted) {
                const bounds = L.latLngBounds(waypoints.map(w => [w.lat, w.lon]));
                map.fitBounds(bounds, { padding: [50, 50] });
                
                console.log(`✅ Đã vẽ ${waypoints.length - 1} đoạn đường`);
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Lỗi trong drawAllRoutes:', error);
            }
        }
    })();
}

// ========== DELETE MEAL SLOT ==========
function deleteMealSlot(mealKey) {
    if (!currentPlan) return;
    
    if (confirm('Bạn có chắc muốn xóa bữa ăn này?')) {
        delete currentPlan[mealKey];
        
        // Reset waiting state nếu đang chờ chọn quán cho slot này
        if (waitingForPlaceSelection === mealKey) {
            waitingForPlaceSelection = null;
        }
        
        displayPlanVertical(currentPlan, isEditMode);
    }
}

// ========== SELECT PLACE FOR MEAL ==========
function selectPlaceForMeal(mealKey) {
    if (waitingForPlaceSelection === mealKey) {
        waitingForPlaceSelection = null;
        selectedPlaceForReplacement = null;
    } else {
        waitingForPlaceSelection = mealKey;
    }
    displayPlanVertical(currentPlan, isEditMode);

    // ✅ THÊM LOG ĐỂ DEBUG
    console.log('🔍 Kiểm tra refreshCurrentSidebar:', typeof window.refreshCurrentSidebar);
    
    if (typeof window.refreshCurrentSidebar === 'function') {
        setTimeout(() => {
            console.log('🔄 Gọi refreshCurrentSidebar');
            window.refreshCurrentSidebar();
        }, 100);
    } else {
        console.error('❌ refreshCurrentSidebar không tồn tại!');
    }
}

// ========== REPLACE PLACE IN MEAL ==========
function replacePlaceInMeal(newPlace) {
    // 🔥 KIỂM TRA ĐẦY ĐỦ
    if (!waitingForPlaceSelection) {
        console.error("❌ Không có slot nào đang chờ chọn quán");
        return false;
    }
    
    if (!currentPlan) {
        console.error("❌ currentPlan không tồn tại");
        return false;
    }
    
    const mealKey = waitingForPlaceSelection;
    
    // 🔥 KIỂM TRA MEAL KEY CÓ TỒN TẠI KHÔNG
    if (!currentPlan[mealKey]) {
        console.error("❌ Meal key không tồn tại trong plan:", mealKey);
        return false;
    }
    
    // ✅ Tính khoảng cách từ vị trí trước đó
    let prevLat, prevLon;
    if (window.currentUserCoords) {
        prevLat = window.currentUserCoords.lat;
        prevLon = window.currentUserCoords.lon;
    }
    
    // Tìm quán trước đó (nếu có)
    const allKeys = Object.keys(currentPlan)
        .filter(k => k !== '_order')
        .sort((a, b) => {
            const timeA = currentPlan[a]?.time || '00:00';
            const timeB = currentPlan[b]?.time || '00:00';
            return timeA.localeCompare(timeB);
        });
    
    const currentIndex = allKeys.indexOf(mealKey);
    
    for (let i = currentIndex - 1; i >= 0; i--) {
        const prevMeal = currentPlan[allKeys[i]];
        if (prevMeal && prevMeal.place) {
            prevLat = prevMeal.place.lat;
            prevLon = prevMeal.place.lon;
            break;
        }
    }
    
    const distance = calculateDistanceJS(prevLat, prevLon, newPlace.lat, newPlace.lon);
    const travelTime = Math.round((distance / 25) * 60);
    
    const mealTime = currentPlan[mealKey].time;
    const arriveTime = new Date(`2000-01-01 ${mealTime}`);
    const suggestLeave = new Date(arriveTime.getTime() - travelTime * 60000);
    const suggestLeaveStr = suggestLeave.toTimeString().substring(0, 5);
    
    // ✅ CẬP NHẬT QUÁN
    currentPlan[mealKey].place = {
        ten_quan: newPlace.ten_quan,
        dia_chi: newPlace.dia_chi,
        rating: parseFloat(newPlace.rating) || 0,
        lat: newPlace.lat,
        lon: newPlace.lon,
        distance: Math.round(distance * 100) / 100,
        travel_time: travelTime,
        suggest_leave: suggestLeaveStr,
        data_id: newPlace.data_id,
        hinh_anh: newPlace.hinh_anh || '',
        gia_trung_binh: newPlace.gia_trung_binh || '',
        khau_vi: newPlace.khau_vi || '',
        gio_mo_cua: newPlace.gio_mo_cua || ''
    };
    
    console.log("✅ Đã cập nhật quán cho mealKey:", mealKey, currentPlan[mealKey]);
    
    // ✅ RESET waiting state
    waitingForPlaceSelection = null;
    
    // ✅ RENDER LẠI NGAY LẬP TỨC
    displayPlanVertical(currentPlan, isEditMode);
    
    // ✅ SCROLL ĐẾN QUÁN VỪA THÊM
    setTimeout(() => {
        const addedItem = document.querySelector(`[data-meal-key="${mealKey}"]`);
        if (addedItem) {
            addedItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // ✅ HIGHLIGHT CARD VỪA THÊM
            const card = addedItem.querySelector('.meal-card-vertical');
            if (card) {
                card.style.border = '3px solid #4caf50';
                card.style.boxShadow = '0 0 20px rgba(76, 175, 80, 0.5)';
                
                setTimeout(() => {
                    card.style.border = '';
                    card.style.boxShadow = '';
                }, 2000);
            }
        }
    }, 100);
    
    return true; // 🔥 RETURN TRUE KHI THÀNH CÔNG
}

function calculateDistanceJS(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// ========== DRAG AND DROP ==========
function setupDragAndDrop() {
    const mealItems = document.querySelectorAll('.meal-item[draggable="true"]');
    
    mealItems.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
        item.addEventListener('dragover', handleDragOverItem);  // 🔥 ĐỔI TỪ dragenter
    });
    
    const container = document.querySelector('.timeline-container');
    if (container) {
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('drop', handleDrop);  // 🔥 THÊM DROP
    }
}

function handleDragStart(e) {
    draggedElement = this;
    window.draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
    
    lastTargetElement = null;
    enableGlobalDragTracking(); // ✅ Bật tracking
    startAutoScroll();
}

function handleDragEnd(e) {
    if (draggedElement) {
        draggedElement.classList.remove('dragging');
    }
    
    document.querySelectorAll('.meal-card-vertical.drop-target').forEach(card => {
        card.classList.remove('drop-target');
    });
    
    draggedElement = null;
    window.draggedElement = null;
    lastDragY = 0;
    lastTargetElement = null;
    
    stopAutoScroll();
    disableGlobalDragTracking(); // ✅ Tắt tracking
}

// ========== DRAG OVER ITEM - HIGHLIGHT VỊ TRÍ MUỐN ĐỔI ==========
function handleDragOverItem(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    
    if (!draggedElement || draggedElement === this) return;
    
    e.dataTransfer.dropEffect = 'move';
    
    // 🔥 XÓA highlight cũ
    document.querySelectorAll('.meal-card-vertical.drop-target').forEach(card => {
        card.classList.remove('drop-target');
    });
    
    // 🔥 HIGHLIGHT card đích
    const targetCard = this.querySelector('.meal-card-vertical');
    if (targetCard) {
        targetCard.classList.add('drop-target');
    }
    
    lastTargetElement = this;
    lastDragY = e.clientY;
    return false;
}

// ========== DRAG ENTER - ĐỘI VỊ TRÍ NGAY LẬP TỨC KHI CHẠM ==========
function handleDragEnter(e) {
    if (!draggedElement || draggedElement === this) return;
    
    const draggedKey = draggedElement.dataset.mealKey;
    const targetKey = this.dataset.mealKey;
    
    // 🔥 CHỈ ĐỔI 1 LẦN - TRÁNH ĐỔI LẶP LẠI
    if (lastTargetElement !== this) {
        lastTargetElement = this;
        
        // ✅ ĐỔI VỊ TRÍ TRONG DOM
        if (draggedElement.parentNode === this.parentNode) {
            const temp = draggedElement.innerHTML;
            draggedElement.innerHTML = this.innerHTML;
            this.innerHTML = temp;
            
            // ✅ ĐỔI ATTRIBUTE
            const tempKey = draggedElement.dataset.mealKey;
            draggedElement.dataset.mealKey = this.dataset.mealKey;
            this.dataset.mealKey = tempKey;
        }
        
        // ✅ ĐỔI DỮ LIỆU TRONG currentPlan
        if (currentPlan && draggedKey && targetKey) {
            const temp = currentPlan[draggedKey];
            currentPlan[draggedKey] = currentPlan[targetKey];
            currentPlan[targetKey] = temp;
        }
    }
}

// ✨ AUTO-SCROLL TOÀN BỘ PANEL - CỰC NHANH VÀ MƯỢT
function startAutoScroll() {
    if (autoScrollInterval) return;
    
    let frameCount = 0;
    
    autoScrollInterval = setInterval(() => {
        if (!draggedElement) {
            stopAutoScroll();
            return;
        }
        
        // ✅ Giảm tần suất xuống 30fps thay vì 60fps
        frameCount++;
        if (frameCount % 2 !== 0) return;
        
        const container = document.querySelector('.panel-content');
        if (!container) return;
        
        const rect = container.getBoundingClientRect();
        
        // 🔥 DÙNG lastDragY CẬP NHẬT LIÊN TỤC
        if (lastDragY === 0) return;
        
        // 🔥 VÙNG KÍCH HOẠT RỘNG HƠN - 200px thay vì 150px
        const topEdge = rect.top + 200;      // Vùng trên
        const bottomEdge = rect.bottom - 200; // Vùng dưới
        
        let scrollSpeed = 0;
        
       // CUỘN LÊNNN
        if (lastDragY < topEdge) {
            const distance = topEdge - lastDragY;
            const ratio = Math.min(1, distance / 200);
            scrollSpeed = -(15 + ratio * 50);
            container.scrollTop += scrollSpeed;
            container.classList.add('scrolling-up'); // 🔥 THÊM
            container.classList.remove('scrolling-down');
        }
        // CUỘN XUỐNG
        else if (lastDragY > bottomEdge) {
            const distance = lastDragY - bottomEdge;
            const ratio = Math.min(1, distance / 200);
            scrollSpeed = (15 + ratio * 50);
            container.scrollTop += scrollSpeed;
            container.classList.add('scrolling-down'); // 🔥 THÊM
            container.classList.remove('scrolling-up');
        } else {
            // 🔥 XÓA CLASS KHI KHÔNG SCROLL
            container.classList.remove('scrolling-up', 'scrolling-down');
        }
        
    }, 16); // 60fps - mượt
}

function stopAutoScroll() {
    if (autoScrollInterval) {
        clearInterval(autoScrollInterval);
        autoScrollInterval = null;
    }

    // ✅ Cleanup visual indicators
    const container = document.querySelector('.panel-content');
    if (container) {
        container.classList.remove('scrolling-up', 'scrolling-down');
    }
}

// ✨ THEO DÕI CHUỘT TRÊN TOÀN BỘ DOCUMENT
let globalDragListener = null;

function enableGlobalDragTracking() {
    if (globalDragListener) return;
    
    globalDragListener = (e) => {
        if (draggedElement) {
            lastDragY = e.clientY;
        }
    };
    
    document.addEventListener('dragover', globalDragListener, { passive: true });
}

function disableGlobalDragTracking() {
    if (globalDragListener) {
        document.removeEventListener('dragover', globalDragListener);
        globalDragListener = null;
    }
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    
    // 🔥 CẬP NHẬT LiÊN TỤC VỊ TRÍ Y TOÀN CẦU
    lastDragY = e.clientY;
    
    if (!draggedElement) return;
    
    e.dataTransfer.dropEffect = 'move';
    
    // Tìm phần tử nằm sau vị trí hiện tại
    const afterElement = getDragAfterElement(
        document.querySelector('.timeline-container'),
        e.clientY
    );
    
    if (afterElement == null) {
        document.querySelector('.timeline-container').appendChild(draggedElement);
    } else {
        document.querySelector('.timeline-container').insertBefore(draggedElement, afterElement);
    }
    
    return false;
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    if (!draggedElement || !lastTargetElement) return;
    
    if (draggedElement === lastTargetElement) return;
    
    const draggedKey = draggedElement.dataset.mealKey;
    const targetKey = lastTargetElement.dataset.mealKey;
    
    // ✅ Cập nhật dữ liệu TRƯỚC khi đổi
    const draggedTitleInput = draggedElement.querySelector('.meal-title-input, input[onchange*="updateMealTitle"]');
    const draggedHourInput = draggedElement.querySelector('.time-input-hour[data-meal-key="' + draggedKey + '"]');
    const draggedMinuteInput = draggedElement.querySelector('.time-input-minute[data-meal-key="' + draggedKey + '"]');
    
    if (draggedTitleInput && draggedKey && currentPlan[draggedKey]) {
        currentPlan[draggedKey].title = draggedTitleInput.value;
    }
    if (draggedHourInput && draggedMinuteInput && draggedKey && currentPlan[draggedKey]) {
        const hour = draggedHourInput.value.padStart(2, '0');
        const minute = draggedMinuteInput.value.padStart(2, '0');
        currentPlan[draggedKey].time = `${hour}:${minute}`;
    }
    
    const targetTitleInput = lastTargetElement.querySelector('.meal-title-input, input[onchange*="updateMealTitle"]');
    const targetHourInput = lastTargetElement.querySelector('.time-input-hour[data-meal-key="' + targetKey + '"]');
    const targetMinuteInput = lastTargetElement.querySelector('.time-input-minute[data-meal-key="' + targetKey + '"]');
    
    if (targetTitleInput && targetKey && currentPlan[targetKey]) {
        currentPlan[targetKey].title = targetTitleInput.value;
    }
    if (targetHourInput && targetMinuteInput && targetKey && currentPlan[targetKey]) {
        const hour = targetHourInput.value.padStart(2, '0');
        const minute = targetMinuteInput.value.padStart(2, '0');
        currentPlan[targetKey].time = `${hour}:${minute}`;
    }
    
    // ✅ SWAP dữ liệu
    if (currentPlan && draggedKey && targetKey) {
        const temp = currentPlan[draggedKey];
        currentPlan[draggedKey] = currentPlan[targetKey];
        currentPlan[targetKey] = temp;
    }
    
    // 🔥 LƯU VỊ TRÍ CŨ để biết quán nào bị di chuyển
    const allMealItems = document.querySelectorAll('.meal-item[data-meal-key]');
    const oldOrder = Array.from(allMealItems).map(item => item.dataset.mealKey);
    const draggedOldIndex = oldOrder.indexOf(draggedKey);
    const targetOldIndex = oldOrder.indexOf(targetKey);
    
    // Cập nhật thứ tự mới
    const newOrder = [...oldOrder];
    [newOrder[draggedOldIndex], newOrder[targetOldIndex]] = [newOrder[targetOldIndex], newOrder[draggedOldIndex]];
    
    if (!currentPlan._order) {
        currentPlan._order = [];
    }
    currentPlan._order = newOrder;
    
    // ✅ RENDER lại
    displayPlanVertical(currentPlan, isEditMode);
    
    // 🔥 THÊM HIỆU ỨNG CHO CẢ 2 QUÁN BỊ HOÁN ĐỔI
    setTimeout(() => {
        // Quán được kéo
        const draggedCard = document.querySelector(`[data-meal-key="${draggedKey}"] .meal-card-vertical`);
        if (draggedCard) {
            draggedCard.classList.add('just-dropped');
            
            // Thêm icon mũi tên
            const draggedNewIndex = newOrder.indexOf(draggedKey);
            const direction = draggedNewIndex < draggedOldIndex ? '⬆️' : '⬇️';
            const indicator1 = document.createElement('div');
            indicator1.className = 'reposition-indicator';
            indicator1.textContent = direction;
            draggedCard.style.position = 'relative';
            draggedCard.appendChild(indicator1);
            
            // Scroll đến quán được kéo
            const draggedItem = document.querySelector(`[data-meal-key="${draggedKey}"]`);
            if (draggedItem) {
                draggedItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            // Xóa sau 1.5s
            setTimeout(() => {
                draggedCard.classList.remove('just-dropped');
                if (indicator1.parentNode) {
                    indicator1.remove();
                }
            }, 1500);
        }
        
        // Quán đích (bị đẩy)
        const targetCard = document.querySelector(`[data-meal-key="${targetKey}"] .meal-card-vertical`);
        if (targetCard) {
            targetCard.classList.add('just-dropped');
            
            // Thêm icon mũi tên (ngược hướng với quán kéo)
            const targetNewIndex = newOrder.indexOf(targetKey);
            const direction = targetNewIndex < targetOldIndex ? '⬆️' : '⬇️';
            const indicator2 = document.createElement('div');
            indicator2.className = 'reposition-indicator';
            indicator2.textContent = direction;
            targetCard.style.position = 'relative';
            targetCard.appendChild(indicator2);
            
            // Xóa sau 1.5s
            setTimeout(() => {
                targetCard.classList.remove('just-dropped');
                if (indicator2.parentNode) {
                    indicator2.remove();
                }
            }, 1500);
        }
    }, 100);
    
    return false;
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.meal-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// ========== UPDATE MEAL TIME ==========
function updateMealTime(mealKey, newTime) {
    if (currentPlan && currentPlan[mealKey]) {
        currentPlan[mealKey].time = newTime;
        
        // 🔥 CẬP NHẬT TITLE TỪ INPUT (nếu có)
        const mealCard = document.querySelector(`[data-meal-key="${mealKey}"]`);
        if (mealCard) {
            const titleInput = mealCard.querySelector('input[onchange*="updateMealTitle"]');
            if (titleInput && titleInput.value) {
                currentPlan[mealKey].title = titleInput.value;
            }
        }
    }
}

// ========== UPDATE MEAL TITLE ==========
function updateMealTitle(mealKey, newTitle) {
    if (currentPlan && currentPlan[mealKey]) {
        currentPlan[mealKey].title = newTitle;
    }
}

// ========== UPDATE MEAL ICON ==========
function updateMealIcon(mealKey, newIcon) {
    if (currentPlan && currentPlan[mealKey]) {
        currentPlan[mealKey].icon = newIcon;
        displayPlanVertical(currentPlan, isEditMode);
    }
}

// ========== ICON OPTIONS ==========
const iconOptions = ['🍳', '🥐', '🍜', '🍚', '🍛', '🍝', '🍕', '🍔', '🌮', '🥗', '🍱', '🍤', '🍣', '🦞', '☕', '🧋', '🍵', '🥤', '🍰', '🍨', '🧁', '🍩', '🍪', '🍽️'];

function updateAutoPlanName(newName) {
    if (!currentPlanId) return;
    
    const cleanName = newName.trim() || 'Kế hoạch';
    
    // 🔥 Nếu tên không đổi thì KHÔNG làm gì
    if (window.currentPlanName === cleanName) return;
    
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    const plan = savedPlans.find(p => p.id === currentPlanId);
    
    if (plan) {
        plan.name = cleanName;
        window.currentPlanName = plan.name;
        localStorage.setItem('food_plans', JSON.stringify(savedPlans));
        
        // 🔥 CẬP NHẬT LIST "LỊCH TRÌNH ĐÃ LƯU"
        displaySavedPlansList(savedPlans);
    }
}

function flyToPlace(lat, lon, placeId, placeName) {
    if (typeof map !== 'undefined') {
        map.setView([lat, lon], 17, { animate: true });
        
        function waitForMapReady() {
            return new Promise((resolve) => {
                if (!map._animatingZoom) {
                    resolve();
                    return;
                }
                
                map.once('moveend', () => {
                    setTimeout(resolve, 1500);
                });
            });
        }
        
        function tryClick(attempt) {
            let targetMarker = null;
            
            // 🔥 ƯU TIÊN 1: TÌM THEO placeId (chính xác nhất)
            if (placeId && typeof window.placeMarkersById !== 'undefined') {
                targetMarker = window.placeMarkersById[placeId];
                if (targetMarker) {
                    console.log('✅ Tìm thấy marker theo ID:', placeId);
                }
            }
            
            // 🔥 ƯU TIÊN 2: TÌM THEO TÊN QUÁN (nếu không có ID)
            if (!targetMarker && placeName) {
                map.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        const data = layer.options.placeData || layer.placeData;
                        if (data && data.ten_quan === placeName) {
                            targetMarker = layer;
                            console.log('✅ Tìm thấy marker theo tên:', placeName);
                            return;
                        }
                    }
                });
            }
            
            // 🔥 ƯU TIÊN 3: TÌM THEO TỌA ĐỘ (fallback - ít chính xác nhất)
            if (!targetMarker) {
                let minDistance = Infinity;
                
                map.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        const markerLatLng = layer.getLatLng();
                        
                        const dLat = markerLatLng.lat - lat;
                        const dLng = markerLatLng.lng - lon;
                        const distance = Math.sqrt(dLat * dLat + dLng * dLng);
                        
                        // 🔥 GIảM NGƯỠNG: 0.0005 → 0.00001 (chỉ chấp nhận marker RẤT GẦN)
                        if (distance < 0.00001 && distance < minDistance) {
                            minDistance = distance;
                            targetMarker = layer;
                        }
                    }
                });
                
                if (targetMarker) {
                    console.log('✅ Tìm thấy marker theo tọa độ, khoảng cách:', minDistance.toFixed(8));
                }
            }
            
            // 🔥 NẾU TÌM THẤY MARKER → CLICK
            if (targetMarker) {
                let placeData = targetMarker.options.placeData || targetMarker.placeData;
                
                if (placeData) {
                    console.log('✅ Marker có dữ liệu:', placeData.ten_quan);
                } else {
                    console.warn('⚠️ Marker không có placeData → Tìm trong allPlacesData');
                    
                    // Tìm trong allPlacesData
                    if (typeof allPlacesData !== 'undefined' && allPlacesData.length > 0) {
                        let foundPlace = null;
                        
                        if (placeId) {
                            foundPlace = allPlacesData.find(p => p.data_id === placeId);
                        }
                        
                        if (!foundPlace && placeName) {
                            foundPlace = allPlacesData.find(p => p.ten_quan === placeName);
                        }
                        
                        if (!foundPlace) {
                            foundPlace = allPlacesData.find(p => {
                                const pLat = parseFloat(p.lat);
                                const pLon = parseFloat(p.lon);
                                const dist = Math.sqrt(
                                    Math.pow(pLat - lat, 2) + 
                                    Math.pow(pLon - lon, 2)
                                );
                                return dist < 0.00001;
                            });
                        }
                        
                        if (foundPlace) {
                            console.log('✅ Tìm thấy place trong allPlacesData:', foundPlace.ten_quan);
                            targetMarker.options.placeData = foundPlace;
                            targetMarker.placeData = foundPlace;
                            placeData = foundPlace;
                        }
                    }
                }
                
                // ✅ CLICK VÀO MARKER **CHỈ 1 LẦN**
                console.log('🔥 Trigger click vào marker');
                targetMarker.fire('click');  // ✅ CHỈ CLICK 1 LẦN
                
                return true;
            }
            
            // ✅ Giảm retry từ 25 → 8 lần
            const MAX_RETRIES = 8;
            
            if (attempt < MAX_RETRIES) {
                console.log(`⏳ Lần thử ${attempt + 1}/${MAX_RETRIES} - Chưa tìm thấy marker`);
                setTimeout(() => tryClick(attempt + 1), 800); // ✅ 800ms thay vì 1000ms
            } else {
                console.error(`❌ Không tìm thấy marker sau ${MAX_RETRIES} lần thử`);
                
                // ✅ CHỈ reload 1 lần duy nhất
                if (attempt === MAX_RETRIES && typeof loadMarkersInViewport === 'function') {
                    console.log('🔄 Thử reload markers lần cuối...');
                    loadMarkersInViewport();
                    setTimeout(() => tryClick(MAX_RETRIES + 1), 1500);
                }
            }
            
            return false;
        }
        
        waitForMapReady().then(() => {
            tryClick(0);
        });
    }
}

// ========== EXPOSE FUNCTIONS TO WINDOW ==========
window.foodPlannerState = {
    isEditMode: () => {
        return isEditMode;
    },
    isWaitingForPlaceSelection: () => {
        return waitingForPlaceSelection !== null;
    },
    selectPlace: (place) => {
        if (waitingForPlaceSelection) {
            // AUTO MODE
            const success = replacePlaceInMeal(place);
            return success;
        }
        return false;
    }
};

// ========== EVENT LISTENERS ==========
document.getElementById('foodPlannerPanel')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeFoodPlanner();
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isPlannerOpen) {
        closeFoodPlanner();
    }
});
// ========== LOAD POLYLINE OFFSET PLUGIN ==========
(function() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/leaflet-polylineoffset@1.1.1/leaflet.polylineoffset.min.js';
    script.onload = function() {
        console.log('✅ Leaflet PolylineOffset loaded');
    };
    script.onerror = function() {
        console.error('❌ Failed to load PolylineOffset plugin');
    };
    document.head.appendChild(script);
})();
// ========== CYCLIC TIME INPUT ==========
document.addEventListener('DOMContentLoaded', function() {
    function setupCyclicInput(id, maxValue) {
        const input = document.getElementById(id);
        if (!input) return;
        
        let lastValue = parseInt(input.value) || 0;
        
        // 🔥 CHO PHÉP XÓA TỰ DO KHI FOCUS
        input.addEventListener('focus', function() {
            this.select(); // Select all để dễ gõ đè
        });
        
        // 🔥 CHỈ FORMAT KHI BLUR (CLICK RA NGOÀI)
        input.addEventListener('blur', function() {
            if (this.value === '' || this.value === null || this.value.trim() === '') {
                this.value = '00';
                lastValue = 0;
                return;
            }
            
            let val = parseInt(this.value);
            
            if (isNaN(val)) {
                this.value = '00';
                lastValue = 0;
                return;
            }
            
            if (val > maxValue) val = maxValue;
            if (val < 0) val = 0;
            
            this.value = val.toString().padStart(2, '0');
            lastValue = val;
        });
        
        // 🔥 XỬ LÝ PHÍM MŨI TÊN + CHO PHÉP BACKSPACE/DELETE
        input.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                let val = parseInt(this.value) || 0;
                val = val >= maxValue ? 0 : val + 1;
                this.value = val.toString().padStart(2, '0');
                lastValue = val;
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                let val = parseInt(this.value) || 0;
                val = val <= 0 ? maxValue : val - 1;
                this.value = val.toString().padStart(2, '0');
                lastValue = val;
            }
            // 🔥 CHO PHÉP XÓA BẰNG BACKSPACE/DELETE - KHÔNG BLOCK
            // else if (e.key === 'Backspace' || e.key === 'Delete') {
            //     // Không làm gì, cho phép xóa tự nhiên
            // }
        });
        
        // 🔥 SCROLL CHUỘT
        input.addEventListener('wheel', function(e) {
            e.preventDefault();
            let val = parseInt(this.value) || 0;
            
            if (e.deltaY < 0) {
                val = val >= maxValue ? 0 : val + 1;
            } else {
                val = val <= 0 ? maxValue : val - 1;
            }
            
            this.value = val.toString().padStart(2, '0');
            lastValue = val;
        }, { passive: false });
    }
    
    // Áp dụng cho tất cả input
    setupCyclicInput('startHour', 23);
    setupCyclicInput('endHour', 23);
    setupCyclicInput('startMinute', 59);
    setupCyclicInput('endMinute', 59);
});
// ========== SETUP CYCLIC TIME INPUTS FOR EDIT MODE ==========
function setupEditModeTimeInputs() {
    document.querySelectorAll('.time-input-hour, .time-input-minute').forEach(input => {
        const isHour = input.classList.contains('time-input-hour');
        const maxValue = isHour ? 23 : 59;
        
        // Xử lý wheel scroll
        let scrollTimeout = null;
        // ✅ Debounce để giảm tần suất update
        let wheelTimeout = null;

        input.addEventListener('wheel', function(e) {
            e.preventDefault();
            
            // ✅ Debounce - chỉ update sau 50ms
            clearTimeout(wheelTimeout);
            
            let val = parseInt(this.value) || 0;
            
            if (e.deltaY < 0) {
                val = val >= maxValue ? 0 : val + 1;
            } else {
                val = val <= 0 ? maxValue : val - 1;
            }
            
            this.value = val.toString().padStart(2, '0');
            
            // ✅ Chỉ update sau khi dừng scroll
            wheelTimeout = setTimeout(() => {
                updateTimeFromInputs(this);
            }, 50);
            
        }, { passive: false }); // ✅ Bỏ capture: true
        
        // Xử lý arrow keys
        input.addEventListener('keydown', function(e) {
            let val = parseInt(this.value) || 0;
            
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                val = val >= maxValue ? 0 : val + 1;
                this.value = val.toString().padStart(2, '0');
                updateTimeFromInputs(this);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                val = val <= 0 ? maxValue : val - 1;
                this.value = val.toString().padStart(2, '0');
                updateTimeFromInputs(this);
            }
        });
        
        // Xử lý blur để format
        input.addEventListener('blur', function() {
            let val = parseInt(this.value) || 0;
            if (val > maxValue) val = maxValue;
            if (val < 0) val = 0;
            this.value = val.toString().padStart(2, '0');
            updateTimeFromInputs(this);
        });
        
        // Xử lý change
        input.addEventListener('change', function() {
            let val = parseInt(this.value) || 0;
            if (val > maxValue) val = 0;
            if (val < 0) val = maxValue;
            this.value = val.toString().padStart(2, '0');
            updateTimeFromInputs(this);
        });
    });
}

function updateTimeFromInputs(input) {
    const mealKey = input.dataset.mealKey;
    const parent = input.closest('.meal-item');
    if (!parent) return;
    
    const hourInput = parent.querySelector('.time-input-hour[data-meal-key="' + mealKey + '"]');
    const minuteInput = parent.querySelector('.time-input-minute[data-meal-key="' + mealKey + '"]');
    
    if (hourInput && minuteInput) {
        const hour = hourInput.value.padStart(2, '0');
        const minute = minuteInput.value.padStart(2, '0');
        const newTime = `${hour}:${minute}`;
        
        if (currentPlan && currentPlan[mealKey]) {
            // 🔥 LƯU VỊ TRÍ CŨ trước khi sort
            const oldOrder = currentPlan._order ? [...currentPlan._order] : 
                Object.keys(currentPlan)
                    .filter(k => k !== '_order' && currentPlan[k] && currentPlan[k].time)
                    .sort((a, b) => currentPlan[a].time.localeCompare(currentPlan[b].time));
            
            const oldIndex = oldOrder.indexOf(mealKey);
            
            // Cập nhật thời gian
            currentPlan[mealKey].time = newTime;
            
            // Cập nhật title nếu có
            const titleInput = parent.querySelector('input[onchange*="updateMealTitle"]');
            if (titleInput && titleInput.value) {
                currentPlan[mealKey].title = titleInput.value;
            }
            
            // 🔥 SORT lại theo thời gian
            const newOrder = Object.keys(currentPlan)
                .filter(k => k !== '_order' && currentPlan[k] && currentPlan[k].time)
                .sort((a, b) => {
                    const timeA = currentPlan[a].time || '00:00';
                    const timeB = currentPlan[b].time || '00:00';
                    return timeA.localeCompare(timeB);
                });
            
            const newIndex = newOrder.indexOf(mealKey);
            
            currentPlan._order = newOrder;
            
            // ✅ RENDER lại
            displayPlanVertical(currentPlan, isEditMode);
            
            // 🔥 HIGHLIGHT card vừa di chuyển + HIỂN THỊ ICON
            setTimeout(() => {
                const movedCard = document.querySelector(`[data-meal-key="${mealKey}"] .meal-card-vertical`);
                if (movedCard && oldIndex !== newIndex) {
                    // Thêm class animation
                    movedCard.classList.add('repositioned');
                    
                    // Thêm icon mũi tên
                    const direction = newIndex < oldIndex ? '⬆️' : '⬇️';
                    const indicator = document.createElement('div');
                    indicator.className = 'reposition-indicator';
                    indicator.textContent = direction;
                    movedCard.style.position = 'relative';
                    movedCard.appendChild(indicator);
                    
                    // Scroll đến vị trí mới
                    const mealItem = document.querySelector(`[data-meal-key="${mealKey}"]`);
                    if (mealItem) {
                        mealItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    
                    // Xóa animation và icon sau 1.5s
                    setTimeout(() => {
                        movedCard.classList.remove('repositioned');
                        if (indicator.parentNode) {
                            indicator.remove();
                        }
                    }, 1500);
                }
            }, 100);
        }
    }
}
// ========== CẬP NHẬT BÁN KÍNH KHI CHỌN ==========
document.addEventListener('DOMContentLoaded', function() {
    const radiusInputs = document.querySelectorAll('input[name="radius"]');
    
    radiusInputs.forEach(input => {
        input.addEventListener('change', function() {
            const radiusValue = this.value || '10'; // Mặc định 10km nếu chọn "Bán kính mặc định"
            
            // 🔥 CẬP NHẬT BIẾN TOÀN CỤC
            window.currentRadius = radiusValue;
            
            // 🔥 CẬP NHẬT HIDDEN INPUT
            const hiddenInput = document.getElementById('radius');
            if (hiddenInput) {
                hiddenInput.value = radiusValue;
            }
            
            console.log('✅ Đã cập nhật bán kính:', radiusValue + ' km');
        });
    });
    
    // 🔥 ĐẶT GIÁ TRỊ BAN ĐẦU
    const checkedRadius = document.querySelector('input[name="radius"]:checked');
    if (checkedRadius) {
        window.currentRadius = checkedRadius.value || '10';
        const hiddenInput = document.getElementById('radius');
        if (hiddenInput) {
            hiddenInput.value = window.currentRadius;
        }
    }
});

// ========== DELETE ALL MEALS ==========
function deleteAllMeals() {
    if (!currentPlan) return;
    
    const mealCount = Object.keys(currentPlan).filter(k => k !== '_order').length;
    
    if (mealCount === 0) {
        alert('⚠️ Lịch trình đã trống rồi!');
        return;
    }
    
    if (!confirm(`🗑️ Bạn có chắc muốn xóa tất cả ${mealCount} quán trong lịch trình?`)) {
        return;
    }
    
    // Xóa tất cả keys trừ _order
    Object.keys(currentPlan).forEach(key => {
        if (key !== '_order') {
            delete currentPlan[key];
        }
    });
    
    // Reset _order
    currentPlan._order = [];
    
    // Reset waiting state
    waitingForPlaceSelection = null;
    
    // Render lại
    displayPlanVertical(currentPlan, isEditMode);
    
    alert('✅ Đã xóa tất cả quán!');
}
</script>
'''