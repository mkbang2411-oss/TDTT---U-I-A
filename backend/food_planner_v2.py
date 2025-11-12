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

def is_open_now(opening_hours_str):
    """Kiểm tra quán có đang mở cửa không"""
    if not opening_hours_str or pd.isna(opening_hours_str):
        return True
    
    try:
        now = datetime.now()
        current_time = now.time()
        
        hours_str = str(opening_hours_str).lower()
        
        if 'always' in hours_str or '24' in hours_str or 'ca ngay' in hours_str or 'mo ca ngay' in hours_str:
            return True
        
        if 'dong cua luc' in hours_str:
            parts = hours_str.split('dong cua luc')
            if len(parts) > 1:
                time_part = parts[1].strip().split()[0]
                try:
                    close_time = datetime.strptime(time_part, '%H:%M').time()
                    open_time = datetime.strptime('06:00', '%H:%M').time()
                    
                    if open_time <= close_time:
                        return open_time <= current_time <= close_time
                    else:
                        return current_time >= open_time or current_time <= close_time
                except:
                    pass
        
        return True
    except:
        return True

# ==================== THEME MAPPING ====================

THEME_CATEGORIES = {
    'street_food': {
        'name': 'Ẩm thực đường phố',
        'keywords': ['banh mi', 'pho', 'bun', 'com tam', 'xoi', 'che', 'street', 'via he'],
        'icon': '🍜'
    },
    'seafood': {
        'name': 'Hải sản',
        'keywords': ['hai san', 'seafood', 'fish', 'cua', 'tom', 'oc', 'ngao'],
        'icon': '🦞'
    },
    'coffee_chill': {
        'name': 'Cà phê chill',
        'keywords': ['cafe', 'coffee', 'ca phe', 'tra', 'tea', 'milk tea', 'tra sua'],
        'icon': '☕'
    },
    'luxury_dining': {
        'name': 'Nhà hàng sang trọng',
        'keywords': ['nha hang', 'restaurant', 'fine dining', 'buffet'],
        'icon': '🍽️'
    },
    'asian_fusion': {
        'name': 'Ẩm thực châu Á',
        'keywords': ['sushi', 'ramen', 'korean', 'han quoc', 'nhat ban', 'thai', 'trung hoa'],
        'icon': '🍱'
    },
    'vegetarian': {
        'name': 'Món chay',
        'keywords': ['chay', 'vegetarian', 'vegan', 'healthy'],
        'icon': '🥗'
    },
    'dessert_bakery': {
        'name': 'Tráng miệng & Bánh ngọt',
        'keywords': ['banh', 'cake', 'dessert', 'kem', 'ice cream', 'bakery', 'banh kem'],
        'icon': '🍰'
    },
    'spicy_food': {
        'name': 'Đồ cay',
        'keywords': ['cay', 'spicy', 'hot pot', 'lau', 'mi cay'],
        'icon': '🌶️'
    }
}

# ==================== FIND PLACES WITH ADVANCED FILTERS ====================

