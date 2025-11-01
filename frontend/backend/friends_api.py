import json
import os
from flask import Blueprint, request, jsonify

friends_bp = Blueprint('friends', __name__)
FRIENDS_DB = "friends_data.json"

def load_friends_data():
    """Đọc dữ liệu từ file JSON"""
    if not os.path.exists(FRIENDS_DB):
        return {}
    try:
        with open(FRIENDS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_friends_data(data):
    """Lưu dữ liệu vào file JSON"""
    with open(FRIENDS_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_data(username):
    """Lấy hoặc tạo dữ liệu user"""
    data = load_friends_data()
    if username not in data:
        data[username] = {"friends": [], "pending": [], "sent": []}
        save_friends_data(data)
    return data[username]

@friends_bp.route('/api/friends/all-users')
def get_all_users():
    """Lấy danh sách tất cả users"""
    data = load_friends_data()
    return jsonify(list(data.keys()))

@friends_bp.route('/api/friends/stats')
def get_stats():
    """Lấy thống kê"""
    user = request.args.get('user')
    if not user:
        return jsonify({"error": "Thiếu user"}), 400
    user_data = get_user_data(user)
    return jsonify({
        "friends": len(user_data["friends"]),
        "pending": len(user_data["pending"]),
        "sent": len(user_data["sent"])
    })

@friends_bp.route('/api/friends/discover')
def discover_users():
    """Tìm người để kết bạn"""
    user = request.args.get('user')
    if not user:
        return jsonify([])
    data = load_friends_data()
    user_data = get_user_data(user)
    all_users = set(data.keys())
    excluded = set([user] + user_data["friends"] + user_data["sent"])
    available = list(all_users - excluded)
    return jsonify(available)

@friends_bp.route('/api/friends/list')
def get_friends_list():
    """Danh sách bạn bè"""
    user = request.args.get('user')
    if not user:
        return jsonify([])
    user_data = get_user_data(user)
    return jsonify(user_data["friends"])

@friends_bp.route('/api/friends/pending')
def get_pending():
    """Lời mời nhận được"""
    user = request.args.get('user')
    if not user:
        return jsonify([])
    user_data = get_user_data(user)
    return jsonify(user_data["pending"])

@friends_bp.route('/api/friends/sent')
def get_sent():
    """Lời mời đã gửi"""
    user = request.args.get('user')
    if not user:
        return jsonify([])
    user_data = get_user_data(user)
    return jsonify(user_data["sent"])

@friends_bp.route('/api/friends/send', methods=['POST'])
def send_request():
    """Gửi lời mời kết bạn"""
    req_data = request.get_json()
    from_user = req_data.get('from')
    to_user = req_data.get('to')
    if not from_user or not to_user:
        return jsonify({"error": "Thiếu thông tin"}), 400
    data = load_friends_data()
    if from_user not in data:
        data[from_user] = {"friends": [], "pending": [], "sent": []}
    if to_user not in data:
        data[to_user] = {"friends": [], "pending": [], "sent": []}
    if to_user not in data[from_user]["sent"]:
        data[from_user]["sent"].append(to_user)
    if from_user not in data[to_user]["pending"]:
        data[to_user]["pending"].append(from_user)
    save_friends_data(data)
    return jsonify({"message": f"✅ Đã gửi lời mời đến {to_user}!"})

@friends_bp.route('/api/friends/accept', methods=['POST'])
def accept_request():
    """Chấp nhận lời mời"""
    req_data = request.get_json()
    user = req_data.get('user')
    from_user = req_data.get('from')
    if not user or not from_user:
        return jsonify({"error": "Thiếu thông tin"}), 400
    data = load_friends_data()
    if from_user in data[user]["pending"]:
        data[user]["pending"].remove(from_user)
    if user in data[from_user]["sent"]:
        data[from_user]["sent"].remove(user)
    if from_user not in data[user]["friends"]:
        data[user]["friends"].append(from_user)
    if user not in data[from_user]["friends"]:
        data[from_user]["friends"].append(user)
    save_friends_data(data)
    return jsonify({"message": f"🎉 Bạn và {from_user} đã là bạn bè!"})

@friends_bp.route('/api/friends/reject', methods=['POST'])
def reject_request():
    """Từ chối lời mời"""
    req_data = request.get_json()
    user = req_data.get('user')
    from_user = req_data.get('from')
    if not user or not from_user:
        return jsonify({"error": "Thiếu thông tin"}), 400
    data = load_friends_data()
    if from_user in data[user]["pending"]:
        data[user]["pending"].remove(from_user)
    if user in data[from_user]["sent"]:
        data[from_user]["sent"].remove(user)
    save_friends_data(data)
    return jsonify({"message": f"❌ Đã từ chối {from_user}"})

@friends_bp.route('/api/friends/remove', methods=['POST'])
def remove_friend():
    """Xóa bạn bè"""
    req_data = request.get_json()
    user = req_data.get('user')
    friend = req_data.get('friend')
    if not user or not friend:
        return jsonify({"error": "Thiếu thông tin"}), 400
    data = load_friends_data()
    if friend in data[user]["friends"]:
        data[user]["friends"].remove(friend)
    if user in data[friend]["friends"]:
        data[friend]["friends"].remove(user)
    save_friends_data(data)
    return jsonify({"message": f"🗑️ Đã xóa {friend}"})

@friends_bp.route('/api/friends/cancel', methods=['POST'])
def cancel_request():
    """Hủy lời mời đã gửi"""
    req_data = request.get_json()
    user = req_data.get('user')
    to_user = req_data.get('to')
    if not user or not to_user:
        return jsonify({"error": "Thiếu thông tin"}), 400
    data = load_friends_data()
    if to_user in data[user]["sent"]:
        data[user]["sent"].remove(to_user)
    if user in data[to_user]["pending"]:
        data[to_user]["pending"].remove(user)
    save_friends_data(data)
    return jsonify({"message": f"↩️ Đã hủy lời mời"})
