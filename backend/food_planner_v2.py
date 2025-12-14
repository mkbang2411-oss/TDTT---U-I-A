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

def is_open_now(opening_hours_str, check_time=None, min_hours_before_close=1, place_name=None):
    """
    Kiểm tra quán có đang mở cửa không VÀ còn đủ thời gian hoạt động
    
    Args:
        opening_hours_str: Chuỗi giờ mở cửa từ CSV (VD: "Mở cửa vào 4:30 · Đóng cửa vào 12:00")
        check_time: Thời gian cần kiểm tra (HH:MM hoặc time object)
        min_hours_before_close: Số giờ tối thiểu trước khi đóng cửa (mặc định 1 giờ)
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
        
        # 🔥 THAY ĐOẠN NÀY (từ dòng "# 3 điều kiện để quán hợp lệ:")
        
        # 🔥 CHỈ KIỂM TRA 2 ĐIỀU KIỆN:
        # 1. Đã đến giờ mở cửa
        is_open = (current_minutes >= open_minutes)

        # 2. Còn đủ thời gian hoạt động (ít nhất 1 giờ từ current_time đến giờ đóng)
        min_minutes_before_close = min_hours_before_close * 60
        has_enough_time = ((close_minutes - current_minutes) >= min_minutes_before_close)

        # 🔥 CHẶN CHẶT: Nếu KHÔNG thỏa mãn CẢ 2 điều kiện → CHẶN LUÔN
        if not (is_open and has_enough_time):
            return False

        # ✅ Nếu đến đây → CẢ 2 ĐIỀU KIỆN ĐỀU ĐÚNG
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
            'thực dưỡng', 'thuần chay',
            # 🔥 THÊM KEYWORDS MỚI 🔥
            'chay zen', 'chay buffet', 'quán chay',
            'ăn chay', 'thực phẩm chay', 'chay healthy',
            'bánh mì chay', 'lẩu chay', 'nướng chay',
            'cà ri chay', 'mì chay', 'hủ tiếu chay'
        ],
        'icon': '🥗'
    },
    'dessert_bakery': {
        'name': 'Tráng miệng',
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
        'bánh bèo', 'cơm tấm', 'mì quảng',
        # 🔥 THÊM KEYWORDS MÓN CHAY CHO BỮA SÁNG 🔥
        'chay', 'vegetarian', 'vegan', 'healthy', 'rau củ', 'rau sạch',
        'cơm chay', 'bún chay', 'phở chay', 'đậu hũ', 'tofu', 'nấm'
        # 🔥 THÊM KEYWORDS NHÀ HÀNG SANG TRỌNG 🔥
        'nhà hàng', 'restaurant', 'buffet', 'resort', 'fine dining', 'luxury'
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
        # 🔥 THÊM KEYWORDS NHÀ HÀNG SANG TRỌNG 🔥
        'nhà hàng', 'restaurant', 'buffet', 'resort', 'fine dining', 'luxury'
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
        # 🔥 THÊM KEYWORDS NHÀ HÀNG SANG TRỌNG 🔥
        'nhà hàng', 'restaurant', 'buffet', 'resort', 'fine dining', 'luxury'
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
        'bánh xèo', 'nem', 'gỏi', 'cháo', 'xôi', 'cao lầu',
        # 🔥 THÊM NHÀ HÀNG 🔥
        'nhà hàng', 'restaurant', 'buffet'
    ],
    
    'meal1': [
        # Bữa chính 1
        'cơm', 'bún', 'phở', 'mì', 'hủ tiếu', 'cơm tấm', 'bánh mì',
        'bánh xèo', 'miến', 'cao lầu', 'mì quảng',
        # 🔥 THÊM NHÀ HÀNG 🔥
        'nhà hàng', 'restaurant', 'buffet'
    ],
    
    'meal2': [
        # Bữa phụ nhẹ hơn
        'cơm', 'bún', 'phở', 'mì', 'bánh mì', 'nem', 'gỏi cuốn',
        'bánh xèo', 'bánh', 'xôi', 'chè',
        # 🔥 THÊM NHÀ HÀNG 🔥
        'nhà hàng', 'restaurant'
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
            check_time_str = filters.get('meal_time')  # Thời gian gắn quán vào lịch trình
            ten_quan = str(row.get('ten_quan', ''))
            name_normalized = normalize_text_with_accent(ten_quan)
            
            if check_time_str:
                # min_hours_before_close=1 → quán phải còn mở ít nhất 1h từ check_time
                if not is_open_now(gio_mo_cua, check_time=check_time_str, min_hours_before_close=1, place_name=ten_quan):
                    continue
            else:
                # Fallback: dùng thời gian hiện tại
                if not is_open_now(gio_mo_cua, min_hours_before_close=1, place_name=ten_quan):
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
                        mo_ta = str(row.get('mo_ta', '')).strip()
                        
                        # 🔥 THÊM LOG DEBUG
                        if mo_ta.lower() == 'michelin':
                            print(f"✅ [MICHELIN MATCH] {row.get('ten_quan')} | Giờ: {row.get('gio_mo_cua')} | Check time: {filters.get('meal_time')}")
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

            # 🔥 Lọc BÁNH MÌ + BÁNH XÈO KHỎI THEME dessert_bakery
            if theme and 'dessert_bakery' in theme_list:
                name_for_check = normalize_text(str(row.get('ten_quan', '')))
                # chuẩn hoá thêm để bắt được "banh-xeo"
                name_for_check = ' '.join(name_for_check.replace('-', ' ').split())

                banh_mi_variants = ['banhmi', 'banh mi', 'banhmy', 'banh my']
                if any(v in name_for_check for v in banh_mi_variants):
                    continue

                banh_xeo_variants = ['banh xeo', 'banhxeo']
                if any(v in name_for_check for v in banh_xeo_variants):
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
    Chọn theme phù hợp cho từng bữa ăn/uống
    """
    # Nếu là bữa uống/tráng miệng (drink_*)
    if meal_key.startswith('drink_'):
        if 'coffee_chill' in user_selected_themes:
            return 'coffee_chill'
        elif 'dessert_bakery' in user_selected_themes:
            return 'dessert_bakery'
        else:
            return 'coffee_chill'
    
    # Nếu là bữa ăn (meal_*)
    if user_selected_themes:
        # Lọc bỏ theme không phù hợp cho bữa ăn
        food_themes = ['street_food', 'asian_fusion', 'seafood', 'spicy_food', 
                      'luxury_dining', 'vegetarian', 'food_street', 'michelin']
        
        suitable_themes = [t for t in user_selected_themes if t in food_themes]
        
        if suitable_themes:
            return suitable_themes[0]
    
    # Fallback mặc định
    return 'street_food'

def assign_drink_themes_to_plan(plan, user_selected_themes):
    """
    Random theme cho từng drink_*.
    Nếu có cả coffee + dessert và có >=2 slot thì đảm bảo có ít nhất 1 coffee và 1 dessert.
    Đồng thời update title/icon đúng theo theme.
    """
    has_coffee = user_selected_themes and ('coffee_chill' in user_selected_themes)
    has_dessert = user_selected_themes and ('dessert_bakery' in user_selected_themes)

    # Lấy danh sách drink keys theo thứ tự
    order = plan.get('_order')
    if order:
        drink_keys = [k for k in order if isinstance(k, str) and k.startswith('drink_') and k in plan]
    else:
        drink_keys = [k for k in plan.keys() if isinstance(k, str) and k.startswith('drink_')]
        def _idx(k):
            try:
                return int(k.split('_', 1)[1])
            except:
                return 999999
        drink_keys.sort(key=_idx)

    if not drink_keys:
        return

    # Helper label/icon theo giờ + theme
    def drink_label_icon(time_str, drink_theme):
        try:
            hour = int(str(time_str).split(':')[0])
        except:
            hour = 12

        if 5 <= hour < 10:
            segment = 'buổi sáng'
        elif 10 <= hour < 14:
            segment = 'buổi trưa'
        elif 14 <= hour < 18:
            segment = 'xế chiều'
        elif 18 <= hour < 22:
            segment = 'buổi tối'
        elif 22 <= hour < 24:
            segment = 'buổi đêm'
        else:
            segment = 'đêm khuya'

        if drink_theme == 'dessert_bakery':
            return f'Tráng miệng {segment}', THEME_CATEGORIES['dessert_bakery']['icon']
        return f'Giải khát {segment}', THEME_CATEGORIES['coffee_chill']['icon']

    # Nếu không chọn đủ 2 theme -> cố định 1 loại
    if not (has_coffee and has_dessert):
        fixed = 'coffee_chill' if has_coffee else ('dessert_bakery' if has_dessert else 'coffee_chill')
        for k in drink_keys:
            plan[k]['theme'] = fixed
            title, icon = drink_label_icon(plan[k].get('time'), fixed)
            plan[k]['title'] = title
            plan[k]['icon'] = icon
        return

    # Có cả 2 theme -> random theo slot, nhưng đảm bảo mix nếu >=2
    n = len(drink_keys)
    if n == 1:
        themes = [random.choice(['coffee_chill', 'dessert_bakery'])]
    else:
        themes = ['coffee_chill', 'dessert_bakery']
        for _ in range(n - 2):
            themes.append(random.choice(['coffee_chill', 'dessert_bakery']))
        random.shuffle(themes)

    for k, t in zip(drink_keys, themes):
        plan[k]['theme'] = t
        title, icon = drink_label_icon(plan[k].get('time'), t)
        plan[k]['title'] = title
        plan[k]['icon'] = icon


# ==================== GENERATE SMART PLAN ====================

def generate_meal_schedule(time_start_str, time_end_str, user_selected_themes):
    """
    Generate meal schedule - Hỗ trợ QUA ĐÊM, KHÔNG SORT
    Giữ nguyên thứ tự thời gian thực tế
    
    🔥 FIX: Cho phép tạo quán đúng vào thời điểm end_time
    """
    from datetime import datetime, timedelta
    
    time_start = datetime.strptime(time_start_str, '%H:%M')
    time_end = datetime.strptime(time_end_str, '%H:%M')
    
    # 🔥 TÍNH DURATION (hỗ trợ qua đêm)
    if time_start_str == time_end_str:
        duration_hours = 24.0
    elif time_end <= time_start:
        # Qua đêm: tính từ start -> 24h + 0h -> end
        duration_hours = ((24 * 60 - time_start.hour * 60 - time_start.minute) + 
                         (time_end.hour * 60 + time_end.minute)) / 60.0
    else:
        duration_hours = (time_end - time_start).seconds / 3600.0
    
    # Kiểm tra theme
    has_drink_theme = any(t in ['coffee_chill', 'dessert_bakery'] for t in user_selected_themes) if user_selected_themes else False
    
    plan = {}
    order = []
    
    current_time = time_start
    meal_counter = 1
    drink_counter = 1
    elapsed_hours = 0.0
    
    def format_time(dt):
        """Format thời gian, cho phép vượt qua 24h"""
        return dt.strftime('%H:%M')
    
    def get_meal_label(time_obj):
        """Phân loại bữa ăn theo giờ"""
        hour = time_obj.hour
        if 5 <= hour < 10:
            return 'Bữa sáng', '🍳'
        elif 10 <= hour < 14:
            return 'Bữa trưa', '🍚'
        elif 14 <= hour < 18:
            return 'Bữa xế', '🥖'
        elif 18 <= hour < 22:
            return 'Bữa tối', '🍽️'
        elif 22 <= hour < 24:
            return 'Bữa đêm', '🌙'
        else:  # 0-5h
            return 'Bữa khuya', '🌃'
    
    def decide_drink_theme():
        """Chọn loại slot: Giải khát (coffee_chill) hay Tráng miệng (dessert_bakery)"""
        if not user_selected_themes:
            return 'coffee_chill'
        if 'coffee_chill' in user_selected_themes:
            return 'coffee_chill'
        if 'dessert_bakery' in user_selected_themes:
            return 'dessert_bakery'
        return 'coffee_chill'

    def get_drink_label(time_obj, drink_theme):
        """Tạo label + icon cho bữa uống/tráng miệng theo THEME đã chọn"""
        hour = time_obj.hour
        if 5 <= hour < 10:
            segment = 'buổi sáng'
        elif 10 <= hour < 14:
            segment = 'buổi trưa'
        elif 14 <= hour < 18:
            segment = 'xế chiều'
        elif 18 <= hour < 22:
            segment = 'buổi tối'
        elif 22 <= hour < 24:
            segment = 'buổi đêm'
        else:  # 0-5h
            segment = 'đêm khuya'

        if drink_theme == 'dessert_bakery':
            return f'Tráng miệng {segment}', THEME_CATEGORIES['dessert_bakery']['icon']
        else:
            return f'Giải khát {segment}', THEME_CATEGORIES['coffee_chill']['icon']
    
    # 🔥 LOGIC MỚI: KHÔNG SORT, GIỮ NGUYÊN THỨ TỰ THỜI GIAN THỰC TẾ
    if duration_hours >= 2.5:
        while True:  # 🔥 Đổi từ while elapsed_hours < duration_hours
            # 1. Thêm bữa ăn
            meal_key = f'meal_{meal_counter}'
            meal_label, meal_icon = get_meal_label(current_time)
            
            plan[meal_key] = {
                'time': format_time(current_time),
                'title': meal_label,
                'icon': meal_icon,
                'categories': ['pho', 'com tam', 'bun']
            }
            order.append(meal_key)
            meal_counter += 1
            
            # 2. Thêm bữa uống/tráng miệng sau 2.5h (nếu còn thời gian)
            # 🔥 QUAN TRỌNG: Luôn cộng elapsed_hours để giữ logic thời gian nhất quán
            if elapsed_hours + 2.5 <= duration_hours:
                if has_drink_theme:
                    # Chỉ thêm quán vào plan khi CÓ theme
                    drink_time = current_time + timedelta(hours=2.5)
                    drink_key = f'drink_{drink_counter}'
                    drink_theme = decide_drink_theme()
                    drink_label, drink_icon = get_drink_label(drink_time, drink_theme)
                    
                    plan[drink_key] = {
                        'time': format_time(drink_time),
                        'title': drink_label,
                        'icon': drink_icon,
                        'categories': ['tra sua', 'cafe', 'banh']
                    }
                    order.append(drink_key)
                    drink_counter += 1
                
                # Cộng 2.5h bất kể có thêm quán hay không (để giữ logic nhất quán)
                elapsed_hours += 2.5

            # 3. Chuyển sang bữa ăn tiếp theo (5h sau bữa ăn đầu)
            elapsed_hours += 2.5  # Tổng 5h từ bữa ăn trước
            
            # 🔥 FIX QUAN TRỌNG: Cho phép tạo bữa ăn ĐÚNG VÀO end_time
            # Chỉ dừng khi elapsed_hours VƯỢT QUÁ duration_hours
            if elapsed_hours > duration_hours:
                break
            
            current_time = current_time + timedelta(hours=5)
    else:
        # Duration < 2.5h
        meal_key = 'meal_1'
        meal_label, meal_icon = get_meal_label(current_time)
        
        plan[meal_key] = {
            'time': format_time(current_time),
            'title': meal_label,
            'icon': meal_icon,
            'categories': ['pho', 'com tam', 'bun']
        }
        order.append(meal_key)
        
        # Thêm bữa uống sau 1h nếu còn thời gian VÀ có theme
        if duration_hours >= 1.0 and has_drink_theme:
            drink_time = current_time + timedelta(hours=1)
            drink_key = 'drink_1'
            drink_theme = decide_drink_theme()
            drink_label, drink_icon = get_drink_label(drink_time, drink_theme)
            
            plan[drink_key] = {
                'time': format_time(drink_time),
                'title': drink_label,
                'icon': drink_icon,
                'categories': ['tra sua', 'cafe', 'banh']
            }
            order.append(drink_key)
    
    # 🔥 QUAN TRỌNG: LƯU _order THEO THỨ TỰ TẠO RA, KHÔNG SORT
    plan['_order'] = order
    
    print(f"📊 [SCHEDULE] Duration: {duration_hours}h")
    print(f"📊 [SCHEDULE] Generated order: {order}")
    for key in order:
        if key in plan:
            print(f"  - {key}: {plan[key]['time']} - {plan[key]['title']}")
    
    return plan

# ==================== ĐIỀU CHỈNH MEAL SCHEDULE DỰA TRÊN THEME ====================

def parse_time_to_float(time_str):
    """Parse 'HH:MM' thành float"""
    parts = time_str.split(':')
    return int(parts[0]) + int(parts[1]) / 60.0

def filter_meal_schedule_by_themes(plan, user_selected_themes, start_time='07:00', end_time='21:00'):
    """
    🔥 Logic mới: Xử lý đặc biệt khi CHỈ chọn Giải khát/Tráng miệng
    """
    # ❌ KHÔNG có theme → GIỮ NGUYÊN
    if not user_selected_themes or len(user_selected_themes) == 0:
        return plan
    
    # 🔥 ĐỊNH NGHĨA THEME "ĂN"
    food_themes = {
        'street_food', 'asian_fusion', 'seafood', 'spicy_food', 
        'luxury_dining', 'vegetarian', 'michelin', 'food_street'
    }
    
    has_food_theme = any(theme in food_themes for theme in user_selected_themes)
    has_coffee = 'coffee_chill' in user_selected_themes
    has_dessert = 'dessert_bakery' in user_selected_themes
    
    # ✅ CÓ THEME ĂN → GIỮ NGUYÊN
    if has_food_theme:
        return plan
    
    # 🔥 CHỈ CÓ COFFEE/DESSERT → ÁP DỤNG LOGIC MỚI
    # Random chọn 1 theme nếu có cả 2
    selected_drink_theme = None
    if has_coffee and has_dessert:
        selected_drink_theme = random.choice(['coffee_chill', 'dessert_bakery'])
    elif has_coffee:
        selected_drink_theme = 'coffee_chill'
    elif has_dessert:
        selected_drink_theme = 'dessert_bakery'
    
    start_hour = parse_time_to_float(start_time)
    end_hour = parse_time_to_float(end_time)

    # Tính duration có xử lý qua đêm — kể cả khi start == end vẫn tính qua đêm
    if end_hour > start_hour:
        duration = end_hour - start_hour
    else:
        duration = (24 - start_hour) + end_hour  # qua đêm hoặc start == end
    
    # 🔥 PHÂN BỔ QUÁN THEO THỜI GIAN
    filtered_plan = {}
    
    # Dưới 3h: 1 quán
    if duration < 3:
        mid_time = calculate_time_at_ratio(start_hour, end_hour, 0.5)
        filtered_plan['drink_1'] = {
            'time': mid_time,
            'title': 'Giải khát' if selected_drink_theme == 'coffee_chill' else 'Tráng miệng',
            'categories': ['tra sua', 'cafe', 'banh'],
            'icon': '☕' if selected_drink_theme == 'coffee_chill' else '🍰'
        }
    
    # 3-6h: 2 quán cách 3h
    elif 3 <= duration < 6:
        time1 = format_hour_to_time(start_hour)
        time2 = format_hour_to_time(start_hour + 3)
        
        filtered_plan['drink_1'] = {
            'time': time1,
            'title': 'Giải khát' if selected_drink_theme == 'coffee_chill' else 'Tráng miệng',
            'categories': ['tra sua', 'cafe', 'banh'],
            'icon': '☕' if selected_drink_theme == 'coffee_chill' else '🍰'
        }
        filtered_plan['drink_2'] = {
            'time': time2,
            'title': 'Giải khát' if selected_drink_theme == 'coffee_chill' else 'Tráng miệng',
            'categories': ['tra sua', 'cafe', 'banh'],
            'icon': '☕' if selected_drink_theme == 'coffee_chill' else '🍰'
        }
    
    # >=6h: Mỗi 3h 1 quán
    else:
        num_places = int(duration / 3) + 1
        for i in range(num_places):
            place_time = format_hour_to_time(start_hour + (i * 3))
            filtered_plan[f'drink_{i+1}'] = {
                'time': place_time,
                'title': 'Giải khát' if selected_drink_theme == 'coffee_chill' else 'Tráng miệng',
                'categories': ['tra sua', 'cafe', 'banh'],
                'icon': '☕' if selected_drink_theme == 'coffee_chill' else '🍰'
            }
    
    filtered_plan['_order'] = [k for k in filtered_plan.keys() if k != '_order']
    
    return filtered_plan

def generate_two_drink_times(start_hour, end_hour):
    """
    🔥 TẠO 2 THỜI GIAN BUỔI NƯỚC HỢP LÝ TRONG KHUNG GIỜ
    
    Args:
        start_hour: Giờ bắt đầu (float)
        end_hour: Giờ kết thúc (float)
    
    Returns:
        tuple: (time1, time2) dạng 'HH:MM'
    """
    duration = end_hour - start_hour
    
    if duration < 3:  # Nếu khung giờ quá ngắn (< 3h)
        # Tạo 2 buổi cách đều
        time1_hour = start_hour + duration * 0.3
        time2_hour = start_hour + duration * 0.7
    else:
        # Tạo 2 buổi cách 3 tiếng
        time1_hour = start_hour + 1
        time2_hour = time1_hour + 3
        
        # Đảm bảo time2 không vượt quá end_hour
        if time2_hour >= end_hour:
            time2_hour = end_hour - 0.5
            time1_hour = time2_hour - 3
    
    # Format thành HH:MM
    time1 = format_hour_to_time(time1_hour)
    time2 = format_hour_to_time(time2_hour)
    
    return (time1, time2)

def calculate_time_at_ratio(start_hour, end_hour, ratio):
    """
    🔥 TÍNH THỜI GIAN TẠI % KHUNG GIỜ
    
    Args:
        start_hour: Giờ bắt đầu (float)
        end_hour: Giờ kết thúc (float)
        ratio: Tỷ lệ % (0.0 - 1.0)
    
    Returns:
        str: Thời gian dạng 'HH:MM'
    """
    duration = end_hour - start_hour
    target_hour = start_hour + duration * ratio
    
    return format_hour_to_time(target_hour)

