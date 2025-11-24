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

def is_open_now(opening_hours_str, check_time=None):
    """
    Kiểm tra quán có đang mở cửa không
    
    Args:
        opening_hours_str: Chuỗi giờ mở cửa từ CSV
        check_time: Giờ cần check (string 'HH:MM' hoặc time object). Nếu None thì dùng giờ hiện tại
    """
    if not opening_hours_str or pd.isna(opening_hours_str):
        return True  # Không có thông tin => cho qua
    
    try:
        import re
        
        # Parse check_time
        if check_time is None:
            current_time = datetime.now().time()
        elif isinstance(check_time, str):
            current_time = datetime.strptime(check_time, '%H:%M').time()
        else:
            current_time = check_time
        
        # Chuẩn hóa: bỏ dấu, lowercase
        hours_str = normalize_text(str(opening_hours_str))
        
        # Mở cửa 24/7
        if any(keyword in hours_str for keyword in ['always', '24', 'ca ngay', 'mo ca ngay']):
            return True
        
        # Parse giờ mở
        open_time = None
        open_match = re.search(r'mo cua[^\d]*(\d{1,2}):?(\d{2})?', hours_str)
        if open_match:
            hour = int(open_match.group(1))
            minute = int(open_match.group(2)) if open_match.group(2) else 0
            open_time = datetime.strptime(f'{hour:02d}:{minute:02d}', '%H:%M').time()
        
        # Parse giờ đóng
        close_time = None
        close_match = re.search(r'dong cua[^\d]*(\d{1,2}):?(\d{2})?', hours_str)
        if close_match:
            hour = int(close_match.group(1))
            minute = int(close_match.group(2)) if close_match.group(2) else 0
            close_time = datetime.strptime(f'{hour:02d}:{minute:02d}', '%H:%M').time()
        
        # Nếu không parse được => CHO QUA
        if open_time is None or close_time is None:
            return True
        
        # Kiểm tra giờ
        if open_time <= close_time:
            # Trường hợp bình thường: 8:00 - 22:00
            return open_time <= current_time <= close_time
        else:
            # Trường hợp qua đêm: 22:00 - 02:00
            return current_time >= open_time or current_time <= close_time
            
    except Exception as e:
        print(f"⚠️ Lỗi parse giờ: {opening_hours_str} -> {e}")
        return True  # Lỗi => CHO QUA

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
        'name': 'Cà phê chill',
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
    
    food_street_count = 0
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
            if not is_open_now(gio_mo_cua):
                continue
            
            name_normalized = normalize_text_with_accent(str(row.get('ten_quan', '')))
            
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
                            food_street_count += 1
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
    
    # TRÀ CHIỀU - Cafe/trà sữa
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
    breakfast_time = max(start_hour, 6.5)
    if breakfast_time < start_hour:
        breakfast_time += 24
    if is_in_range(breakfast_time, 6, 10):
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
    
    # 🔥 TRÀ CHIỀU (14:00 - 17:00)
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
                'title': 'Trà chiều',
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
            'radius_km': radius_km
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
                'khau_vi': best_place['khau_vi']
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
    bottom: 200px; /* đặt cao hơn nút 🍜 khoảng 80px */
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
    z-index: 999999 !important;
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

/* ========== TABS ========== */
.tabs-container {
    display: flex;
    background: #f8f9fa;
    border-bottom: 2px solid #e9ecef;
    flex-shrink: 0;
}

.tab {
    flex: 1;
    padding: 14px;
    text-align: center;
    cursor: pointer;
    background: transparent;
    border: none;
    font-size: 14px;
    font-weight: 500;
    color: #6c757d;
    transition: all 0.2s ease;
    position: relative;
}

.tab.active {
    color: #FF6B35;
    background: white;
}

.tab.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: #FF6B35;
}

/* ========== CONTENT AREA ========== */
.panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* ========== FILTERS SECTION ========== */
.filters-wrapper {
    margin-bottom: 20px;
    transition: all 0.3s ease;
    overflow: hidden; 
}

.filters-wrapper.collapsed .filter-section {
    display: none;
}

.filters-wrapper.collapsed .generate-btn {
    display: none;
}

.toggle-filters-btn {
    background: #f8f9fa;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    width: 100%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 15px;
    transition: all 0.2s ease;
}

.toggle-filters-btn:hover {
    background: #e9ecef;
}

.toggle-filters-btn svg {
    width: 18px;
    height: 18px;
    transition: transform 0.3s ease;
}

.filters-wrapper.collapsed .toggle-filters-btn svg {
    transform: rotate(180deg);
}

.filter-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
}

.filter-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 10px;
}

.theme-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}

.theme-card {
    background: white;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
}

.theme-card:hover {
    border-color: #FF6B35;
}

.theme-card.selected {
    background: #FF6B35;
    border-color: #FF6B35;
    color: white;
}

.theme-icon {
    font-size: 26px;
    margin-bottom: 5px;
}

.theme-name {
    font-size: 12px;
    font-weight: 500;
}

.time-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.time-input-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.time-input-group label {
    font-size: 12px;
    color: #666;
}

.time-input-group input {
    padding: 8px 12px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 14px;
    outline: none;
    transition: all 0.2s ease;
}

.time-input-group input:focus {
    border-color: #FF6B35;
}

.generate-btn {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 100%;
    margin-top: 15px;
}

.generate-btn:hover {
    opacity: 0.9;
}

/* ========== SAVED PLANS SECTION ========== */
.saved-plans-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
}

.saved-plans-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 10px;
}

