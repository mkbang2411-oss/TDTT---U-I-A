import pandas as pd
import random
import re

CSV_FILE = "Data_with_flavor.csv"

# Giờ mở cửa random (bạn tự chỉnh ở đây)
OPEN_HOURS = ["7:00","8:00","9:00","7:30","8:30"]

# ====== TỰ CHỈNH Ở ĐÂY ======
START_CSV = 1774      # dòng bắt đầu (giống hệt số dòng trong file CSV)
END_CSV   = 1826      # dòng kết thúc (giống hệt số dòng trong file CSV)
# ============================

df = pd.read_csv(CSV_FILE)

# Tổng số dòng = header + dữ liệu
TOTAL_CSV_LINES = len(df) + 1   # +1 vì header = dòng 1

# Kiểm tra hợp lệ
if START_CSV < 2 or END_CSV > TOTAL_CSV_LINES:
    raise ValueError(
        f"Sai dòng! File CSV có tổng {TOTAL_CSV_LINES} dòng (bao gồm header).\n"
        f"Dữ liệu bắt đầu từ dòng 2 → {TOTAL_CSV_LINES}.\n"
        f"Bạn nhập START={START_CSV}, END={END_CSV}."
    )

# Chuyển đổi về index pandas
START_IDX = START_CSV - 2
END_IDX   = END_CSV   - 2   # dùng END_IDX trong slice có +1 phía dưới

def fix_opening_text(text):
    if pd.isna(text):
        return text

    lower = text.lower().strip()

    # Không xử lý các trường hợp đặc biệt
    if "mở cả ngày" in lower or "không rõ giờ mở cửa" in lower:
        return text
    if text.startswith("Mở cửa lúc") or text.startswith("Mở cửa vào"):
        return text

    CUSTOM_CLOSE_HOURS = ["20:00","21:00","20:30","21:30","22:00"]

    # 1️⃣ "Đã đóng cửa · Mở cửa vào 16:00"
    match_open = re.search(r"Mở cửa vào\s*([0-9]{1,2}:[0-9]{2})", text)
    if match_open:
        return f"Mở cửa vào {match_open.group(1)} ⋅ Đóng cửa vào {random.choice(CUSTOM_CLOSE_HOURS)}"

    # 2️⃣ "Sắp mở cửa · 16:30"
    match_soon = re.search(r"Sắp mở cửa\s*[·-]?\s*([0-9]{1,2}:[0-9]{2})", text)
    if match_soon:
        return f"Mở cửa lúc {match_soon.group(1)} ⋅ Đóng cửa vào {random.choice(CUSTOM_CLOSE_HOURS)}"

    # ⭐ 3️⃣ CASE MỚI — "Sắp đóng cửa · 14:00 · Mở cửa lại vào 15:30"
    match_closing_soon = re.search(r"Sắp đóng cửa\s*[·-]?\s*([0-9]{1,2}:[0-9]{2})", text)
    if match_closing_soon:
        closing_time = match_closing_soon.group(1)
        new_open = random.choice(OPEN_HOURS)
        return f"Mở cửa lúc {new_open} ⋅ Đóng cửa vào {closing_time}"

    # 4️⃣ Trường hợp có giờ đóng cửa
    match_close = re.search(r"Đóng cửa (?:lúc|vào|·)?\s*([0-9]{1,2}:[0-9]{2})", text)
    closing_time = match_close.group(1) if match_close else None

    # 5️⃣ Random giờ mở cửa
    new_open = random.choice(OPEN_HOURS)

    if closing_time:
        return f"Mở cửa lúc {new_open} ⋅ Đóng cửa vào {closing_time}"

    # 6️⃣ Fallback
    return f"Mở cửa lúc {new_open}"



# Preview trước khi update
print("\n===== Preview dòng cũ =====")
print(df.loc[START_IDX:END_IDX, ["ten_quan", "gio_mo_cua"]])

# Apply update (lưu ý END_IDX+1 vì slice bên phải là exclusive)
df.loc[START_IDX:END_IDX, "gio_mo_cua"] = (
    df.loc[START_IDX:END_IDX, "gio_mo_cua"].apply(fix_opening_text)
)

print("\n===== Preview dòng mới =====")
print(df.loc[START_IDX:END_IDX, ["ten_quan", "gio_mo_cua"]])

# Lưu lại file
df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
print(f"\n🎉 Đã cập nhật đúng CHÍNH XÁC từ dòng CSV {START_CSV} → {END_CSV}!")