def format_hour_to_time(hour_float):
    """
    🔥 FORMAT GIỜ DẠNG FLOAT THÀNH 'HH:MM'
    
    Args:
        hour_float: Giờ dạng float (ví dụ: 14.5 = 14:30)
    
    Returns:
        str: Thời gian dạng 'HH:MM'
    """
    hour_float = hour_float % 24  # Quay vòng 24 giờ
    hour = int(hour_float)
    minute = int((hour_float % 1) * 60)
    return f'{hour:02d}:{minute:02d}'

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
    
    # 🔥 TẠO MEAL SCHEDULE
    plan = generate_meal_schedule(start_time, end_time, user_selected_themes)
    
    # 🔥🔥🔥 LỌC LỊCH TRÌNH DỰA TRÊN THEME 🔥🔥🔥
    plan = filter_meal_schedule_by_themes(plan, user_selected_themes, start_time, end_time)
    assign_drink_themes_to_plan(plan, user_selected_themes)

    # 🔥🔥 THÊM DÒNG DEBUG 🔥🔥
    print(f"🔍 Plan sau filter: {list(plan.keys())}")
    
    current_lat, current_lon = user_lat, user_lon
    used_place_ids = set()
    
    places_found = 0
    keys_to_remove = []
    
    for key, meal in plan.items():
        # 🔥🔥 BỎ QUA KEY _order 🔥🔥
        if key == '_order':
            continue
            
        # 🔥 CHỌN THEME PHÙ HỢP CHO TỪNG BỮA
        meal_theme = meal.get('theme') or get_theme_for_meal(key, user_selected_themes)
        
        print(f"🔍 Tìm quán cho {key} với theme {meal_theme}")
        
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
        if places and (key == 'dessert' or meal_theme == 'dessert_bakery'):
            filtered_places = []
            for p in places:
                name_lower = normalize_text(p['ten_quan'])  # Dùng normalize_text (BỎ DẤU)
                # Loại bỏ tất cả quán có "banh mi" hoặc "banhmi"
                if ('banhmi' not in name_lower and 'banh mi' not in name_lower
                    and 'banhxeo' not in name_lower and 'banh xeo' not in name_lower):
                    filtered_places.append(p)
            places = filtered_places
        
        # 🔥 Lọc CHẶT THEO KEYWORD - NHƯNG BỎ QUA CHO THEME ĐẶC BIỆT
        keyword_key = None
        if key in MEAL_TYPE_KEYWORDS:
            keyword_key = key
        elif key.startswith('drink_'):
            # Slot nước/tráng miệng: nếu đang là tráng miệng thì dùng bộ keyword dessert
            keyword_key = 'dessert' if meal_theme == 'dessert_bakery' else 'drink'
        elif key.startswith('meal_'):
            keyword_key = 'meal'

        if places and keyword_key:

            # ⚡ KIỂM TRA XEM CÓ PHẢI THEME ĐẶC BIỆT KHÔNG
            skip_keyword_filter = False
            
            if meal_theme in ['food_street', 'michelin', 'luxury_dining']:
                skip_keyword_filter = True
                print(f"⚡ Theme đặc biệt '{meal_theme}' - BỎ QUA lọc keyword")
            
            # ⚡ CHỈ LỌC NẾU KHÔNG PHẢI THEME ĐẶC BIỆT
            if not skip_keyword_filter:
                meal_keywords = MEAL_TYPE_KEYWORDS[keyword_key]
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
    top: 160px;
    right: -30%;
    width: 30%;
    height: calc(100% - 160px);
    max-height: calc(100vh - 60px);
    background: white;
    z-index: 9999999999999 !important;
    transition: right 0.3s ease;
    display: flex;
    flex-direction: column;
    /* ❌ bỏ overflow-y: auto ở đây */
    overflow: visible; /* ✅ để panel không trở thành scroll container */
}

.food-planner-panel.active {
    right: 0;
}


.panel-header {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
    padding: 18px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
    gap: 16px; /* 🔥 THÊM khoảng cách giữa title và nút */
}

.panel-header h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
    flex: 1; /* 🔥 THÊM: cho phép title chiếm không gian còn lại */
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
    position: relative;        /* ✅ thêm dòng này cho chắc */
    overflow-y: auto;          /* ✅ đây mới là thằng scroll chính */
    padding: 20px;
    padding-top: 10px;
}

/* THAY BẰNG */
.tab-content {
    height: auto;
    min-height: 500px; /* Nếu muốn giữ chiều cao tối thiểu */
}

.food-planner-panel .tab-content {
    height: auto !important;
    max-height: none !important;
    min-height: 0 !important;
}

.food-planner-panel .tab-content.active {
    height: auto !important;
    display: block !important;
}

/* 🔥 BẮT BUỘC: bỏ overflow trên tab-content trong panel
   để sticky dùng scroll của .panel-content */
.food-planner-panel .tab-content,
.food-planner-panel .tab-content.active {
    overflow: visible !important;
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
    align-items: stretch; /* 🔥 Thay đổi từ center → stretch */
    justify-content: space-between;
    gap: 16px;
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 2px solid #E9ECEF;
    box-sizing: border-box; /* 🔥 THÊM dòng này */
}

.time-picker-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0; /* 🔥 THÊM dòng này để tránh overflow */
    box-sizing: border-box;
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
    width: 100%; /* 🔥 THÊM dòng này */
    box-sizing: border-box; /* 🔥 THÊM dòng này */
    max-width: 100%; /* 🔥 THÊM dòng này để chặn overflow */
}

.time-input {
    width: 52px;
    height: 48px;
    padding: 0 !important;
    margin: 0;
    border: 2px solid #FF6B35;
    border-radius: 10px;
    font-size: 18px;
    font-weight: 700;
    text-align: center;
    background: white;
    color: #FF6B35;
    outline: none;
    transition: all 0.2s ease;
    box-sizing: border-box; /* 🔥 THÊM DÒNG NÀY */
    line-height: 44px;
}

/* 🔥 Override input[type="number"] mặc định */
input.time-input[type="number"] {
    padding: 0 !important;
    padding-block: 0 !important;
    padding-inline: 0 !important;
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
    display: none;
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

/* 🔥 CARD VÀNG GOLD CHO KHU ẨM THỰC & MICHELIN - GIỐNG CARD GỢI Ý */
.meal-card-vertical.gold-card {
    background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%) !important;
    border: 3px dashed #FFB84D !important;
    box-shadow: 
        0 6px 20px rgba(255, 184, 77, 0.25),
        0 2px 8px rgba(255, 184, 77, 0.15) !important;
    position: relative;
    overflow: hidden;
}

/* ✨ HOVER STATE */
.meal-card-vertical.gold-card:hover {
    border-color: #FFA500 !important;
    box-shadow: 
        0 8px 28px rgba(255, 165, 0, 0.35),
        0 4px 12px rgba(255, 184, 77, 0.25) !important;
    transform: translateY(-4px);
}

/* 📝 PHẦN TIÊU ĐỀ */
.meal-card-vertical.gold-card .meal-title-vertical {
    border-bottom: 2px solid rgba(255, 184, 77, 0.2) !important;
}

/* 📦 PHẦN THÔNG TIN QUÁN */
.meal-card-vertical.gold-card .place-info-vertical {
    background: #FFFEF5 !important;
    border: 1px solid rgba(255, 184, 77, 0.2) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
}

/* 🏷️ TÊN QUÁN */
.meal-card-vertical.gold-card .place-name-vertical {
    color: #FF6B35 !important;
    font-weight: 700 !important;
}

/* 📊 META ITEMS */
.meal-card-vertical.gold-card .meta-item-vertical {
    background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%) !important;
    border: 1px solid #FFD699 !important;
    color: #8B6914 !important;
    font-weight: 600 !important;
}