.saved-plans-header:hover {
    color: #FF6B35;
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
    border: 2px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.saved-plan-item:hover {
    border-color: #FF6B35;
}

.saved-plan-info {
    flex: 1;
}

.saved-plan-name {
    font-weight: 600;
    color: #333;
    font-size: 14px;
    margin-bottom: 4px;
    /* 🔥 RÚT GỌN text khi dài */
    max-width: 180px; /* Giới hạn chiều rộng */
    white-space: nowrap; /* Không xuống dòng */
    overflow: hidden; /* Ẩn phần thừa */
    text-overflow: ellipsis; /* Thêm dấu ... */
}

.saved-plan-date {
    font-size: 12px;
    color: #999;
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

/* ========== TIMELINE VERTICAL ========== */
.timeline-container {
    position: relative;
    padding-left: 0;
    margin-top: 20px;
    padding-bottom: 10px;
}

.timeline-line {
    position: absolute;
    left: 120px; /* 🔥 TĂNG từ 80px lên 120px */
    top: 12px;
    bottom: 15px;
    width: 3px;
    background: linear-gradient(to bottom, #FF6B35, #FF8E53);
}

.meal-item {
    position: relative;
    margin-bottom: 25px;
    padding-left: 130px;
}

.meal-item:last-child {
    margin-bottom: 0;
}

.meal-item.dragging {
    opacity: 0.5;
}

.time-marker {
    position: absolute;
    left: 0;
    top: 0;
    width: 115px; /* 🔥 TĂNG từ 75px lên 115px */
    text-align: right;
    padding-right: 15px;
}

.time-badge {
    display: inline-block;
    background: #FF6B35;
    color: white;
    padding: 5px 10px;
    border-radius: 16px;
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(255, 107, 53, 0.2);
    white-space: nowrap;
}

.time-dot {
    position: absolute;
    left: 112px; /* 🔥 TĂNG từ 72px lên 112px */
    top: 8px;
    width: 16px;
    height: 16px;
    background: #FF6B35;
    border: 3px solid white;
    border-radius: 50%;
    z-index: 2;
    box-shadow: 0 0 0 2px #FF6B35;
}

.meal-card-vertical {
    background: #FFF5F0;
    border: 2px solid #FFE5D9;
    border-radius: 12px;
    padding: 14px;
    transition: all 0.2s ease;
    cursor: pointer;
}

.meal-card-vertical:hover {
    border-color: #FF6B35;
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.15);
}

.meal-card-vertical.edit-mode {
    cursor: default;
}

.meal-card-vertical.empty-slot {
    background: #f0f9ff;
    border: 2px dashed #4caf50;
    cursor: default;
}

.meal-card-vertical.empty-slot:hover {
    border-color: #45a049;
    background: #e8f5e9;
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
.meal-item.drag-over {
    transform: scale(1.02);
    transition: transform 0.2s ease;
}

.meal-card-vertical.drop-target {
    border: 2px dashed #4caf50 !important;
    background: #E8F5E9 !important;
}

/* Hiệu ứng sau khi thả - giống với repositioned */
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
    font-size: 15px;
    font-weight: 600;
    color: #333;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.meal-title-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.meal-actions {
    display: none;
    gap: 6px;
}

.meal-card-vertical.edit-mode .meal-actions {
    display: flex;
}

.meal-action-btn {
    background: white;
    border: 1px solid #e9ecef;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    font-size: 14px;
}

.meal-action-btn:hover {
    border-color: #FF6B35;
    background: #FFF5F0;
}

.meal-action-btn.delete-meal {
    background: #fee;
    border-color: #e74c3c;
}

.meal-action-btn.delete-meal:hover {
    background: #e74c3c;
    color: white;
}

.meal-action-btn.select-meal {
    background: #e8f5e9;
    border-color: #4caf50;
}

.meal-action-btn.select-meal:hover {
    background: #4caf50;
    color: white;
}

.meal-action-btn.select-meal.active {
    background: #4caf50;
    color: white;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.place-info-vertical {
    background: white;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
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
    gap: 12px;
    flex-wrap: wrap;
    font-size: 12px;
    margin-bottom: 10px;
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
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    cursor: pointer;
    transition: transform 0.15s ease;
    flex-shrink: 0;  /* 🔥 THÊM DÒNG NÀY */
    min-width: 44px;  /* 🔥 ĐẢM BẢO KHÔNG BỊ NÉN NHỎ HƠN */
}

.action-btn:hover {
    transform: translateY(-4px);
}

.action-btn.secondary {
    background: #FF6B35;
    color: #fff;
}

.action-btn.secondary:hover {
    background: #FF8E53;
}

.action-btn.edit {
    background: #FFA500;
    color: #fff;
}

.action-btn.edit:hover {
    background: #FF8C00;
}

.action-btn.edit.active {
    background: #4caf50;
}

.action-btn.primary {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
}

.action-btn.primary:hover {
    opacity: 0.9;
}

.action-btn.add {
    background: #4caf50;
    color: white;
}

.action-btn.add:hover {
    background: #45a049;
}

.action-btn svg {
    width: 20px;
    height: 20px;
    fill: white;
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

/* ========== MANUAL MODE ========== */
.meal-item.drag-over {  
    background-color: #fff3cd !important;  
    border: 2px solid #ffc107 !important;
}

.manual-plans-container {
    transition: max-height 0.3s ease;
    overflow: hidden;
}

.search-box-manual {
    margin-bottom: 15px;
}

.search-box-manual input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 14px;
    outline: none;
    transition: all 0.2s ease;
}

.search-box-manual input:focus {
    border-color: #FF6B35;
}

.search-results-manual {
    max-height: 280px;
    overflow-y: auto;
    margin-top: 10px;
}

.place-result-card {
    background: white;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.place-result-card:hover {
    border-color: #FF6B35;
}

.place-result-name {
    font-weight: 600;
    color: #FF6B35;
    margin-bottom: 4px;
    font-size: 14px;
}

.place-result-info {
    font-size: 12px;
    color: #666;
}

.manual-timeline {
    margin-top: 20px;
}

.manual-meal-item {
    background: #FFF5F0;
    border: 2px solid #FFE5D9;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
}

.manual-meal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.manual-meal-header input[type="time"] {
    padding: 6px 10px;
    border: 2px solid #FFE5D9;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
}

.remove-meal-btn {
    background: #e74c3c;
    color: white;
    border: none;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.remove-meal-btn:hover {
    background: #c0392b;
}

.manual-meal-place {
    background: white;
    border-radius: 8px;
    padding: 10px;
}

.manual-meal-note {
    margin-top: 8px;
}

.manual-meal-note input {
    width: 100%;
    padding: 8px 10px;
    border: 2px solid #FFE5D9;
    border-radius: 6px;
    font-size: 12px;
    outline: none;
}

.manual-meal-note input:focus {
    border-color: #FF6B35;
}

.save-manual-plan-btn {
    background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    width: 100%;
    margin-top: 15px;
    transition: all 0.2s ease;
}

.save-manual-plan-btn:hover {
    opacity: 0.9;
}

.empty-manual-plan {
    text-align: center;
    padding: 40px 20px;
    color: #999;
}

.loading-planner {
    text-align: center;
    padding: 40px;
    color: #FF6B35;
}

.loading-spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #FF6B35;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.error-message {
    text-align: center;
    padding: 30px;
    color: #e74c3c;
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
        padding-left: 0;
    }
    
    .meal-item {
        padding-left: 130px; /* 🔥 TĂNG từ 100px */
    }
    
    .time-dot {
        left: 112px; /* 🔥 TĂNG từ 72px */
    }
    
    .timeline-line {
        left: 120px; /* 🔥 THÊM DÒNG NÀY */
    }
    
    .time-marker {
        width: 115px; /* 🔥 THÊM DÒNG NÀY */
    }
    
    .food-planner-btn {
        right: 20px;
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

</style>

<!-- Food Planner Button -->
<div class="food-planner-btn" id="foodPlannerBtn" title="Lên kế hoạch ăn uống">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z"/>
    </svg>
</div>

<!-- Food Planner Panel -->
<div class="food-planner-panel" id="foodPlannerPanel">
    <div class="panel-inner">
        <div class="panel-header">
            <h2>🍽️ Kế hoạch ăn uống</h2>
            <div class="header-actions">
                <button class="header-btn" onclick="closeFoodPlanner()" title="Đóng">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <div class="tabs-container">
            <button class="tab active" onclick="switchTab('auto', event)">🤖 Tự động tạo</button>
            <button class="tab" onclick="switchTab('manual', event)">✋ Tự chọn quán</button>
        </div>
        
        <div class="panel-content">
            <!-- AUTO MODE -->
            <div class="tab-content active" id="autoTab">
                <div class="filters-wrapper" id="filtersWrapper">
                    <button class="toggle-filters-btn" id="toggleFiltersBtn" onclick="toggleFilters()">
                        <span>⚙️ Tùy chọn lọc</span>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                        </svg>
                    </button>
                    
                    <div class="filter-section">
                        <div class="filter-title">🎭 Chọn chủ đề</div>
                        <div class="theme-grid" id="themeGrid"></div>
                    </div>
                    
                    <div class="filter-section">
                        <div class="filter-title">⏰ Khoảng thời gian</div>
                        <div class="time-inputs">
                            <div class="time-input-group">
                                <label>Từ</label>
                                <div style="display: flex; gap: 5px; align-items: center;">
                                    <input type="number" id="startHour" min="0" max="23" value="07" 
                                        style="width: 60px; padding: 8px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 14px; text-align: center;">
                                    <span style="font-weight: bold;">:</span>
                                    <input type="number" id="startMinute" min="0" max="59" value="00" 
                                        style="width: 60px; padding: 8px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 14px; text-align: center;">
                                </div>
                            </div>
                            <div class="time-input-group">
                                <label>Đến</label>
                                <div style="display: flex; gap: 5px; align-items: center;">
                                    <input type="number" id="endHour" min="0" max="23" value="21" 
                                        style="width: 60px; padding: 8px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 14px; text-align: center;">
                                    <span style="font-weight: bold;">:</span>
                                    <input type="number" id="endMinute" min="0" max="59" value="00" 
                                        style="width: 60px; padding: 8px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 14px; text-align: center;">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <button class="generate-btn" onclick="generateAutoPlan()">🎯 Tạo kế hoạch tự động</button>
                </div>
                
                <!-- Saved Plans Section -->
                <div class="saved-plans-section" id="savedPlansSection" style="display: none;">
                    <div class="saved-plans-header" onclick="toggleSavedPlans()">
                        <div class="filter-title" style="margin: 0;">📋 Lịch trình đã lưu</div>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width: 18px; height: 18px; transition: transform 0.3s ease;" id="savedPlansArrow">
                            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                        </svg>
                    </div>
                    <div class="saved-plans-list" id="savedPlansList"></div>
                </div>
                
                <div id="planResult"></div>
            </div>
            
            <!-- MANUAL MODE -->
            <div class="tab-content" id="manualTab">
                <div class="filter-section">
                    <div class="filter-title" style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleManualPlansSection()">
                        <span>📋 Kế hoạch của bạn</span>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width: 20px; height: 20px; transition: transform 0.3s ease;" id="manualPlansArrow">
                            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                        </svg>
                    </div>
                    
                    <div class="manual-plans-container" id="manualPlansContainer" style="max-height: 0; overflow: hidden; transition: max-height 0.3s ease;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 10px;">
                            <span style="font-size: 13px; color: #666;">Danh sách kế hoạch</span>
                            <button onclick="event.stopPropagation(); createNewManualPlan()" style="background: #4caf50; color: white; border: none; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center;">+</button>
                        </div>
                        <div id="manualPlansList" style="max-height: 300px; overflow-y: auto;"></div>
                    </div>
                </div>
                
                <div id="manualPlanContent"></div>
            </div>
        </div>
    </div>
</div>

<script>
// ========== GLOBAL STATE ==========
let isPlannerOpen = false;
let currentTab = 'auto';
let selectedThemes = []; // Đổi từ selectedTheme thành selectedThemes (array)
let currentPlan = null;
let currentPlanId = null;
let filtersCollapsed = false;
let manualPlan = [];
let manualPlans = []; // Danh sách các kế hoạch manual
let currentManualPlanId = null; // ID của kế hoạch manual đang chỉnh sửa
let isEditMode = false;
let draggedElement = null;
let selectedPlaceForReplacement = null;
let waitingForPlaceSelection = null;
let isManualEditMode = false;
let autoScrollInterval = null;
let lastDragY = 0;
let dragDirection = 0;
let lastTargetElement = null;
window.currentPlanName = null;

// Themes data
const themes = {
    'street_food': { name: 'Ẩm thực đường phố', icon: '🍜' },
    'seafood': { name: 'Hải sản', icon: '🦞' },
    'coffee_chill': { name: 'Cà phê chill', icon: '☕' },
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
    initManualSearch();
    loadSavedPlans();
});

function initThemeGrid() {
    const grid = document.getElementById('themeGrid');
    if (!grid) return;
    
    Object.keys(themes).forEach(key => {
        const theme = themes[key];
        const card = document.createElement('div');
        card.className = 'theme-card';
        card.dataset.theme = key;
        card.innerHTML = `
            <div class="theme-icon">${theme.icon}</div>
            <div class="theme-name">${theme.name}</div>
        `;
        card.onclick = () => selectTheme(key);
        grid.appendChild(card);
    });
}

function initManualSearch() {
    loadManualPlans();
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

// ========== TOGGLE FILTERS ==========
function toggleFilters() {
    const wrapper = document.getElementById('filtersWrapper');
    filtersCollapsed = !filtersCollapsed;
    
    if (filtersCollapsed) {
        wrapper.classList.add('collapsed');
    } else {
        wrapper.classList.remove('collapsed');
    }
}

// ========== SAVED PLANS ==========
function displaySavedPlansList(plans) {
    const listDiv = document.getElementById('savedPlansList');
    if (!plans || plans.length === 0) {
        listDiv.innerHTML = '<p style="color: #999; font-size: 13px; padding: 15px; text-align: center;">Chưa có kế hoạch nào</p>';
        return;
    }
    
    let html = '';
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

// ========== SAVE PLAN - SỬ DỤNG ARRAY THAY VÌ OBJECT ==========
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

    // Cập nhật order
    currentPlan._order = planArray.map(x => x.key);

    // 🔥 LẤY TÊN TỪ DOM (nếu user đã edit inline)
    const titleElement = document.querySelector('.schedule-title span[contenteditable]');
    let currentDisplayName = titleElement ? titleElement.textContent.trim() : (window.currentPlanName || '');
    
    // Nếu chưa có tên hoặc là tên mặc định, hỏi user
    if (!currentDisplayName || currentDisplayName === 'Lịch trình của bạn') {
        currentDisplayName = prompt('Đặt tên cho kế hoạch:', `Kế hoạch ${new Date().toLocaleDateString('vi-VN')}`);
        if (!currentDisplayName) return; // User cancel
    } else if (!currentPlanId) {
        // Plan mới nhưng đã có tên custom → hỏi lại để confirm
        const newName = prompt('Đặt tên cho kế hoạch:', currentDisplayName);
        if (!newName) return;
        currentDisplayName = newName;
    }
    // Nếu đã có planId và đã có tên custom → dùng luôn, không hỏi
    
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    
    const planRecord = {
        id: currentPlanId || Date.now().toString(),
        name: currentDisplayName, // 🔥 DÙNG TÊN ĐÃ EDIT
        plan: planArray,  // ← Array có thứ tự
        savedAt: new Date().toISOString()
    };
    
    if (currentPlanId) {
        const index = savedPlans.findIndex(p => p.id === currentPlanId);
        if (index !== -1) {
            savedPlans[index] = planRecord;
        }
    } else {
        savedPlans.unshift(planRecord);
        currentPlanId = planRecord.id;
    }
    
    if (savedPlans.length > 20) {
        savedPlans.length = 20;
    }
    
    localStorage.setItem('food_plans', JSON.stringify(savedPlans));
    
    // 🔥 CẬP NHẬT TÊN HIỂN THỊ
    window.currentPlanName = planRecord.name;
    
    alert('✅ Đã lưu kế hoạch thành công!');
    loadSavedPlans();
    
    if (isEditMode) {
        toggleEditMode();
    }
}

// ========== LOAD SAVED PLAN - RESTORE TỪARAY VỀ OBJECT ==========
function loadSavedPlans(planId) {
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    const section = document.getElementById('savedPlansSection');
    
    // 🔥 HIỂN THỊ SECTION NẾU CÓ PLANS
    if (savedPlans.length > 0) {
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
    
    displaySavedPlansList(savedPlans);
    
    // Nếu có planId, load plan đó
    if (planId) {
        const filtersWrapper = document.getElementById('filtersWrapper');
        if (filtersWrapper && !filtersWrapper.classList.contains('collapsed')) {
            toggleFilters(); // Gọi hàm có sẵn để đóng
        }
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
            isEditMode = false;
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
    
    if (savedPlans.length === 0) {
        document.getElementById('savedPlansSection').style.display = 'none';
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

// ========== TAB SWITCHING ==========
function switchTab(tab, event) {
    currentTab = tab;
    
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    if (tab === 'auto') {
        document.getElementById('autoTab').classList.add('active');
    } else {
        document.getElementById('manualTab').classList.add('active');
        // Reset manual plan content khi chuyển tab
        if (!currentManualPlanId) {
            document.getElementById('manualPlanContent').innerHTML = '';
        }
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
    
    // Tự động vẽ lại đường đi
    setTimeout(() => {
        if (currentTab === 'auto' && currentPlan && !isEditMode) {
            const hasPlaces = Object.keys(currentPlan)
                .filter(k => k !== '_order')
                .some(k => currentPlan[k] && currentPlan[k].place);
            
            if (hasPlaces) {
                drawRouteOnMap(currentPlan);
            }
        } else if (currentTab === 'manual' && currentManualPlanId && !isManualEditMode) {
            const hasPlaces = manualPlan.some(item => item.place);
            if (hasPlaces) {
                drawManualRouteOnMap();
            }
        }
    }, 300);
}

function closeFoodPlanner() {
    document.getElementById('foodPlannerPanel').classList.remove('active');
    isPlannerOpen = false;
    clearRoutes(); // Xóa đường khi đóng panel
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
        
        const radius = window.currentRadius || document.getElementById('radius')?.value || '';
        
        if (!radius || radius === '') {
            resultDiv.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Chưa chọn bán kính</h3>
                    <p>Vui lòng chọn bán kính tìm kiếm trước khi tạo kế hoạch</p>
                </div>
            `;
            return;
        }
        
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
        
        if (!filtersCollapsed) {
            toggleFilters();
        }
        
        isEditMode = false;
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

    let html = `
    <div class="schedule-header">
        <h3 class="schedule-title">
            <span style="margin-right: 8px;">📅</span>
            <span ${editMode ? 'contenteditable="true" class="editable" onblur="updateAutoPlanName(this.textContent)"' : ''}><span>${window.currentPlanName || 'Lịch trình của bạn'}</span></span>
        </h3>
        <div class="action-buttons" id="actionButtons">
            <button class="action-btn secondary" onclick="generateAutoPlan()" title="Tạo lại">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                    <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                </svg>
            </button>
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
            <button class="action-btn secondary" onclick="sharePlan()" title="Chia sẻ kế hoạch">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="white">
                    <path d="M15 8l4.39 4.39a1 1 0 010 1.42L15 18.2v-3.1c-4.38.04-7.43 1.4-9.88 4.3.94-4.67 3.78-8.36 9.88-8.4V8z"/>
                </svg>
            </button>
            ${editMode ? `
            <button class="action-btn add" onclick="addNewMealSlot()" title="Thêm quán mới">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
            </button>
            ` : ''}
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
                <div class="meal-item" data-meal-key="${key}">
                    <div class="time-marker">
                        ${editMode ? 
                            `<div style="display: flex; gap: 5px; align-items: center;">
                                <input type="number" min="0" max="23" value="${meal.time.split(':')[0]}" 
                                    class="time-input-hour" data-meal-key="${key}"
                                    style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                                <span style="font-weight: bold; color: #FF6B35;">:</span>
                                <input type="number" min="0" max="59" value="${meal.time.split(':')[1]}" 
                                    class="time-input-minute" data-meal-key="${key}"
                                    style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                            </div>` :
                            `<div class="time-badge">${meal.time}</div>`
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
                                <button class="meal-action-btn delete-meal" onclick="deleteMealSlot('${key}')" title="Xóa">
                                    🗑️
                                </button>
                                <button class="meal-action-btn select-meal ${isWaitingForSelection ? 'active' : ''}" 
                                        onclick="selectPlaceForMeal('${key}')" title="Chọn quán">
                                    ${isWaitingForSelection ? '⏳' : '✔'}
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
        
        const cardClickEvent = editMode ? '' : `onclick="flyToPlace(${place.lat}, ${place.lon})"`;
        const cardCursor = editMode ? 'cursor: default;' : 'cursor: pointer;';
        
        const isWaitingForSelection = waitingForPlaceSelection === key;
        
        html += `
            <div class="meal-item" draggable="${editMode}" data-meal-key="${key}">
                <div class="time-marker">
                    ${editMode ? 
                        `<div style="display: flex; gap: 5px; align-items: center;">
                            <input type="number" min="0" max="23" value="${meal.time.split(':')[0]}" 
                                class="time-input-hour" data-meal-key="${key}"
                                style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                            <span style="font-weight: bold; color: #FF6B35;">:</span>
                            <input type="number" min="0" max="59" value="${meal.time.split(':')[1]}" 
                                class="time-input-minute" data-meal-key="${key}"
                                style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                        </div>` :
                        `<div class="time-badge">${meal.time}</div>`
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
                            ${editMode ? 
                                `<div style="display: flex; gap: 4px; align-items: center; flex: 1;">
                                    <input type="text" value="${meal.title}" onchange="updateMealTitle('${key}', this.value)" 
                                        class="time-input-inline" onclick="event.stopPropagation();" placeholder="Nhập tên bữa ăn">
                                </div>` :
                                `<span>${meal.title}</span>`
                            }
                        </div>
                        ${editMode ? `
                        <div class="meal-actions">
                            <button class="meal-action-btn delete-meal" onclick="deleteMealSlot('${key}')" title="Xóa quán">
                                🗑️
                            </button>
                            <button class="meal-action-btn select-meal ${isWaitingForSelection ? 'active' : ''}" 
                                    onclick="selectPlaceForMeal('${key}')" title="Chọn quán mới">
                                ${isWaitingForSelection ? '⏳' : '✔'}
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
                            ${place.gia_trung_binh ? `
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

function drawManualRouteOnMap() {
    if (typeof map === 'undefined' || typeof L === 'undefined') {
        console.log('Map chưa sẵn sàng');
        return;
    }
    
    clearRoutes();
    currentRouteAbortController = new AbortController();
    const signal = currentRouteAbortController.signal;
    
    const drawnSegments = [];
    const waypoints = [];
    
    if (window.currentUserCoords) {
        waypoints.push({
            lat: window.currentUserCoords.lat,
            lon: window.currentUserCoords.lon,
            name: 'Vị trí của bạn',
            isUser: true
        });
    }
    
    const sortedPlan = [...manualPlan].sort((a, b) => a.time.localeCompare(b.time));
    
    sortedPlan.forEach(item => {
        if (item.place) {
            waypoints.push({
                lat: item.place.lat,
                lon: item.place.lon,
                name: item.place.ten_quan,
                time: item.time,
                isUser: false
            });
        }
    });
    
    if (waypoints.length < 2) {
        console.log('Không đủ điểm để vẽ đường');
        return;
    }
    
    const totalRoutes = waypoints.length - 1;
    const routeWeight = 6;
    
    // 🔥 FUNCTION drawSingleRoute - ĐÚNG CẤU TRÚC
    async function drawSingleRoute(startPoint, endPoint, index) {
        try {
            const url = `https://router.project-osrm.org/route/v1/driving/${startPoint.lon},${startPoint.lat};${endPoint.lon},${endPoint.lat}?overview=full&geometries=geojson`;
            const response = await fetch(url, { signal });
            const data = await response.json();
            
            if (data.code === 'Ok' && data.routes && data.routes[0]) {
                const route = data.routes[0];
                const coords = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
                const color = getRouteColor(index, totalRoutes);
                
                let offsetPixels = 0;
                for (let i = 0; i < drawnSegments.length; i++) {
                    if (checkRouteOverlap(coords, drawnSegments[i].coords)) {
                        const overlapCount = drawnSegments.filter(seg => 
                            checkRouteOverlap(coords, seg.coords)
                        ).length;
                        offsetPixels = (overlapCount % 2 === 0) ? 8 : -8;
                        break;
                    }
                }
                
                drawnSegments.push({ coords: coords, index: index });
                
                const outlinePolyline = L.polyline(coords, {
                    color: '#FFFFFF',
                    weight: routeWeight + 3,
                    opacity: 0.9,
                    smoothFactor: 1
                }).addTo(map);
                routeLayers.push(outlinePolyline);
                
                const mainPolyline = L.polyline(coords, {
                    color: color,
                    weight: routeWeight,
                    opacity: 1,
                    smoothFactor: 1,
                    dashArray: null
                }).addTo(map);
                
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
    } // 🔥 ĐÓNG drawSingleRoute() Ở ĐÂY
    
    // 🔥 drawAllRoutes() PHẢI NẰM NGOÀI drawSingleRoute()
    (async function drawAllRoutes() {
        try {
            for (let i = 0; i < waypoints.length - 1; i++) {
                if (signal.aborted) {
                    console.log('⚠️ Đã dừng vẽ tất cả routes do bị hủy');
                    return;
                }
                await drawSingleRoute(waypoints[i], waypoints[i + 1], i);
            }
            
            if (!signal.aborted) {
                const bounds = L.latLngBounds(waypoints.map(w => [w.lat, w.lon]));
                map.fitBounds(bounds, { padding: [50, 50] });
                console.log(`✅ Đã vẽ ${waypoints.length - 1} đoạn đường (Manual Mode)`);
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Lỗi trong drawAllRoutes:', error);
            }
        }
    })();
} // 🔥 ĐÓNG drawManualRouteOnMap() Ở ĐÂY


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
    
    let prevLat, prevLon;
    if (window.currentUserCoords) {
        prevLat = window.currentUserCoords.lat;
        prevLon = window.currentUserCoords.lon;
    }
    
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
    
    // 🔥 CẬP NHẬT QUÁN
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
        khau_vi: newPlace.khau_vi || ''
    };
    
    console.log("✅ Da cap nhat quan cho mealKey:", mealKey);
    waitingForPlaceSelection = null;
    displayPlanVertical(currentPlan, isEditMode);
    
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

function setupManualDragAndDrop() {
    const mealItems = document.querySelectorAll('.meal-item[draggable="true"]');
    
    mealItems.forEach(item => {
        item.addEventListener('dragstart', handleManualDragStart);
        item.addEventListener('dragend', handleManualDragEnd);
        item.addEventListener('dragover', handleManualDragOverItem);
    });
    
    const container = document.querySelector('.timeline-container');
    if (container) {
        container.addEventListener('dragover', handleManualDragOver);
        container.addEventListener('drop', handleManualDrop);
    }
}

function handleManualDragStart(e) {
    draggedElement = this;
    window.draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
    lastTargetElement = null;
    startAutoScroll();
}

function handleManualDragEnd(e) {
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
}

function handleManualDragOverItem(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    
    if (!draggedElement || draggedElement === this) return;
    
    e.dataTransfer.dropEffect = 'move';
    
    document.querySelectorAll('.meal-card-vertical.drop-target').forEach(card => {
        card.classList.remove('drop-target');
    });
    
    const targetCard = this.querySelector('.meal-card-vertical');
    if (targetCard) {
        targetCard.classList.add('drop-target');
    }
    
    lastTargetElement = this;
    lastDragY = e.clientY;
    return false;
}

function handleManualDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    
    lastDragY = e.clientY;
    
    if (!draggedElement) return;
    
    e.dataTransfer.dropEffect = 'move';
    
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

function handleManualDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    if (!draggedElement || !lastTargetElement) return;
    if (draggedElement === lastTargetElement) return;
    
    const draggedId = parseInt(draggedElement.dataset.mealId);
    const targetId = parseInt(lastTargetElement.dataset.mealId);
    
    // Cập nhật title và time từ DOM trước khi swap
    const draggedTitleInput = draggedElement.querySelector('.time-input-inline');
    const draggedHourInput = draggedElement.querySelector('.time-input-hour-manual[data-item-id="' + draggedId + '"]');
    const draggedMinuteInput = draggedElement.querySelector('.time-input-minute-manual[data-item-id="' + draggedId + '"]');
    
    const draggedItem = manualPlan.find(i => i.id === draggedId);
    if (draggedTitleInput && draggedItem) {
        draggedItem.title = draggedTitleInput.value;
    }
    if (draggedHourInput && draggedMinuteInput && draggedItem) {
        const hour = draggedHourInput.value.padStart(2, '0');
        const minute = draggedMinuteInput.value.padStart(2, '0');
        draggedItem.time = `${hour}:${minute}`;
    }
    
    const targetTitleInput = lastTargetElement.querySelector('.time-input-inline');
    const targetHourInput = lastTargetElement.querySelector('.time-input-hour-manual[data-item-id="' + targetId + '"]');
    const targetMinuteInput = lastTargetElement.querySelector('.time-input-minute-manual[data-item-id="' + targetId + '"]');
    
    const targetItem = manualPlan.find(i => i.id === targetId);
    if (targetTitleInput && targetItem) {
        targetItem.title = targetTitleInput.value;
    }
    if (targetHourInput && targetMinuteInput && targetItem) {
        const hour = targetHourInput.value.padStart(2, '0');
        const minute = targetMinuteInput.value.padStart(2, '0');
        targetItem.time = `${hour}:${minute}`;
    }
    
    // Swap data
    const draggedIndex = manualPlan.findIndex(i => i.id === draggedId);
    const targetIndex = manualPlan.findIndex(i => i.id === targetId);
    
    if (draggedIndex !== -1 && targetIndex !== -1) {
        [manualPlan[draggedIndex], manualPlan[targetIndex]] = [manualPlan[targetIndex], manualPlan[draggedIndex]];
    }
    
    displayManualPlanTimeline();
    
    setTimeout(() => {
        const draggedCard = document.querySelector(`[data-meal-id="${draggedId}"] .meal-card-vertical`);
        const targetCard = document.querySelector(`[data-meal-id="${targetId}"] .meal-card-vertical`);
        
        if (draggedCard) {
            draggedCard.classList.add('just-dropped');
            const direction = draggedIndex < targetIndex ? '⬇️' : '⬆️';
            const indicator1 = document.createElement('div');
            indicator1.className = 'reposition-indicator';
            indicator1.textContent = direction;
            draggedCard.style.position = 'relative';
            draggedCard.appendChild(indicator1);
            
            const draggedItem = document.querySelector(`[data-meal-id="${draggedId}"]`);
            if (draggedItem) {
                draggedItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            setTimeout(() => {
                draggedCard.classList.remove('just-dropped');
                if (indicator1.parentNode) {
                    indicator1.remove();
                }
            }, 1500);
        }
        
        if (targetCard) {
            targetCard.classList.add('just-dropped');
            const direction = targetIndex < draggedIndex ? '⬇️' : '⬆️';
            const indicator2 = document.createElement('div');
            indicator2.className = 'reposition-indicator';
            indicator2.textContent = direction;
            targetCard.style.position = 'relative';
            targetCard.appendChild(indicator2);
            
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

function handleDragStart(e) {
    draggedElement = this;
    window.draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
    
    lastTargetElement = null; // 🔥 RESET
    startAutoScroll();
}

function handleDragEnd(e) {
    if (draggedElement) {
        draggedElement.classList.remove('dragging');
    }
    
    // 🔥 XÓA tất cả highlight
    document.querySelectorAll('.meal-card-vertical.drop-target').forEach(card => {
        card.classList.remove('drop-target');
    });
    
    draggedElement = null;
    window.draggedElement = null;
    lastDragY = 0;
    lastTargetElement = null;
    
    stopAutoScroll();
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
    
    autoScrollInterval = setInterval(() => {
        if (!draggedElement) {
            stopAutoScroll();
            return;
        }
        
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
}

// ✨ THEO DÕI CHUỘT TRÊN TOÀN BỘ DOCUMENT
document.addEventListener('dragover', (e) => {
    if (draggedElement) {
        lastDragY = e.clientY;
    }
}, { passive: true });

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

// ========== MANUAL MODE: PLANS MANAGEMENT ==========
function toggleManualEditMode() {
    isManualEditMode = !isManualEditMode;
    
    const editBtn = document.getElementById('editManualPlanBtn');
    if (editBtn) {
        if (isManualEditMode) {
            editBtn.classList.add('active');
            editBtn.title = 'Thoát chỉnh sửa';
            clearRoutes();
        } else {
            editBtn.classList.remove('active');
            editBtn.title = 'Chỉnh sửa';
            waitingForPlaceSelection = null;
        }
    }
    
    // Lưu title từ input trước khi render lại
    if (isManualEditMode) {
        const mealItems = document.querySelectorAll('.meal-item');
        mealItems.forEach(item => {
            const itemId = parseInt(item.dataset.mealId);
            const manualItem = manualPlan.find(i => i.id === itemId);
            if (manualItem) {
                const titleInput = item.querySelector('input[onchange*="updateManualItemTitle"]');
                if (titleInput && titleInput.value) {
                    manualItem.title = titleInput.value;
                }
            }
        });
    }
    
    displayManualPlanTimeline();
}

function loadManualPlans() {
    manualPlans = JSON.parse(localStorage.getItem('manual_food_plans') || '[]');
    displayManualPlansList();
}

function displayManualPlansList() {
    const listDiv = document.getElementById('manualPlansList');
    
    if (manualPlans.length === 0) {
        listDiv.innerHTML = '<p style="color: #999; font-size: 13px; padding: 15px; text-align: center;">Chưa có kế hoạch nào</p>';
        return;
    }
    
    let html = '';
    manualPlans.forEach((plan) => {
        const date = new Date(plan.createdAt);
        const dateStr = date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
        const itemCount = plan.items && Array.isArray(plan.items) ? plan.items.length : 0;
        html += `
            <div class="saved-plan-item" onclick="event.stopPropagation(); openManualPlan('${plan.id}')">
                <div class="saved-plan-info">
                    <div class="saved-plan-name">${plan.name}</div>
                    <div class="saved-plan-date">📅 ${dateStr} • ${itemCount} quán</div>
                </div>
                <button class="delete-plan-btn" onclick="event.stopPropagation(); deleteManualPlan('${plan.id}')">×</button>
            </div>
        `;
    });
    
    listDiv.innerHTML = html;
}

function toggleManualPlansSection() {
    const container = document.getElementById('manualPlansContainer');
    const arrow = document.getElementById('manualPlansArrow');
    
    if (container.style.maxHeight === '0px' || container.style.maxHeight === '') {
        container.style.maxHeight = '400px';
        arrow.style.transform = 'rotate(180deg)';
    } else {
        container.style.maxHeight = '0';
        arrow.style.transform = 'rotate(0deg)';
    }
}

function createNewManualPlan() {
    const now = new Date();
    const dateStr = now.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    const planName = prompt('Đặt tên cho kế hoạch:', `Kế hoạch ngày ${dateStr}`);
    
    if (planName) {
        const newPlan = {
            id: Date.now().toString(),
            name: planName,
            items: [{
                id: Date.now(),
                place: null,
                time: timeStr,
                title: 'Bữa mới'
            }],
            createdAt: new Date().toISOString()
        };
        
        manualPlans.unshift(newPlan);
        localStorage.setItem('manual_food_plans', JSON.stringify(manualPlans));
        
        displayManualPlansList();  // ← Cập nhật list
        openManualPlan(newPlan.id); // ← Mở plan và đóng list
    }
}

function openManualPlan(planId) {
    const plan = manualPlans.find(p => p.id === planId);
    if (!plan) return;
    
    currentManualPlanId = planId;
    manualPlan = plan.items.length > 0 ? [...plan.items] : [];
    isManualEditMode = false;
    waitingForPlaceSelection = null;
    
    clearRoutes(); // ⚡ THÊM DÒNG NÀY
    
    // Đóng "Kế hoạch của bạn"
    const container = document.getElementById('manualPlansContainer');
    const arrow = document.getElementById('manualPlansArrow');
    
    if (container && arrow) {
        container.style.maxHeight = '0';
        container.style.overflow = 'hidden';
        arrow.style.transform = 'rotate(0deg)';
    }
    
    displayManualPlanTimeline();

    // Scroll lên top
    const panelContent = document.querySelector('.panel-content');
    if (panelContent) {
        panelContent.scrollTop = 0;
    }
}

function deleteManualPlan(planId) {
    if (!confirm('Bạn có chắc muốn xóa kế hoạch này?')) return;
    
    manualPlans = manualPlans.filter(p => p.id !== planId);
    localStorage.setItem('manual_food_plans', JSON.stringify(manualPlans));
    
    if (currentManualPlanId === planId) {
        currentManualPlanId = null;
        manualPlan = [];
        document.getElementById('manualPlanContent').innerHTML = '';
    }
    
    displayManualPlansList();
}

function displayManualPlanTimeline() {
    const contentDiv = document.getElementById('manualPlanContent');
    
    const currentPlanData = manualPlans.find(p => p.id === currentManualPlanId);
    if (!currentPlanData) return;
    
    const planName = currentPlanData.name;
    const editMode = isManualEditMode;
    
    // ⚡ Kiểm tra nếu đã xóa hết quán trong edit mode
    if (manualPlan.length === 0 && editMode) {
        contentDiv.innerHTML = `
            <div class="error-message">
                <h3>🗑️ Đã xóa hết lịch trình</h3>
                <p>Bạn đã xóa tất cả các quán trong lịch trình này</p>
                <button onclick="addManualMealSlot();" 
                    style="margin-top: 15px; padding: 10px 20px; background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600;">
                    ✨ Thêm quán mới
                </button>
            </div>
        `;
        clearRoutes();
        return;
    }
    
    let html = `
    <div class="schedule-header">
        <h3 class="schedule-title">
            <span style="margin-right: 8px;">📅</span>
            <span ${editMode ? 'contenteditable="true" class="editable" onblur="updateManualPlanName(this.textContent)"' : ''}><span>${planName}</span></span>
        </h3>
        <div class="action-buttons">
            <button class="action-btn edit ${editMode ? 'active' : ''}" id="editManualPlanBtn" onclick="toggleManualEditMode()" title="${editMode ? 'Thoát chỉnh sửa' : 'Chỉnh sửa'}">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                </svg>
            </button>
            <button class="action-btn primary" onclick="saveManualPlanChanges()" title="Lưu">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                    <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
                </svg>
            </button>
            <button class="action-btn secondary" onclick="shareManualPlan()" title="Chia sẻ kế hoạch">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="white">
                    <path d="M15 8l4.39 4.39a1 1 0 010 1.42L15 18.2v-3.1c-4.38.04-7.43 1.4-9.88 4.3.94-4.67 3.78-8.36 9.88-8.4V8z"/>
                </svg>
            </button>
            ${editMode ? `
            <button class="action-btn add" onclick="addManualMealSlot()" title="Thêm quán mới">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
            </button>
            ` : ''}
        </div>
    </div>
    <div class="timeline-container"><div class="timeline-line"></div>
    `;
    
    manualPlan.sort((a, b) => a.time.localeCompare(b.time));
    let hasPlaces = false;
    
    manualPlan.forEach((item, index) => {
        const isWaiting = waitingForPlaceSelection === item.id;
        const icon = item.icon || '🍽️';
        
        if (!item.place) {
            // Card trống
            html += `
                <div class="meal-item" data-meal-id="${item.id}" draggable="${editMode}">
                    <div class="time-marker">
                        ${editMode ? 
                            `<div style="display: flex; gap: 5px; align-items: center;">
                                <input type="number" min="0" max="23" value="${item.time.split(':')[0]}" 
                                    class="time-input-hour time-input-hour-manual" data-item-id="${item.id}"
                                    style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                                <span style="font-weight: bold; color: #FF6B35;">:</span>
                                <input type="number" min="0" max="59" value="${item.time.split(':')[1]}" 
                                    class="time-input-minute time-input-minute-manual" data-item-id="${item.id}"
                                    style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                            </div>` :
                            `<div class="time-badge">${item.time}</div>`
                        }
                    </div>
                    <div class="time-dot"></div>
                    <div class="meal-card-vertical empty-slot ${editMode ? 'edit-mode' : ''}">
                        <div class="meal-title-vertical">
                            <div class="meal-title-left">
                                ${editMode ? `
                                    <select onchange="updateManualItemIcon(${item.id}, this.value)" style="border: none; background: transparent; font-size: 22px; cursor: pointer; outline: none; padding: 0;" onclick="event.stopPropagation();">
                                        ${iconOptions.map(ico => `<option value="${ico}" ${ico === icon ? 'selected' : ''}>${ico}</option>`).join('')}
                                    </select>
                                ` : `<span style="font-size: 22px;">${icon}</span>`}
                                ${editMode ? 
                                    `<input type="text" value="${item.title}" onchange="updateManualItemTitle(${item.id}, this.value)" 
                                        class="time-input-inline" onclick="event.stopPropagation();" placeholder="Nhập tên bữa ăn">` :
                                    `<span>${item.title}</span>`
                                }
                            </div>
                            ${editMode ? `
                            <div class="meal-actions">
                                <button class="meal-action-btn delete-meal" onclick="deleteManualItem(${item.id})" title="Xóa">
                                    🗑️
                                </button>
                                <button class="meal-action-btn select-meal ${isWaiting ? 'active' : ''}" 
                                        onclick="selectPlaceForManualItem(${item.id})" title="Chọn quán">
                                    ${isWaiting ? '⏳' : '✔'}
                                </button>
                            </div>
                            ` : ''}
                        </div>
                        <div class="empty-slot-content">
                            <div class="icon">🪧</div>
                            <div class="text">${isWaiting ? 'Đang chờ chọn quán...' : 'Chưa có quán'}</div>
                            ${!editMode ? '<div style="font-size: 12px; margin-top: 8px; color: #999;">Bật chế độ chỉnh sửa để thêm quán</div>' : '<div style="font-size: 12px; margin-top: 8px; color: #999;">Nhấn nút ✔ để chọn quán từ bản đồ</div>'}
                        </div>
                    </div>
                </div>
            `;
        } else {
            hasPlaces = true;
            const place = item.place;
            const cardClickEvent = editMode ? '' : `onclick="flyToPlace(${place.lat}, ${place.lon})"`;
            const cardCursor = editMode ? 'cursor: default;' : 'cursor: pointer;';
            
            html += `
                <div class="meal-item" data-meal-id="${item.id}" draggable="${editMode}">
                    <div class="time-marker">
                        ${editMode ? 
                            `<div style="display: flex; gap: 5px; align-items: center;">
                                <input type="number" min="0" max="23" value="${item.time.split(':')[0]}" 
                                    class="time-input-hour time-input-hour-manual" data-item-id="${item.id}"
                                    style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                                <span style="font-weight: bold; color: #FF6B35;">:</span>
                                <input type="number" min="0" max="59" value="${item.time.split(':')[1]}" 
                                    class="time-input-minute time-input-minute-manual" data-item-id="${item.id}"
                                    style="width: 48px; padding: 6px 4px; border: 2px solid #FFE5D9; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 600;">
                            </div>` :
                            `<div class="time-badge">${item.time}</div>`
                        }
                    </div>
                    <div class="time-dot"></div>
                    <div class="meal-card-vertical ${editMode ? 'edit-mode' : ''}" ${cardClickEvent} style="${cardCursor}">
                        <div class="meal-title-vertical">
                            <div class="meal-title-left">
                                ${editMode ? `
                                    <select onchange="updateManualItemIcon(${item.id}, this.value)" style="border: none; background: transparent; font-size: 22px; cursor: pointer; outline: none; padding: 0;" onclick="event.stopPropagation();">
                                        ${iconOptions.map(ico => `<option value="${ico}" ${ico === icon ? 'selected' : ''}>${ico}</option>`).join('')}
                                    </select>
                                ` : `<span style="font-size: 22px;">${icon}</span>`}
                                ${editMode ? 
                                    `<input type="text" value="${item.title}" onchange="updateManualItemTitle(${item.id}, this.value)" 
                                        class="time-input-inline" onclick="event.stopPropagation();" placeholder="Nhập tên bữa ăn">` :
                                    `<span>${item.title}</span>`
                                }
                            </div>
                            ${editMode ? `
                            <div class="meal-actions">
                                <button class="meal-action-btn delete-meal" onclick="event.stopPropagation(); deleteManualItem(${item.id})" title="Xóa quán">
                                    🗑️
                                </button>
                                <button class="meal-action-btn select-meal ${isWaiting ? 'active' : ''}" 
                                        onclick="event.stopPropagation(); selectPlaceForManualItem(${item.id})" title="Chọn quán mới">
                                    ${isWaiting ? '⏳' : '✔'}
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
                                    <strong>${place.rating ? place.rating.toFixed(1) : 'N/A'}</strong>
                                </div>
                                ${place.gia_trung_binh ? `
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
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;
    
    if (editMode) {
        setupManualDragAndDrop();
        setTimeout(() => setupManualModeTimeInputs(), 100);
    }
    
    // Vẽ đường đi khi không ở edit mode
    if (!editMode && hasPlaces) {
        setTimeout(() => drawManualRouteOnMap(), 500);
    } else {
        clearRoutes();
    }
    
    // Kiểm tra text có dài hơn khung không
    setTimeout(() => {
        const titleContainer = document.querySelector('.schedule-title > span:last-child');
        if (titleContainer && !titleContainer.hasAttribute('contenteditable')) {
            const textSpan = titleContainer.querySelector('span');
            if (textSpan && textSpan.scrollWidth > titleContainer.clientWidth) {
                titleContainer.classList.add('overflow');
            } else {
                titleContainer.classList.remove('overflow');
            }
        }
    }, 100);
}

function updateManualPlanName(newName) {
    if (!currentManualPlanId) return;
    
    const cleanName = newName.trim() || 'Kế hoạch';
    
    const plan = manualPlans.find(p => p.id === currentManualPlanId);
    if (plan) {
        // 🔥 Nếu tên không đổi thì KHÔNG làm gì
        if (plan.name === cleanName) return;
        
        plan.name = cleanName;
        localStorage.setItem('manual_food_plans', JSON.stringify(manualPlans));
        displayManualPlansList();
    }
}

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

function addManualMealSlot() {
    const lastTime = manualPlan.length > 0 
        ? manualPlan[manualPlan.length - 1].time 
        : '07:00';
    
    const newTime = addMinutesToTime(lastTime, 60);
    
    manualPlan.push({
        id: Date.now(),
        place: null,
        time: newTime,
        title: 'Bữa ăn mới'
    });
    
    displayManualPlanTimeline();
    
    setTimeout(() => {
        const timeline = document.querySelector('.timeline-container');
        if (timeline) {
            timeline.scrollTop = timeline.scrollHeight;
        }
    }, 100);
}

function deleteManualItem(itemId) {
    if (!confirm('Bạn có chắc muốn xóa bữa ăn này?')) return;
    
    manualPlan = manualPlan.filter(item => item.id !== itemId);
    
    if (waitingForPlaceSelection === itemId) {
        waitingForPlaceSelection = null;
    }
    
    displayManualPlanTimeline();
}

function updateManualItemTime(itemId, newTime) {
    const item = manualPlan.find(i => i.id === itemId);
    if (item) {
        item.time = newTime;
    }
}

function updateManualItemTitle(itemId, newTitle) {
    const item = manualPlan.find(i => i.id === itemId);
    if (item) {
        item.title = newTitle;
    }
}

function updateManualItemIcon(itemId, newIcon) {
    const item = manualPlan.find(i => i.id === itemId);
    if (item) {
        item.icon = newIcon;
        displayManualPlanTimeline();
    }
}

function selectPlaceForManualItem(itemId) {
    if (waitingForPlaceSelection === itemId) {
        waitingForPlaceSelection = null;
    } else {
        waitingForPlaceSelection = itemId;
    }
    displayManualPlanTimeline();
}

function resetManualPlan() {
    if (!confirm('Bạn có chắc muốn reset kế hoạch này?')) return;
    
    manualPlan = [];
    waitingForPlaceSelection = null;
    displayManualPlanTimeline();
}

function saveManualPlanChanges() {
    if (!currentManualPlanId) return;

    // Cập nhật time và title từ DOM
    const mealItems = document.querySelectorAll('.meal-item');
    mealItems.forEach(item => {
        const itemId = parseInt(item.dataset.mealId);
        const timeInputs = item.querySelectorAll('.time-input-hour-manual, .time-input-minute-manual');
        
        if (timeInputs.length === 2) {
            const manualItem = manualPlan.find(i => i.id === itemId);
            if (manualItem) {
                const hour = timeInputs[0].value.padStart(2, '0');
                const minute = timeInputs[1].value.padStart(2, '0');
                manualItem.time = `${hour}:${minute}`;
            }
        }
        
        const titleInput = item.querySelector('.time-input-inline');
        if (titleInput) {
            const manualItem = manualPlan.find(i => i.id === itemId);
            if (manualItem) {
                manualItem.title = titleInput.value;
            }
        }
    });

    const plan = manualPlans.find(p => p.id === currentManualPlanId);
    if (plan) {
        plan.items = [...manualPlan];
        plan.updatedAt = new Date().toISOString();
        localStorage.setItem('manual_food_plans', JSON.stringify(manualPlans));
        
        // Thoát edit mode sau khi lưu
        if (isManualEditMode) {
            toggleManualEditMode();
        }
        
        alert('✅ Đã lưu kế hoạch thành công!');
        displayManualPlansList();
    }
}

// ========== MANUAL MODE: SEARCH PLACES ==========
async function searchPlacesManual(query) {
    const resultsDiv = document.getElementById('searchResultsManual');
    
    try {
        const response = await fetch(`/api/places?query=${encodeURIComponent(query)}`);
        const places = await response.json();
        
        if (places.length === 0) {
            resultsDiv.innerHTML = '<p style="color: #999; font-size: 13px; padding: 15px; text-align: center;">Không tìm thấy quán</p>';
            return;
        }
        
        let html = '';
        places.slice(0, 10).forEach(place => {
            html += `
                <div class="place-result-card" onclick='addToManualPlan(${JSON.stringify(place).replace(/'/g, "&#39;")})'>
                    <div class="place-result-name">${place.ten_quan}</div>
                    <div class="place-result-info">📍 ${place.dia_chi}</div>
                    <div class="place-result-info" style="margin-top: 4px;">⭐ ${place.rating || 'N/A'} ${place.gia_trung_binh ? ' • 💰 ' + place.gia_trung_binh : ''}</div>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
        
    } catch (error) {
        console.error('Search error:', error);
        resultsDiv.innerHTML = '<p style="color: #e74c3c; font-size: 13px; padding: 15px; text-align: center;">Lỗi tìm kiếm</p>';
    }
}

// ========== MANUAL MODE: ADD TO PLAN ==========
function addToManualPlan(place) {
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    const planItem = {
        id: Date.now(),
        place: place,
        time: timeStr,
        note: ''
    };
    
    manualPlan.push(planItem);
    displayManualPlan();
    
    document.getElementById('searchPlaceManual').value = '';
    document.getElementById('searchResultsManual').innerHTML = '';
}

// ========== MANUAL MODE: DISPLAY PLAN ==========
function displayManualPlan() {
    const timelineDiv = document.getElementById('manualTimeline');
    
    if (manualPlan.length === 0) {
        timelineDiv.innerHTML = `
            <div class="empty-manual-plan">
                <p>📝 Chưa có quán nào</p>
                <p style="font-size: 13px; margin-top: 8px;">Hãy tìm và thêm quán vào kế hoạch!</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    manualPlan.forEach((item, index) => {
        html += `
            <div class="manual-meal-item">
                <div class="manual-meal-header">
                    <input type="time" value="${item.time}" onchange="updateManualTime(${item.id}, this.value)">
                    <button class="remove-meal-btn" onclick="removeFromManualPlan(${item.id})">×</button>
                </div>
                <div class="manual-meal-place">
                    <div style="font-weight: 600; color: #FF6B35; margin-bottom: 4px; font-size: 14px;">${item.place.ten_quan}</div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">📍 ${item.place.dia_chi}</div>
                    <div style="font-size: 12px; color: #666;">⭐ ${item.place.rating || 'N/A'}</div>
                </div>
                <div class="manual-meal-note">
                    <input type="text" placeholder="Thêm ghi chú (vd: Ăn nhẹ, check-in...)" value="${item.note}" 
                           onchange="updateManualNote(${item.id}, this.value)">
                </div>
            </div>
        `;
    });
    
    html += '<button class="save-manual-plan-btn" onclick="saveManualPlan()">💾 Lưu kế hoạch</button>';
    
    timelineDiv.innerHTML = html;
}

function updateManualTime(id, newTime) {
    const item = manualPlan.find(p => p.id === id);
    if (item) {
        item.time = newTime;
    }
}

function updateManualNote(id, newNote) {
    const item = manualPlan.find(p => p.id === id);
    if (item) {
        item.note = newNote;
    }
}

function removeFromManualPlan(id) {
    manualPlan = manualPlan.filter(p => p.id !== id);
    displayManualPlan();
}

function saveManualPlan() {
    if (manualPlan.length === 0) {
        alert('⚠️ Chưa có quán nào trong kế hoạch!');
        return;
    }
    
    manualPlan.sort((a, b) => a.time.localeCompare(b.time));
    
    const planName = prompt('Đặt tên cho kế hoạch:', `Kế hoạch ${new Date().toLocaleDateString('vi-VN')}`);
    
    if (planName) {
        const savedPlans = JSON.parse(localStorage.getItem('manual_food_plans') || '[]');
        savedPlans.unshift({
            id: Date.now().toString(),
            name: planName,
            plan: manualPlan,
            savedAt: new Date().toISOString()
        });
        
        if (savedPlans.length > 10) {
            savedPlans.length = 10;
        }
        
        localStorage.setItem('manual_food_plans', JSON.stringify(savedPlans));
        
        alert('✅ Đã lưu kế hoạch thành công!');
        
        manualPlan = [];
        displayManualPlan();
    }
}

// ========== FLY TO PLACE ON MAP ==========
function flyToPlace(lat, lon) {
    if (typeof map !== 'undefined') {
        map.setView([lat, lon], 17, { animate: true });
        
        setTimeout(() => {
            map.eachLayer((layer) => {
                if (layer instanceof L.Marker) {
                    const markerLatLng = layer.getLatLng();
                    if (Math.abs(markerLatLng.lat - lat) < 0.0001 && 
                        Math.abs(markerLatLng.lng - lon) < 0.0001) {
                        layer.fire('click');
                    }
                }
            });
        }, 500);
    }
}

// ========== EXPOSE FUNCTIONS TO WINDOW ==========
window.foodPlannerState = {
    isEditMode: () => {
        return isEditMode || isManualEditMode;
    },
    isWaitingForPlaceSelection: () => {
        return waitingForPlaceSelection !== null;
    },
    selectPlace: (place) => {
        if (waitingForPlaceSelection) {
            if (currentTab === 'manual') {
                // MANUAL MODE
                const item = manualPlan.find(i => i.id === waitingForPlaceSelection);
                if (item) {
                    item.place = {
                        ten_quan: place.ten_quan,
                        dia_chi: place.dia_chi,
                        rating: place.rating || 0,
                        lat: place.lat,
                        lon: place.lon,
                        data_id: place.data_id,
                        hinh_anh: place.hinh_anh || '',
                        gia_trung_binh: place.gia_trung_binh || '',
                        khau_vi: place.khau_vi || ''
                    };
                    waitingForPlaceSelection = null;
                    displayManualPlanTimeline();
                    return true;
                } else {
                    console.error("❌ Không tìm thấy item trong manualPlan");
                    return false;
                }
            } else {
                // AUTO MODE
                const success = replacePlaceInMeal(place);
                return success;
            }
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
        let isSpinnerClick = false; // 🔥 BIẾN ĐÁNH DẤU
        
        // 🔥 BẮT SPINNER CLICK - DÙNG INPUT EVENT
        let spinnerTimeout;
        input.addEventListener('input', function(e) {
            // Chỉ xử lý khi có thay đổi từ spinner
            if (document.activeElement === this) {
                clearTimeout(spinnerTimeout);
                spinnerTimeout = setTimeout(() => {
                    let val = parseInt(this.value);
                    
                    if (isNaN(val)) {
                        this.value = '00';
                        lastValue = 0;
                        return;
                    }
                    
                    // 🔥 CYCLE LOGIC
                    if (val > maxValue) {
                        this.value = 0;
                        lastValue = 0;
                    } else if (val < 0) {
                        this.value = maxValue;
                        lastValue = maxValue;
                    } else {
                        lastValue = val;
                    }
                    
                    this.value = this.value.toString().padStart(2, '0');
                }, 50);
            }
        });
        
        // Theo dõi mọi thay đổi
        const observer = new MutationObserver(() => {
            if (!isSpinnerClick) checkAndCycle();
        });
        
        observer.observe(input, { attributes: true, attributeFilter: ['value'] });
        
        input.addEventListener('input', function() {
            if (!isSpinnerClick) checkAndCycle();
        });
        input.addEventListener('change', checkAndCycle);
        
        function checkAndCycle() {
            let val = parseInt(input.value);
            
            if (isNaN(val)) {
                input.value = '00';
                lastValue = 0;
                return;
            }
            
            if (val > maxValue) {
                input.value = 0;
                lastValue = 0;
            } else if (val < 0) {
                input.value = maxValue;
                lastValue = maxValue;
            } else {
                lastValue = val;
            }
        }
        
        // Xử lý blur để format
        input.addEventListener('blur', function() {
            let val = parseInt(this.value) || 0;
            if (val > maxValue) val = 0;
            if (val < 0) val = maxValue;
            this.value = val.toString().padStart(2, '0');
            lastValue = val;
        });
        
        // Xử lý phím mũi tên
        input.addEventListener('keydown', function(e) {
            const currentValue = parseInt(this.value) || 0;
            
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.value = currentValue >= maxValue ? 0 : currentValue + 1;
                this.value = this.value.toString().padStart(2, '0');
                lastValue = parseInt(this.value);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.value = currentValue <= 0 ? maxValue : currentValue - 1;
                this.value = this.value.toString().padStart(2, '0');
                lastValue = parseInt(this.value);
            }
        });
        
        // Xử lý scroll chuột
        input.addEventListener('wheel', function(e) {
            e.preventDefault();
            const currentValue = parseInt(this.value) || 0;
            
            if (e.deltaY < 0) {
                this.value = currentValue >= maxValue ? 0 : currentValue + 1;
            } else {
                this.value = currentValue <= 0 ? maxValue : currentValue - 1;
            }
            
            this.value = this.value.toString().padStart(2, '0');
            lastValue = parseInt(this.value);
        });
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
        input.addEventListener('wheel', function(e) {
            e.preventDefault();
            let val = parseInt(this.value) || 0;
            
            if (e.deltaY < 0) {
                val = val >= maxValue ? 0 : val + 1;
            } else {
                val = val <= 0 ? maxValue : val - 1;
            }
            
            this.value = val.toString().padStart(2, '0');
            updateTimeFromInputs(this);
        }, { passive: false });
        
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
// ========== SETUP CYCLIC TIME INPUTS FOR MANUAL MODE ==========
function setupManualModeTimeInputs() {
    document.querySelectorAll('.time-input-hour-manual, .time-input-minute-manual').forEach(input => {
        const isHour = input.classList.contains('time-input-hour-manual');
        const maxValue = isHour ? 23 : 59;
        
        input.addEventListener('wheel', function(e) {
            e.preventDefault();
            let val = parseInt(this.value) || 0;
            
            if (e.deltaY < 0) {
                val = val >= maxValue ? 0 : val + 1;
            } else {
                val = val <= 0 ? maxValue : val - 1;
            }
            
            this.value = val.toString().padStart(2, '0');
            updateManualTimeFromInputs(this);
        }, { passive: false });
        
        input.addEventListener('keydown', function(e) {
            let val = parseInt(this.value) || 0;
            
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                val = val >= maxValue ? 0 : val + 1;
                this.value = val.toString().padStart(2, '0');
                updateManualTimeFromInputs(this);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                val = val <= 0 ? maxValue : val - 1;
                this.value = val.toString().padStart(2, '0');
                updateManualTimeFromInputs(this);
            }
        });
        
        input.addEventListener('blur', function() {
            let val = parseInt(this.value) || 0;
            if (val > maxValue) val = maxValue;
            if (val < 0) val = 0;
            this.value = val.toString().padStart(2, '0');
            updateManualTimeFromInputs(this);
        });
        
        input.addEventListener('change', function() {
            let val = parseInt(this.value) || 0;
            if (val > maxValue) val = 0;
            if (val < 0) val = maxValue;
            this.value = val.toString().padStart(2, '0');
            updateManualTimeFromInputs(this);
        });
    });
}

function updateManualTimeFromInputs(input) {
    const itemId = parseInt(input.dataset.itemId);
    const parent = input.closest('.time-marker');
    if (!parent) return;
    
    const hourInput = parent.querySelector('.time-input-hour-manual');
    const minuteInput = parent.querySelector('.time-input-minute-manual');
    
    if (hourInput && minuteInput) {
        const hour = hourInput.value.padStart(2, '0');
        const minute = minuteInput.value.padStart(2, '0');
        const newTime = `${hour}:${minute}`;
        
        const item = manualPlan.find(i => i.id === itemId);
        if (item) {
            // Lưu vị trí cũ
            const oldOrder = [...manualPlan];
            const oldIndex = oldOrder.findIndex(i => i.id === itemId);
            
            // Cập nhật time
            item.time = newTime;
            
            // Cập nhật title nếu có
            const mealCard = document.querySelector(`[data-meal-id="${itemId}"]`);
            if (mealCard) {
                const titleInput = mealCard.querySelector('input[onchange*="updateManualItemTitle"]');
                if (titleInput && titleInput.value) {
                    item.title = titleInput.value;
                }
            }
            
            // Sort lại theo thời gian
            manualPlan.sort((a, b) => a.time.localeCompare(b.time));
            
            const newIndex = manualPlan.findIndex(i => i.id === itemId);
            
            // Render lại
            displayManualPlanTimeline();
            
            // Highlight card vừa di chuyển
            if (oldIndex !== newIndex) {
                setTimeout(() => {
                    const movedCard = document.querySelector(`[data-meal-id="${itemId}"] .meal-card-vertical`);
                    if (movedCard) {
                        movedCard.classList.add('repositioned');
                        
                        const direction = newIndex < oldIndex ? '⬆️' : '⬇️';
                        const indicator = document.createElement('div');
                        indicator.className = 'reposition-indicator';
                        indicator.textContent = direction;
                        movedCard.style.position = 'relative';
                        movedCard.appendChild(indicator);
                        
                        const mealItem = document.querySelector(`[data-meal-id="${itemId}"]`);
                        if (mealItem) {
                            mealItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                        
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
}
</script>
'''