def find_places_advanced(user_lat, user_lon, df, filters, excluded_ids=None, top_n=30):
    """Tìm quán với bộ lọc nâng cao"""
    if excluded_ids is None:
        excluded_ids = set()
    
    results = []
    radius_km = filters.get('radius_km', 5)
    theme = filters.get('theme')
    user_tastes = filters.get('tastes', [])
    categories = filters.get('categories', [])
    
    for _, row in df.iterrows():
        try:
            data_id = clean_value(row['data_id'])
            
            if data_id in excluded_ids:
                continue
            
            place_lat = float(row['lat'])
            place_lon = float(row['lon'])
            distance = calculate_distance(user_lat, user_lon, place_lat, place_lon)
            
            if distance > radius_km:
                continue
            
            if not is_open_now(row.get('gio_mo_cua', '')):
                continue
            
            name_normalized = normalize_text(str(row['ten_quan']))
            
            if theme and theme in THEME_CATEGORIES:
                theme_keywords = THEME_CATEGORIES[theme]['keywords']
                if not any(normalize_text(kw) in name_normalized for kw in theme_keywords):
                    continue
            
            if categories:
                category_match = False
                for cat in categories:
                    if normalize_text(cat) in name_normalized:
                        category_match = True
                        break
                if not category_match:
                    continue
            
            if user_tastes:
                taste_col = row.get('khau_vi', '')
                if taste_col and not pd.isna(taste_col):
                    taste_normalized = normalize_text(str(taste_col))
                    taste_match = any(normalize_text(t) in taste_normalized for t in user_tastes)
                    if not taste_match:
                        continue
            
            results.append({
                'ten_quan': clean_value(row['ten_quan']),
                'dia_chi': clean_value(row['dia_chi']),
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
            continue
    
    results.sort(key=lambda x: (x['distance'], -x['rating']))
    return results[:top_n]

# ==================== GENERATE SMART PLAN ====================

def generate_meal_schedule(time_start_str, time_end_str):
    """Generate meal schedule based on time range"""
    time_start = datetime.strptime(time_start_str, '%H:%M')
    time_end = datetime.strptime(time_end_str, '%H:%M')
    
    duration_hours = (time_end - time_start).seconds / 3600
    
    plan = {}
    
    if duration_hours >= 12:
        plan = {
            'breakfast': {
                'time': '07:00',
                'title': 'Bữa sáng',
                'categories': ['pho', 'banh mi', 'bun'],
                'icon': '🍳'
            },
            'morning_drink': {
                'time': '09:30',
                'title': 'Giải khát buổi sáng',
                'categories': ['tra sua', 'cafe', 'coffee'],
                'icon': '🧋'
            },
            'lunch': {
                'time': '12:00',
                'title': 'Bữa trưa',
                'categories': ['com tam', 'mi', 'bun'],
                'icon': '🍚'
            },
            'afternoon_drink': {
                'time': '15:00',
                'title': 'Trà chiều',
                'categories': ['tra sua', 'cafe', 'banh'],
                'icon': '☕'
            },
            'dinner': {
                'time': '18:30',
                'title': 'Bữa tối',
                'categories': ['com tam', 'mi cay', 'pho'],
                'icon': '🍽️'
            },
            'dessert': {
                'time': '20:30',
                'title': 'Tráng miệng',
                'categories': ['banh kem', 'kem', 'tra sua'],
                'icon': '🍰'
            }
        }
    elif duration_hours >= 6:
        plan = {
            'meal1': {
                'time': time_start_str,
                'title': 'Bữa chính',
                'categories': ['com tam', 'pho', 'bun'],
                'icon': '🍚'
            },
            'drink': {
                'time': (time_start + timedelta(hours=2)).strftime('%H:%M'),
                'title': 'Giải khát',
                'categories': ['tra sua', 'cafe'],
                'icon': '☕'
            },
            'meal2': {
                'time': (time_start + timedelta(hours=4)).strftime('%H:%M'),
                'title': 'Bữa phụ',
                'categories': ['banh mi', 'mi', 'banh'],
                'icon': '🥖'
            }
        }
    else:
        plan = {
            'meal': {
                'time': time_start_str,
                'title': 'Bữa ăn',
                'categories': ['pho', 'com tam', 'bun'],
                'icon': '🍜'
            },
            'drink': {
                'time': (time_start + timedelta(hours=1.5)).strftime('%H:%M'),
                'title': 'Giải khát',
                'categories': ['tra sua', 'cafe'],
                'icon': '☕'
            }
        }
    
    return plan

def generate_food_plan(user_lat, user_lon, csv_file='Data.csv', theme=None, user_tastes=None, start_time='07:00', end_time='21:00'):
    """Tạo kế hoạch ăn uống thông minh"""
    df = pd.read_csv(csv_file)
    
    plan = generate_meal_schedule(start_time, end_time)
    
    current_lat, current_lon = user_lat, user_lon
    used_place_ids = set()
    
    base_filters = {
        'theme': theme,
        'tastes': user_tastes if user_tastes else [],
        'radius_km': 5
    }
    
    for key, meal in plan.items():
        filters = base_filters.copy()
        filters['categories'] = meal.get('categories', [])
        
        places = find_places_advanced(
            current_lat, current_lon, df, 
            filters, excluded_ids=used_place_ids, top_n=20
        )
        
        if places:
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

/* ========== TIMELINE VERTICAL ========== */
.timeline-container {
    position: relative;
    padding-left: 0;
    margin-top: 20px;
    padding-bottom: 10px;
}

.timeline-line {
    position: absolute;
    left: 80px;
    top: 12px;
    bottom: 15px;
    width: 3px;
    background: linear-gradient(to bottom, #FF6B35, #FF8E53);
}

.meal-item {
    position: relative;
    margin-bottom: 25px;
    padding-left: 100px;
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
    width: 75px;
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
    left: 72px;
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
    padding: 4px 8px;
    border: 2px solid #FFE5D9;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    outline: none;
    width: 80px;
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
}

.action-buttons {
    display: flex;
    flex-direction: row-reverse;
    gap: 10px;
}

/* ========== MANUAL MODE ========== */
.meal-item.drag-over {  
    background-color: #fff3cd !important;  
    border: 2px solid #

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
        padding-left: 100px;
    }
    
    .time-dot {
        left: 72px;
    }
    
    .food-planner-btn {
        right: 20px;
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
                                <input type="time" id="startTime" value="07:00">
                            </div>
                            <div class="time-input-group">
                                <label>Đến</label>
                                <input type="time" id="endTime" value="21:00">
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
                <div class="filter-section" onclick="toggleManualPlansSection()" style="cursor: pointer;">
                    <div class="filter-title" style="display: flex; justify-content: space-between; align-items: center;">
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

// Themes data
const themes = {
    'street_food': { name: 'Ẩm thực đường phố', icon: '🍜' },
    'seafood': { name: 'Hải sản', icon: '🦞' },
    'coffee_chill': { name: 'Cà phê chill', icon: '☕' },
    'luxury_dining': { name: 'Nhà hàng sang trọng', icon: '🍽️' },
    'asian_fusion': { name: 'Ẩm thực châu Á', icon: '🍱' },
    'vegetarian': { name: 'Món chay', icon: '🥗' },
    'dessert_bakery': { name: 'Tráng miệng & Bánh', icon: '🍰' },
    'spicy_food': { name: 'Đồ cay', icon: '🌶️' }
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
function loadSavedPlan(planId) {
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    const plan = savedPlans.find(p => p.id === planId);
    
    if (plan) {
        currentPlan = {};
        
        // 🔥 RESTORE từ array về object và giữ thứ tự
        if (Array.isArray(plan.plan)) {
            const orderList = [];
            plan.plan.forEach(item => {
                // Deep copy dữ liệu
                currentPlan[item.key] = JSON.parse(JSON.stringify(item.data));
                orderList.push(item.key);
            });
            currentPlan._order = orderList;
        } else {
            // Fallback cho dữ liệu cũ (object)
            Object.assign(currentPlan, plan.plan);
        }

        currentPlanId = planId;
        isEditMode = false;
        displayPlanVertical(currentPlan, false);

        // 🔥 VẼ ĐƯỜNG ĐI NGAY SAU KHI LOAD
        setTimeout(() => drawRouteOnMap(currentPlan), 500);
    }
}

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
            <div class="saved-plan-item" onclick="loadSavedPlan('${plan.id}')">
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
            // 🔥 CẬP NHẬT NGAY TỪ INPUT TRƯỚC KHI LƯU
            const timeInput = item.querySelector('.time-input-inline');
            if (timeInput && timeInput.value) {
                currentPlan[mealKey].time = timeInput.value;
            }
            
            // Kiểm tra các input khác
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

    const planName = prompt('Đặt tên cho kế hoạch:', `Kế hoạch ${new Date().toLocaleDateString('vi-VN')}`);
    
    if (planName) {
        const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
        
        const planRecord = {
            id: currentPlanId || Date.now().toString(),
            name: planName,
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
        
        alert('✅ Đã lưu kế hoạch thành công!');
        loadSavedPlans();
        
        if (isEditMode) {
            toggleEditMode();
        }
    }
}

// ========== LOAD SAVED PLAN - RESTORE TỪARAY VỀ OBJECT ==========
function loadSavedPlans() {
    const savedPlans = JSON.parse(localStorage.getItem('food_plans') || '[]');
    const section = document.getElementById('savedPlansSection');
    const listDiv = document.getElementById('savedPlansList');

    if (!section || !listDiv) return;

    if (!savedPlans || savedPlans.length === 0) {
        section.style.display = 'none';
        listDiv.innerHTML = '<p style="color: #999; font-size: 13px; padding: 15px; text-align: center;">Chưa có kế hoạch nào</p>';
        return;
    }

    section.style.display = 'block';
    displaySavedPlansList(savedPlans);
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
    
    // 🔥 TỰ ĐỘNG VẼ LẠI ĐƯỜNG ĐI KHI MỞ PANEL
    if (currentPlan && !isEditMode) {
        setTimeout(() => {
            const hasPlaces = Object.keys(currentPlan)
                .filter(k => k !== '_order')
                .some(k => currentPlan[k] && currentPlan[k].place);
            
            if (hasPlaces) {
                drawRouteOnMap(currentPlan);
            }
        }, 300);
    }
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
        
        const startTime = document.getElementById('startTime').value;
        const endTime = document.getElementById('endTime').value;
        
        const selectedFlavors = getSelectedFlavors();
        const tastesParam = selectedFlavors.join(',');
        
        const randomSeed = Date.now();
        let url = `/api/food-plan?lat=${userLat}&lon=${userLon}&random=${randomSeed}&start_time=${startTime}&end_time=${endTime}`;
        
        if (selectedThemes.length > 0) {
            url += `&theme=${selectedThemes.join(',')}`;
        }
        
        if (tastesParam) {
            url += `&tastes=${tastesParam}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Không thể tạo kế hoạch');
        }
        
        currentPlan = await response.json();
        currentPlanId = null;
        
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
    
    let html = `
    <div class="schedule-header">
        <h3 class="schedule-title">📅 Lịch trình của bạn</h3>
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
    
    // 🔥 SẮP XẾP THEO THỜI GIAN THỰC TẾ
    const allMealKeys = Object.keys(plan)
        .filter(k => k !== '_order' && plan[k] && plan[k].time)
        .sort((a, b) => {
            const timeA = plan[a].time || '00:00';
            const timeB = plan[b].time || '00:00';
            return timeA.localeCompare(timeB);
        });
    
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
                            `<input type="time" class="time-input-inline" value="${meal.time}" onchange="updateMealTime('${key}', this.value)">` :
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
                        `<input type="time" class="time-input-inline" value="${meal.time}" onchange="updateMealTime('${key}', this.value)">` :
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
                                <strong>${place.rating.toFixed(1)}</strong>
                            </div>
                            <div class="meta-item-vertical">
                                <span>🚗</span>
                                <strong>${place.distance} km</strong>
                            </div>
                            ${place.gia_trung_binh ? `
                                <div class="meta-item-vertical">
                                    <span>💰</span>
                                    <strong>${place.gia_trung_binh}</strong>
                                </div>
                            ` : ''}
                        </div>
                        ${place.khau_vi ? `
                            <div style="margin-top: 8px; padding: 6px 10px; background: #FFF5E6; border-radius: 6px; font-size: 12px; color: #8B6914;">
                                👅 Khẩu vị: ${place.khau_vi}
                            </div>
                        ` : ''}
                        <div class="travel-info-vertical">
                            🚗 <strong>Nên khởi hành lúc ${place.suggest_leave}</strong><br>
                            ⏱️ Di chuyển khoảng ${place.travel_time} phút
                        </div>
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
    }
    
    // 🔥 VẼ ĐƯỜNG ĐI KHI HIỂN THỊ KẾ HOẠCH
    if (!editMode && hasPlaces) {
        setTimeout(() => drawRouteOnMap(plan), 500);
    } else {
        clearRoutes();
    }
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

function clearRoutes() {
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
    
    clearRoutes();
    
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
        
        const response = await fetch(url);
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
        for (let i = 0; i < waypoints.length - 1; i++) {
            await drawSingleRoute(waypoints[i], waypoints[i + 1], i);
        }
        
        const bounds = L.latLngBounds(waypoints.map(w => [w.lat, w.lon]));
        map.fitBounds(bounds, { padding: [50, 50] });
        
        console.log(`✅ Đã vẽ ${waypoints.length - 1} đoạn đường`);
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
}

// ========== REPLACE PLACE IN MEAL ==========
function replacePlaceInMeal(newPlace) {
    if (!waitingForPlaceSelection || !currentPlan) return;
    
    const mealKey = waitingForPlaceSelection;
    
    let prevLat, prevLon;
    if (window.currentUserCoords) {
        prevLat = window.currentUserCoords.lat;
        prevLon = window.currentUserCoords.lon;
    }
    
    const allKeys = Object.keys(currentPlan).sort((a, b) => {
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
    
    currentPlan[mealKey].place = {
        ten_quan: newPlace.ten_quan,
        dia_chi: newPlace.dia_chi,
        rating: newPlace.rating || 0,
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
    
    waitingForPlaceSelection = null;
    selectedPlaceForReplacement = null;
    displayPlanVertical(currentPlan, isEditMode);
    
    alert('✅ Đã thay đổi quán thành công!');
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
    
    lastTargetElement = null; // 🔥 RESET
    startAutoScroll();
}

function handleDragEnd(e) {
    if (draggedElement) {
        draggedElement.classList.remove('dragging');
    }
    draggedElement = null;
    window.draggedElement = null;
    lastDragY = 0;
    lastTargetElement = null; // 🔥 RESET
    
    stopAutoScroll();
}

// ========== DRAG OVER ITEM - HIGHLIGHT VỊ TRÍ MUỐN ĐỔI ==========
function handleDragOverItem(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    
    if (!draggedElement || draggedElement === this) return;
    
    e.dataTransfer.dropEffect = 'move';
    
    // 🔥 HIGHLIGHT card đích - để người dùng thấy rõ
    if (lastTargetElement && lastTargetElement !== this) {
        lastTargetElement.classList.remove('drag-over');
    }
    
    lastTargetElement = this;
    this.classList.add('drag-over');  // Thêm class để hiện visual feedback
    
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

// ✨ AUTO-SCROLL TOÀN BỘ PANEL - CỰC NHANH
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
        
        // 🔥 DÙNG lastDragY CẬP NHẬT LiÊN TỤC
        if (lastDragY === 0) return;
        
        const topEdge = rect.top + 150;      // Vùng trên
        const bottomEdge = rect.bottom - 150; // Vùng dưới
        
        let scrollSpeed = 0;
        
        // CUỘN LÊN
        if (lastDragY < topEdge) {
            const distance = topEdge - lastDragY;
            const ratio = Math.min(1, distance / 150);
            scrollSpeed = -(10 + ratio * 40); // 10-50 px/frame
            container.scrollTop += scrollSpeed;
        }
        // CUỘN XUỐNG
        else if (lastDragY > bottomEdge) {
            const distance = lastDragY - bottomEdge;
            const ratio = Math.min(1, distance / 150);
            scrollSpeed = (10 + ratio * 40); // 10-50 px/frame
            container.scrollTop += scrollSpeed;
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
    
    // 🔥 CẬP NHẬT DỮ LIỆU TRƯỚC KHI ĐỔI
    // Từ input tên của draggedElement
    const draggedTitleInput = draggedElement.querySelector('.meal-title-input');
    const draggedTimeInput = draggedElement.querySelector('.time-input-inline');
    if (draggedTitleInput && draggedKey && currentPlan[draggedKey]) {
        currentPlan[draggedKey].title = draggedTitleInput.value;
    }
    if (draggedTimeInput && draggedKey && currentPlan[draggedKey]) {
        currentPlan[draggedKey].time = draggedTimeInput.value;
    }
    
    // Từ input tên của targetElement
    const targetTitleInput = lastTargetElement.querySelector('.meal-title-input');
    const targetTimeInput = lastTargetElement.querySelector('.time-input-inline');
    if (targetTitleInput && targetKey && currentPlan[targetKey]) {
        currentPlan[targetKey].title = targetTitleInput.value;
    }
    if (targetTimeInput && targetKey && currentPlan[targetKey]) {
        currentPlan[targetKey].time = targetTimeInput.value;
    }
    
    // ✅ SWAP DỮ LIỆU
    if (currentPlan && draggedKey && targetKey) {
        const temp = currentPlan[draggedKey];
        currentPlan[draggedKey] = currentPlan[targetKey];
        currentPlan[targetKey] = temp;
    }
    
    // ✅ RENDER LẠI (không swap HTML trực tiếp)
    displayPlanVertical(currentPlan, isEditMode);
    
    // 🔥 REMOVE HIGHLIGHT
    if (lastTargetElement) {
        lastTargetElement.classList.remove('drag-over');
    }
    
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
    
    // Reset waiting state khi thoát edit mode
    if (!isManualEditMode) {
        waitingForPlaceSelection = null;
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
            <div class="saved-plan-item" onclick="openManualPlan('${plan.id}')">
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
    isManualEditMode = false; // Reset edit mode khi mở plan mới
    waitingForPlaceSelection = null; // Reset waiting state
    
    // Đóng danh sách kế hoạch
    const container = document.getElementById('manualPlansContainer');
    const arrow = document.getElementById('manualPlansArrow');
    container.style.maxHeight = '0';
    arrow.style.transform = 'rotate(0deg)';
    
    // Hiển thị timeline
    displayManualPlanTimeline();
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
    const editMode = isManualEditMode; // Dùng biến state để kiểm soát edit mode
    
    let html = `
    <div class="schedule-header">
        <h3 class="schedule-title" ${editMode ? 'contenteditable="true" onblur="updateManualPlanName(this.textContent)"' : ''} style="outline: none; ${editMode ? 'cursor: text;' : ''}">${planName}</h3>
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
    
    manualPlan.forEach((item, index) => {
        const isWaiting = waitingForPlaceSelection === item.id;
        
        if (!item.place) {
            // Card trống
            html += `
                <div class="meal-item" data-meal-id="${item.id}">
                    <div class="time-marker">
                        ${editMode ? 
                            `<input type="time" class="time-input-inline" value="${item.time}" onchange="updateManualItemTime(${item.id}, this.value)">` :
                            `<div class="time-badge">${item.time}</div>`
                        }
                    </div>
                    <div class="time-dot"></div>
                    <div class="meal-card-vertical empty-slot ${editMode ? 'edit-mode' : ''}">
                        <div class="meal-title-vertical">
                            <div class="meal-title-left">
                                ${editMode ? `
                                    <select onchange="updateManualItemIcon(${item.id}, this.value)" style="border: none; background: transparent; font-size: 22px; cursor: pointer; outline: none; padding: 0;" onclick="event.stopPropagation();">
                                        ${iconOptions.map(ico => `<option value="${ico}" ${ico === (item.icon || '🍽️') ? 'selected' : ''}>${ico}</option>`).join('')}
                                    </select>
                                ` : `<span style="font-size: 22px;">${item.icon || '🍽️'}</span>`}
                                ${editMode ? 
                                    `<input type="text" value="${item.title}" onchange="updateManualItemTitle(${item.id}, this.value)" 
                                        style="border: none; background: transparent; font-size: 15px; font-weight: 600; outline: none; flex: 1;" onclick="event.stopPropagation();">` :
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
                            <div class="icon">🏪</div>
                            <div class="text">${isWaiting ? 'Đang chờ chọn quán...' : 'Chưa có quán'}</div>
                            ${!editMode ? '<div style="font-size: 12px; margin-top: 8px; color: #999;">Bật chế độ chỉnh sửa để thêm quán</div>' : '<div style="font-size: 12px; margin-top: 8px; color: #999;">Nhấn nút ✔ để chọn quán từ bản đồ</div>'}
                        </div>
                    </div>
                </div>
            `;
        } else {
                    // Card có quán
                    const place = item.place;
                    const cardClickEvent = editMode ? '' : `onclick="flyToPlace(${place.lat}, ${place.lon})"`;
                    const cardCursor = editMode ? 'cursor: default;' : 'cursor: pointer;';
                    
                    html += `
                        <div class="meal-item" data-meal-id="${item.id}">
                            <div class="time-marker">
                                ${editMode ? 
                                    `<input type="time" class="time-input-inline" value="${item.time}" onchange="updateManualItemTime(${item.id}, this.value)">` :
                                    `<div class="time-badge">${item.time}</div>`
                                }
                            </div>
                            <div class="time-dot"></div>
                            <div class="meal-card-vertical ${editMode ? 'edit-mode' : ''}" ${cardClickEvent} style="${cardCursor}">
                                <div class="meal-title-vertical">
                                    <div class="meal-title-left">
                                        ${editMode ? `
                                            <select onchange="updateManualItemIcon(${item.id}, this.value)" style="border: none; background: transparent; font-size: 22px; cursor: pointer; outline: none; padding: 0;" onclick="event.stopPropagation();">
                                                ${iconOptions.map(ico => `<option value="${ico}" ${ico === (item.icon || '🍽️') ? 'selected' : ''}>${ico}</option>`).join('')}
                                            </select>
                                        ` : `<span style="font-size: 22px;">${item.icon || '🍽️'}</span>`}
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
                                </div>
                            </div>
                        </div>
                    `;
                }
            });
            
            html += '</div>';
            contentDiv.innerHTML = html;
        }

function updateManualPlanName(newName) {
    if (!currentManualPlanId) return;
    
    const plan = manualPlans.find(p => p.id === currentManualPlanId);
    if (plan) {
        plan.name = newName.trim() || 'Kế hoạch';
        localStorage.setItem('manual_food_plans', JSON.stringify(manualPlans));
        displayManualPlansList();
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

    // 🔥 Cập nhật time từ DOM
    const mealItems = document.querySelectorAll('.meal-item');
    mealItems.forEach(item => {
        const mealId = parseInt(item.dataset.mealId);
        const timeInput = item.querySelector('.time-input-inline');
        if (timeInput) {
            const manualItem = manualPlan.find(i => i.id === mealId);
            if (manualItem) {
                manualItem.time = timeInput.value;
            }
        }
    });

    const plan = manualPlans.find(p => p.id === currentManualPlanId);
    if (plan) {
        plan.items = [...manualPlan];
        plan.updatedAt = new Date().toISOString();
        localStorage.setItem('manual_food_plans', JSON.stringify(manualPlans));
        
        // 🔥 THÊM: Thoát edit mode sau khi lưu
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
    isEditMode: () => isEditMode || currentManualPlanId !== null,
    isWaitingForPlaceSelection: () => waitingForPlaceSelection !== null,
    selectPlace: (place) => {
        if (waitingForPlaceSelection) {
            // Kiểm tra xem đang ở mode nào
            if (currentManualPlanId) {
                // Manual mode
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
                }
            } else {
                // Auto mode
                selectedPlaceForReplacement = place;
                replacePlaceInMeal(place);
            }
            return true;
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
</script>
'''