/* 🔧 EDIT MODE */
.meal-card-vertical.gold-card.edit-mode {
    background: linear-gradient(135deg, #FFF9E6 0%, #FFEFC7 100%) !important;
    border-color: #FFB84D !important;
    border-style: solid !important;
}

/* 🎆 HIỆU ỨNG KHI DRAG/DROP */
.meal-card-vertical.gold-card.just-dropped,
.meal-card-vertical.gold-card.repositioned {
    animation: goldPulse 1.5s ease-in-out;
}

@keyframes goldPulse {
    0%, 100% {
        background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
        border-color: #FFB84D;
        box-shadow: 0 0 0 0 rgba(255, 184, 77, 0);
    }
    25% {
        background: linear-gradient(135deg, #FFE5B3 0%, #FFD699 100%);
        border-color: #FFA500;
        box-shadow: 0 0 0 8px rgba(255, 184, 77, 0.3);
    }
    50% {
        background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
        border-color: #FFB84D;
        box-shadow: 0 0 0 0 rgba(255, 184, 77, 0);
    }
    75% {
        background: linear-gradient(135deg, #FFE5B3 0%, #FFD699 100%);
        border-color: #FFA500;
        box-shadow: 0 0 0 8px rgba(255, 184, 77, 0.3);
    }
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
    width: 60px;
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
    min-width: 40px;      /* bé lại */
    height: 40px;         /* bé lại */
    border-radius: 50%;   /* giữ hình tròn */
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0;           /* quan trọng: bỏ padding để nút không bị hình bầu dục */
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
    font-size: 14px;      /* nhỏ lại cho hợp kích thước */
    font-weight: 700;
    position: relative;
    overflow: hidden;
}

/* mini bubble chỉ dùng trong meal card */
.meal-actions .action-btn.mini{
  width: 34px;
  height: 34px;
  min-width: 34px;
}

.meal-actions .action-btn.mini .btn-icon{
  font-size: 18px;
  line-height: 1;
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
/* 🔥 STYLE ĐẶC BIỆT CHO NÚT THOÁT */
.action-btn[onclick*="exitSharedPlanView"]:hover {
    background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%) !important;
    box-shadow: 0 8px 24px rgba(231, 76, 60, 0.4) !important;
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
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
}

.action-btn.share:hover {
    background: linear-gradient(135deg, #FFB84D 0%, #FF9F2D 100%);
    box-shadow: 0 8px 24px rgba(255, 184, 77, 0.4);
}

/* ========== SCHEDULE HEADER ========== */
.schedule-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    background: white;
    z-index: 100; /* 🔥 TĂNG Z-INDEX */
    padding: 16px 20px;
    border-bottom: 2px solid #FFE5D9;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    margin: 0;
    margin-bottom: 0 !important;
}

/* 🔥 ĐẢM BẢO PANEL CONTENT KHÔNG CÓ PADDING TOP */
.panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 0; /* 🔥 BỎ PADDING TOP */
    padding-bottom: 20px; /* 🔥 CHỈ GIỮ PADDING BOTTOM */
}

/* 🔥 THÊM PADDING CHO NỘI DUNG BÊN TRONG */
.filters-wrapper-new,
.saved-plans-section,
#planResult {
    margin: 20px; /* 🔥 THÊM MARGIN CHO CÁC PHẦN TỬ CON */
}

/* 🔥 TIMELINE CONTAINER KHÔNG CẦN PADDING TOP */
.timeline-container {
    position: relative;
    padding: 0 0 20px 0; /* 🔥 BỎ PADDING TOP */
    margin-top: 0; /* 🔥 BỎ MARGIN TOP */
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
.meal-title-input,
.time-input-inline {
    padding: 6px 10px; /* 🔥 SỬA: Tăng padding */
    border: 2px solid #FFE5D9;
    border-radius: 6px;
    font-size: 14px; /* 🔥 SỬA: Tăng font */
    font-weight: 600;
    outline: none;
    text-align: center;
    background: white;
    line-height: 1.5; /* 🔥 THÊM */
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
    top: 65%;
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
    box-shadow: none;
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
    right: 30% !important; /* ✅ LỒI RA BÊN TRÁI PANEL */
    box-shadow: -6px 0 20px rgba(255, 107, 53, 0.4);
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

/* ========== CUSTOM SCROLLBAR CHO PANEL ========== */
.panel-content::-webkit-scrollbar {
    width: 6px;
}

.panel-content::-webkit-scrollbar-track {
    background: transparent; /* Nền thanh cuộn trong suốt */
}

.panel-content::-webkit-scrollbar-thumb {
    /* Màu cam nhạt mờ, phù hợp với theme Food Planner */
    background: rgba(255, 107, 53, 0.3);
    border-radius: 3px;
    transition: background 0.3s ease;
}

.panel-content::-webkit-scrollbar-thumb:hover {
    /* Đậm hơn khi hover */
    background: rgba(255, 107, 53, 0.6);
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

/* ========== CUSTOM SCROLLBAR CHO SAVED PLANS LIST ========== */
.saved-plans-list.open {
    scrollbar-width: thin; /* Firefox */
    scrollbar-color: rgba(255, 107, 53, 0.6) transparent;
}

.saved-plans-list.open::-webkit-scrollbar {
    width: 6px; /* muốn mảnh hơn nữa thì chỉnh 4px */
}

.saved-plans-list.open::-webkit-scrollbar-track {
    background: transparent;
}

.saved-plans-list.open::-webkit-scrollbar-thumb {
    background: rgba(255, 107, 53, 0.3);
    border-radius: 3px;
    transition: background 0.3s ease;
}

.saved-plans-list.open::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 107, 53, 0.6);
}


/* ===== Nút đề xuất: ép buộc tròn 100% ===== */
/* ========== FIX NÚT ĐỀ XUẤT TRÒN Y NHƯ NÚT EDIT ========== */
#suggestionsBtn {
    width: 40px !important;
    height: 40px !important;

    min-width: 40px !important;
    padding: 0 !important;
    border-radius: 50% !important;

    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;

    background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;

    cursor: pointer;
}

.suggestions-wrapper {
    position: relative;
    width: 40px;
    height: 40px;
    display: none; /* ẩn mặc định */
}

.suggestions-wrapper .notif-dot {
    position: absolute;
    bottom: 0px;   /* Kéo sát vào mép dưới */
    right: 1px;    /* Kéo sát vào mép phải */
    width: 10px;
    height: 10px;
    background: #00c853;
    border-radius: 50%;
    border: 2px solid white;
    animation: notif-blink 0.9s infinite ease-in-out;
    box-shadow: 0 0 4px rgba(0, 200, 83, 0.6);
    z-index: 9999;
}

/* Nhấp nháy */
@keyframes notif-blink {
    0%   { transform: scale(1); opacity: 1; }
    50%  { transform: scale(1.35); opacity: 1; }  /* giữ opacity để không “mất màu” */
    100% { transform: scale(1); opacity: 1; }
}

#suggestionCount { display: none !important; }

.action-btn.icon-only{
  width: 40px;           /* chỉnh bằng size nút edit của bạn */
  height: 40px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.action-btn.icon-only.mini{
  width: 34px;
  height: 34px;
}

.action-btn.icon-only.mini svg{
  width: 18px;
  height: 18px;
}

.action-btn.icon-only.mini .btn-icon{
  font-size: 18px;
  line-height: 1;
}

/* spinner rotate */
.btn-spin{
  animation: btnSpin 1s linear infinite;
}
@keyframes btnSpin { to { transform: rotate(360deg); } }

.action-btn.icon-only svg{
  width: 20px;
  height: 20px;
}

/* Ẩn nhưng vẫn tồn tại (screen-reader vẫn đọc được) */
.sr-only{
  position: absolute !important;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ===== Radius card (planner) ===== */
.planner-radius-card{
  display:flex; align-items:center; justify-content:space-between;
  gap:12px; padding:14px 16px; margin: 0 0 16px;
  background:#fff; border:1px solid #FFE5D9; border-radius:16px;
  box-shadow: 0 6px 18px rgba(0,0,0,.06);
}

.planner-radius-meta{ flex:1; min-width:0; display:flex; flex-direction:column; gap:6px; }
.planner-radius-title-row{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.planner-radius-icon{ font-size:16px; line-height:1; }
.planner-radius-title{ font-size:14px; font-weight:900; color:#1f2937; }
.planner-radius-badge{
  font-size:12px; font-weight:800; color:#B45309;
  background:#FFF7ED; border:1px solid #FED7AA;
  padding:2px 8px; border-radius:999px; white-space:nowrap;
}

.planner-radius-hint{ font-size:12px; color:#6b7280; line-height:1.3; }
.planner-radius-actions{ display:flex; flex-direction:column; align-items:flex-end; gap:8px; }
.planner-radius-value{ font-size:22px; font-weight:950; color:#FF6B35; line-height:1; }
.planner-radius-value span{ font-size:14px; font-weight:900; margin-left:4px; color:#FB923C; }
.planner-radius-btn{
  border:none; cursor:pointer; white-space:nowrap;
  padding:10px 12px; border-radius:12px;
  font-size:13px; font-weight:900; color:#fff;
  background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
  box-shadow: 0 6px 16px rgba(255, 107, 53, .25);
}

.planner-radius-btn:active{ transform: translateY(1px); }

.planner-budget-card{
  display:flex; align-items:center; justify-content:space-between;
  gap:12px; padding:14px 16px; margin: 0 0 16px; /* full width */
  background: linear-gradient(135deg, rgba(255,107,53,.10) 0%, rgba(255,142,83,.08) 100%);
  border:1px solid #FFE5D9;
  border-radius:16px;
  box-shadow: 0 6px 18px rgba(255,107,53,.10);
}

.planner-budget-value .budget-unit{
  font-size:14px;
  font-weight:900;
  margin-left:4px;
  color:#FB923C; /* giống km */
}

.planner-budget-left{ display:flex; align-items:center; gap:12px; min-width:0; }
.planner-budget-icon{
  width:36px; height:36px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  background: rgba(255,107,53,.14);
  border: 1px solid rgba(255,107,53,.18);
  font-size:18px; line-height:1;
}

.planner-budget-meta{ display:flex; flex-direction:column; gap:4px; min-width:0; }
.planner-budget-title{ font-size:14px; font-weight:900; color:#1f2937; line-height:1.1; }
.planner-budget-hint{ font-size:12px; color:#6b7280; line-height:1.2; }

.planner-budget-right{ display:flex; flex-direction:column; align-items:flex-end; gap:6px; }
.planner-budget-value{ font-size:22px; font-weight:950; color:#FF6B35; line-height:1; white-space:nowrap; }

.planner-budget-pill,
.planner-budget-note{
  font-size:12px; font-weight:800; color:#B45309;
  background:#FFF7ED; border:1px solid #FED7AA;
  padding:2px 8px; border-radius:999px; white-space:nowrap;
}
.planner-budget-pill{ margin-right:8px; font-weight:900; }

@media (max-width: 420px){
  .planner-budget-card{ align-items:flex-start; }
  .planner-budget-right{ align-items:flex-start; }
}

/* ========== SUGGESTIONS PANEL STYLES ========== */
.suggestion-card-item:hover {
    transform: translateY(-2px);
    border-color: #FFB084;
    box-shadow: 0 8px 24px rgba(255, 126, 75, 0.25);
}

.sug-btn-detail:hover {
    background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%) !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 24px rgba(255, 126, 75, 0.7);
}

.sug-btn-approve:hover {
    background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%) !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 24px rgba(76, 175, 80, 0.5);
}

.sug-btn-reject:hover {
    background: linear-gradient(135deg, #F87171 0%, #EF4444 100%) !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 24px rgba(239, 68, 68, 0.5);
}

/* ========== SUGGESTIONS CARD ANIMATION ========== */
.suggestion-card-item {
    opacity: 0;
    transform: translateX(-100%);
    animation: slideInFromLeft 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes slideInFromLeft {
    0% {
        opacity: 0;
        transform: translateX(-100%);
    }
    100% {
        opacity: 1;
        transform: translateX(0);
    }
}

.suggestion-card-item:hover {
    transform: translateY(-2px);
    border-color: #FFB084;
    box-shadow: 0 8px 24px rgba(255, 126, 75, 0.25);
}

.sug-btn-detail:hover {
    background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%) !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 24px rgba(255, 126, 75, 0.7);
}

.sug-btn-approve:hover {
    background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%) !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 24px rgba(76, 175, 80, 0.5);
}

.sug-btn-reject:hover {
    background: linear-gradient(135deg, #F87171 0%, #EF4444 100%) !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 24px rgba(239, 68, 68, 0.5);
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
        <span style="font-size: 26px;" data-translate="food_planning_title">📋 Lên kế hoạch ăn uống</span>
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
                            
                            <div class="time-arrow"></div>
                            
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
                        <span class="btn-text">Tạo kế hoạch tự động</span>
                    </button>
                </div>
                
                <!-- Saved Plans Section -->
                <div class="saved-plans-section" id="savedPlansSection" style="display: block;">
                    <div class="saved-plans-header" onclick="toggleSavedPlans()">
                        <div class="filter-title" style="margin: 0; font-size: 16px; font-weight: 700; color: #FF6B35;">
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
let suggestedMichelin = null; 
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
window.loadedFromSavedPlan = false;
let cachedPendingSuggestionsCount = 0; // Lưu số lượng suggestions pending

const ICON_PENCIL = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
  <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
</svg>`;

const ICON_SPINNER = `
<svg class="btn-spin" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
  <path d="M12 4a8 8 0 1 0 8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>`;

// Themes data
const themes = {
    'street_food': { name: 'Ẩm thực đường phố', icon: '🍜' },
    'seafood': { name: 'Hải sản', icon: '🦞' },
    'coffee_chill': { name: 'Giải khát', icon: '☕' },
    'luxury_dining': { name: 'Nhà hàng sang trọng', icon: '🍽️' },
    'asian_fusion': { name: 'Ẩm thực châu Á', icon: '🍱' },
    'vegetarian': { name: 'Món chay', icon: '🥗' },
    'dessert_bakery': { name: 'Tráng miệng', icon: '🍰' },
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
            title: 'Địa điểm nổi bật',
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

    // Chọn sẵn 3 theme khi lần đầu mở
    setTimeout(() => {
        const defaultThemes = ['coffee_chill', 'dessert_bakery', 'food_street'];
        
        defaultThemes.forEach(themeKey => {
            if (!selectedThemes.includes(themeKey)) {
                selectedThemes.push(themeKey);
            }
            
            const card = document.querySelector(`[data-theme="${themeKey}"]`);
            if (card) {
                card.classList.add('selected');
            }
        });
    }, 100);
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
    
    // 🔥 LỌC TRÙNG LẶP - CHỈ GIỮ 1 PLAN DUY NHẤT
    const uniquePlans = [];
    const seenIds = new Set();
    
    plans.forEach(plan => {
        if (!seenIds.has(plan.id)) {
            seenIds.add(plan.id);
            uniquePlans.push(plan);
        }
    });
    
    console.log('🔍 Original plans:', plans.length, 'Unique plans:', uniquePlans.length);
    
    // ✅ Nếu có plans → thêm từng plan vào html
    uniquePlans.forEach((plan, index) => {
        // 🔥 CODE FIX TIMEZONE
        const rawCreated = plan.created_at || plan.savedAt || null;

        let dateStr = 'Không rõ ngày';
        let timeStr = '';

        if (rawCreated) {
            try {
                let isoString = rawCreated;
                
                if (isoString.includes(' ') && !isoString.includes('T')) {
                    isoString = isoString.replace(' ', 'T');
                }
                
                const parts = isoString.match(/(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2}):(\d{2})?/);
                
                if (!parts) {
                    throw new Error('Invalid date format');
                }
                
                const year = parseInt(parts[1]);
                const month = parseInt(parts[2]) - 1;
                const day = parseInt(parts[3]);
                let hour = parseInt(parts[4]);
                const minute = parseInt(parts[5]);
                const second = parseInt(parts[6] || '0');
                
                hour += 7;
                if (hour >= 24) {
                    hour -= 24;
                }
                
                const date = new Date(year, month, day, hour, minute, second);

                if (!isNaN(date.getTime())) {
                    const dd = String(date.getDate()).padStart(2, '0');
                    const mm = String(date.getMonth() + 1).padStart(2, '0');
                    const yyyy = date.getFullYear();
                    dateStr = `${dd}/${mm}/${yyyy}`;
                    
                    const hh = String(date.getHours()).padStart(2, '0');
                    const min = String(date.getMinutes()).padStart(2, '0');
                    timeStr = `${hh}:${min}`;
                }
            } catch (error) {
                console.error('❌ Lỗi parse datetime:', error, 'Input:', rawCreated);
                dateStr = 'Không rõ ngày';
                timeStr = '';
            }
        }
        
        // 🔥 THÊM BADGE CHO SHARED PLAN
        const sharedBadge = plan.is_shared ? 
            `<span style="font-size: 10px; background: #2196F3; color: white; padding: 2px 6px; border-radius: 8px; margin-left: 6px;">Chia sẻ</span>` 
            : '';

        html += `
            <div class="saved-plan-item" onclick="loadSavedPlans(${plan.id})">
                <div class="saved-plan-info">
                    <div class="saved-plan-name">${plan.name}${sharedBadge}</div>
                    <div class="saved-plan-date">📅 ${dateStr} • ⏰ ${timeStr}</div>
                    ${plan.is_shared ? `<div style="font-size: 11px; color: #2196F3; margin-top: 4px;">👤 ${plan.owner_username}</div>` : ''}
                </div>
                ${!plan.is_shared ? `
                    <button class="delete-plan-btn" onclick="event.stopPropagation(); deleteSavedPlan(${plan.id})" title="Xóa lịch trình">×</button>
                ` : `
                    <button class="delete-plan-btn" onclick="event.stopPropagation(); leaveSharedPlan(${plan.id})" title="Ngừng xem plan này" style="background: #FF9800;">×</button>
                `}
            </div>
        `;
    });

    listDiv.innerHTML = html;
}

// ========== TOGGLE SAVED PLANS - SỬA LẠI ĐƠN GIẢN HƠN ==========
function toggleSavedPlans() {
    const listDiv = document.getElementById('savedPlansList');
    const arrow = document.getElementById('savedPlansArrow');
    
    if (!listDiv || !arrow) {
        console.error('❌ Không tìm thấy savedPlansList hoặc savedPlansArrow');
        return;
    }
    
    // 🔥 TOGGLE CLASS 'open'
    const isOpen = listDiv.classList.contains('open');
    
    if (isOpen) {
        // Đang mở → đóng lại
        listDiv.classList.remove('open');
        arrow.style.transform = 'rotate(0deg)';
        console.log('✅ Đóng saved plans');
    } else {
        // Đang đóng → mở ra
        listDiv.classList.add('open');
        arrow.style.transform = 'rotate(180deg)';
        console.log('✅ Mở saved plans');
        
        // 🔥 ĐÓNG FILTERS nếu đang mở
        const filtersWrapper = document.querySelector('.filters-wrapper-new');
        if (filtersWrapper && !filtersWrapper.classList.contains('collapsed')) {
            const filterHeader = document.querySelector('.section-header');
            if (filterHeader && typeof filterHeader.click === 'function') {
                // Không làm gì - giữ nguyên filters
            }
        }
    }
}

// ========== SAVE PLAN - Lưu vào Database Django ==========
async function savePlan() {
    if (!currentPlan) return;

    // 🔥 KIỂM TRA ĐĂNG NHẬP
    const checkAuth = await fetch('/api/check-auth/');
    const authData = await checkAuth.json();
    
    if (!authData.is_logged_in) {
        alert('⚠️ Bạn cần đăng nhập để lưu lịch trình!');
        window.location.href = '/accounts/login/';
        return;
    }

    // 🔥 LƯU THỨ TỰ VỀ DOM
    const mealItems = document.querySelectorAll('.meal-item');
    const planArray = [];
    
    mealItems.forEach(item => {
        const mealKey = item.dataset.mealKey;
        if (mealKey && currentPlan[mealKey]) {
            // Cập nhật thời gian từ input
            const hourInput = item.querySelector('.time-input-hour[data-meal-key="' + mealKey + '"]');
            const minuteInput = item.querySelector('.time-input-minute[data-meal-key="' + mealKey + '"]');
            
            if (hourInput && minuteInput) {
                const hour = hourInput.value.padStart(2, '0');
                const minute = minuteInput.value.padStart(2, '0');
                currentPlan[mealKey].time = `${hour}:${minute}`;
            }
            
            // Cập nhật TITLE từ input
            const titleInput = item.querySelector('input[onchange*="updateMealTitle"]');
            if (titleInput && titleInput.value) {
                currentPlan[mealKey].title = titleInput.value;
            }
            
            planArray.push({
                key: mealKey,
                data: JSON.parse(JSON.stringify(currentPlan[mealKey]))
            });
        }
    });

    // ✅ KIỂM TRA PLAN CÓ DỮ LIỆU KHÔNG
    if (planArray.length === 0) {
        alert('⚠️ Lịch trình trống! Hãy thêm ít nhất 1 quán trước khi lưu.');
        return;
    }

    currentPlan._order = planArray.map(x => x.key);

    // Xóa quán gợi ý trước khi lưu
    suggestedFoodStreet = null;
    suggestedMichelin = null;

    // 🔥 LẤY TÊN TỪ DOM
    const titleElement = document.querySelector('.schedule-title span[contenteditable]');
    let currentDisplayName = titleElement ? titleElement.textContent.trim() : (window.currentPlanName || '');
    
    // ✅ XỬ LÝ TÊN PLAN
    if (!currentDisplayName || currentDisplayName === 'Lịch trình của bạn') {
        currentDisplayName = prompt('Đặt tên cho kế hoạch:', `Kế hoạch ${new Date().toLocaleDateString('vi-VN')}`);
        if (!currentDisplayName || currentDisplayName.trim() === '') {
            alert('⚠️ Bạn phải đặt tên để lưu lịch trình!');
            return;
        }
        currentDisplayName = currentDisplayName.trim();
    }

    // 🔥 GỌI API DJANGO ĐỂ LƯU
    try {
        const response = await fetch('/api/accounts/food-plan/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: currentDisplayName,
                plan_data: planArray
            })
        });

                const result = await response.json();

        if (result.status === 'success') {
            alert('✅ Đã lưu kế hoạch thành công!');
            window.currentPlanName = currentDisplayName;
            
            // ✅ TẮT EDIT MODE SAU KHI LƯU
            if (isEditMode) {
                toggleEditMode();
            }
            
            // 🔥 LẤY ID PLAN VỪA LƯU (NẾU API TRẢ VỀ)
            let newPlanId = null;
            if (result.plan && result.plan.id) {
                newPlanId = result.plan.id;
            } else if (result.plan_id) {
                newPlanId = result.plan_id;
            }

            if (newPlanId) {
                currentPlanId = newPlanId;
            }
            
            // ✅ LOAD LẠI DANH SÁCH + MỞ LUÔN PLAN VỪA LƯU
            if (newPlanId) {
                // forceReload = true để không bị nhánh "click lại cùng planId" đóng plan
                await loadSavedPlans(newPlanId, true);
            } else {
                // fallback: nếu API chưa trả id thì giữ behaviour cũ
                await loadSavedPlans();
            }

        } else {
            alert('❌ Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Error saving plan:', error);
        alert('❌ Không thể lưu lịch trình!');
    }
}

// ========== LOAD SAVED PLANS ==========
async function loadSavedPlans(planId, forceReload = false) {
    try {

        // 🧹 ĐÓNG LỊCH TRÌNH NẾU BẤM LẠI CÙNG 1 PLAN ĐANG MỞ
        if (
            !forceReload &&                      // không phải load lại bắt buộc
            typeof planId !== 'undefined' &&
            planId !== null &&
            currentPlanId !== null &&
            String(currentPlanId) === String(planId)
        ) {
            console.log('🧹 Đóng lịch trình hiện tại vì click lại cùng planId:', planId);

            // Reset trạng thái liên quan tới plan
            isViewingSharedPlan = false;
            isSharedPlan = false;
            sharedPlanOwnerId = null;
            sharedPlanOwnerName = '';
            hasEditPermission = false;

            currentPlan = null;
            currentPlanId = null;
            isEditMode = false;
            waitingForPlaceSelection = null;
            window.currentPlanName = null;
            window.loadedFromSavedPlan = false;
            window.originalSharedPlanData = null; // 🔥 MỚI: Xóa original data khi đóng plan

            // Xóa route + clear khu vực lịch trình
            clearRoutes();
            const resultDiv = document.getElementById('planResult');
            if (resultDiv) {
                resultDiv.innerHTML = '';
            }

            // Hiện lại bộ lọc (filters)
            const filtersWrapper = document.querySelector('.filters-wrapper-new');
            if (filtersWrapper) {
                filtersWrapper.style.display = 'block';
            }

            // ⭐ HIỆN LẠI TẤT CẢ MARKER CÁC QUÁN (từ kết quả search trước đó)
            if (
                typeof displayPlaces === 'function' &&
                typeof allPlacesData !== 'undefined' &&
                Array.isArray(allPlacesData) &&
                allPlacesData.length > 0
            ) {
                // false = không zoom lại map, chỉ vẽ marker
                displayPlaces(allPlacesData, false);
            }

            // 👉 Không gọi API nữa, coi như "đóng lịch trình"
            return;
        }

        // 🔥 GỌI API DJANGO - BÂY GIỜ TRẢ VỀ CẢ SHARED PLANS
        const response = await fetch('/api/accounts/food-plan/list/');
        const data = await response.json();
        
        if (data.status !== 'success') {
            console.error('Lỗi load plans:', data.message);
            return;
        }
        
        const savedPlans = data.plans || [];
        
        // ✅ THÊM: GỌI API LẤY SHARED PLANS
        let sharedPlans = [];
        try {
            const sharedResponse = await fetch('/api/accounts/food-plan/shared/');
            const sharedData = await sharedResponse.json();
            if (sharedData.status === 'success') {
                sharedPlans = sharedData.shared_plans || [];
            }
        } catch (error) {
            console.error('Error loading shared plans:', error);
        }
        
        const section = document.getElementById('savedPlansSection');
        
        // ✅ LUÔN HIỂN THỊ SECTION
        section.style.display = 'block';
        
        
        // ✅ GỘP 2 DANH SÁCH
        const allPlans = [...savedPlans, ...sharedPlans];
        
        displaySavedPlansList(allPlans);
        
        // Nếu có planId, load plan đó
        if (planId) {
            const plan = allPlans.find(p => p.id === planId);
            
            if (plan) {
                currentPlan = {};
                
                // 🔥 XỬ LÝ SHARED PLAN
                if (plan.is_shared) {
                    isSharedPlan = true;
                    isViewingSharedPlan = true;
                    sharedPlanOwnerId = plan.owner_id;
                    sharedPlanOwnerName = plan.owner_username;
                    hasEditPermission = (plan.permission === 'edit');

                    // 🔥 MỚI: LƯU BẢN SAO ORIGINAL PLAN
                    window.originalSharedPlanData = null; // Reset trước
                    
                    // 🔥 FIX: THÊM AWAIT ĐỂ ĐỢI PENDING CHECK HOÀN TẤT
                    if (hasEditPermission) {
                        await checkPendingSuggestions(planId);
                        console.log('✅ Đã check pending suggestion sau reload:', hasPendingSuggestion);
                    }
                } else {
                    isSharedPlan = false;
                    isViewingSharedPlan = false; // 🔥 THÊM DÒNG NÀY
                    sharedPlanOwnerId = null;
                    sharedPlanOwnerName = '';
                    hasEditPermission = false;
                }
                        
                        // 🔥 CHUYỂN ĐỔI TỪ plan_data
                    const planData = plan.plan_data;
                    if (Array.isArray(planData)) {
                        const orderList = [];
                        planData.forEach(item => {
                            currentPlan[item.key] = JSON.parse(JSON.stringify(item.data));
                            orderList.push(item.key);
                        });
                        currentPlan._order = orderList;
                    } else {
                        Object.assign(currentPlan, planData);
                    }

                    // 🔥 MỚI: LƯU BẢN SAO ORIGINAL (SAU KHI PARSE)
                    if (plan.is_shared && hasEditPermission) {
                        window.originalSharedPlanData = JSON.parse(JSON.stringify(currentPlan));
                        console.log('💾 Đã lưu original shared plan data');
                    }

                        currentPlanId = planId;
                        window.currentPlanName = plan.name;
                        window.loadedFromSavedPlan = true;
                        isEditMode = false;
                        suggestedFoodStreet = null;
                        suggestedMichelin = null;
                        displayPlanVertical(currentPlan, false);

                        if (!plan.is_shared) {
                            // 🔥 AWAIT để đợi API hoàn thành TRƯỚC KHI render
                            await checkPendingSuggestions(planId);
                        } else if (hasEditPermission) {
                            // 🔥 AWAIT cho shared plan có quyền edit
                            await checkPendingSuggestions(planId);
                        }

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
                        checkPendingSuggestions(planId);
                    }
                }
            } catch (error) {
                console.error('Error loading plans:', error);
        }
    }

// ========== HELPER: CONVERT UTC TO LOCAL TIMEZONE ==========
function formatDateTimeWithTimezone(datetimeString) {
    if (!datetimeString) return 'Không rõ ngày';
    
    try {
        // Parse ISO string
        let date;
        
        // Nếu có 'T' thì đã đúng format ISO
        if (datetimeString.includes('T')) {
            date = new Date(datetimeString);
        } else {
            // Nếu format 'YYYY-MM-DD HH:MM:SS' thì thêm 'T'
            const normalized = datetimeString.replace(' ', 'T');
            date = new Date(normalized);
        }
        
        // 🔥 BỎ PHẦN CỘNG 7 GIỜ - CHỈ FORMAT LẠI
        // JavaScript Date tự động convert sang timezone local rồi
        
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hour = String(date.getHours()).padStart(2, '0');
        const minute = String(date.getMinutes()).padStart(2, '0');
        const second = String(date.getSeconds()).padStart(2, '0');
        
        return `${hour}:${minute}:${second} ${day}/${month}/${year}`;
        
    } catch (error) {
        console.error('❌ Lỗi format datetime:', error);
        return 'Lỗi định dạng';
    }
}
// ========== DELETE PLAN - Xóa từ Database Django ==========
async function deleteSavedPlan(planId) {
    if (!confirm('Bạn có chắc muốn xóa kế hoạch này?')) return;
    
    try {
        const response = await fetch(`/api/accounts/food-plan/delete/${planId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.status === 'success') {
            alert('✅ Đã xóa kế hoạch!');
            
            if (currentPlanId === planId) {
                currentPlanId = null;
                currentPlan = null;
                document.getElementById('planResult').innerHTML = '';
                isEditMode = false;
            }
            
            await loadSavedPlans();
        } else {
            alert('❌ Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Error deleting plan:', error);
        alert('❌ Không thể xóa lịch trình!');
    }
}
// ========== DELETE PLAN - Xóa từ Database Django ==========
async function deleteSavedPlan(planId) {
    if (!confirm('Bạn có chắc muốn xóa kế hoạch này?')) return;
    
    try {
        const response = await fetch(`/api/accounts/food-plan/delete/${planId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.status === 'success') {
            alert('✅ Đã xóa kế hoạch!');
            
            if (currentPlanId === planId) {
                currentPlanId = null;
                currentPlan = null;
                document.getElementById('planResult').innerHTML = '';
                isEditMode = false;
            }
            
            await loadSavedPlans();
        } else {
            alert('❌ Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Error deleting plan:', error);
        alert('❌ Không thể xóa lịch trình!');
    }
}

// ========== LEAVE SHARED PLAN ==========
async function leaveSharedPlan(planId) {
    if (!confirm('Bạn có chắc muốn ngừng xem lịch trình này? Lịch trình sẽ biến mất khỏi danh sách của bạn')) return;
    
    try {
        const response = await fetch(`/api/accounts/food-plan/leave-shared/${planId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.status === 'success') {
            alert('✅ Đã ngừng xem lịch trình!');
            
            if (currentPlanId === planId) {
                currentPlanId = null;
                currentPlan = null;
                document.getElementById('planResult').innerHTML = '';
                isEditMode = false;
                clearRoutes();
            }
            
            await loadSavedPlans();
        } else {
            alert('❌ Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Error leaving shared plan:', error);
        alert('❌ Không thể rời khỏi lịch trình!');
    }
}
// ========== TẠO LỊCH TRÌNH TRỐNG MỚI ==========
function createNewEmptyPlan() {
    isViewingSharedPlan = false;
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
    window.loadedFromSavedPlan = true;
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
            clearRoutes();
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
        // ⬅⬅ RESET DOT NGAY LẬP TỨC (ngăn nháy)
        const btn = document.getElementById("suggestionsBtn");
        const dot = document.getElementById("suggestionDot");
        const count = document.getElementById("suggestionCount");

        if (btn) btn.style.display = "none";
        if (dot) dot.style.display = "none";
        if (count) count.textContent = "0";

        // ⬅ Render giao diện
        displayPlanVertical(currentPlan, isEditMode);

        // ⬅ Sau khi render xong → gọi API update lại đúng trạng thái
        if (currentPlanId) checkPendingSuggestions(currentPlanId);
    }
    
    // 🔥 HIỂN THỊ NÚT NGAY LẬP TỨC KHI THOÁT EDIT MODE
    if (!isEditMode && !isSharedPlan && currentPlanId) {
        // Hiển thị nút ngay từ cache
        setTimeout(() => {
            showSuggestionsButtonImmediately();
        }, 100); // 100ms để đợi DOM render xong
        
        // Sau đó fetch lại để cập nhật chính xác
        setTimeout(() => {
            checkPendingSuggestions(currentPlanId);
        }, 300);
    }
}
// ========== OPEN/CLOSE PLANNER ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 DOMContentLoaded fired');
    
    const foodPlannerBtn = document.getElementById('foodPlannerBtn');
    
    if (foodPlannerBtn) {
        console.log('✅ Tìm thấy foodPlannerBtn');
        
        foodPlannerBtn.addEventListener('click', function(e) {
            console.log('🔍 Food Planner Button clicked');
            e.preventDefault();
            e.stopPropagation();
            
            if (isPlannerOpen) {
                closeFoodPlanner();
            } else {
                openFoodPlanner();
            }
        });
    } else {
        console.error('❌ Không tìm thấy foodPlannerBtn');
    }
});

function openFoodPlanner() {
    console.log('🚀 Opening Food Planner.');
    
    const panel = document.getElementById('foodPlannerPanel');
    console.log('Panel element:', panel);
    
    if (!panel) {
        console.error('❌ Không tìm thấy foodPlannerPanel');
        return;
    }
    
    panel.classList.add('active');
    isPlannerOpen = true;
    loadSavedPlans();
    
    // 🔥 Nếu đã có currentPlan (và không ở edit mode) thì vẽ lại route + marker theo plan
    setTimeout(() => {
        if (currentPlan && !isEditMode) {
            const hasPlaces = Object.keys(currentPlan)
                .filter(k => k !== '_order')
                .some(k => currentPlan[k] && currentPlan[k].place);
            
            if (hasPlaces) {
                // Vẽ đường đi cho lịch trình
                if (typeof drawRouteOnMap === 'function') {
                    drawRouteOnMap(currentPlan);
                }

                // 🔥 Ẩn marker quán ngoài lịch trình, chỉ giữ quán trong plan
                if (typeof window.showMarkersForPlaceIds === 'function') {
                    window.showMarkersForPlaceIds(currentPlan);
                }
            }
        }
    }, 300);
}


function closeFoodPlanner() {
    const panel = document.getElementById('foodPlannerPanel');
    if (panel) {
        panel.classList.remove('active');
    }

    isPlannerOpen = false;
    isViewingSharedPlan = false;
    window.originalSharedPlanData = null; // 🔥 MỚI: Xóa original data
    // ✅ Cleanup toàn bộ route / drag
    clearRoutes();
    stopAutoScroll();
    disableGlobalDragTracking();
    
    // ✅ Reset drag state
    draggedElement = null;
    window.draggedElement = null;
    lastTargetElement = null;
    lastDragY = 0;

    // ✅ Reset trạng thái chọn quán cho bữa ăn (nếu đang chờ)
    waitingForPlaceSelection = null;
    selectedPlaceForReplacement = null;
    
    // 🔥 ẨN NÚT X KHI ĐÓNG PANEL
    const exitBtn = document.getElementById('exitSharedPlanBtn');
    if (exitBtn) {
        exitBtn.style.display = 'none';
    }

    // 🔥 KHI ĐÓNG FOOD PLANNER → HIỆN LẠI TẤT CẢ MARKER QUÁN BÌNH THƯỜNG
    try {
        // Ưu tiên dùng data search đang có (allPlacesData)
        if (typeof displayPlaces === 'function' &&
            Array.isArray(window.allPlacesData) &&
            window.allPlacesData.length > 0) {

            // false = không đổi zoom, chỉ vẽ lại marker
            displayPlaces(window.allPlacesData, false);
        } else if (typeof loadMarkersInViewport === 'function' && window.map) {
            // Fallback: nếu chưa có allPlacesData thì bật lại lazy-load + load marker
            window.map.on('moveend', loadMarkersInViewport);
            loadMarkersInViewport();
        }
    } catch (e) {
        console.error('❌ Lỗi khi restore marker sau khi đóng Food Planner:', e);
    }
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
// ========== RANDOM LẠI QUÁN GỢI Ý ==========
async function randomSuggestedPlace(themeType) {
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
        
        // 🔥 GIỜ THOẢI MÁI - RANDOM TỪ 0-23 GIỜ
        const randomHour = Math.floor(Math.random() * 24);
        const randomMinute = Math.floor(Math.random() * 60);
        const searchTime = `${randomHour.toString().padStart(2, '0')}:${randomMinute.toString().padStart(2, '0')}`;
        
        const randomSeed = Date.now();
        const url = `/api/food-plan?lat=${userLat}&lon=${userLon}&random=${randomSeed}&start_time=${searchTime}&end_time=${searchTime}&radius_km=${radius}&theme=${themeType}`;
        
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
        console.error(`Lỗi random ${themeType}:`, error);
        return null;
    }
}

// 🔥 HÀM CẬP NHẬT TRỰC TIẾP CARD GỢI Ý (KHÔNG RENDER LẠI TOÀN BỘ)
function updateSuggestedCard(themeType, place) {
    // 🔥 TÌM CARD BẰNG TITLE CỤ THỂ (an toàn hơn icon)
    const titleToFind = themeType === 'food_street' ? 'Khu ẩm thực đêm' : 'Nhà hàng Michelin';
    
    let targetCard = null;
    
    // Tìm tất cả các div có "Gợi ý cho bạn"
    const allSuggestionCards = document.querySelectorAll('#planResult > div');
    
    allSuggestionCards.forEach(card => {
        // 🔥 KIỂM TRA CẢ "Gợi ý" VÀ TITLE CỤ THỂ
        const cardHTML = card.innerHTML;
        if (cardHTML.includes('Gợi ý cho bạn') && cardHTML.includes(titleToFind)) {
            targetCard = card;
            console.log(`✅ Tìm thấy card ${themeType}:`, titleToFind);
        }
    });
    
    if (!targetCard) {
        console.error(`❌ Không tìm thấy card ${themeType}`);
        return;
    }
    
    // Format giờ mở cửa (giữ nguyên code cũ)
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
    
    // 🔥 THÊM ICON VÀO BIẾN
    const cardIcon = themeType === 'food_street' ? '🪔' : '⭐';
    const cardTitle = themeType === 'food_street' ? 'Khu ẩm thực đêm' : 'Nhà hàng Michelin';
    
    // Tạo HTML mới cho card (giữ nguyên phần còn lại)
    const newHTML = `
        <div style="margin-top: 40px; padding: 0 20px;">
            <div style="
                background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
                border: 3px dashed #FFB84D;
                border-radius: 20px;
                padding: 20px;
                position: relative;
                box-shadow: 0 6px 20px rgba(255, 184, 77, 0.25);
                max-width: 100%;
            ">
                
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
                    <span style="font-size: 32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">${cardIcon}</span>
                    <div>
                        <div style="font-size: 16px; font-weight: 700; color: #6B5410; margin-bottom: 4px;">
                            ${cardTitle}
                        </div>
                        <div style="font-size: 13px; color: #8B6914; font-weight: 500;">
                            🕐 ${displayTime}
                        </div>
                    </div>
                </div>
                
                <!-- NỘI DUNG -->
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 16px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                    border: 1px solid rgba(255, 184, 77, 0.2);
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onclick="flyToPlace(${place.lat}, ${place.lon}, '${place.data_id}', '${place.ten_quan.replace(/'/g, "\\'")}')"
                onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.1)';"
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.04)';">
                    <div style="font-weight: 700; color: #FF6B35; margin-bottom: 8px; font-size: 15px; display: flex; align-items: center; gap: 6px;">
                        <span>🍽️</span>
                        <span>${place.ten_quan}</span>
                    </div>
                    <div style="color: #666; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                        📍 ${place.dia_chi}
                    </div>
                    <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px;">
                        <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%); border-radius: 20px; color: #8B6914; font-weight: 600; border: 1px solid #FFD699;">
                            <span style="font-size: 16px;">⭐</span>
                            <strong>${place.rating ? parseFloat(place.rating).toFixed(1) : 'N/A'}</strong>
                        </div>
                        ${place.gia_trung_binh && !['$', '$$', '$$$', '$$$$'].includes(place.gia_trung_binh.trim()) ? `
                            <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%); border-radius: 20px; color: #8B6914; font-weight: 600; border: 1px solid #FFD699;">
                                <span style="font-size: 16px;">💰</span>
                                <strong>${place.gia_trung_binh}</strong>
                            </div>
                        ` : ''}
                    </div>
                    ${place.khau_vi ? `
                        <div style="margin-top: 12px; padding: 8px 12px; background: #FFF5E6; border-left: 3px solid #FFB84D; border-radius: 6px; font-size: 12px; color: #8B6914;">
                            👅 Khẩu vị: ${place.khau_vi}
                        </div>
                    ` : ''}
                </div>
                
                <!-- 2 NÚT -->
                <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: center;">
                    <button onclick="event.stopPropagation(); random${themeType === 'food_street' ? 'FoodStreet' : 'Michelin'}();" style="
                        flex: 1;
                        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(76, 175, 80, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(76, 175, 80, 0.3)';">
                        <span>Đổi quán khác</span>
                    </button>
                    
                    <button onclick="event.stopPropagation(); addSuggestedToSchedule(suggested${themeType === 'food_street' ? 'FoodStreet' : 'Michelin'}, '${themeType}');" style="
                        flex: 1;
                        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(255, 107, 53, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 53, 0.3)';">
                        <span>Thêm vào lịch</span>
                    </button>
                </div>
                
                <!-- FOOTER -->
                <div style="margin-top: 16px; text-align: center; font-size: 13px; color: #8B6914; font-weight: 600;">
                    Nhấn vào card để xem trên bản đồ
                </div>
            </div>
        </div>
    `;
    
    // ✅ THAY THẾ HTML CŨ BẰNG HTML MỚI
    targetCard.outerHTML = newHTML;
    
    console.log(`✅ Đã update card ${themeType}:`, place.ten_quan);
}

// 🔥 HÀM RANDOM LẠI KHU ẨM THỰC
async function randomFoodStreet() {
    const btn = event.target.closest('button');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span style="font-size: 18px;">⏳</span> Đang tìm...';
    }
    
    const newPlace = await randomSuggestedPlace('food_street');
    
    if (newPlace) {
        suggestedFoodStreet = newPlace;
        
        // ✅ CHỈ CẬP NHẬT CARD GỢI Ý - KHÔNG RENDER LẠI TOÀN BỘ
        updateSuggestedCard('food_street', newPlace);
    } else {
        alert('⚠️ Không tìm thấy khu ẩm thực khác trong bán kính này');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span>Đổi quán khác</span>';
        }
    }
}

// 🔥 HÀM RANDOM LẠI MICHELIN
async function randomMichelin() {
    const btn = event.target.closest('button');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span style="font-size: 18px;">⏳</span> Đang tìm...';
    }
    
    // 🔥 RETRY 3 LẦN VỚI GIỜ 18:30
    let newPlace = null;
    for (let attempt = 0; attempt < 3; attempt++) {
        try {
            let userLat, userLon;
            
            if (window.currentUserCoords) {
                userLat = window.currentUserCoords.lat;
                userLon = window.currentUserCoords.lon;
            } else {
                break;
            }
            
            const radiusInput = document.getElementById('radius');
            const radius = radiusInput?.value || window.currentRadius || '10';
            
            const searchTime = '18:30';  // 🔥 CỐ ĐỊNH 18:30
            const randomSeed = Date.now() + attempt * 1000;
            const url = `/api/food-plan?lat=${userLat}&lon=${userLon}&random=${randomSeed}&start_time=${searchTime}&end_time=${searchTime}&radius_km=${radius}&theme=michelin`;
            
            const response = await fetch(url);
            if (!response.ok) continue;
            
            const data = await response.json();
            if (data.error || !data) continue;
            
            for (const key in data) {
                if (key !== '_order' && data[key] && data[key].place) {
                    newPlace = data[key].place;
                    break;
                }
            }
            
            if (newPlace) break;
        } catch (error) {
            console.error('Lỗi retry Michelin:', error);
        }
    }
    
    if (newPlace) {
        suggestedMichelin = newPlace;
        updateSuggestedCard('michelin', newPlace);
    } else {
        alert('⚠️ Không tìm thấy nhà hàng Michelin khác');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span>Đổi quán khác</span>';
        }
    }
}

// 🔥 HÀM THÊM QUÁN GỢI Ý VÀO LỊCH TRÌNH
function addSuggestedToSchedule(suggestedPlace, themeType) {
    if (!suggestedPlace) return;
    
    if (!currentPlan) {
        currentPlan = {};
    }
    
    // Tạo key mới
    const newKey = 'custom_' + Date.now();
    
    // Tính thời gian mới (sau quán cuối 1 tiếng)
    const lastMealTime = getLastMealTime();
    const newTime = addMinutesToTime(lastMealTime, 60);
    
    // Tính khoảng cách từ vị trí trước đó
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
    
    for (let i = allKeys.length - 1; i >= 0; i--) {
        const prevMeal = currentPlan[allKeys[i]];
        if (prevMeal && prevMeal.place) {
            prevLat = prevMeal.place.lat;
            prevLon = prevMeal.place.lon;
            break;
        }
    }
    
    const distance = calculateDistanceJS(prevLat, prevLon, suggestedPlace.lat, suggestedPlace.lon);
    const travelTime = Math.round((distance / 25) * 60);
    
    const arriveTime = new Date(`2000-01-01 ${newTime}`);
    const suggestLeave = new Date(arriveTime.getTime() - travelTime * 60000);
    const suggestLeaveStr = suggestLeave.toTimeString().substring(0, 5);
    
    // Tạo meal mới
    currentPlan[newKey] = {
        time: newTime,
        title: themeType === 'food_street' ? 'Khu ẩm thực' : 'Nhà hàng Michelin',
        icon: themeType === 'food_street' ? '🪔' : '⭐',
        place: {
            ten_quan: suggestedPlace.ten_quan,
            dia_chi: suggestedPlace.dia_chi,
            rating: parseFloat(suggestedPlace.rating) || 0,
            lat: suggestedPlace.lat,
            lon: suggestedPlace.lon,
            distance: Math.round(distance * 100) / 100,
            travel_time: travelTime,
            suggest_leave: suggestLeaveStr,
            data_id: suggestedPlace.data_id,
            hinh_anh: suggestedPlace.hinh_anh || '',
            gia_trung_binh: suggestedPlace.gia_trung_binh || '',
            khau_vi: suggestedPlace.khau_vi || '',
            gio_mo_cua: suggestedPlace.gio_mo_cua || ''
        }
    };
    
    if (!currentPlan._order) {
        currentPlan._order = [];
    }
    currentPlan._order.push(newKey);
    
    // Render lại
    displayPlanVertical(currentPlan, isEditMode);
    
    // Scroll đến quán vừa thêm
    setTimeout(() => {
        const addedItem = document.querySelector(`[data-meal-key="${newKey}"]`);
        if (addedItem) {
            addedItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
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
    
    alert('✅ Đã thêm quán vào lịch trình!');
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
        console.error('Lỗi tìm khu ẩm thực gợi ý:', error);
        return null;
    }
}

// Tìm quán Michelin (17:00 - 00:00)
async function findSuggestedMichelin() {
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
        const searchTime = '18:30';
        const randomSeed = Date.now();
        
        const url = `/api/food-plan?lat=${userLat}&lon=${userLon}&random=${randomSeed}&start_time=${searchTime}&end_time=${searchTime}&radius_km=${radius}&theme=michelin`;
        
        const response = await fetch(url);
        if (!response.ok) return null;
        
        const data = await response.json();
        if (data.error) return null;
        
        // Tìm quán trong response
        for (const key in data) {
            if (key !== '_order' && data[key]?.place) {
                return data[key].place;
            }
        }
        
        return null;
        
    } catch (error) {
        console.error('Error finding Michelin restaurant:', error);
        return null;
    }
}

// ========== AUTO MODE: GENERATE PLAN ==========
async function generateAutoPlan() {
isViewingSharedPlan = false;
    const resultDiv = document.getElementById('planResult');

    window.loadedFromSavedPlan = false;

    // 🔁 Reset ID & tên lịch khi tạo lịch mới
    currentPlanId = null;           // không còn gắn với plan đã lưu
    window.currentPlanName = null;  // để header dùng lại "Lịch trình của bạn"

    // ✅ THÊM 2 DÒNG NÀY
    suggestedFoodStreet = null;
    suggestedMichelin = null;
    
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

        console.log('🔍 [Generate] Selected themes:', selectedThemes);
        console.log('🔍 [Generate] BEFORE fetch - suggestedMichelin:', suggestedMichelin);

        // 🔥 TÌM FOOD STREET TRƯỚC
        if (selectedThemes.includes('food_street')) {
            console.log('🔍 Đang fetch Food Street...');
            suggestedFoodStreet = await findSuggestedFoodStreet();
            console.log('📍 After fetch Food Street:', suggestedFoodStreet?.ten_quan || 'NULL');
        }

        // 🔥 SAU ĐÓ TÌM MICHELIN
        if (selectedThemes.includes('michelin')) {
            console.log('🔍 Đang fetch Michelin...');
            suggestedMichelin = await findSuggestedMichelin();
            console.log('📍 After fetch Michelin:', suggestedMichelin?.ten_quan || 'NULL');
        }

        // 🔥 RENDER 1 LẦN DUY NHẤT SAU KHI CẢ 2 XONG
        console.log('🎨 [Final] Render với:', {
            foodStreet: suggestedFoodStreet?.ten_quan || 'null',
            michelin: suggestedMichelin?.ten_quan || 'null',
            selectedThemes: selectedThemes
        });

        displayPlanVertical(currentPlan, false);
        
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
  const cur = '<span class="budget-unit">₫</span>'; // hoặc đổi thành 'đ' nếu bạn thích
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1).replace('.0', '') + ' triệu ' + cur;
  } else if (value >= 1000) {
    return (value / 1000).toFixed(0) + '.000 ' + cur;
  } else {
    return value + ' ' + cur;
  }
}

// ========== SHARE PLAN LOGIC ==========
let isSharedPlan = false;
let sharedPlanOwnerId = null;
let hasEditPermission = false;
let sharedPlanOwnerName = ''; // ✅ THÊM DÒNG NÀY
let isViewingSharedPlan = false; // 🔥 BIẾN MỚI - theo dõi có đang xem shared plan không
window.originalSharedPlanData = null; // 🔥 MỚI: Lưu bản gốc của shared plan
// 🔥 THÊM BIẾN MỚI - LƯU TRẠNG THÁI CÁC THAY ĐỔI TẠM THỜI
let pendingApprovals = {}; // { suggestionId: { approvedChanges: [], rejectedChanges: [] } }
let hasPendingSuggestion = false; // 🔥 THÊM: Theo dõi có suggestion pending không

// ========== SO SÁNH 2 PLAN DATA ==========
function comparePlanData(plan1, plan2) {
    // Bỏ qua _order khi so sánh
    const keys1 = Object.keys(plan1).filter(k => k !== '_order').sort();
    const keys2 = Object.keys(plan2).filter(k => k !== '_order').sort();
    
    // Kiểm tra số lượng keys
    if (keys1.length !== keys2.length) {
        console.log('🔍 [COMPARE] Khác số lượng keys:', keys1.length, 'vs', keys2.length);
        return false;
    }
    
    // Kiểm tra xem keys có giống nhau không
    if (JSON.stringify(keys1) !== JSON.stringify(keys2)) {
        console.log('🔍 [COMPARE] Khác danh sách keys');
        return false;
    }
    
    // So sánh từng key
    for (const key of keys1) {
        const meal1 = plan1[key];
        const meal2 = plan2[key];
        
        // So sánh time
        if (meal1.time !== meal2.time) {
            console.log(`🔍 [COMPARE] Key ${key} - Khác time:`, meal1.time, 'vs', meal2.time);
            return false;
        }
        
        // So sánh title
        if (meal1.title !== meal2.title) {
            console.log(`🔍 [COMPARE] Key ${key} - Khác title:`, meal1.title, 'vs', meal2.title);
            return false;
        }
        
        // So sánh icon
        if (meal1.icon !== meal2.icon) {
            console.log(`🔍 [COMPARE] Key ${key} - Khác icon:`, meal1.icon, 'vs', meal2.icon);
            return false;
        }
        
        // So sánh place
        const place1 = meal1.place;
        const place2 = meal2.place;
        
        // Nếu 1 cái có place, 1 cái không có
        if ((place1 && !place2) || (!place1 && place2)) {
            console.log(`🔍 [COMPARE] Key ${key} - Khác place existence`);
            return false;
        }
        
        // Nếu cả 2 đều có place, so sánh data_id
        if (place1 && place2) {
            if (place1.data_id !== place2.data_id) {
                console.log(`🔍 [COMPARE] Key ${key} - Khác place:`, place1.data_id, 'vs', place2.data_id);
                return false;
            }
        }
    }
    
    console.log('✅ [COMPARE] Plan giống nhau hoàn toàn');
    return true;
}

async function sharePlan() {
 // 🔥 KIỂM TRA NẾU MODAL ĐÃ TỒN TẠI
    if (document.getElementById('shareModal')) {
        console.log('⚠️ Modal chia sẻ đã mở rồi');
        return;
    }
    if (!currentPlan || !currentPlanId) {
        alert('⚠️ Chưa có lịch trình để chia sẻ');
        return;
    }

    // ✅ Đóng tạm Food Planner khi mở popup chia sẻ (KHÔNG reset data)
    const panel = document.getElementById('foodPlannerPanel');
    if (panel) {
    panel.dataset.prevActiveShare = panel.classList.contains('active') ? '1' : '0';
    panel.classList.remove('active');
    }
    window._prevIsPlannerOpenShare = isPlannerOpen;
    isPlannerOpen = false;

    // ✅ Khóa scroll nền
    document.body.dataset.prevOverflowShare = document.body.style.overflow || '';
    document.body.style.overflow = 'hidden';
    
    try {
        // Lấy danh sách bạn bè
        const response = await fetch('/api/accounts/my-friends/');
        const data = await response.json();
        
        if (!data.friends || data.friends.length === 0) {
            alert('Bạn chưa có bạn bè nào để chia sẻ');
            return;
        }
        
        // Tạo modal chọn bạn bè
        const friendsList = data.friends.map(friend => `
            <label style="display: flex; align-items: center; gap: 8px; padding: 8px; cursor: pointer;">
                <input type="checkbox" value="${friend.id}" class="friend-checkbox">
                <span>${friend.username}</span>
            </label>
        `).join('');
        
        const modalHTML = `
            <div id="shareModal" style="
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
                z-index: 2147483647;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                animation: fadeIn 0.3s ease;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.96);
                    backdrop-filter: blur(26px) saturate(180%);
                    -webkit-backdrop-filter: blur(26px) saturate(180%);
                    border-radius: 28px;
                    max-width: 450px;
                    width: 100%;
                    border: 1px solid #FFE5D9;
                    box-shadow: 0 10px 35px rgba(148, 85, 45, 0.25), 0 24px 60px rgba(203, 92, 37, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.9);
                    overflow: hidden;
                    font-family: 'Montserrat', sans-serif;
                    animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                ">
                    <!-- Header -->
                    <div style="
                        position: relative;
                        padding: 18px 24px 14px;
                        background: linear-gradient(135deg, rgba(255, 107, 53, 0.14) 0%, rgba(255, 142, 83, 0.10) 100%);
                        border-bottom: 1px solid #FFE5D9;
                    ">
                        <div style="
                            position: absolute;
                            top: 0;
                            left: 0;
                            right: 0;
                            height: 1px;
                            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
                        "></div>
                        
                        <h3 style="
                            margin: 0;
                            font-weight: 700;
                            font-size: 18px;
                            letter-spacing: -0.02em;
                            background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;
                        ">
                            Chia sẻ lịch trình
                        </h3>
                    </div>
                    
                    <!-- Body -->
                    <div style="padding: 20px 24px;">
                        <p style="
                            color: #555555;
                            font-size: 13px;
                            margin: 0 0 15px 0;
                            line-height: 1.5;
                            font-weight: 500;
                        ">Chọn bạn bè bạn muốn chia sẻ:</p>
                        
                        <!-- Friends List -->
                        <div style="
                            max-height: 300px;
                            overflow-y: auto;
                            overflow-x: hidden;
                            background: #FFF5F0;
                            border: 1px solid #FFE5D9;
                            border-radius: 12px;
                            padding: 12px;
                            margin: 15px 0;
                        ">
                            <style>
                                #shareModal .friends-scroll::-webkit-scrollbar {
                                    width: 6px;
                                }
                                #shareModal .friends-scroll::-webkit-scrollbar-track {
                                    background: #FFE5D9;
                                    border-radius: 10px;
                                    margin: 8px 0;
                                }
                                #shareModal .friends-scroll::-webkit-scrollbar-thumb {
                                    background: linear-gradient(135deg, #FFB084, #FF8E53);
                                    border-radius: 10px;
                                    border: 2px solid transparent;
                                    background-clip: padding-box;
                                }
                                
                                /* Custom Checkbox Style */
                                #shareModal input[type="checkbox"] {
                                    appearance: none;
                                    -webkit-appearance: none;
                                    width: 20px;
                                    height: 20px;
                                    border: 2px solid #FFB084;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    position: relative;
                                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                                    background: white;
                                }
                                
                                #shareModal input[type="checkbox"]:hover {
                                    border-color: #FF8E53;
                                    box-shadow: 0 0 8px rgba(255, 142, 83, 0.3);
                                    transform: scale(1.05);
                                }
                                
                                #shareModal input[type="checkbox"]:checked {
                                    background: white;
                                    border-color: #FF8E53;
                                }
                                
                                #shareModal input[type="checkbox"]:checked::after {
                                    content: '';
                                    position: absolute;
                                    left: 5px;
                                    top: 2px;
                                    width: 6px;
                                    height: 10px;
                                    border: solid #FF8E53;
                                    border-width: 0 2.5px 2.5px 0;
                                    transform: rotate(45deg);
                                }
                                
                                /* Friend Item Style */
                                #shareModal .friend-item {
                                    display: flex;
                                    align-items: center;
                                    gap: 12px;
                                    padding: 12px;
                                    margin-bottom: 8px;
                                    background: white;
                                    border: 1px solid #FFE5D9;
                                    border-radius: 12px;
                                    cursor: pointer;
                                    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                                }
                                
                                #shareModal .friend-item:hover {
                                    background: #FFF9F5;
                                    border-color: #FFB084;
                                    transform: translateX(4px);
                                    box-shadow: 0 4px 12px rgba(255, 142, 83, 0.2);
                                }
                                
                                #shareModal .friend-item label {
                                    cursor: pointer;
                                    font-size: 14px;
                                    font-weight: 600;
                                    color: #FF8E53;
                                    flex: 1;
                                    user-select: none;
                                }
                            </style>
                            <div class="friends-scroll">
                                ${friendsList}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="
                        padding: 12px 16px;
                        border-top: 1px solid #FFE5D9;
                        background: linear-gradient(135deg, #FFF5F0 0%, #FFE5D9 100%);
                        display: flex;
                        gap: 10px;
                        position: relative;
                    ">
                        <div style="
                            position: absolute;
                            top: 0;
                            left: 0;
                            right: 0;
                            height: 1px;
                            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.9), transparent);
                        "></div>
                        
                        <button onclick="confirmShare()" style="
                            flex: 1;
                            border: none;
                            padding: 12px 20px;
                            border-radius: 25px;
                            background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
                            color: #ffffff;
                            font-size: 14px;
                            font-weight: 700;
                            cursor: pointer;
                            box-shadow: 0 4px 16px rgba(255, 126, 75, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.35);
                            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                            font-family: 'Montserrat', sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 8px;
                        " onmouseover="this.style.transform='translateY(-2px) scale(1.05)'; this.style.boxShadow='0 8px 24px rgba(255, 126, 75, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.35)';" onmouseout="this.style.transform=''; this.style.boxShadow='0 4px 16px rgba(255, 126, 75, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.35)';">
                            Chia sẻ
                        </button>
                        
                        <button onclick="closeShareModal()" style="
                            flex: 1;
                            border: 2px solid #FFB084;
                            padding: 12px 20px;
                            border-radius: 25px;
                            background: rgba(255, 255, 255, 0.9);
                            color: #FF8E53;
                            font-size: 14px;
                            font-weight: 700;
                            cursor: pointer;
                            box-shadow: 0 2px 8px rgba(255, 126, 75, 0.2);
                            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                            font-family: 'Montserrat', sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 8px;
                        " onmouseover="this.style.transform='translateY(-2px) scale(1.05)'; this.style.background='#FFF5F0'; this.style.boxShadow='0 4px 12px rgba(255, 126, 75, 0.3)';" onmouseout="this.style.transform=''; this.style.background='rgba(255, 255, 255, 0.9)'; this.style.boxShadow='0 2px 8px rgba(255, 126, 75, 0.2)';">
                            Hủy
                        </button>
                    </div>
                </div>
            </div>
            
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(30px) scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
            </style>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
    } catch (error) {
        console.error('Error loading friends:', error);
        alert('Không thể tải danh sách bạn bè');
    }
}

function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) modal.remove();

  // ✅ Mở lại Food Planner như lúc trước khi mở popup
  const panel = document.getElementById('foodPlannerPanel');
  if (panel && panel.dataset.prevActiveShare === '1') {
    panel.classList.add('active');
    isPlannerOpen = true;
  } else {
    isPlannerOpen = false;
  }
  if (panel) delete panel.dataset.prevActiveShare;

  // ✅ Mở lại scroll nền
  document.body.style.overflow = document.body.dataset.prevOverflowShare || '';
  delete document.body.dataset.prevOverflowShare;
}

async function confirmShare() {
    const checkedBoxes = document.querySelectorAll('.friend-checkbox:checked');
    const friend_ids = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
    
    if (friend_ids.length === 0) {
        alert('Vui lòng chọn ít nhất 1 bạn bè');
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/food-plan/share/${currentPlanId}/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                friend_ids: friend_ids,
                permission: 'edit'
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('✅ ' + result.message);
            closeShareModal();
        } else {
            alert('❌ ' + result.message);
        }
        
    } catch (error) {
        console.error('Error sharing plan:', error);
        alert('Không thể chia sẻ lịch trình');
    }
}

// ========== LOAD SHARED PLANS ==========
async function loadSharedPlans() {
    try {
        const response = await fetch('/api/accounts/food-plan/shared/');
        const data = await response.json();
        
        if (data.status === 'success' && data.shared_plans.length > 0) {
            // Thêm vào saved plans list
            displaySavedPlansList(data.shared_plans, true); // true = là shared plans
        }
    } catch (error) {
        console.error('Error loading shared plans:', error);
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
    
    // 🔥 ẨN/HIỆN FILTERS DựA vào trạng thái xem shared plan
const filtersWrapper = document.querySelector('.filters-wrapper-new');
if (filtersWrapper) {
    if (isViewingSharedPlan) {
        filtersWrapper.style.display = 'none'; // Ẩn khi xem shared plan
    } else {
        filtersWrapper.style.display = 'block'; // Hiện khi không xem shared plan
    }
}

   let html = `
<div class="schedule-header">
    <div>
        <h3 class="schedule-title">
            <span style="margin-right: 8px;">📅</span>
            <span ${!isSharedPlan && editMode ? 'contenteditable="true" class="editable" onblur="updateAutoPlanName(this.textContent)"' : ''}><span>${window.currentPlanName || 'Lịch trình của bạn'}</span></span>
        </h3>
        ${isSharedPlan ? `
            <p style="font-size: 12px; color: #666; margin: 5px 0 0 0;">
                Được chia sẻ bởi <strong>${sharedPlanOwnerName}</strong>
            </p>
        ` : ''}
    </div>
    <div class="action-buttons" id="actionButtons">
  
    
   ${isSharedPlan ? `
    ${hasEditPermission ? `

        <button class="action-btn edit ${editMode ? 'active' : ''}" id="editPlanBtn" onclick="toggleEditMode()" title="${editMode ? 'Thoát chỉnh sửa' : 'Chỉnh sửa'}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
        </button>
        
        <button class="action-btn"
            onclick="viewMySuggestions(${currentPlanId})"
            style="background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);"
            title="Xem đề xuất của tôi">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
            </svg>
        </button>
        
        <button class="action-btn primary icon-only"
                onclick="submitSuggestion()"
                title="Gửi đề xuất"
                ${hasPendingSuggestion ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
        </svg>

        <!-- vẫn có text nhưng không hiện -->
        <span class="btn-label sr-only">
            ${hasPendingSuggestion ? 'Đang chờ duyệt' : 'Gửi đề xuất'}
        </span>
        </button>
    ` : ''}
` : `
    <div class="suggestions-wrapper" style="display: none;">  <!-- ✅ THÊM style ẨN MẶC ĐỊNH -->
        <button class="action-btn"
                onclick="openSuggestionsPanel()"
                id="suggestionsBtn"
                title="Xem đề xuất chỉnh sửa"
                style="width: 40px; height: 40px;">  <!-- ✅ BỎ display: none, chỉ giữ kích thước -->

            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
            </svg>

            <span id="suggestionCount">0</span>
        </button>

        <span class="notif-dot" id="suggestionDot"></span>
    </div>
    
    <button class="action-btn edit ${editMode ? 'active' : ''}" id="editPlanBtn" onclick="toggleEditMode()" title="${editMode ? 'Thoát chỉnh sửa' : 'Chỉnh sửa'}">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
        </svg>
    </button>

    <button class="action-btn primary" onclick="savePlan()" title="Lưu">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
            <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
        </svg>
    </button>

    <button class="action-btn share" onclick="sharePlan()" title="Chia sẻ kế hoạch">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="white">
            <path d="M15 8l4.39 4.39a1 1 0 010 1.42L15 18.2v-3.1c-4.38.04-7.43 1.4-9.88 4.3.94-4.67 3.78-8.36 9.88-8.4V8z"/>
        </svg>
    </button>
`}
    </div>
</div>
  <div class="timeline-container"><div class="timeline-line"></div>
`;
    

  
    
    const mealOrder = ['breakfast', 'morning_drink', 'lunch', 'afternoon_drink', 'dinner', 'dessert', 'meal', 'meal1', 'drink', 'meal2'];
    let hasPlaces = false;
    
    let allMealKeys;
    if (plan._order && plan._order.length > 0) {
        // 🔥 GIỮ NGUYÊN THỨ TỰ _order, KHÔNG SORT LẠI
        allMealKeys = plan._order.filter(k => plan[k] && plan[k].time);
        console.log('✅ Dùng _order từ backend:', allMealKeys);
    } else {
        // 🔥 Fallback: lấy tất cả keys KHÔNG SORT
        allMealKeys = Object.keys(plan).filter(k => k !== '_order' && plan[k] && plan[k].time);
        plan._order = allMealKeys;
        console.log('⚠️ Không có _order, lấy tất cả keys:', allMealKeys);
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
                                <button class="action-btn edit icon-only mini meal-action-bubble ${isWaitingForSelection ? 'active' : ''}"
                                        onclick="event.stopPropagation(); selectPlaceForMeal('${key}')"
                                        title="${isWaitingForSelection ? 'Đang chờ bạn chọn quán khác trên bản đồ...' : 'Nhấn để đổi sang quán khác'}">
                                    ${isWaitingForSelection ? ICON_SPINNER : ICON_PENCIL}
                                    <span class="sr-only">${isWaitingForSelection ? 'Đang đổi.' : 'Đổi quán'}</span>
                                </button>

                                <button class="action-btn edit icon-only mini meal-action-bubble delete-meal"
                                        onclick="event.stopPropagation(); deleteMealSlot('${key}')"
                                        title="Xóa bữa ăn này">
                                    <span class="btn-icon">✕</span>
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
                <div class="meal-card-vertical ${editMode ? 'edit-mode' : ''} ${(() => {
                    // 🔥 KIỂM TRA NHIỀU NGUỒN: mo_ta, title, icon
                    const moTa = (place.mo_ta || '').toLowerCase();
                    const title = (meal.title || '').toLowerCase();
                    const icon = meal.icon || '';
                    
                    // Kiểm tra từ MÔ TẢ (mo_ta)
                    const isKhuAmThucFromMoTa = moTa.includes('khu') && moTa.includes('am thuc');
                    const isMichelinFromMoTa = moTa === 'michelin';
                    
                    // Kiểm tra từ TITLE của meal
                    const isKhuAmThucFromTitle = title.includes('khu') && title.includes('ẩm thực');
                    const isMichelinFromTitle = title.includes('michelin');
                    
                    // Kiểm tra từ ICON
                    const isKhuAmThucFromIcon = icon === '🪔';
                    const isMichelinFromIcon = icon === '⭐';
                    
                    // TRẢ VỀ CLASS
                    const isGold = isKhuAmThucFromMoTa || isMichelinFromMoTa || 
                                isKhuAmThucFromTitle || isMichelinFromTitle ||
                                isKhuAmThucFromIcon || isMichelinFromIcon;
                    
                    return isGold ? 'gold-card' : '';
                })()}" ${cardClickEvent} style="${cardCursor}">
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
                            <button class="action-btn edit icon-only mini meal-action-bubble ${isWaitingForSelection ? 'active' : ''}"
                                    onclick="event.stopPropagation(); selectPlaceForMeal('${key}')"
                                    title="${isWaitingForSelection ? 'Đang chờ bạn chọn quán khác trên bản đồ...' : 'Nhấn để đổi sang quán khác'}">
                                ${isWaitingForSelection ? ICON_SPINNER : ICON_PENCIL}
                                <span class="sr-only">${isWaitingForSelection ? 'Đang đổi.' : 'Đổi quán'}</span>
                            </button>

                            <button class="action-btn edit icon-only mini meal-action-bubble delete-meal"
                                    onclick="event.stopPropagation(); deleteMealSlot('${key}')"
                                    title="Xóa bữa ăn này">
                                <span class="btn-icon">✕</span>
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
    
    html += '</div>'; // Đóng timeline-container

    // 🔥 NÚT THÊM/XÓA (CHỈ KHI EDIT MODE)
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
                
                <!-- NÚT LÀM TRỐNG -->
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <button onclick="deleteAllMeals()" style="
                        background: linear-gradient(135deg, #FF6B35 0%, #FFB84D 100%);
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
                        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
                        transition: all 0.2s ease;
                    " onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 6px 16px rgba(255, 107, 53, 0.4)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 53, 0.3)';" title="Làm trống lịch trình">
                        ✕
                    </button>
                    <div style="margin-top: 10px; font-size: 14px; color: #FF6B35; font-weight: 600;">
                        Làm trống
                    </div>
                </div>
            </div>
        `;
    }

    // 📍 Bán Kính Tìm Kiếm - CHỈ HIỆN KHI TẠO MỚI
    if (!window.loadedFromSavedPlan && !isViewingSharedPlan) {
        html += `
        <div class="planner-radius-card" role="group" aria-label="Bán kính tìm kiếm">
            <div class="planner-radius-meta">
            <div class="planner-radius-title-row">
                <div class="planner-radius-title">Bán kính tìm kiếm</div>
            </div>
            <div class="planner-radius-hint">Nhấn “Đổi bán kính” để mở bộ lọc bán kính trên bản đồ.</div>
            </div>

            <div class="planner-radius-actions">
            <div class="planner-radius-value" id="plannerRadiusValue">
                ${window.currentRadius || '10'}<span>km</span>
            </div>
            <button type="button" class="planner-radius-btn" onclick="openRadiusPickerFromPlanner()">
                Đổi bán kính
            </button>
            </div>
        </div>
        `;
    }
        
    // 💰 Tổng Kinh Phí (NEW UI - cam chủ đạo, full width như radius card)
    html += `
    <div class="planner-budget-card" role="group" aria-label="Tổng kinh phí dự kiến">
        <div class="planner-budget-left">
        <div class="planner-budget-icon" aria-hidden="true">💰</div>

        <div class="planner-budget-meta">
            <div class="planner-budget-title">Tổng kinh phí dự kiến</div>
            <div class="planner-budget-hint">Ước tính theo giá trung bình</div>
        </div>
        </div>

        <div class="planner-budget-right">
        <div class="planner-budget-value">
            ${budget.hasOverPrice ? '<span class="planner-budget-pill">Trên</span>' : ''}
            ${formatMoney(budget.total)}
        </div>

        ${budget.unknown > 0 ? `<div class="planner-budget-note">Không tính ${budget.unknown} quán</div>` : ''}
        </div>
    </div>
    `;

// 🔥 CARD GỢI Ý MICHELIN (17:00 - 00:00)
console.log('🔍 [displayPlanVertical] Check Michelin:', {
    suggestedMichelin: suggestedMichelin,
    tenQuan: suggestedMichelin?.ten_quan,
    selectedThemes: selectedThemes,
    hasMichelinTheme: selectedThemes.includes('michelin')
});

const shouldShowMichelinSuggestion = suggestedMichelin && 
                                      selectedThemes.includes('michelin');

console.log('🎯 shouldShowMichelinSuggestion:', shouldShowMichelinSuggestion);

if (shouldShowMichelinSuggestion) {
    console.log('✅ RENDER Michelin card:', suggestedMichelin.ten_quan);
    html += `
        <div style="margin-top: 40px; padding: 0 20px;">
            <div style="
                background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
                border: 3px dashed #FFB84D;
                border-radius: 20px;
                padding: 20px;
                position: relative;
                box-shadow: 0 6px 20px rgba(255, 184, 77, 0.25);
                max-width: 100%;
            ">
                
                <!-- ✅ TAG Gợi ý cho bạn -->
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
                    <span style="font-size: 32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">⭐</span>
                    <div>
                        <div style="font-size: 16px; font-weight: 700; color: #6B5410; margin-bottom: 4px;">
                            Nhà hàng Michelin
                        </div>
                        ${(() => {
                            const gioMoCua = suggestedMichelin.gio_mo_cua || '';
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
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onclick="flyToPlace(${suggestedMichelin.lat}, ${suggestedMichelin.lon}, '${suggestedMichelin.data_id}', '${suggestedMichelin.ten_quan.replace(/'/g, "\\'")}')"
                onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.1)';"
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.04)';">
                    <div style="font-weight: 700; color: #FF6B35; margin-bottom: 8px; font-size: 15px; display: flex; align-items: center; gap: 6px;">
                        <span>🍽️</span>
                        <span>${suggestedMichelin.ten_quan}</span>
                    </div>
                    <div style="color: #666; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                        📍 ${suggestedMichelin.dia_chi}
                    </div>
                    <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px;">
                        <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%); border-radius: 20px; color: #8B6914; font-weight: 600; border: 1px solid #FFD699;">
                            <span style="font-size: 16px;">⭐</span>
                            <strong>${suggestedMichelin.rating ? parseFloat(suggestedMichelin.rating).toFixed(1) : 'N/A'}</strong>
                        </div>
                        ${suggestedMichelin.gia_trung_binh && !['$', '$$', '$$$', '$$$$'].includes(suggestedMichelin.gia_trung_binh.trim()) ? `
                            <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: linear-gradient(135deg, #FFF5E6 0%, #FFE5CC 100%); border-radius: 20px; color: #8B6914; font-weight: 600; border: 1px solid #FFD699;">
                                <span style="font-size: 16px;">💰</span>
                                <strong>${suggestedMichelin.gia_trung_binh}</strong>
                            </div>
                        ` : ''}
                    </div>
                    ${suggestedMichelin.khau_vi ? `
                        <div style="margin-top: 12px; padding: 8px 12px; background: #FFF5E6; border-left: 3px solid #FFB84D; border-radius: 6px; font-size: 12px; color: #8B6914;">
                            👅 Khẩu vị: ${suggestedMichelin.khau_vi}
                        </div>
                    ` : ''}
                </div>
                
                <!-- 🔥 2 NÚT MỚI -->
                <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: center;">
                    <button onclick="event.stopPropagation(); randomMichelin();" style="
                        flex: 1;
                        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(76, 175, 80, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(76, 175, 80, 0.3)';">
                        <span>Đổi quán khác</span>
                    </button>
                    
                    <button onclick="event.stopPropagation(); addSuggestedToSchedule(suggestedMichelin, 'michelin');" style="
                        flex: 1;
                        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(255, 107, 53, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 53, 0.3)';">
                        <span>Thêm vào lịch</span>
                    </button>
                </div>
                
                <!-- FOOTER -->
                <div style="margin-top: 16px; text-align: center; font-size: 13px; color: #8B6914; font-weight: 600;">
                    Nhấn vào card để xem trên bản đồ
                </div>
            </div>
        </div>
    `;
}

// 🔥 CARD GỢI Ý KHU ẨM THỰC (GIỮ NGUYÊN - CÓ TAG "GỢI Ý")
const shouldShowFoodStreetSuggestion = suggestedFoodStreet && 
                                        selectedThemes.includes('food_street');

if (shouldShowFoodStreetSuggestion) {
    html += `
        <div style="margin-top: 40px; padding: 0 20px;">
            <div style="
                background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B3 100%);
                border: 3px dashed #FFB84D;
                border-radius: 20px;
                padding: 20px;
                position: relative;
                box-shadow: 0 6px 20px rgba(255, 184, 77, 0.25);
                max-width: 100%;
            ">
                
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
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onclick="flyToPlace(${suggestedFoodStreet.lat}, ${suggestedFoodStreet.lon}, '${suggestedFoodStreet.data_id}', '${suggestedFoodStreet.ten_quan.replace(/'/g, "\\'")}')"
                onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.1)';"
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.04)';">
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
                
                <!-- 🔥 2 NÚT MỚI -->
                <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: center;">
                    <button onclick="event.stopPropagation(); randomFoodStreet();" style="
                        flex: 1;
                        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(76, 175, 80, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(76, 175, 80, 0.3)';">
                        <span>Đổi quán khác</span>
                    </button>
                    
                    <button onclick="event.stopPropagation(); addSuggestedToSchedule(suggestedFoodStreet, 'food_street');" style="
                        flex: 1;
                        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(255, 107, 53, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 53, 0.3)';">
                        <span>Thêm vào lịch</span>
                    </button>
                </div>
                
                <!-- FOOTER -->
                <div style="margin-top: 16px; text-align: center; font-size: 13px; color: #8B6914; font-weight: 600;">
                    Nhấn vào card để xem trên bản đồ
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

    // 🔥 THÊM ĐOẠN CODE MỚI Ở ĐÂY
    const exitBtn = document.getElementById('exitSharedPlanBtn');
    if (exitBtn) {
        if (isViewingSharedPlan) {
            console.log('✅ Hiện nút X vì đang xem shared plan');
            exitBtn.style.display = 'flex';
        } else {
            console.log('❌ Ẩn nút X vì không xem shared plan');
            exitBtn.style.display = 'none';
        }
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

    // 🔥 ẨN TẤT CẢ MARKER KHÁC, CHỈ GIỮ MARKER CỦA QUÁN TRONG LỊCH TRÌNH
    if (hasPlaces && window.showMarkersForPlaceIds) {
        window.showMarkersForPlaceIds(plan);
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
    
    // 🔥 THÊM ĐOẠN NÀY - HIỆN TẤT CẢ QUÁN KHI TẠO CARD MỚI
    setTimeout(() => {
        // Ưu tiên dùng data tìm kiếm hiện tại
        if (typeof displayPlaces === 'function' &&
            Array.isArray(window.allPlacesData) &&
            window.allPlacesData.length > 0) {
            
            // false = không đổi zoom, chỉ vẽ lại marker
            displayPlaces(window.allPlacesData, false);
            console.log('✅ Đã hiện lại tất cả quán sau khi tạo card mới');
        } else if (typeof loadMarkersInViewport === 'function' && window.map) {
            // Fallback: nếu chưa có allPlacesData thì bật lại lazy-load
            window.map.on('moveend', loadMarkersInViewport);
            loadMarkersInViewport();
            console.log('✅ Đã bật lại lazy-load marker sau khi tạo card mới');
        }
    }, 100);
    
    // 🔥 THÊM: Kích hoạt refresh sidebar
    if (typeof window.refreshCurrentSidebar === 'function') {
        setTimeout(() => {
            console.log('🔄 Refresh sidebar sau khi thêm quán mới');
            window.refreshCurrentSidebar();
        }, 100);
    }
    
    // Scroll to bottom
    setTimeout(() => {
        const timeline = document.querySelector('.timeline-container');
        if (timeline) {
            timeline.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, 200);
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
    
    // 🔥 DÙNG _order TRỰC TIẾP - KHÔNG SORT THEO TIME
    const allMealKeys = plan._order 
        ? plan._order.filter(k => plan[k] && plan[k].place)
        : Object.keys(plan).filter(k => k !== '_order' && plan[k] && plan[k].place);
    
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
            // 🔥 MAPBOX URL
            const MAPBOX_TOKEN = 'pk.eyJ1IjoidHRraGFuZzI0MTEiLCJhIjoiY21qMWVpeGJnMDZqejNlcHdkYnQybHdhbCJ9.V0_GUI2CBTtEhkrnajG3Ug'; // Token demo, bạn nên lấy token riêng tại mapbox.com
            
            const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${startPoint.lon},${startPoint.lat};${endPoint.lon},${endPoint.lat}?geometries=geojson&overview=full&access_token=${MAPBOX_TOKEN}`;
            
            const response = await fetch(url, { signal });
            const data = await response.json();
            
            // 🔥 MapBox format: data.routes[0].geometry.coordinates
            if (data.routes && data.routes[0] && data.routes[0].geometry) {
                const route = data.routes[0];
                
                // MapBox trả: coordinates = [[lon, lat], [lon, lat]]
                const coords = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
                
                const color = getRouteColor(index, totalRoutes);
                
                // 🔥 KIỂM TRA TRÙNG VÀ TÍNH OFFSET
                let offsetPixels = 0;
                
                for (let i = 0; i < drawnSegments.length; i++) {
                    if (checkRouteOverlap(coords, drawnSegments[i].coords)) {
                        const overlapCount = drawnSegments.filter(seg => 
                            checkRouteOverlap(coords, seg.coords)
                        ).length;
                        
                        offsetPixels = (overlapCount % 2 === 0) ? 8 : -8;
                        console.log(`⚠️ Đường ${index} trùng ${overlapCount} đường, offset = ${offsetPixels}px`);
                        break;
                    }
                }
                
                drawnSegments.push({ coords: coords, index: index });
                
                // VẼ VIỀN TRẮNG
                const outlinePolyline = L.polyline(coords, {
                    color: '#FFFFFF',
                    weight: routeWeight + 3,
                    opacity: 0.9,
                    smoothFactor: 1
                }).addTo(map);
                
                routeLayers.push(outlinePolyline);
                
                // VẼ ĐƯỜNG MÀU CHÍNH
                const mainPolyline = L.polyline(coords, {
                    color: color,
                    weight: routeWeight,
                    opacity: 1,
                    smoothFactor: 1,
                    dashArray: null
                }).addTo(map);
                
                // ÁP DỤNG OFFSET
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
                
                // 🔥 FIX: ĐÁNH SỐ TỪ 1 THAY VÌ 0
                if (!startPoint.isUser) {
                    // Số hiển thị = index nếu có user coords, index+1 nếu không có
                    const displayNumber = window.currentUserCoords ? index : index + 1;
                    
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
                            ">${displayNumber}</div>`,
                            iconSize: [40, 40],
                            iconAnchor: [20, 20]
                        }),
                        zIndexOffset: 1000
                    }).addTo(map);
                    
                    routeLayers.push(numberMarker);
                }
                
                // 🔥 FIX: ĐÁNH SỐ CUỐI
                if (index === totalRoutes - 1 && !endPoint.isUser) {
                    const lastColor = getRouteColor(totalRoutes - 1, totalRoutes);
                    // Số cuối = totalRoutes nếu có user coords, ngược lại là số lượng quán
                    const lastDisplayNumber = window.currentUserCoords ? totalRoutes : allMealKeys.length;
                    
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
                            ">${lastDisplayNumber}</div>`,
                            iconSize: [40, 40],
                            iconAnchor: [20, 20]
                        }),
                        zIndexOffset: 1000
                    }).addTo(map);
                    
                    routeLayers.push(lastNumberMarker);
                }
                
            } else {
                // 🔥 LOG ĐỂ DEBUG
                console.log('❌ MapBox response:', data);
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
            if (error.name === 'AbortError') {
                console.log(`⚠️ Request vẽ đường ${index} đã bị hủy`);
                return;
            }
        
            console.error('❌ Lỗi vẽ route:', error);
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
    // Xem trước đó có đang chờ chọn quán cho meal này không
    const wasWaiting = (waitingForPlaceSelection === mealKey);

    if (wasWaiting) {
        // Nhấn lại lần nữa -> hủy chế độ đổi quán
        waitingForPlaceSelection = null;
        selectedPlaceForReplacement = null;
    } else {
        // Bắt đầu chế độ đổi quán cho meal này
        waitingForPlaceSelection = mealKey;
    }

    // Render lại timeline (vẫn giữ logic hide marker theo lịch trình)
    displayPlanVertical(currentPlan, isEditMode);

    // 🔥 Nếu VỪA BẮT ĐẦU chế độ "Đổi quán" -> hiện TẤT CẢ marker quán
    if (!wasWaiting && waitingForPlaceSelection === mealKey) {
        // Ưu tiên dùng data tìm kiếm hiện tại
        if (typeof displayPlaces === 'function' &&
            Array.isArray(window.allPlacesData) &&
            window.allPlacesData.length > 0) {

            // Không đổi zoom, chỉ vẽ lại toàn bộ marker từ allPlacesData
            displayPlaces(window.allPlacesData, false);
        } else if (typeof loadMarkersInViewport === 'function' && window.map) {
            // Fallback: nếu chưa có allPlacesData thì bật lại lazy-load
            window.map.on('moveend', loadMarkersInViewport);
            loadMarkersInViewport();
        }
    }

    // Giữ nguyên phần refreshCurrentSidebar như cũ
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
    
    // 🔥 CẬP NHẬT _order THEO VỊ TRÍ MỚI (KHÔNG SORT THEO TIME)
    const allMealItems = document.querySelectorAll('.meal-item[data-meal-key]');
    const newOrder = Array.from(allMealItems).map(item => item.dataset.mealKey);
    
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
    const cleanName = (newName || '').trim() || 'Kế hoạch';

    // Tên không đổi thì thôi
    if (window.currentPlanName === cleanName) return;

    // Cập nhật lại tên hiện tại đang dùng trong UI / khi bấm "Lưu"
    window.currentPlanName = cleanName;
}

function flyToPlace(lat, lon, placeId, placeName) {
     // ✅ GỌI HÀM RIÊNG TỪ script.js
    if (typeof window.flyToPlaceFromPlanner === 'function') {
        window.flyToPlaceFromPlanner(lat, lon, placeId, placeName);
    } else {
        console.error('❌ Hàm flyToPlaceFromPlanner chưa được load từ script.js');
        alert('Có lỗi khi mở quán. Vui lòng thử lại!');
    }
}

// ===== Radius flow: close planner -> open radius filter -> reopen planner =====
window.__reopenPlannerAfterRadiusChange = false;
window.__plannerReturnPlan = null;

function openRadiusPickerFromPlanner() {
  window.__reopenPlannerAfterRadiusChange = true;
  window.__plannerReturnPlan = currentPlan || null;

  // 1) Đóng Food Planner
  if (typeof closeFoodPlanner === 'function') closeFoodPlanner();

  // 2) Mở dropdown Search Radius trên map
  setTimeout(() => {
    const radiusBtn = document.getElementById('radiusBtn');
    if (radiusBtn) {
      radiusBtn.click();
    } else {
      console.warn('⚠️ Không tìm thấy #radiusBtn để mở Search Radius.');
    }
  }, 150);
}
window.openRadiusPickerFromPlanner = openRadiusPickerFromPlanner;

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
            // ✅ CHỈ CẬP NHẬT TIME, KHÔNG SORT LẠI _order
            currentPlan[mealKey].time = newTime;
            
            // Cập nhật title nếu có
            const titleInput = parent.querySelector('input[onchange*="updateMealTitle"]');
            if (titleInput && titleInput.value) {
                currentPlan[mealKey].title = titleInput.value;
            }
            
            // 🔥 KHÔNG SORT LẠI, CHỈ RENDER LẠI
            displayPlanVertical(currentPlan, isEditMode);
            
            console.log('✅ Updated time:', mealKey, newTime, '- No sorting applied');
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

            // cập nhật số km trên card nếu panel đang mở
            const radiusValueEl = document.getElementById('plannerRadiusValue');
            if (radiusValueEl) radiusValueEl.innerHTML = `${radiusValue}<span>km</span>`;

            // 🔁 Nếu vừa bấm "Đổi bán kính" từ planner -> mở lại planner
            if (window.__reopenPlannerAfterRadiusChange) {
            window.__reopenPlannerAfterRadiusChange = false;

            const planToShow = window.__plannerReturnPlan || currentPlan;

            setTimeout(() => {
                const panel = document.getElementById('foodPlannerPanel');
                const btn = document.getElementById('foodPlannerBtn');
                if (panel && !panel.classList.contains('active')) btn?.click();

                if (planToShow) displayPlanVertical(planToShow, isEditMode);
            }, 150);
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
// ========== CHECK PENDING SUGGESTION ==========
async function checkPendingSuggestion(planId) {
    try {
        console.log('🔍 Checking pending suggestion for plan:', planId);
        
        const response = await fetch(`/api/accounts/food-plan/check-pending/${planId}/`);
        const data = await response.json();
        
        console.log('📥 Response from API:', data);
        
        if (data.status === 'success') {
            hasPendingSuggestion = data.has_pending;
            
            console.log('✅ hasPendingSuggestion updated to:', hasPendingSuggestion);
            
            // Cập nhật UI nút "Gửi đề xuất"
            updateSubmitSuggestionButton();
        }
    } catch (error) {
        console.error('❌ Error checking pending suggestion:', error);
    }
}

function updateSubmitSuggestionButton() {
    const submitBtn = document.querySelector('button[onclick*="submitSuggestion"]');
    
    if (!submitBtn) return;
    
    if (hasPendingSuggestion) {
        // Disable button và đổi style
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.5';
        submitBtn.style.cursor = 'not-allowed';
        submitBtn.title = 'Bạn đã có 1 đề xuất đang chờ duyệt';
        
        // Đổi text
        const btnLabel = submitBtn.querySelector('.btn-label');
        if (btnLabel) {
            btnLabel.textContent = 'Đang chờ duyệt';
        }
    } else {
        // Enable button
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
        submitBtn.title = 'Gửi đề xuất';
        
        // Đổi text về ban đầu
        const btnLabel = submitBtn.querySelector('.btn-label');
        if (btnLabel) {
            btnLabel.textContent = 'Gửi đề xuất';
        }
    }
}
async function submitSuggestion() {
    if (!currentPlan || !currentPlanId) {
        alert('⚠️ Không có thay đổi để gửi');
        return;
    }
    
    // 🔥 THÊM: Kiểm tra pending
    if (hasPendingSuggestion) {
        alert('⚠️ Bạn đã có 1 đề xuất đang chờ duyệt. Vui lòng đợi chủ sở hữu xử lý trước khi gửi đề xuất mới.');
        return;
    }
    
    // 🔥 MỚI: KIỂM TRA CÓ THAY ĐỔI THỰC SỰ KHÔNG
    if (window.originalSharedPlanData) {
        // Lưu dữ liệu từ input trước khi so sánh
        const mealItems = document.querySelectorAll('.meal-item');
        mealItems.forEach(item => {
            const mealKey = item.dataset.mealKey;
            if (mealKey && currentPlan[mealKey]) {
                // Lưu title
                const titleInput = item.querySelector('input[onchange*="updateMealTitle"]');
                if (titleInput && titleInput.value) {
                    currentPlan[mealKey].title = titleInput.value;
                }
                
                // Lưu time
                const hourInput = item.querySelector('.time-input-hour');
                const minuteInput = item.querySelector('.time-input-minute');
                if (hourInput && minuteInput) {
                    const hour = hourInput.value.padStart(2, '0');
                    const minute = minuteInput.value.padStart(2, '0');
                    currentPlan[mealKey].time = `${hour}:${minute}`;
                }
            }
        });
        
        // So sánh với bản gốc
        const hasChanges = !comparePlanData(currentPlan, window.originalSharedPlanData);
        
        if (!hasChanges) {
            alert('⚠️ Bạn chưa thực hiện thay đổi nào so với lịch trình gốc!');
            return;
        }
        
        console.log('✅ Phát hiện có thay đổi, cho phép gửi đề xuất');
    }
    
    const message = prompt('Nhập lời nhắn kèm theo đề xuất (tùy chọn):');
    if (message === null) return; // User clicked Cancel
    
    try {
        // 🔥 LƯU DỮ LIỆU TỪ INPUT TRƯỚC KHI GỬI
        const mealItems = document.querySelectorAll('.meal-item');
        mealItems.forEach(item => {
            const mealKey = item.dataset.mealKey;
            if (mealKey && currentPlan[mealKey]) {
                // Lưu title
                const titleInput = item.querySelector('input[onchange*="updateMealTitle"]');
                if (titleInput && titleInput.value) {
                    currentPlan[mealKey].title = titleInput.value;
                }
                
                // Lưu time
                const hourInput = item.querySelector('.time-input-hour');
                const minuteInput = item.querySelector('.time-input-minute');
                if (hourInput && minuteInput) {
                    const hour = hourInput.value.padStart(2, '0');
                    const minute = minuteInput.value.padStart(2, '0');
                    currentPlan[mealKey].time = `${hour}:${minute}`;
                }
            }
        });
        
        // 🔥 CHUẨN BỊ DỮ LIỆU GỬI ĐI
        const planArray = [];
        const orderKeys = currentPlan._order || Object.keys(currentPlan).filter(k => k !== '_order');
        
        orderKeys.forEach(key => {
            if (currentPlan[key]) {
                planArray.push({
                    key: key,
                    data: JSON.parse(JSON.stringify(currentPlan[key]))
                });
            }
        });
        
        const response = await fetch(`/api/accounts/food-plan/suggest/${currentPlanId}/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                suggested_data: planArray,
                message: message || ''
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('✅ Đã gửi đề xuất chỉnh sửa! Chờ chủ sở hữu phê duyệt.');
            
            // 🔥 THÊM: Đánh dấu đã có pending
            hasPendingSuggestion = true;
            updateSubmitSuggestionButton();
            
            // Tắt edit mode
            if (isEditMode) {
                toggleEditMode();
            }
        } else {
            alert('❌ ' + result.message);
        }
        
    } catch (error) {
        console.error('Error submitting suggestion:', error);
        alert('Không thể gửi đề xuất');
    }
}
// ========== CHECK PENDING SUGGESTIONS ==========
async function checkPendingSuggestions(planId) {
    try {
        const response = await fetch(`/api/accounts/food-plan/suggestions/${planId}/`);
        const data = await response.json();
        
        const wrapper = document.querySelector('.suggestions-wrapper');  // ✅ LẤY WRAPPER
        const suggestionsBtn = document.getElementById('suggestionsBtn');
        const suggestionCount = document.getElementById('suggestionCount');
        const dot = document.getElementById("suggestionDot");
        
        if (!wrapper || !suggestionsBtn || !suggestionCount || !dot) return;  // ✅ KIỂM TRA WRAPPER
        
        // 🔥 LỌC CHỈ LẤY PENDING
        const pendingSuggestions = data.suggestions ? 
            data.suggestions.filter(s => s.status === 'pending') : [];
        
        // 🔥 LƯU VÀO CACHE
        cachedPendingSuggestionsCount = pendingSuggestions.length;
        
        if (pendingSuggestions.length > 0) {
            wrapper.style.display = 'flex';   // ✅ HIỆN WRAPPER
            dot.style.display = 'block';
            suggestionCount.textContent = pendingSuggestions.length;
        } else {
            wrapper.style.display = 'none';   // ✅ ẨN WRAPPER
            dot.style.display = 'none';
            suggestionCount.textContent = '0';
        }
        
    } catch (error) {
        console.error('Error checking suggestions:', error);
    }
}

// 🔥 HÀM MỚI - HIỂN THỊ NÚT ĐỀ XUẤT NGAY LẬP TỨC
function showSuggestionsButtonImmediately() {
    const wrapper = document.querySelector('.suggestions-wrapper');  // ✅ THÊM
    const suggestionsBtn = document.getElementById('suggestionsBtn');
    const suggestionCount = document.getElementById('suggestionCount');
    
    if (!wrapper || !suggestionsBtn || !suggestionCount) return;  // ✅ KIỂM TRA WRAPPER
    
    if (cachedPendingSuggestionsCount > 0) {
        wrapper.style.display = 'flex';  // ✅ HIỆN WRAPPER TRƯỚC
        suggestionCount.textContent = cachedPendingSuggestionsCount;
    }
}

// ========== OPEN SUGGESTIONS PANEL ==========
async function openSuggestionsPanel() {
    // 🔥 KIỂM TRA NẾU MODAL ĐÃ TỒN TẠI → KHÔNG MỞ THÊM
    if (document.getElementById('suggestionsModal')) {
        console.log('⚠️ Modal đã mở rồi, không mở thêm');
        return;
    }
    
    if (!currentPlanId) {
        alert('⚠️ Không có lịch trình đang mở');
        return;
    }

    // ✅ Đóng tạm Food Planner khi mở popup chia sẻ (KHÔNG reset data)
    const panel = document.getElementById('foodPlannerPanel');
    if (panel) {
        panel.dataset.prevActiveShare = panel.classList.contains('active') ? '1' : '0';
        panel.classList.remove('active');
    }
    window._prevIsPlannerOpenShare = isPlannerOpen;
    isPlannerOpen = false;

    // ✅ Khóa scroll nền
    document.body.dataset.prevOverflowShare = document.body.style.overflow || '';
    document.body.style.overflow = 'hidden';
    
    try {
        const response = await fetch(`/api/accounts/food-plan/suggestions/${currentPlanId}/`);
        const data = await response.json();
        
        if (data.status !== 'success' || !data.suggestions || data.suggestions.length === 0) {
            alert('ℹ️ Không có đề xuất nào');
            return;
        }
        
        // 🔥 LỌC CHỈ LẤY PENDING
        const suggestions = data.suggestions.filter(s => s.status === 'pending');
        
        if (suggestions.length === 0) {
            alert('ℹ️ Không còn đề xuất pending nào');
            return;
        }
        
        // 🔥 TẠO HTML CHO MỖI ĐỀ XUẤT - MỖI NGƯỜI 1 CARD
        const suggestionsHTML = suggestions.map((sug, index) => {
            return `
                <div class="suggestion-card-item" style="
                    animation-delay: ${index * 0.1}s;
                    background: #FFFFFF;
                    border-radius: 18px;
                    margin-bottom: 14px;
                    font-family: 'Montserrat', sans-serif;
                    position: relative;
                    box-shadow: 0 4px 16px rgba(255, 126, 75, 0.15);
                    overflow: hidden;
                    border: 1px solid #FFE5D9;
                    padding: 16px 20px;
                ">
                    <!-- Header -->
                    <div class="suggestion-item-title" style="
                        font-size: 14px;
                        font-weight: 600;
                        color: #1f2933;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        letter-spacing: -0.01em;
                        margin-bottom: 8px;
                    ">
                        <span style="font-size: 16px;">👤</span>
                        ${sug.suggested_by_username}
                        
                        <span class="notification-status-badge" style="
                            margin-left: auto;
                            font-size: 10px;
                            font-weight: 700;
                            padding: 3px 8px;
                            border-radius: 12px;
                            background: linear-gradient(135deg, #FFB084, #FF8E53);
                            color: #ffffff;
                            box-shadow: 0 2px 6px rgba(255, 126, 75, 0.4);
                        ">
                            Mới
                        </span>
                    </div>
                    
                    <!-- Time -->
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        font-size: 11px;
                        color: #6b7280;
                        margin-bottom: 10px;
                        font-weight: 500;
                    ">
                        <span>🕐</span>
                        <span>${new Date(sug.created_at).toLocaleString('vi-VN')}</span>
                    </div>
                    
                    <!-- Message -->
                    ${sug.message ? `
                        <div class="notification-item-message" style="
                            font-size: 13px;
                            color: #555555;
                            line-height: 1.5;
                            margin-bottom: 12px;
                            background: #FFF5F0;
                            padding: 10px;
                            border-radius: 10px;
                            border-left: 3px solid #FFB084;
                        ">
                            ${sug.message}
                        </div>
                    ` : ''}
                    
                    <!-- Action Buttons -->
                    <div style="display: flex; gap: 8px; margin-top: 12px;">
                        <button class="sug-btn-detail" onclick="viewSuggestionComparison(${sug.id})" style="
                            flex: 1;
                            border: none;
                            padding: 10px 18px;
                            border-radius: 25px;
                            background: #FFFFFF;
                            color: #FF8E53;
                            font-size: 13px;
                            font-weight: 600;
                            cursor: pointer;
                            font-family: 'Montserrat', sans-serif;
                            border: 1px solid #FFE5D9;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            gap: 6px;
                            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                        " onmouseenter="this.style.background='linear-gradient(135deg, #FFB084 0%, #FF8E53 100%)'; this.style.color='#ffffff'; this.style.transform='translateY(-2px) scale(1.02)'; this.style.boxShadow='0 8px 24px rgba(255, 126, 75, 0.7)'"
                        onmouseleave="this.style.background='#FFFFFF'; this.style.color='#FF8E53'; this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='none'">
                            Xem chi tiết
                        </button>
                        
                        <button class="sug-btn-approve" onclick="approveSuggestion(${sug.id})" style="
                            flex: 1;
                            border: none;
                            padding: 10px 18px;
                            border-radius: 25px;
                            background: #FFFFFF;
                            color: #4CAF50;
                            font-size: 13px;
                            font-weight: 600;
                            cursor: pointer;
                            font-family: 'Montserrat', sans-serif;
                            border: 1px solid #E8F5E9;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            gap: 6px;
                            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                        " onmouseenter="this.style.background='linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%)'; this.style.color='#ffffff'; this.style.transform='translateY(-2px) scale(1.02)'; this.style.boxShadow='0 8px 24px rgba(76, 175, 80, 0.5)'"
                        onmouseleave="this.style.background='#FFFFFF'; this.style.color='#4CAF50'; this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='none'">
                            Chấp nhận
                        </button>
                        
                        <button class="sug-btn-reject" onclick="rejectSuggestion(${sug.id})" style="
                            flex: 1;
                            border: none;
                            padding: 10px 18px;
                            border-radius: 25px;
                            background: #FFFFFF;
                            color: #EF4444;
                            font-size: 13px;
                            font-weight: 600;
                            cursor: pointer;
                            font-family: 'Montserrat', sans-serif;
                            border: 1px solid #FFEBEE;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            gap: 6px;
                            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                        " onmouseenter="this.style.background='linear-gradient(135deg, #F87171 0%, #EF4444 100%)'; this.style.color='#ffffff'; this.style.transform='translateY(-2px) scale(1.02)'; this.style.boxShadow='0 8px 24px rgba(239, 68, 68, 0.5)'"
                        onmouseleave="this.style.background='#FFFFFF'; this.style.color='#EF4444'; this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='none'">
                            Từ chối
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // 🔥 TẠO MODAL VỚI HEADER GIỐNG NOTIFICATION
        const modalHTML = `
            <div id="suggestionsModal" style="
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.5);
                backdrop-filter: blur(4px);
                z-index: 99999999999999;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                animation: fadeIn 0.3s ease;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.96);
                    backdrop-filter: blur(26px) saturate(180%);
                    border-radius: 28px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 85vh;
                    border: 1px solid #FFE5D9;
                    box-shadow: 0 10px 35px rgba(148, 85, 45, 0.25), 0 24px 60px rgba(203, 92, 37, 0.18);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    font-family: 'Montserrat', sans-serif;
                ">
                    <!-- Header giống notification -->
                    <div style="
                        position: relative;
                        padding: 18px 24px 14px;
                        background: linear-gradient(135deg, rgba(255, 107, 53, 0.14) 0%, rgba(255, 142, 83, 0.10) 100%);
                        color: #1f2933;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        border-bottom: 1px solid #FFE5D9;
                    ">
                        <div style="
                            display: flex;
                            align-items: center;
                            gap: 10px;
                            font-weight: 700;
                            font-size: 18px;
                            letter-spacing: -0.02em;
                            background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                        ">
                            <span style="font-size: 20px; -webkit-text-fill-color: initial;">🔔</span>
                            Đề xuất chỉnh sửa
                        </div>
                        
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="
                                background: #FFFFFF;
                                border: 2px solid #FF8E53;
                                border-radius: 12px;
                                padding: 4px 12px;
                                font-size: 13px;
                                font-weight: 700;
                                color: #FF8E53;
                            ">
                                ${suggestions.length}
                            </div>
                            
                            <button onclick="closeSuggestionsModal()" style="
                                background: rgba(255, 255, 255, 0.9);
                                border: 1px solid #FFE5D9;
                                color: #94a3b8;
                                font-size: 20px;
                                width: 32px;
                                height: 32px;
                                border-radius: 50%;
                                cursor: pointer;
                                display: inline-flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                                font-weight: 300;
                            " onmouseenter="this.style.background='#FF8E53'; this.style.color='#ffffff'; this.style.transform='rotate(90deg)'; this.style.borderColor='#FF8E53'"
                            onmouseleave="this.style.background='rgba(255, 255, 255, 0.9)'; this.style.color='#94a3b8'; this.style.transform='rotate(0deg)'; this.style.borderColor='#FFE5D9'">
                                ×
                            </button>
                        </div>
                    </div>
                    
                    <!-- Danh sách đề xuất - scroll như notification -->
                    <div style="
                        padding: 12px 16px;
                        overflow-y: auto;
                        max-height: 65vh;
                        background: #FFF5F0;
                    " class="notification-list">
                        ${suggestionsHTML}
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
    } catch (error) {
        console.error('Error loading suggestions:', error);
        alert('Không thể tải đề xuất');
    }
}

function closeSuggestionsModal() {
    const modal = document.getElementById('suggestionsModal');
    if (modal) modal.remove();
    
    // ✅ Mở lại Food Planner như lúc trước khi mở popup
    const panel = document.getElementById('foodPlannerPanel');
    if (panel && panel.dataset.prevActiveShare === '1') {
        panel.classList.add('active');
        isPlannerOpen = true;
    } else {
        isPlannerOpen = false;
    }
    if (panel) delete panel.dataset.prevActiveShare;

    // ✅ Mở lại scroll nền
    document.body.style.overflow = document.body.dataset.prevOverflowShare || '';
    delete document.body.dataset.prevOverflowShare;
}

// ========== VIEW SUGGESTION COMPARISON ==========
// ==============================
// ✅ COMPARISON MODAL - ORANGE THEME (render only, logic unchanged)
// ==============================

function ensureComparisonStyles() {
    if (document.getElementById('comparisonModalStyles')) return;

    const style = document.createElement('style');
    style.id = 'comparisonModalStyles';
    style.textContent = `
/* ===== Comparison Modal (match notification vibe) ===== */
#comparisonModal.cmp-overlay{
  --cmp-orange-1:#FFB084;
  --cmp-orange-2:#FF8E53;
  --cmp-orange-3:#FF6B35;
  --cmp-ink:#1f2933;
  --cmp-sub:#6b7280;
  --cmp-bg:#FFF5F0;
  --cmp-border:#FFE5D9;

  position:fixed;
  inset:0;
  background: rgba(0,0,0,0.20);              /* tối vừa phải */
  backdrop-filter: blur(12px) saturate(100%); /* mờ nền */
  -webkit-backdrop-filter: blur(12px) saturate(120%);
  display:flex;
  align-items:center;
  justify-content:center;
  z-index:2147483647;
  padding:20px;
  animation: cmpFadeIn 0.22s ease;
}

@keyframes cmpFadeIn{
  from{opacity:0;}
  to{opacity:1;}
}

#comparisonModal .cmp-modal{
  width:100%;
  max-width:980px;
  max-height:86vh;
  background: rgba(255,255,255,0.96);
  backdrop-filter: blur(26px) saturate(180%);
  -webkit-backdrop-filter: blur(26px) saturate(180%);
  border:1px solid var(--cmp-border);
  border-radius:28px;
  box-shadow:
    0 10px 35px rgba(148, 85, 45, 0.22),
    0 24px 60px rgba(203, 92, 37, 0.14),
    inset 0 1px 0 rgba(255,255,255,0.9);
  overflow:hidden;
  display:flex;
  flex-direction:column;
  font-family:"Montserrat",sans-serif;
  animation: cmpPopIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes cmpPopIn{
  from{opacity:0; transform: translateY(26px) scale(0.96);}
  to{opacity:1; transform: translateY(0) scale(1);}
}

#comparisonModal .cmp-header{
  position:relative;
  padding:18px 24px 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  background: linear-gradient(135deg, rgba(255,107,53,0.14) 0%, rgba(255,142,83,0.10) 100%);
  border-bottom:1px solid var(--cmp-border);
}

#comparisonModal .cmp-header::before{
  content:"";
  position:absolute;
  top:0; left:0; right:0;
  height:1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.85), transparent);
}

#comparisonModal .cmp-title{
  display:flex;
  align-items:center;
  gap:10px;
  font-weight:700;
  font-size:18px;
  letter-spacing:-0.02em;
  background: linear-gradient(135deg, var(--cmp-orange-1) 0%, var(--cmp-orange-2) 100%);
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
}

#comparisonModal .cmp-title .cmp-title-icon{
  -webkit-text-fill-color: initial;
  color: var(--cmp-orange-2);
  filter: drop-shadow(0 6px 10px rgba(255,126,75,0.25));
  font-size:20px;
}

#comparisonModal .cmp-close{
  background: rgba(255,255,255,0.9);
  border: 1px solid var(--cmp-border);
  color: #94a3b8;
  font-size:20px;
  width:32px;
  height:32px;
  border-radius:50%;
  cursor:pointer;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight:300;
}

#comparisonModal .cmp-close:hover{
  background:#fff;
  color: var(--cmp-orange-1);
  transform: rotate(90deg);
  border-color: var(--cmp-orange-1);
  box-shadow: 0 4px 14px rgba(255,126,75,0.35);
}

#comparisonModal .cmp-body{
  padding:14px 16px 18px;
  background: var(--cmp-bg);
  overflow:auto;
}

#comparisonModal .cmp-body::-webkit-scrollbar{ width:6px; }
#comparisonModal .cmp-body::-webkit-scrollbar-track{
  background: var(--cmp-border);
  border-radius:10px;
  margin:8px 0;
}
#comparisonModal .cmp-body::-webkit-scrollbar-thumb{
  background: linear-gradient(135deg, var(--cmp-orange-1), var(--cmp-orange-2));
  border-radius:10px;
  border:2px solid transparent;
  background-clip: padding-box;
}

#comparisonModal .cmp-grid{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:16px;
}

@media (max-width: 860px){
  #comparisonModal .cmp-grid{ grid-template-columns: 1fr; }
}

#comparisonModal .cmp-col{
  background: rgba(255,255,255,0.55);
  border: 1px solid rgba(255,229,217,0.9);
  border-radius: 22px;
  overflow:hidden;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
}

#comparisonModal .cmp-col-head{
  padding:14px 16px 12px;
  border-bottom:1px solid var(--cmp-border);
  background: linear-gradient(135deg, rgba(255,176,132,0.16), rgba(255,142,83,0.10));
}

#comparisonModal .cmp-col-title{
  font-weight:700;
  font-size:14px;
  color: var(--cmp-ink);
  letter-spacing:-0.01em;
}

#comparisonModal .cmp-col-content{
  padding:12px 12px 6px;
}

#comparisonModal .cmp-empty{
  padding:26px 14px;
  text-align:center;
  color: var(--cmp-sub);
  font-size:13px;
  font-weight:500;
}

#comparisonModal .cmp-card{
  position:relative;
  background:#fff;
  border:1px solid var(--cmp-border);
  border-radius:18px;
  padding:12px 12px 12px;
  margin-bottom:10px;
  overflow:hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 10px rgba(148,85,45,0.06);
}

#comparisonModal .cmp-card::before{
  content:"";
  position:absolute;
  inset:0;
  background: linear-gradient(135deg, rgba(255,107,53,0.10), rgba(255,142,83,0.06));
  opacity:0;
  transition: opacity 0.25s ease;
}

#comparisonModal .cmp-card:hover{
  border-color: var(--cmp-orange-1);
  box-shadow: 0 10px 24px rgba(255,126,75,0.16);
}

#comparisonModal .cmp-card:hover::before{ opacity:1; }

/* gentle shine (not too bright) */
#comparisonModal .cmp-card:not(.cmp-locked)::after{
  content:"";
  position:absolute;
  top:0; left:-120%;
  width:80%;
  height:100%;
  background: linear-gradient(90deg, transparent, rgba(255,176,132,0.22), transparent);
  transform: skewX(-12deg);
  animation: cmpShine 3.2s ease-in-out infinite;
  pointer-events:none;
}
@keyframes cmpShine{
  0%{ left:-120%; }
  55%, 100%{ left:140%; }
}

#comparisonModal .cmp-locked{
  opacity:0.55;
  pointer-events:none;
}

#comparisonModal .cmp-tag{
  position:absolute;
  top:10px;
  right:10px;
  padding:4px 10px;
  border-radius:999px;
  font-size:11px;
  font-weight:800;
  letter-spacing:0.02em;
  color:#fff;
  z-index:3;
  box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}

#comparisonModal .cmp-tag.added{
  background: linear-gradient(135deg, rgba(16,185,129,0.95), rgba(34,197,94,0.92));
}
#comparisonModal .cmp-tag.removed{
  background: linear-gradient(135deg, rgba(239,68,68,0.95), rgba(244,63,94,0.92));
}
#comparisonModal .cmp-tag.modified{
  background: linear-gradient(135deg, var(--cmp-orange-1), var(--cmp-orange-2));
}

#comparisonModal .cmp-main{
  position:relative;
  z-index:2;
  padding-top:22px;
}

#comparisonModal .cmp-row{
  display:flex;
  align-items:flex-start;
  gap:10px;
}

#comparisonModal .cmp-emoji{
  font-size:20px;
  line-height:1;
  margin-top:1px;
  filter: drop-shadow(0 6px 10px rgba(255,126,75,0.10));
}

#comparisonModal .cmp-text{ flex:1; min-width:0; }

#comparisonModal .cmp-titleline{
  font-weight:700;
  font-size:13px;
  color: var(--cmp-ink);
  letter-spacing:-0.01em;
}

#comparisonModal .cmp-subline{
  margin-top:4px;
  font-size:12px;
  color:#555;
}

#comparisonModal .cmp-subline.muted{ color:#8b8b8b; }

#comparisonModal .cmp-subline.small{
  font-size:11px;
  color:#6b7280;
}

#comparisonModal .cmp-strike{
  text-decoration: line-through;
  opacity: 0.85;
}

#comparisonModal .cmp-divider{
  height:1px;
  background: rgba(255,229,217,0.9);
  margin:12px 0 10px;
}

#comparisonModal .cmp-actions{
  display:flex;
  gap:10px;
}

#comparisonModal .cmp-btn{
  flex:1;
  border:none;
  padding:10px 12px;
  border-radius:16px;
  font-size:12px;
  font-weight:700;
  cursor:pointer;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:6px;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

#comparisonModal .cmp-btn:active{ transform: scale(0.98); }

#comparisonModal .cmp-btn-approve{
  background: linear-gradient(135deg, rgba(16,185,129,0.95), rgba(34,197,94,0.92));
  color:#fff;
  box-shadow: 0 8px 18px rgba(16,185,129,0.18);
}
#comparisonModal .cmp-btn-approve:hover{
  transform: translateY(-2px);
  box-shadow: 0 12px 22px rgba(16,185,129,0.22);
}

#comparisonModal .cmp-btn-reject{
  background: rgba(239,68,68,0.10);
  border: 1px solid rgba(239,68,68,0.25);
  color: rgba(239,68,68,0.95);
}
#comparisonModal .cmp-btn-reject:hover{
  background: rgba(239,68,68,0.92);
  color:#fff;
  border-color: rgba(239,68,68,0.92);
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(239,68,68,0.18);
}

#comparisonModal .cmp-status-badge{
  position:absolute;
  top:50%;
  left:50%;
  transform: translate(-50%, -50%);
  padding:12px 22px;
  border-radius:999px;
  font-size:13px;
  font-weight:800;
  color:#fff;
  z-index:4;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
#comparisonModal .cmp-status-badge.approved{
  background: linear-gradient(135deg, rgba(16,185,129,0.96), rgba(34,197,94,0.92));
}
#comparisonModal .cmp-status-badge.rejected{
  background: linear-gradient(135deg, rgba(239,68,68,0.96), rgba(244,63,94,0.92));
}

/* modified before/after blocks */
#comparisonModal .cmp-compare-block{
  border-radius:14px;
  padding:10px 10px;
  border: 1px solid rgba(255,229,217,0.95);
  background: rgba(255,255,255,0.85);
}
#comparisonModal .cmp-compare-label{
  font-size:11px;
  font-weight:800;
  letter-spacing:0.02em;
  color: #E65100;
  margin-bottom:6px;
}
#comparisonModal .cmp-arrow{
  text-align:center;
  font-size:18px;
  margin:8px 0;
  opacity:0.9;
}

/* footer actions (primary orange like notification-footer-btn) */
#comparisonModal .cmp-footer{
  padding:12px 16px;
  border-top:1px solid var(--cmp-border);
  background: linear-gradient(135deg, #FFF5F0 0%, #FFE5D9 100%);
  display:flex;
  gap:10px;
}

#comparisonModal .cmp-footer .cmp-footer-btn{
  flex:1;
  border:none;
  padding:10px 18px;
  border-radius:25px;
  font-size:13px;
  font-weight:600;
  cursor:pointer;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

#comparisonModal .cmp-footer .cmp-footer-primary{
  background: linear-gradient(135deg, var(--cmp-orange-1) 0%, var(--cmp-orange-2) 100%);
  color:#fff;
  box-shadow: 0 4px 16px rgba(255, 126, 75, 0.45), inset 0 1px 0 rgba(255,255,255,0.35);
}
#comparisonModal .cmp-footer .cmp-footer-primary:hover{
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 10px 24px rgba(255, 126, 75, 0.55), inset 0 1px 0 rgba(255,255,255,0.35);
}

#comparisonModal .cmp-footer .cmp-footer-danger{
  background: rgba(239,68,68,0.12);
  border:1px solid rgba(239,68,68,0.25);
  color: rgba(239,68,68,0.95);
}
#comparisonModal .cmp-footer .cmp-footer-danger:hover{
  background: rgba(239,68,68,0.92);
  border-color: rgba(239,68,68,0.92);
  color:#fff;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 10px 24px rgba(239,68,68,0.20);
}
    `;
    document.head.appendChild(style);
}

async function viewSuggestionComparison(suggestionId) {
    const suggestionsModal = document.getElementById('suggestionsModal');
    if (suggestionsModal) {
        suggestionsModal.remove();
    }

    // 🔥 KIỂM TRA NẾU MODAL ĐÃ TỒN TẠI
    if (document.getElementById('comparisonModal')) {
        console.log('⚠️ Modal so sánh đã mở rồi');
        return;
    }

    try {
        ensureComparisonStyles();

        const response = await fetch(`/api/accounts/food-plan/suggestion-detail/${suggestionId}/`);
        const data = await response.json();

        if (data.status !== 'success') {
            alert('❌ ' + data.message);
            return;
        }

        const suggestion = data.suggestion;
        const currentData = suggestion.current_data;
        const suggestedData = suggestion.suggested_data;

        // 🔥 PHÂN TÍCH THAY ĐỔI
        const changes = analyzeChanges(currentData, suggestedData);

        const comparisonHTML = `
            <div id="comparisonModal" class="cmp-overlay">
                <div class="cmp-modal">
                    <div class="cmp-header">
                        <div class="cmp-title">
                            <span class="cmp-title-icon">🔍</span>
                            <span>So sánh thay đổi</span>
                        </div>
                        <button class="cmp-close" onclick="closeComparisonModal()" aria-label="Đóng">×</button>
                    </div>

                    <div class="cmp-body">
                        <div class="cmp-grid">
                            <div class="cmp-col">
                                <div class="cmp-col-head">
                                    <div class="cmp-col-title">📅 Lịch trình hiện tại</div>
                                </div>
                                <div class="cmp-col-content">
                                    ${renderPlanPreview(currentData)}
                                </div>
                            </div>

                            <div class="cmp-col">
                                <div class="cmp-col-head">
                                    <div class="cmp-col-title">✨ Đề xuất thay đổi</div>
                                </div>
                                <div class="cmp-col-content">
                                    ${renderChangesWithActions(changes, suggestionId)}
                                </div>
                            </div>
                        </div>
                    </div>

                    ${suggestion.status === 'pending' && changes.length > 0 ? `
                        <div class="cmp-footer">
                            <button class="cmp-footer-btn cmp-footer-primary" onclick="approveAllChanges(${suggestionId})">
                                Lưu thay đổi
                            </button>
                            <button class="cmp-footer-btn cmp-footer-danger" onclick="rejectSuggestion(${suggestionId})">
                                Từ chối toàn bộ đề xuất
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', comparisonHTML);

    } catch (error) {
        console.error('Error loading comparison:', error);
        alert('Không thể tải chi tiết');
    }
}

// ========== ANALYZE CHANGES ==========
function analyzeChanges(currentData, suggestedData) {
    const changes = [];

    // Tạo map để dễ so sánh
    const currentMap = {};
    const suggestedMap = {};

    currentData.forEach(item => {
        currentMap[item.key] = item.data;
    });

    suggestedData.forEach(item => {
        suggestedMap[item.key] = item.data;
    });

    // 1. Tìm quán BỊ XÓA (có trong current nhưng không có trong suggested)
    currentData.forEach(item => {
        if (!suggestedMap[item.key]) {
            changes.push({
                type: 'removed',
                key: item.key,
                data: item.data
            });
        }
    });

    // 2. Tìm quán MỚI THÊM (có trong suggested nhưng không có trong current)
    suggestedData.forEach(item => {
        if (!currentMap[item.key]) {
            changes.push({
                type: 'added',
                key: item.key,
                data: item.data
            });
        }
    });

    // 3. Tìm quán BỊ THAY ĐỔI (cùng key nhưng khác place hoặc time/title)
    suggestedData.forEach(item => {
        if (currentMap[item.key]) {
            const current = currentMap[item.key];
            const suggested = item.data;

            // So sánh place
            const placeChanged =
                current.place?.data_id !== suggested.place?.data_id;

            // So sánh time hoặc title
            const detailsChanged =
                current.time !== suggested.time ||
                current.title !== suggested.title ||
                current.icon !== suggested.icon;

            if (placeChanged || detailsChanged) {
                changes.push({
                    type: 'modified',
                    key: item.key,
                    oldData: current,
                    newData: suggested
                });
            }
        }
    });

    return changes;
}

// ========== RENDER CHANGES WITH ACTION BUTTONS ==========
function renderChangesWithActions(changes, suggestionId) {
    if (changes.length === 0) {
        return `
            <div class="cmp-empty">
                <div style="font-size:44px; opacity:0.55; margin-bottom:10px;">🟧</div>
                Không có thay đổi nào
            </div>
        `;
    }

    // 🔥 LẤY TRẠNG THÁI ĐÃ LƯU
    const pending = pendingApprovals[suggestionId] || { approvedChanges: [], rejectedChanges: [] };

    return changes.map((change, index) => {
        // 🔥 KIỂM TRA ĐÃ APPROVE/REJECT CHƯA
        const isApproved = pending.approvedChanges.some(c => c.changeKey === change.key);
        const isRejected = pending.rejectedChanges.some(c => c.changeKey === change.key);
        const lockedClass = (isApproved || isRejected) ? 'cmp-locked' : '';

        const badgeHTML = isApproved
            ? `<div class="cmp-status-badge approved">Đã đánh dấu chấp nhận</div>`
            : isRejected
                ? `<div class="cmp-status-badge rejected">Đã đánh dấu từ chối</div>`
                : '';

        if (change.type === 'added') {
            const meal = change.data;
            const place = meal.place;

            return `
                <div id="change-${index}" class="cmp-card ${lockedClass}">
                    ${badgeHTML}
                    <div class="cmp-tag added">THÊM MỚI</div>

                    <div class="cmp-main">
                        <div class="cmp-row">
                            <div class="cmp-emoji">${meal.icon || '🍽️'}</div>
                            <div class="cmp-text">
                                <div class="cmp-titleline">⏰ ${meal.time} - ${meal.title}</div>
                                ${place ? `
                                    <div class="cmp-subline">🏪 ${place.ten_quan}</div>
                                    <div class="cmp-subline small">📍 ${place.dia_chi}</div>
                                ` : `<div class="cmp-subline muted">Chưa có quán</div>`}
                            </div>
                        </div>

                        <div class="cmp-divider"></div>

                        <div class="cmp-actions">
                            <button class="cmp-btn cmp-btn-approve"
                                onclick="approveChange(${suggestionId}, ${index}, 'added', '${change.key}')">
                                Chấp nhận
                            </button>
                            <button class="cmp-btn cmp-btn-reject"
                                onclick="rejectChange(${suggestionId}, ${index}, 'added', '${change.key}')">
                                Từ chối
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (change.type === 'removed') {
            const meal = change.data;
            const place = meal.place;

            return `
                <div id="change-${index}" class="cmp-card ${lockedClass}">
                    ${badgeHTML}
                    <div class="cmp-tag removed">XÓA BỎ</div>

                    <div class="cmp-main">
                        <div class="cmp-row">
                            <div class="cmp-emoji">${meal.icon || '🍽️'}</div>
                            <div class="cmp-text">
                                <div class="cmp-titleline cmp-strike">⏰ ${meal.time} - ${meal.title}</div>
                                ${place ? `
                                    <div class="cmp-subline cmp-strike">🏪 ${place.ten_quan}</div>
                                ` : ``}
                            </div>
                        </div>

                        <div class="cmp-divider"></div>

                        <div class="cmp-actions">
                            <button class="cmp-btn cmp-btn-approve"
                                onclick="approveChange(${suggestionId}, ${index}, 'removed', '${change.key}')">
                                Đồng ý xóa
                            </button>
                            <button class="cmp-btn cmp-btn-reject"
                                onclick="rejectChange(${suggestionId}, ${index}, 'removed', '${change.key}')">
                                Giữ lại
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // modified
        if (change.type === 'modified') {
            const oldMeal = change.oldData;
            const newMeal = change.newData;

            return `
                <div id="change-${index}" class="cmp-card ${lockedClass}">
                    ${badgeHTML}
                    <div class="cmp-tag modified">THAY ĐỔI</div>

                    <div class="cmp-main">
                        <div class="cmp-compare-block" style="opacity:0.78;">
                            <div class="cmp-compare-label">Trước</div>
                            <div class="cmp-row">
                                <div class="cmp-emoji">${oldMeal.icon || '🍽️'}</div>
                                <div class="cmp-text">
                                    <div class="cmp-titleline">⏰ ${oldMeal.time} - ${oldMeal.title}</div>
                                    ${oldMeal.place ? `<div class="cmp-subline small">🏪 ${oldMeal.place.ten_quan}</div>` : ``}
                                </div>
                            </div>
                        </div>

                        <div class="cmp-arrow">\n</div>

                        <div class="cmp-compare-block" style="border-color: rgba(255,176,132,0.9);">
                            <div class="cmp-compare-label">Sau</div>
                            <div class="cmp-row">
                                <div class="cmp-emoji">${newMeal.icon || '🍽️'}</div>
                                <div class="cmp-text">
                                    <div class="cmp-titleline">⏰ ${newMeal.time} - ${newMeal.title}</div>
                                    ${newMeal.place ? `<div class="cmp-subline small">🏪 ${newMeal.place.ten_quan}</div>` : ``}
                                </div>
                            </div>
                        </div>

                        <div class="cmp-divider"></div>

                        <div class="cmp-actions">
                            <button class="cmp-btn cmp-btn-approve"
                                onclick="approveChange(${suggestionId}, ${index}, 'modified', '${change.key}')">
                                Chấp nhận
                            </button>
                            <button class="cmp-btn cmp-btn-reject"
                                onclick="rejectChange(${suggestionId}, ${index}, 'modified', '${change.key}')">
                                Từ chối
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        return '';
    }).join('');
}

function renderPlanPreview(planData) {
    if (!planData || planData.length === 0) {
        return `
            <div class="cmp-empty">
                <div style="font-size:42px; opacity:0.55; margin-bottom:10px;">📭</div>
                Không có dữ liệu
            </div>
        `;
    }

    return planData.map((item) => {
        const meal = item.data;
        const place = meal.place;

        return `
            <div class="cmp-card">
                <div class="cmp-main" style="padding-top:0;">
                    <div class="cmp-row">
                        <div class="cmp-emoji">${meal.icon || '🍽️'}</div>
                        <div class="cmp-text">
                            <div class="cmp-titleline">⏰ ${meal.time} - ${meal.title}</div>
                            ${place ? `
                                <div class="cmp-subline">🏪 ${place.ten_quan}</div>
                            ` : `<div class="cmp-subline muted">Chưa có quán</div>`}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function closeComparisonModal() {
    const modal = document.getElementById('comparisonModal');
    if (modal) modal.remove();

    // ✅ Mở lại Food Planner như lúc trước khi mở popup
    const panel = document.getElementById('foodPlannerPanel');
    if (panel && panel.dataset.prevActiveShare === '1') {
        panel.classList.add('active');
        isPlannerOpen = true;
    } else {
        isPlannerOpen = false;
    }
    if (panel) delete panel.dataset.prevActiveShare;

    // ✅ Mở lại scroll nền
    document.body.style.overflow = document.body.dataset.prevOverflowShare || '';
    delete document.body.dataset.prevOverflowShare;

}


async function approveSuggestion(suggestionId) {
    if (!confirm('✅ Xác nhận chấp nhận đề xuất này?')) return;
    
    try {
        const response = await fetch(`/api/accounts/food-plan/suggestion-approve/${suggestionId}/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 🔥 HIỂN THỊ THÔNG BÁO VỀ SỐ ĐỀ XUẤT BỊ TỪ CHỐI
            let alertMsg = '✅ Đã chấp nhận đề xuất!';
            if (result.rejected_count && result.rejected_count > 0) {
                alertMsg += `\n\n🔄 Đã tự động từ chối ${result.rejected_count} đề xuất khác.`;
            }
            alert(alertMsg);
            
            // Đóng tất cả modal
            closeComparisonModal();
            closeSuggestionsModal();
            
            // 🔥 CẬP NHẬT SỐ LƯỢNG ĐỀ XUẤT PENDING
            if (currentPlanId) {
                await checkPendingSuggestions(currentPlanId);
                await loadSavedPlans(currentPlanId);
            }
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        console.error('Error approving suggestion:', error);
        alert('Không thể chấp nhận đề xuất');
    }
}
async function rejectSuggestion(suggestionId) {
    if (!confirm('❌ Xác nhận từ chối TOÀN BỘ đề xuất này?')) return;
    
    try {
        const response = await fetch(`/api/accounts/food-plan/suggestion-reject/${suggestionId}/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 🔥 XÓA TRẠNG THÁI TẠM
            delete pendingApprovals[suggestionId];
            
            alert('✅ Đã từ chối toàn bộ đề xuất!');
            
            closeComparisonModal();
            closeSuggestionsModal();
            
            if (currentPlanId) {
                await checkPendingSuggestions(currentPlanId);
            }
            // 🔥 THÊM: Reset pending status nếu đang xem shared plan
            if (isViewingSharedPlan && hasEditPermission) {
                hasPendingSuggestion = false;
                updateSubmitSuggestionButton();
            }
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        console.error('Error rejecting suggestion:', error);
        alert('Không thể từ chối đề xuất');
    }
}

// ========== EXIT SHARED PLAN VIEW ==========
function exitSharedPlanView() {
    if (!confirm('Bạn có chắc muốn thoát chế độ xem shared plan?')) return;
    
    // Reset tất cả trạng thái
    isViewingSharedPlan = false;
    isSharedPlan = false;
    sharedPlanOwnerId = null;
    sharedPlanOwnerName = '';
    hasEditPermission = false;
    currentPlan = null;
    currentPlanId = null;
    isEditMode = false;
    waitingForPlaceSelection = null;
    
    // Xóa routes trên map
    clearRoutes();
    
    // Clear nội dung
    const resultDiv = document.getElementById('planResult');
    if (resultDiv) {
        resultDiv.innerHTML = '';
    }
    
    // Hiện lại filters
    const filtersWrapper = document.querySelector('.filters-wrapper-new');
    if (filtersWrapper) {
        filtersWrapper.style.display = 'block';
    }
    
    // 🔥 ẨN NÚT X KHI THOÁT CHẾ ĐỘ XEM
    const exitBtn = document.getElementById('exitSharedPlanBtn');
    if (exitBtn) {
        exitBtn.style.display = 'none';
    }
    
    // Reload danh sách plans
    loadSavedPlans();
    
    console.log('✅ Đã thoát chế độ xem shared plan');
}

// ========== APPROVE SINGLE CHANGE - CHỈ LƯU TRẠNG THÁI TẠM ==========
async function approveChange(suggestionId, changeIndex, changeType, changeKey) {
    if (!confirm('✅ Xác nhận chấp nhận thay đổi này?')) return;
    
    // 🔥 KHỞI TẠO NẾU CHƯA CÓ
    if (!pendingApprovals[suggestionId]) {
        pendingApprovals[suggestionId] = {
            approvedChanges: [],
            rejectedChanges: []
        };
    }
    
    // 🔥 LƯU VÀO DANH SÁCH TẠM
    const changeInfo = { changeIndex, changeType, changeKey };
    
    // Xóa khỏi rejected nếu có
    pendingApprovals[suggestionId].rejectedChanges = 
        pendingApprovals[suggestionId].rejectedChanges.filter(c => c.changeKey !== changeKey);
    
    // Thêm vào approved (nếu chưa có)
    if (!pendingApprovals[suggestionId].approvedChanges.some(c => c.changeKey === changeKey)) {
        pendingApprovals[suggestionId].approvedChanges.push(changeInfo);
    }
    
    console.log('✅ Đã lưu trạng thái tạm:', pendingApprovals[suggestionId]);
    
    // 🔥 THAY THẾ 2 NÚT BẰNG 1 NÚT DUY NHẤT
    const changeEl = document.getElementById(`change-${changeIndex}`);
    if (changeEl) {
        const actionsDiv = changeEl.querySelector('.cmp-actions');
        if (actionsDiv) {
            actionsDiv.innerHTML = `
                <button class="cmp-btn" style="
                    flex: 1;
                    background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(34,197,94,0.12));
                    border: 1px solid rgba(16,185,129,0.3);
                    color: rgba(16,185,129,0.95);
                    cursor: not-allowed;
                    pointer-events: none;
                ">
                    Đã đánh dấu chấp nhận
                </button>
            `;
        }
    }
}

// ========== REJECT SINGLE CHANGE - CHỈ LƯU TRẠNG THÁI TẠM ==========
async function rejectChange(suggestionId, changeIndex, changeType, changeKey) {
    if (!confirm('❌ Xác nhận từ chối thay đổi này?')) return;
    
    // 🔥 KHỞI TẠO NẾU CHƯA CÓ
    if (!pendingApprovals[suggestionId]) {
        pendingApprovals[suggestionId] = {
            approvedChanges: [],
            rejectedChanges: []
        };
    }
    
    // 🔥 LƯU VÀO DANH SÁCH TẠM
    const changeInfo = { changeIndex, changeType, changeKey };
    
    // Xóa khỏi approved nếu có
    pendingApprovals[suggestionId].approvedChanges = 
        pendingApprovals[suggestionId].approvedChanges.filter(c => c.changeKey !== changeKey);
    
    // Thêm vào rejected (nếu chưa có)
    if (!pendingApprovals[suggestionId].rejectedChanges.some(c => c.changeKey === changeKey)) {
        pendingApprovals[suggestionId].rejectedChanges.push(changeInfo);
    }
    
    console.log('❌ Đã lưu trạng thái từ chối:', pendingApprovals[suggestionId]);
    
    // 🔥 THAY THẾ 2 NÚT BẰNG 1 NÚT DUY NHẤT
    const changeEl = document.getElementById(`change-${changeIndex}`);
    if (changeEl) {
        const actionsDiv = changeEl.querySelector('.cmp-actions');
        if (actionsDiv) {
            actionsDiv.innerHTML = `
                <button class="cmp-btn" style="
                    flex: 1;
                    background: rgba(239,68,68,0.12);
                    border: 1px solid rgba(239,68,68,0.25);
                    color: rgba(239,68,68,0.95);
                    cursor: not-allowed;
                    pointer-events: none;
                ">
                    Đã đánh dấu từ chối
                </button>
            `;
        }
    }
}

async function approveAllChanges(suggestionId) {
    const pending = pendingApprovals[suggestionId];
    
    // 🔥 BƯỚC 1: Lấy tổng số thay đổi từ suggestion
    let totalChanges = 0;
    try {
        const response = await fetch(`/api/accounts/food-plan/suggestion-detail/${suggestionId}/`);
        const data = await response.json();
        
        if (data.status !== 'success') {
            alert('❌ ' + data.message);
            return;
        }
        
        const suggestion = data.suggestion;
        const changes = analyzeChanges(suggestion.current_data, suggestion.suggested_data);
        totalChanges = changes.length;
        
        // 🔥 CASE 1: Không đánh dấu gì cả → Chấp nhận TẤT CẢ
        if (!pending || (!pending.approvedChanges.length && !pending.rejectedChanges.length)) {
            if (!confirm(`Bạn chưa xử lý bất kỳ thay đổi nào.\n\n✅ Xác nhận chấp nhận TẤT CẢ ${totalChanges} thay đổi?`)) {
                return;
            }
            
            // Tự động chấp nhận tất cả
            if (!pendingApprovals[suggestionId]) {
                pendingApprovals[suggestionId] = {
                    approvedChanges: [],
                    rejectedChanges: []
                };
            }
            
            changes.forEach((change, index) => {
                pendingApprovals[suggestionId].approvedChanges.push({
                    changeIndex: index,
                    changeType: change.type,
                    changeKey: change.key
                });
            });
            
            console.log('✅ Đã tự động chấp nhận tất cả thay đổi:', pendingApprovals[suggestionId]);
        }
        // 🔥 CASE 2: Đã đánh dấu một vài cái → KIỂM TRA có xử lý hết chưa
        else {
            const approvedCount = pending.approvedChanges.length;
            const rejectedCount = pending.rejectedChanges.length;
            const processedCount = approvedCount + rejectedCount;
            
            // Nếu chưa xử lý hết → BẮT BUỘC phải xử lý hết
            if (processedCount < totalChanges) {
                const remainingCount = totalChanges - processedCount;
                alert(`⚠️ Bạn còn ${remainingCount} thay đổi chưa xử lý!\n\n` +
                      `📊 Tổng: ${totalChanges} thay đổi\n` +
                      `✅ Đã chấp nhận: ${approvedCount}\n` +
                      `❌ Đã từ chối: ${rejectedCount}\n\n` +
                      `Vui lòng xử lý HẾT các thay đổi còn lại trước khi lưu.`);
                return;
            }
            
               // 🔥 CASE ĐẶC BIỆT: Nếu TẤT CẢ đều bị từ chối → Gọi API reject toàn bộ suggestion
            if (approvedCount === 0 && rejectedCount === totalChanges) {
                if (!confirm(`⚠️ Bạn đã từ chối TẤT CẢ ${totalChanges} thay đổi.\n\nXác nhận từ chối toàn bộ đề xuất này?`)) {
                    return;
                }
                
                // Gọi API reject suggestion
                try {
                    const response = await fetch(`/api/accounts/food-plan/suggestion-reject/${suggestionId}/`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'}
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('✅ Đã từ chối toàn bộ đề xuất!');
                        
                        // Xóa trạng thái tạm
                        delete pendingApprovals[suggestionId];
                        
                        // Đóng modal
                        closeComparisonModal();
                        closeSuggestionsModal();
                        
                        // Reload
                        if (currentPlanId) {
                            await checkPendingSuggestions(currentPlanId);
                        }
                        
                        // Reset pending status nếu đang xem shared plan
                        if (isViewingSharedPlan && hasEditPermission) {
                            hasPendingSuggestion = false;
                            updateSubmitSuggestionButton();
                        }
                    } else {
                        alert('❌ ' + result.message);
                    }
                    
                } catch (error) {
                    console.error('Error rejecting suggestion:', error);
                    alert('Không thể từ chối đề xuất');
                }
                
                return; // Dừng hàm, không chạy tiếp phần approve
            }
            
            // Xác nhận cuối cùng
            const confirmMsg = `📊 Tổng kết:\nChấp nhận: ${approvedCount} thay đổi\nTừ chối: ${rejectedCount} thay đổi\n\nXác nhận áp dụng các thay đổi đã chọn?`;
            
            if (!confirm(confirmMsg)) return;
        }
        
    } catch (error) {
        console.error('Error loading suggestion:', error);
        alert('⚠️ Không thể tải thông tin đề xuất');
        return;
    }
    
    // 🔥 PHẦN CODE GỬI API VẪN GIỮ NGUYÊN
    const approvedCount = pendingApprovals[suggestionId].approvedChanges.length;
    const rejectedCount = pendingApprovals[suggestionId].rejectedChanges.length;
    
    try {
        const response = await fetch('/api/accounts/food-plan/approve-all-changes/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                suggestion_id: suggestionId,
                approved_changes: pendingApprovals[suggestionId].approvedChanges
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            let alertMsg = `✅ Đã áp dụng ${result.applied_count} thay đổi!`;
            if (result.rejected_count && result.rejected_count > 0) {
                alertMsg += `\n\n🔄 Đã tự động từ chối ${result.rejected_count} đề xuất khác.`;
            }
            alert(alertMsg);
            
            delete pendingApprovals[suggestionId];
            
            closeComparisonModal();
            closeSuggestionsModal();
            
            if (currentPlanId) {
                await checkPendingSuggestions(currentPlanId);
                await loadSavedPlans(currentPlanId, true);
            }
            if (isViewingSharedPlan && hasEditPermission) {
                hasPendingSuggestion = false;
                updateSubmitSuggestionButton();
            }
        } else {
            alert('❌ ' + result.message);
        }
        
    } catch (error) {
        console.error('Error approving all changes:', error);
        alert('Không thể áp dụng thay đổi');
    }
}

// ========== VIEW MY SUGGESTIONS ==========
async function viewMySuggestions(planId) {
    // 🔥 KIỂM TRA NẾU MODAL ĐÃ TỒN TẠI → KHÔNG MỞ THÊM
    if (document.getElementById('mySuggestionsModal')) {
        console.log('⚠️ Modal đã mở rồi, không mở thêm');
        return;
    }
    
    if (!planId) {
        alert('⚠️ Không có lịch trình đang mở');
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/food-plan/my-suggestions/${planId}/`);
        const data = await response.json();
        
        if (data.status !== 'success') {
            alert('❌ ' + data.message);
            return;
        }
        
        const suggestions = data.suggestions || [];
        
        if (suggestions.length === 0) {
            alert('ℹ️ Bạn chưa gửi đề xuất nào cho lịch trình này');
            return;
        }
        
        // Tạo HTML hiển thị
        const suggestionsHTML = suggestions.map((sug, index) => {
            const statusBg = sug.status === 'pending' ? '#FFF3E0' : 
                           sug.status === 'accepted' ? '#E8F5E9' : '#FFEBEE';
            const statusColor = sug.status === 'pending' ? '#F57C00' : 
                              sug.status === 'accepted' ? '#2E7D32' : '#C62828';
            const statusIcon = sug.status === 'pending' ? '⏳' : 
                             sug.status === 'accepted' ? '✅' : '❌';
            const statusText = sug.status === 'pending' ? 'Chờ duyệt' : 
                             sug.status === 'accepted' ? 'Đã chấp nhận' : 'Đã từ chối';
            
            // 🔥 SỬA: Dùng hàm formatDateTimeWithTimezone
            const createdAtFormatted = formatDateTimeWithTimezone(sug.created_at);
            const reviewedAtFormatted = sug.reviewed_at ? 
                formatDateTimeWithTimezone(sug.reviewed_at) : null;
            
            return `
                <div style="
                    background: white;
                    border: 2px solid ${sug.status === 'pending' ? '#FF9800' : sug.status === 'accepted' ? '#4CAF50' : '#F44336'};
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 16px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <div style="font-weight: 700; color: #333; font-size: 15px; margin-bottom: 8px;">
                                📝 Đề xuất #${suggestions.length - index}
                            </div>
                            <div style="font-size: 13px; color: #666;">
                                📅 ${createdAtFormatted}
                            </div>
                            ${reviewedAtFormatted ? `
                                <div style="font-size: 13px; color: #666; margin-top: 4px;">
                                    🕐 Xét duyệt: ${reviewedAtFormatted}
                                </div>
                            ` : ''}
                        </div>
                        <span style="
                            padding: 6px 14px;
                            border-radius: 12px;
                            font-size: 13px;
                            font-weight: 700;
                            background: ${statusBg};
                            color: ${statusColor};
                        ">
                            ${statusIcon} ${statusText}
                        </span>
                    </div>
                    
                    ${sug.message ? `
                        <div style="
                            background: #F5F5F5;
                            border-left: 3px solid #FF6B35;
                            padding: 10px 12px;
                            border-radius: 6px;
                            margin-bottom: 12px;
                            font-size: 13px;
                            color: #555;
                        ">
                            💬 ${sug.message}
                        </div>
                    ` : ''}
                    
                    ${sug.status === 'accepted' ? `
                        <div style="
                            background: #E8F5E9;
                            border: 1px solid #4CAF50;
                            padding: 10px;
                            border-radius: 8px;
                            font-size: 13px;
                            color: #2E7D32;
                            font-weight: 600;
                        ">
                            ✨ Đề xuất của bạn đã được chấp nhận và áp dụng vào lịch trình!
                        </div>
                    ` : ''}
                    
                    ${sug.status === 'rejected' ? `
                        <div style="
                            background: #FFEBEE;
                            border: 1px solid #F44336;
                            padding: 10px;
                            border-radius: 8px;
                            font-size: 13px;
                            color: #C62828;
                            font-weight: 600;
                        ">
                            😔 Đề xuất của bạn đã bị từ chối
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        // Tạo modal
        const modalHTML = `
            <style>
                #mySuggestionsModal::-webkit-scrollbar {
                    width: 6px;
                }
                #mySuggestionsModal::-webkit-scrollbar-track {
                    background: transparent;
                }
                #mySuggestionsModal::-webkit-scrollbar-thumb {
                    background: #FF9A6C;
                    border-radius: 10px;
                }
                #mySuggestionsModal::-webkit-scrollbar-thumb:hover {
                    background: #FF8C5A;
                }
                .suggestions-content::-webkit-scrollbar {
                    width: 6px;
                }
                .suggestions-content::-webkit-scrollbar-track {
                    background: #FFE5D9;
                    border-radius: 10px;
                    margin: 8px 0;
                }
                .suggestions-content::-webkit-scrollbar-thumb {
                    background: linear-gradient(135deg, #FFB084, #FF8E53);
                    border-radius: 10px;
                    border: 2px solid transparent;
                    background-clip: padding-box;
                }
                
                @keyframes slideInFromLeft {
                    0% {
                        opacity: 0;
                        transform: translateX(-100%);
                    }
                    100% {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                
                @keyframes shine-slide {
                    0% {
                        left: -100%;
                    }
                    50%, 100% {
                        left: 100%;
                    }
                }
            </style>
            <div id="mySuggestionsModal" style="
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
                z-index: 99999999999999;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.96);
                    backdrop-filter: blur(26px) saturate(180%);
                    -webkit-backdrop-filter: blur(26px) saturate(180%);
                    border-radius: 28px;
                    max-width: 600px;
                    width: 100%;
                    max-height: 85vh;
                    border: 1px solid #FFE5D9;
                    box-shadow:
                        0 10px 35px rgba(148, 85, 45, 0.25),
                        0 24px 60px rgba(203, 92, 37, 0.18),
                        inset 0 1px 0 rgba(255, 255, 255, 0.9);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    font-family: 'Montserrat', sans-serif;
                ">
                <!-- HEADER -->
                <div style="
                    position: relative;
                    padding: 18px 24px 14px;
                    background: linear-gradient(
                        135deg,
                        rgba(255, 107, 53, 0.14) 0%,
                        rgba(255, 142, 83, 0.10) 100%
                    );
                    color: #1f2933;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 1px solid #FFE5D9;
                ">
                    <div style="
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 1px;
                        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
                    "></div>
                    
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        font-weight: 700;
                        font-size: 18px;
                        letter-spacing: -0.02em;
                        background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    ">
                        <span style="font-size: 20px;">🔔</span>
                        <span>Đề xuất của tôi</span>
                    </div>
                    
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 12px;
                    ">
                        <div style="
                            background: #FFFFFF;
                            border: 1px solid #FFE5D9;
                            color: #FFB084;
                            font-size: 13px;
                            font-weight: 700;
                            padding: 6px 12px;
                            border-radius: 12px;
                            box-shadow: 0 2px 4px rgba(255, 126, 75, 0.15);
                        ">${suggestions.length}</div>
                        
                        <button onclick="closeMySuggestionsModal()" style="
                            background: rgba(255, 255, 255, 0.9);
                            backdrop-filter: blur(10px);
                            border: 1px solid #FFE5D9;
                            color: #94a3b8;
                            font-size: 20px;
                            width: 32px;
                            height: 32px;
                            border-radius: 50%;
                            cursor: pointer;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                            font-weight: 300;
                        " onmouseover="this.style.background='#FFFFFF'; this.style.color='#FFB084'; this.style.transform='rotate(90deg)'; this.style.borderColor='#FFB084'; this.style.boxShadow='0 4px 14px rgba(255, 126, 75, 0.4)';" onmouseout="this.style.background='rgba(255, 255, 255, 0.9)'; this.style.color='#94a3b8'; this.style.transform='rotate(0deg)'; this.style.borderColor='#FFE5D9'; this.style.boxShadow='none';">×</button>
                    </div>
                </div>
                    
                    <!-- CONTENT -->
                    <div class="suggestions-content" style="
                        padding: 12px 16px;
                        overflow-y: auto;
                        max-height: 60vh;
                        overflow-x: hidden;
                        background: #FFF5F0;
                    ">
                        ${suggestions.map((sug, index) => {
                            const isRead = sug.status !== 'pending';
                            const statusBg = sug.status === 'pending' ? 'linear-gradient(135deg, #FFB084, #FF8E53)' : 
                                        sug.status === 'accepted' ? 'linear-gradient(135deg, #FFB084, #FF8E53)' : 'rgba(239, 68, 68, 0.15)';
                            const statusColor = sug.status === 'pending' ? '#ffffff' : 
                                            sug.status === 'accepted' ? '#ffffff' : '#EF4444';
                            const statusText = sug.status === 'pending' ? 'Mới' : 
                                            sug.status === 'accepted' ? 'Đã chấp nhận' : 'Đã từ chối';
                            const borderColor = sug.status === 'pending' ? '#FFE5D9' : 
                                            sug.status === 'accepted' ? '#FFE5D9' : 'rgba(239, 68, 68, 0.3)';
                            
                            const createdAtFormatted = formatDateTimeWithTimezone(sug.created_at);
                            const reviewedAtFormatted = sug.reviewed_at ? 
                                formatDateTimeWithTimezone(sug.reviewed_at) : null;
                            
                            return `
                                <div class="${!isRead ? 'new-item slide-in' : ''}" style="
                                    display: flex;
                                    flex-direction: column;
                                    gap: 6px;
                                    padding: 14px 16px;
                                    margin-bottom: 10px;
                                    border-radius: 18px;
                                    background: #FFFFFF;
                                    backdrop-filter: blur(10px);
                                    border: 1px solid ${borderColor};
                                    cursor: pointer;
                                    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                                    position: relative;
                                    overflow: hidden;
                                    ${isRead ? 'opacity: 0.75;' : ''}
                                " onmouseover="this.style.background='#FFF9F5'; this.style.transform='translateY(-2px) translateX(4px)'; this.style.borderColor='#FFB084'; this.style.boxShadow='0 8px 24px rgba(255, 126, 75, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.85)';" onmouseout="this.style.background='#FFFFFF'; this.style.transform='translateY(0) translateX(0)'; this.style.borderColor='${borderColor}'; this.style.boxShadow='none';">
                                    ${!isRead ? `
                                        <div style="
                                            content: '';
                                            position: absolute;
                                            top: 0;
                                            left: -100%;
                                            width: 100%;
                                            height: 100%;
                                            background: linear-gradient(
                                                90deg,
                                                transparent 0%,
                                                rgba(255, 176, 132, 0.4) 50%,
                                                transparent 100%
                                            );
                                            animation: shine-slide 3s ease-in-out infinite;
                                            pointer-events: none;
                                            z-index: 1;
                                        "></div>
                                    ` : ''}
                                    
                                    <div style="
                                        font-size: 14px;
                                        font-weight: 600;
                                        color: #1f2933;
                                        display: flex;
                                        align-items: center;
                                        gap: 6px;
                                        letter-spacing: -0.01em;
                                        position: relative;
                                        z-index: 2;
                                    ">
                                        <span style="font-size: 16px;">🔔</span>
                                        <span>Đề xuất mới</span>
                                    </div>
                                    
                                    ${sug.message ? `
                                        <div style="
                                            font-size: 13px;
                                            color: #555555;
                                            line-height: 1.5;
                                            position: relative;
                                            z-index: 2;
                                        ">
                                            ${sug.message}
                                        </div>
                                    ` : ''}
                                    
                                    <div style="
                                        display: flex;
                                        align-items: center;
                                        justify-content: space-between;
                                        gap: 8px;
                                        font-size: 11px;
                                        color: #6b7280;
                                        margin-top: 2px;
                                        font-weight: 500;
                                        position: relative;
                                        z-index: 2;
                                    ">
                                        <div style="display: flex; align-items: center; gap: 4px;">
                                            <span style="font-size: 12px;">🕐</span>
                                            <span>${createdAtFormatted}</span>
                                        </div>
                                        
                                        <div style="
                                            display: flex;
                                            align-items: center;
                                            gap: 8px;
                                            margin-left: auto;
                                        ">
                                            <span style="
                                                font-size: 10px;
                                                font-weight: 700;
                                                padding: 3px 8px;
                                                border-radius: 12px;
                                                flex-shrink: 0;
                                                white-space: nowrap;
                                                background: ${statusBg};
                                                color: ${statusColor};
                                                ${sug.status !== 'pending' && sug.status !== 'accepted' ? 'border: 1px solid rgba(239, 68, 68, 0.3);' : 'box-shadow: 0 2px 6px rgba(255, 126, 75, 0.4);'}
                                            ">
                                                ${statusText}
                                            </span>
                                        </div>
                                    </div>
                                    
                                    ${reviewedAtFormatted ? `
                                        <div style="
                                            font-size: 11px;
                                            color: #6b7280;
                                            display: flex;
                                            align-items: center;
                                            gap: 4px;
                                            position: relative;
                                            z-index: 2;
                                        ">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FFB084" stroke-width="2.5">
                                                <polyline points="20 6 9 17 4 12"></polyline>
                                            </svg>
                                            <span>Xét duyệt: ${reviewedAtFormatted}</span>
                                        </div>
                                    ` : ''}
                                    
                                    ${sug.status === 'accepted' ? `
                                        <div style="
                                            background: linear-gradient(135deg, rgba(255, 176, 132, 0.15) 0%, rgba(255, 142, 83, 0.1) 100%);
                                            padding: 12px;
                                            border-radius: 8px;
                                            font-size: 13px;
                                            color: #FF6B35;
                                            font-weight: 600;
                                            margin-top: 6px;
                                            position: relative;
                                            z-index: 2;
                                        ">
                                            Đề xuất của bạn đã được chấp nhận và áp dụng vào lịch trình ✨
                                        </div>
                                    ` : ''}
                                    
                                    ${sug.status === 'rejected' ? `
                                        <div style="
                                            background: rgba(239, 68, 68, 0.1);
                                            padding: 12px;
                                            border-radius: 8px;
                                            font-size: 13px;
                                            color: #EF4444;
                                            font-weight: 600;
                                            margin-top: 6px;
                                            position: relative;
                                            z-index: 2;
                                        ">
                                            Đề xuất của bạn đã bị từ chối !
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // ✅ Đóng tạm Food Planner khi mở popup chia sẻ (KHÔNG reset data)
        const panel = document.getElementById('foodPlannerPanel');
        if (panel) {
        panel.dataset.prevActiveShare = panel.classList.contains('active') ? '1' : '0';
        panel.classList.remove('active');
        }
        window._prevIsPlannerOpenShare = isPlannerOpen;
        isPlannerOpen = false;

        // ✅ Khóa scroll nền
        document.body.dataset.prevOverflowShare = document.body.style.overflow || '';
        document.body.style.overflow = 'hidden';

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
    } catch (error) {
        console.error('Error loading my suggestions:', error);
        alert('Không thể tải đề xuất của bạn');
    }
}

function closeMySuggestionsModal() {
  const modal = document.getElementById('mySuggestionsModal');
  if (modal) modal.remove();

  // ✅ Mở lại Food Planner như lúc trước khi mở popup
  const panel = document.getElementById('foodPlannerPanel');
  if (panel && panel.dataset.prevActiveShare === '1') {
    panel.classList.add('active');
    isPlannerOpen = true;
  } else {
    isPlannerOpen = false;
  }
  if (panel) delete panel.dataset.prevActiveShare;

  // ✅ Mở lại scroll nền
  document.body.style.overflow = document.body.dataset.prevOverflowShare || '';
  delete document.body.dataset.prevOverflowShare;
}

</script>
'''