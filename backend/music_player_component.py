import os
import json


def _scan_music_and_covers():
    """Scan ../frontend/music và ../frontend/disc_covers.

    Quy ước file nhạc:
      - "Đom Đóm - Jack - J97_1.mpeg"
            -> title: "Đom Đóm - Jack - J97"
            -> id: "1" (dùng match cover)
      - Ảnh đĩa: "1.png" (hoặc .jpg/.jpeg/.webp/.gif)
            -> cover cho id=1

      - Nếu không có "_số":
            base = tên file bỏ đuôi
            id   = base
            title= base
    """
    root_dir = os.path.dirname(__file__)
    music_dir = os.path.normpath(os.path.join(root_dir, "..", "frontend", "music"))
    cover_dir = os.path.normpath(os.path.join(root_dir, "..", "frontend", "disc_covers"))

    tracks: list[dict] = []

    allowed_ext = (".mp3", ".wav", ".ogg", ".m4a", ".mpeg", ".mp4")

    cover_map: dict[str, str] = {}
    if os.path.isdir(cover_dir):
        for fname in os.listdir(cover_dir):
            lower = fname.lower()
            if not lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                continue
            base, _ = os.path.splitext(fname)
            # URL static cho frontend (giữ như cũ)
            cover_map[base] = f"/disc_covers/{fname}"

    if not os.path.isdir(music_dir):
        return tracks

    for fname in sorted(os.listdir(music_dir)):
        lower = fname.lower()
        if not lower.endswith(allowed_ext):
            continue

        base, _ = os.path.splitext(fname)
        title = base
        track_id: str | None = None

        # Tên có dạng "..._1" thì lấy "1" làm id
        if "_" in base:
            title_part, maybe_id = base.rsplit("_", 1)
            if maybe_id.isdigit():
                title = title_part
                track_id = maybe_id

        if track_id is None:
            track_id = base

        cover_url = cover_map.get(track_id, "")

        tracks.append(
            {
                "id": track_id,
                "title": title,
                "artist": "",
                "mood": "",
                "file": f"/music/{fname}",
                "cover": cover_url,
                "accent": "",
            }
        )

    return tracks


def get_music_player_html() -> str:
    """Return HTML block to inject into main page."""
    tracks = _scan_music_and_covers()
    tracks_json = json.dumps(tracks, ensure_ascii=False)

    base_html = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ========== FLOATING MUSIC BUTTON (CAM GIỐNG FOOD PLANNER) ========== */
    .music-player-btn {
        position: fixed;
        bottom: 370px;
        right: 30px;
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
        box-shadow:
            0 8px 32px rgba(255, 107, 53, 0.45),
            0 0 0 0 rgba(255, 107, 53, 0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999997;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        animation: music-pulse 2s ease-in-out infinite;
    }

    .music-disc-icon img,
    .track-disc-mini img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        position: absolute;
        top: 0;
        left: 0;
        z-index: 2;
        pointer-events: none;
    }

    @keyframes music-pulse {
        0%, 100% {
            box-shadow:
                0 8px 32px rgba(255, 107, 53, 0.45),
                0 0 0 0 rgba(255, 107, 53, 0.4);
        }
        50% {
            box-shadow:
                0 8px 32px rgba(255, 107, 53, 0.45),
                0 0 0 12px rgba(255, 107, 53, 0);
        }
    }

    .music-player-btn:hover {
        transform: translateY(-6px) scale(1.08);
        box-shadow:
            0 16px 48px rgba(255, 107, 53, 0.6),
            0 0 0 0 rgba(255, 107, 53, 0.4);
    }

    .music-player-btn.active {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
        box-shadow:
            0 16px 48px rgba(255, 126, 75, 0.65),
            0 0 0 0 rgba(255, 126, 75, 0.4);
    }

    /* ===== MUSIC NOTE ICON ===== */
    .music-disc-icon,
    .track-disc-mini {
        position: relative;
        border-radius: 50%;
        overflow: hidden;
        transform-origin: center;
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.95), rgba(255, 142, 83, 0.95));
        box-shadow:
            0 4px 12px rgba(255, 107, 53, 0.4),
            inset 0 2px 4px rgba(255, 255, 255, 0.3);
    }

    .music-disc-icon {
        width: 52px;
        height: 52px;
    }

    .track-disc-mini {
        width: 44px;
        height: 44px;
        flex-shrink: 0;
        font-size: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .track-disc-mini::before {
        content: "♪";
        position: relative;
        z-index: 1;
        color: #FFFFFF;
    }

    /* Khi có cover: dùng cover làm nền với nốt nhạc trắng */
    .music-disc-icon.has-cover,
    .track-disc-mini.has-cover {
        background-size: cover;
        background-position: center;
        box-shadow:
            0 4px 12px rgba(0, 0, 0, 0.2),
            inset 0 2px 6px rgba(0, 0, 0, 0.25);
    }

    .music-disc-icon.has-cover::before,
    .track-disc-mini.has-cover::before {
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }

    .music-disc-icon.playing,
    .track-disc-mini.playing {
        animation: smooth-spin 8s linear infinite;
    }

    @keyframes smooth-spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }

    /* ========== GLASSMORPHIC PANEL (TONE FOOD PLANNER) ========== */
    .music-panel {
        position: fixed;
        right: 110px;
        bottom: 338px;
        width: 420px;
        max-width: calc(100% - 120px);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #1f2933;
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(26px) saturate(180%);
        -webkit-backdrop-filter: blur(26px) saturate(180%);
        border-radius: 28px;
        border: 1px solid #FFE5D9;
        box-shadow:
            0 10px 35px rgba(148, 85, 45, 0.25),
            0 24px 60px rgba(203, 92, 37, 0.18),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
        overflow: hidden;
        z-index: 99999998;
        opacity: 0;
        transform: translateY(24px) scale(0.95);
        pointer-events: none;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .music-panel.open {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: auto;
    }

    /* ===== HEADER ===== */
    .music-panel-header {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 24px 14px;
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.14) 0%,
            rgba(255, 142, 83, 0.10) 100%
        );
        border-bottom: 1px solid #FFE5D9;
    }

    .music-panel-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
    }

    .music-panel-header-left {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .music-panel-title {
        font-weight: 700;
        font-size: 18px;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .music-panel-subtitle {
        font-size: 12px;
        color: #6b7280;
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
    }

    .music-panel-header-right {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .music-close-btn {
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
    }

    .music-close-btn:hover {
        background: #FFFFFF;
        color: #FFB084;
        transform: rotate(90deg);
        border-color: #FFB084;
        box-shadow: 0 4px 14px rgba(255, 126, 75, 0.4);
    }

    /* ===== TRACK LIST ===== */
    .music-track-list {
        padding: 8px 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;

        /* CHIỀU CAO CHUẨN CHO 2 BÀI */
        height: 164px;
        max-height: 164px;
        overflow-y: auto;

        background: #FFF5F0;
        
        /* THÊM DÒNG NÀY */
        flex-shrink: 0;
    }

    .music-track-list::-webkit-scrollbar {
        width: 6px;
    }

    .music-track-list::-webkit-scrollbar-track {
        background: #FFE5D9;
        border-radius: 10px;
        margin: 8px 0;
    }

    .music-track-list::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #FFB084, #FF8E53);
        border-radius: 10px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }

    .track-item {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 14px;
        border-radius: 18px;
        background: #FFFFFF;
        backdrop-filter: blur(10px);
        border: 1px solid #FFE5D9;
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        
        /* THÊM 2 DÒNG NÀY */
        flex-shrink: 0;
        min-height: 68px;  /* Cố định chiều cao mỗi bài */
    }

    .track-item::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.10),
            rgba(255, 142, 83, 0.06)
        );
        opacity: 0;
        transition: opacity 0.25s ease;
    }

    .track-item:hover::before {
        opacity: 1;
    }

    .track-item:hover {
        background: #FFF9F5;
        transform: translateY(-2px) translateX(4px);
        border-color: #FFB084;
        box-shadow:
            0 8px 24px rgba(255, 126, 75, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.85);
    }

    .track-item.active {
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.20),
            rgba(255, 142, 83, 0.15)
        );
        border-color: rgba(255, 126, 75, 0.85);
        box-shadow:
            0 10px 30px rgba(255, 126, 75, 0.35),
            inset 0 1px 0 rgba(255, 255, 255, 0.75);
    }

    .track-item.active::before {
        opacity: 1;
    }

    .track-meta {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
        position: relative;
        z-index: 1;
    }

    .track-title {
        font-size: 14px;
        font-weight: 600;
        color: #1f2933;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        letter-spacing: -0.01em;
    }

    .track-sub {
        font-size: 11px;
        display: flex;
        gap: 8px;
        align-items: center;
        color: #6b7280;
        font-weight: 500;
    }

    .track-sub-pill {
        padding: 2px 8px;
        border-radius: 12px;
        background: #FFE5D9;
        border: 1px solid #FFB084;
        font-size: 10px;
        font-weight: 600;
        color: #9A3412;
    }

    .track-play-btn {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: none;
        background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
        color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        cursor: pointer;
        flex-shrink: 0;
        box-shadow:
            0 4px 16px rgba(255, 126, 75, 0.55),
            inset 0 1px 0 rgba(255, 255, 255, 0.35);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        z-index: 1;
    }

    .track-play-btn:hover {
        transform: translateY(-2px) scale(1.05);
        box-shadow:
            0 8px 24px rgba(255, 126, 75, 0.7),
            inset 0 1px 0 rgba(255, 255, 255, 0.35);
    }

    .track-play-btn.playing {
        background: linear-gradient(135deg, #FF7A3C 0%, #FF9B60 100%);
        box-shadow:
            0 4px 16px rgba(255, 126, 75, 0.65),
            inset 0 1px 0 rgba(255, 255, 255, 0.35);
    }

    .track-play-btn.playing:hover {
        box-shadow:
            0 8px 24px rgba(255, 126, 75, 0.8),
            inset 0 1px 0 rgba(255, 255, 255, 0.35);
    }

    /* ===== FOOTER / SEEK BAR ===== */
    .music-footer {
        border-top: 1px solid #FFE5D9;
        padding: 14px 20px 16px;
        background: linear-gradient(
            135deg,
            #FFF5F0 0%,
            #FFE5D9 100%
        );
        backdrop-filter: blur(20px);
        position: relative;
    }

    .music-footer::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.9), transparent);
    }

    .music-footer-main {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        gap: 12px;
    }

    .music-footer-title {
        flex: 1;
        text-align: center;
        font-size: 13px;
        font-weight: 600;
        color: #1f2933;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        letter-spacing: -0.01em;
    }

    .music-footer-time {
        min-width: 40px;
        font-size: 11px;
        font-weight: 600;
        color: #6b7280;
        font-variant-numeric: tabular-nums;
    }

    .music-footer input[type="range"] {
        width: 100%;
        height: 6px;
        -webkit-appearance: none;
        appearance: none;
        border-radius: 10px;
        background: linear-gradient(
            90deg,
            rgba(255, 107, 53, 0.55) 0%,
            rgba(255, 107, 53, 0.55) 0%,
            rgba(255, 212, 186, 0.9) 0%,
            rgba(255, 212, 186, 0.9) 100%
        );
        outline: none;
        cursor: pointer;
        position: relative;
    }

    .music-footer input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFB084, #FF8E53);
        box-shadow:
            0 2px 8px rgba(255, 126, 75, 0.6),
            0 0 0 4px rgba(255, 255, 255, 0.9),
            0 0 0 6px rgba(255, 126, 75, 0.3);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .music-footer input[type="range"]::-webkit-slider-thumb:hover {
        transform: scale(1.15);
        box-shadow:
            0 4px 12px rgba(255, 126, 75, 0.7),
            0 0 0 4px rgba(255, 255, 255, 1),
            0 0 0 8px rgba(255, 126, 75, 0.35);
    }

    .music-footer input[type="range"]::-moz-range-thumb {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFB084, #FF8E53);
        border: 4px solid rgba(255, 255, 255, 0.9);
        box-shadow:
            0 2px 8px rgba(255, 126, 75, 0.6),
            0 0 0 2px rgba(255, 126, 75, 0.3);
        cursor: pointer;
    }

    /* Empty state */
    .track-list-empty {
        padding: 32px 20px;
        text-align: center;
        color: #6b7280;
        background: #FFF5F0;
    }

    .track-list-empty-icon {
        font-size: 44px;
        margin-bottom: 10px;
        opacity: 0.6;
    }

    .track-list-empty-text {
        font-size: 13px;
        font-weight: 500;
    }

    @media (max-width: 768px) {
        .music-player-btn {
            bottom: 240px;
            right: 20px;
            width: 56px;
            height: 56px;
        }

        .music-disc-icon {
            width: 44px;
            height: 44px;
        }

        .music-panel {
            right: 16px;
            left: 16px;
            bottom: 120px;
            width: auto;
            max-width: none;
        }
    }

/* ===== PLAYLIST MODE DROPDOWN ===== */
    .music-tag {
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.2),
            rgba(255, 142, 83, 0.18)
        );
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 6px 12px;
        font-size: 11px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        color: #9A3412;
        border: 1px solid rgba(255, 148, 94, 0.8);
        position: relative;
        cursor: pointer;
        user-select: none;
    }

    .music-tag:hover {
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.3),
            rgba(255, 142, 83, 0.25)
        );
    }

    .playlist-mode-dropdown {
        position: fixed;  /* Đổi từ absolute thành fixed */
        background: #FFFFFF;
        border: 1px solid #FFE5D9;
        border-radius: 16px;
        box-shadow:
            0 8px 24px rgba(255, 126, 75, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
        overflow: hidden;
        opacity: 0;
        transform: translateY(-10px);
        pointer-events: none;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 10000001;  /* Cao hơn panel */
        min-width: 180px;
    }

    .playlist-mode-dropdown.show {
        opacity: 1;
        transform: translateY(0);
        pointer-events: auto;
    }

    .mode-option {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 13px;
        font-weight: 600;
        color: #1f2933;
    }

    .mode-option:hover {
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.1),
            rgba(255, 142, 83, 0.08)
        );
    }

    .mode-option.active {
        background: linear-gradient(
            135deg,
            rgba(255, 107, 53, 0.15),
            rgba(255, 142, 83, 0.12)
        );
        color: #FF6B35;
    }

    .mode-option-icon {
        font-size: 16px;
    }

    .music-volume-btn {
        font-size: 18px;
        font-weight: 700;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid #FFE5D9;
        color: transparent;
    }

    /* Fix riêng cho Firefox */
    .music-volume-btn::-moz-focus-inner {
        border: 0;
    }

    .music-volume-btn::before {
        content: "🔊";
        position: absolute;
        background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .music-volume-btn:hover {
        background: #FFFFFF;
        border-color: #FFB084;
        transform: scale(1.05);
        box-shadow: 0 4px 14px rgba(255, 126, 75, 0.4);
    }

    /* Volume Slider Dọc - Redesigned */
    .volume-slider-container {
        position: fixed;
        width: 80px;
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(26px) saturate(180%);
        -webkit-backdrop-filter: blur(26px) saturate(180%);
        border: 1px solid #FFE5D9;
        border-radius: 24px;
        padding: 20px 16px;
        box-shadow:
            0 10px 35px rgba(255, 107, 53, 0.25),
            0 24px 60px rgba(203, 92, 37, 0.18),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
        opacity: 0;
        transform: translateX(10px) scale(0.95);
        pointer-events: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 10000001;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
    }

    .volume-slider-container::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
        border-radius: 24px 24px 0 0;
    }

    .volume-slider-container.show {
        opacity: 1;
        transform: translateX(0) scale(1);
        pointer-events: auto;
    }

    .volume-icon {
        font-size: 24px;
        background: linear-gradient(135deg, #FFB084 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .volume-slider {
        -webkit-appearance: slider-vertical;
        appearance: slider-vertical;
        accent-color: #FF8E53;
        width: 6px;
        height: 140px;
        background: transparent;
        border-radius: 10px;
        outline: none;
        cursor: pointer;
        border: none;
        box-shadow: none;
    }

    /* Chrome/Safari - Track */
    .volume-slider::-webkit-slider-runnable-track {
        width: 6px;
        background: linear-gradient(
            to top,
            rgba(255, 107, 53, 0.55) 0%,
            rgba(255, 107, 53, 0.55) var(--volume-percent, 100%),
            rgba(255, 212, 186, 0.9) var(--volume-percent, 100%),
            rgba(255, 212, 186, 0.9) 100%
        );
        border-radius: 10px;
        border: 1px solid rgba(255, 176, 132, 0.4);
        box-shadow:
            inset 0 2px 4px rgba(255, 107, 53, 0.15),
            0 2px 8px rgba(255, 107, 53, 0.1);
    }

    /* Firefox - Track */
    .volume-slider::-moz-range-track {
        width: 6px;
        background: linear-gradient(
            to top,
            rgba(255, 107, 53, 0.55) 0%,
            rgba(255, 107, 53, 0.55) var(--volume-percent, 100%),
            rgba(255, 212, 186, 0.9) var(--volume-percent, 100%),
            rgba(255, 212, 186, 0.9) 100%
        );
        border-radius: 10px;
        border: 1px solid rgba(255, 176, 132, 0.4);
        box-shadow:
            inset 0 2px 4px rgba(255, 107, 53, 0.15),
            0 2px 8px rgba(255, 107, 53, 0.1);
    }

    /* Firefox - Progress */
    .volume-slider::-moz-range-progress {
        background: rgba(255, 107, 53, 0.55);
        border-radius: 10px;
    }

    .volume-slider::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFB084, #FF8E53);
        box-shadow:
            0 4px 12px rgba(255, 126, 75, 0.6),
            0 0 0 3px rgba(255, 255, 255, 0.95),
            0 0 0 5px rgba(255, 126, 75, 0.25),
            inset 0 1px 2px rgba(255, 255, 255, 0.4);
        cursor: grab;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        left: 5px;  /* 👈 THÊM 2 DÒNG NÀY */
    }

    .volume-slider::-webkit-slider-thumb:hover {
        transform: scale(1.15);
        box-shadow:
            0 6px 16px rgba(255, 126, 75, 0.75),
            0 0 0 4px rgba(255, 255, 255, 1),
            0 0 0 7px rgba(255, 126, 75, 0.35),
            inset 0 1px 2px rgba(255, 255, 255, 0.5);
    }

    .volume-slider::-webkit-slider-thumb:active {
        cursor: grabbing;
        transform: scale(1.05);
    }

    .volume-slider::-moz-range-thumb {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFB084, #FF8E53);
        border: 3px solid rgba(255, 255, 255, 0.95);
        box-shadow:
            0 4px 12px rgba(255, 126, 75, 0.6),
            0 0 0 2px rgba(255, 126, 75, 0.25);
        cursor: grab;
    }

    .volume-slider::-moz-range-thumb:active {
        cursor: grabbing;
    }

    .volume-percent {
        font-size: 13px;
        font-weight: 700;
        color: #FF8E53;
        min-width: 45px;
        text-align: center;
        padding: 6px 12px;
        border-radius: 12px;
        background: linear-gradient(
            135deg,
            rgba(255, 176, 132, 0.2),
            rgba(255, 200, 160, 0.15)
        );
        border: 1px solid rgba(255, 176, 132, 0.4);
    }
    
</style>

<div class="music-player-btn" id="musicPlayerBtn" title="🎵 UIA Playlist">
    <div class="music-disc-icon" id="musicBubbleDisc">
        <img src="/disc_covers/c.png" alt="Music" id="musicBubbleIcon">
    </div>
</div>

<div class="music-panel" id="musicPanel">
    <div class="music-panel-header">
        <div class="music-panel-header-left">
            <div class="music-panel-title">🎧 UIA Playlist</div>
        </div>
        <div class="music-panel-header-right">
            <div class="music-tag" id="playlistModeBtn">
                <span id="playlistModeIcon">🎵</span>
                <span id="playlistModeText">auto playlist</span>
                <span style="margin-left: 4px;">▾</span>
            </div>
            <button class="music-volume-btn" id="volumeBtn" title="Điều chỉnh âm lượng">🔊</button>
            <button class="music-close-btn" id="closeMusicPanel" aria-label="Close">×</button>
        </div>
    </div>

    <div class="music-track-list" id="musicTrackList"></div>

    <div class="music-footer">
        <div class="music-footer-main">
            <span class="music-footer-time" id="currentTime">0:00</span>
            <div class="music-footer-title" id="footerTrackTitle">Chưa phát bài nào</div>
            <span class="music-footer-time" id="totalTime">0:00</span>
        </div>
        <input type="range" id="musicSeek" min="0" max="100" value="0">
    </div>
</div>

<!-- DROPDOWN Ở NGOÀI PANEL -->
<div class="playlist-mode-dropdown" id="playlistModeDropdown">
    <div class="mode-option active" data-mode="auto">
        <span class="mode-option-icon">🎵</span>
        <span>Auto Playlist</span>
    </div>
    <div class="mode-option" data-mode="manual">
        <span class="mode-option-icon">🎶</span>
        <span>Tự Chọn</span>
    </div>
    <div class="mode-option" data-mode="random">
        <span class="mode-option-icon">🎼</span>
        <span>Ngẫu Nhiên</span>
    </div>
</div>

<!-- Volume Slider -->
<div class="volume-slider-container" id="volumeSliderContainer">
    <div class="volume-icon">🔊</div>
    <input type="range" class="volume-slider" id="volumeSlider" min="0" max="100" value="100" orient="vertical">
    <div class="volume-percent" id="volumePercent">100%</div>
</div>

<audio id="hiddenMusicAudio"></audio>

<script>
(function() {
    const MUSIC_TRACKS = __MUSIC_TRACKS_PLACEHOLDER__;

    let currentIndex = -1;
    let initialized = false;
    let playlistMode = "auto"; // auto, manual, random

    const musicBtn      = document.getElementById("musicPlayerBtn");
    const musicPanel    = document.getElementById("musicPanel");
    const closeBtn      = document.getElementById("closeMusicPanel");
    const audioEl       = document.getElementById("hiddenMusicAudio");
    const seekEl        = document.getElementById("musicSeek");
    const trackListEl   = document.getElementById("musicTrackList");
    const currentTimeEl = document.getElementById("currentTime");
    const totalTimeEl   = document.getElementById("totalTime");
    const footerTitleEl = document.getElementById("footerTrackTitle");
    const bubbleDiscEl  = document.getElementById("musicBubbleDisc");

    function buildDiscBackground(track) {
        if (track && track.cover) {
            return "url('" + track.cover + "')";
        }
        return "#FFB084";
    }

    function setPlaylistMode(mode) {
        playlistMode = mode;
        const modeBtn = document.getElementById("playlistModeBtn");
        const modeIcon = document.getElementById("playlistModeIcon");
        const modeText = document.getElementById("playlistModeText");
        const dropdown = document.getElementById("playlistModeDropdown");
        
        if (!modeBtn || !modeIcon || !modeText || !dropdown) return;
        
        // Cập nhật UI
        const modeOptions = dropdown.querySelectorAll(".mode-option");
        modeOptions.forEach(function(opt) {
            opt.classList.toggle("active", opt.dataset.mode === mode);
        });
        
        // Cập nhật text và icon
        if (mode === "auto") {
            modeIcon.textContent = "🎵";
            modeText.textContent = "auto playlist";
        } else if (mode === "manual") {
            modeIcon.textContent = "🎶";
            modeText.textContent = "tự chọn";
        } else if (mode === "random") {
            modeIcon.textContent = "🎼";
            modeText.textContent = "ngẫu nhiên";
            
            // TỰ ĐỘNG PHÁT BÀI NGẪU NHIÊN
            if (MUSIC_TRACKS && MUSIC_TRACKS.length > 0) {
                const randomIdx = Math.floor(Math.random() * MUSIC_TRACKS.length);
                playTrack(randomIdx);
            }
        }
        
        dropdown.classList.remove("show");
    }

    function formatTime(sec) {
        if (isNaN(sec)) return "0:00";
        sec = Math.floor(sec);
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return m + ":" + String(s).padStart(2, "0");
    }

    function getDisplayTitle(track) {
        return (track.title || track.id || "Unknown Track");
    }

    function updateBubbleDisc(track, isPlaying) {
        if (!bubbleDiscEl) return;
        const iconImg = document.getElementById("musicBubbleIcon");
        
        bubbleDiscEl.classList.remove("has-cover");
        if (track && track.cover) {
            bubbleDiscEl.style.backgroundImage = buildDiscBackground(track);
            bubbleDiscEl.classList.add("has-cover");
        } else {
            bubbleDiscEl.style.backgroundImage = "";
            bubbleDiscEl.style.backgroundColor = "#FFB084";
        }
        
        // Đổi icon
        if (iconImg) {
            if (isPlaying) {
                iconImg.src = "/disc_covers/c.png";
            } else {
                iconImg.src = "/disc_covers/c.png";
            }
        }
        
        if (isPlaying) {
            bubbleDiscEl.classList.add("playing");
        } else {
            bubbleDiscEl.classList.remove("playing");
        }
    }

    function updateSeekBarGradient() {
        if (!seekEl) return;
        
        // Nếu không có duration hoặc đã pause, reset về 0%
        if (!audioEl.duration || audioEl.paused) {
            seekEl.style.background =
                "linear-gradient(90deg, " +
                "rgba(255, 107, 53, 0.55) 0%, " +
                "rgba(255, 107, 53, 0.55) 0%, " +
                "rgba(255, 212, 186, 0.9) 0%, " +
                "rgba(255, 212, 186, 0.9) 100%)";
            return;
        }
        
        const percent = (audioEl.currentTime / audioEl.duration) * 100;
        seekEl.style.background =
            "linear-gradient(90deg, " +
            "rgba(255, 107, 53, 0.55) 0%, " +
            "rgba(255, 107, 53, 0.55) " + percent + "%, " +
            "rgba(255, 212, 186, 0.9) " + percent + "%, " +
            "rgba(255, 212, 186, 0.9) 100%)";
    }

    function renderTrackList() {
        if (!trackListEl) return;
        trackListEl.innerHTML = "";

        if (!MUSIC_TRACKS || !MUSIC_TRACKS.length) {
            const empty = document.createElement("div");
            empty.className = "track-list-empty";
            empty.innerHTML =
                '<div class="track-list-empty-icon">🎵</div>' +
                '<div class="track-list-empty-text">Không tìm thấy file nhạc trong thư mục /music</div>';
            trackListEl.appendChild(empty);
            updateBubbleDisc(null, false);
            return;
        }

        updateBubbleDisc(MUSIC_TRACKS[0], false);

        MUSIC_TRACKS.forEach(function(track, index) {
            const item = document.createElement("div");
            item.className = "track-item";
            item.dataset.trackIndex = String(index);

            const disc = document.createElement("div");
            disc.className = "track-disc-mini";
            if (track.cover) {
                disc.style.backgroundImage = buildDiscBackground(track);
                disc.classList.add("has-cover");
            } else {
                disc.style.backgroundColor = "#FFB084";
            }

            const meta = document.createElement("div");
            meta.className = "track-meta";

            const title = document.createElement("div");
            title.className = "track-title";
            // Chỉ hiển thị phần trước dấu _
            const displayTitle = getDisplayTitle(track).split('_')[0];
            title.textContent = displayTitle;

            const sub = document.createElement("div");
            sub.className = "track-sub";

            // Nếu KHÔNG PHẢI bài upload → hiển thị format và ID như cũ
            if (!track.isUploaded) {
                const fileName = track.file.split('/').pop();
                const fileBase = fileName.substring(0, fileName.lastIndexOf('.'));
                
                const fmt = document.createElement("span");
                const ext = fileName.split('.').pop().toUpperCase();
                fmt.textContent = ext;

                // Chỉ hiển thị ID nếu có dấu _
                if (fileBase.includes('_')) {
                    const idPart = fileBase.split('_').slice(1).join('_');
                    const idPill = document.createElement("span");
                    idPill.className = "track-sub-pill";
                    idPill.textContent = "#" + idPart;
                    sub.appendChild(idPill);
                }
            }
            // Nếu là bài upload → không hiển thị gì cả (sub rỗng)

            meta.appendChild(title);
            meta.appendChild(sub);

            const playBtn = document.createElement("button");
            playBtn.className = "track-play-btn";
            playBtn.textContent = "▶";

            function onClickRow(e) {
                if (e) e.stopPropagation();
                togglePlayForIndex(index);
            }

            item.addEventListener("click", onClickRow);
            playBtn.addEventListener("click", onClickRow);

            item.appendChild(disc);
            item.appendChild(meta);
            item.appendChild(playBtn);

            trackListEl.appendChild(item);
        });
    }

    function updateActiveUI() {
        if (!trackListEl) return;
        const items = trackListEl.querySelectorAll(".track-item");
        let playingTrack = null;

        items.forEach(function(el, idx) {
            const playBtn = el.querySelector(".track-play-btn");
            const disc = el.querySelector(".track-disc-mini");

            if (idx === currentIndex && audioEl && !audioEl.paused && audioEl.src) {
                el.classList.add("active");
                if (disc) disc.classList.add("playing");
                if (playBtn) {
                    playBtn.classList.add("playing");
                    playBtn.textContent = "⏸";
                }
                playingTrack = MUSIC_TRACKS[idx];
            } else {
                el.classList.remove("active");
                if (disc) disc.classList.remove("playing");
                if (playBtn) {
                    playBtn.classList.remove("playing");
                    playBtn.textContent = "▶";
                }
            }
        });

        updateBubbleDisc(playingTrack, !!playingTrack);
        setFooterTitle(playingTrack);

        // Reset thời gian khi dừng nhạc
        if (!playingTrack) {
            if (currentTimeEl) currentTimeEl.textContent = "0:00";
            if (totalTimeEl) totalTimeEl.textContent = "0:00";
            if (seekEl) {
                seekEl.value = "0";
                updateSeekBarGradient();
            }
        }
    }

    function setFooterTitle(track) {
        if (!footerTitleEl) return;
        if (!track) {
            footerTitleEl.textContent = "Chưa phát bài nào";
        } else {
            footerTitleEl.textContent = getDisplayTitle(track);
        }
    }

    function playTrack(index) {
        if (!audioEl || !MUSIC_TRACKS || !MUSIC_TRACKS[index]) return;

        const track = MUSIC_TRACKS[index];
        currentIndex = index;

        if (!audioEl.src || !audioEl.src.endsWith(track.file)) {
            audioEl.src = track.file;
        }

        audioEl.play().catch(function(err) {
            console.warn("Cannot play music:", err);
        });

        updateActiveUI();
        
        // Scroll tới bài đang phát SAU KHI đã update UI
        scrollToActiveTrack();
    }

    function togglePlayForIndex(index) {
        if (!audioEl) return;
        if (!MUSIC_TRACKS || !MUSIC_TRACKS.length) return;

        if (currentIndex !== index || !audioEl.src) {
            playTrack(index);
            return;
        }

        if (audioEl.paused) {
            audioEl.play().catch(function(err) {
                console.warn(err);
            });
        } else {
            audioEl.pause();
        }
        updateActiveUI();
    }

    function bindEvents() {
        if (!audioEl) return;

        audioEl.addEventListener("timeupdate", function() {
            if (!seekEl) return;
            if (audioEl.duration) {
                const percent = (audioEl.currentTime / audioEl.duration) * 100;
                seekEl.value = String(percent || 0);
                updateSeekBarGradient();
                if (currentTimeEl) currentTimeEl.textContent = formatTime(audioEl.currentTime);
                if (totalTimeEl) totalTimeEl.textContent = formatTime(audioEl.duration);
            }
        });

        audioEl.addEventListener("play", updateActiveUI);
        audioEl.addEventListener("pause", updateActiveUI);
        audioEl.addEventListener("ended", function() {
            updateActiveUI();
            if (MUSIC_TRACKS && MUSIC_TRACKS.length) {
                if (playlistMode === "auto") {
                    // Auto: chạy bài tiếp theo
                    const nextIdx = (currentIndex + 1) % MUSIC_TRACKS.length;
                    playTrack(nextIdx);
                } else if (playlistMode === "random") {
                    // Random: chọn bài ngẫu nhiên
                    let randomIdx;
                    do {
                        randomIdx = Math.floor(Math.random() * MUSIC_TRACKS.length);
                    } while (randomIdx === currentIndex && MUSIC_TRACKS.length > 1);
                    playTrack(randomIdx);
                }
                // Manual: không làm gì, người dùng tự chọn
            }
        });

        if (seekEl) {
            seekEl.addEventListener("input", function() {
                if (!audioEl.duration) return;
                const target = (seekEl.value / 100) * audioEl.duration;
                audioEl.currentTime = target;
                updateSeekBarGradient();
            });
        }
    }

    function scrollToActiveTrack() {
        if (!trackListEl || currentIndex < 0) return;
        
        // Đợi DOM render xong
        setTimeout(function() {
            const items = trackListEl.querySelectorAll('.track-item');
            const activeItem = items[currentIndex];
            
            if (activeItem && trackListEl) {
                // Lấy thông tin
                const containerHeight = trackListEl.clientHeight;
                const itemHeight = activeItem.offsetHeight;
                const gap = 8; // gap giữa các items (từ CSS)
                
                // Tính số items có thể hiển thị trong viewport
                const itemsVisible = Math.floor(containerHeight / (itemHeight + gap));
                
                // Tính index để scroll: muốn active item ở giữa
                // Nếu có 2 items hiển thị được → muốn active ở vị trí thứ 1 (index 0.5)
                const targetIndex = Math.max(0, currentIndex - Math.floor(itemsVisible / 2));
                
                // Scroll tới vị trí của target item
                const targetScroll = targetIndex * (itemHeight + gap);
                
                trackListEl.scrollTo({
                    top: targetScroll,
                    behavior: 'smooth'
                });
            }
        }, 150);
    }

    function initMusicPlayer() {
        if (initialized) return;
        initialized = true;
        renderTrackList();
        bindEvents();
        
        // Tự động phát bài GIAO HƯỞNG TÂN THỜI nếu chưa có bài nào đang chạy
        if (currentIndex === -1 && playlistMode === "auto") {
            let targetIndex = MUSIC_TRACKS.findIndex(function(track) {
                return track.title.includes("GIAO HƯỞNG TÂN THỜI") ||
                    track.file.includes("GIAO HƯỞNG TÂN THỜI");
            });
            
            if (targetIndex === -1) {
                targetIndex = 0;
            }
            
            playTrack(targetIndex);
        }
    }

    function autoPlayOnInit() {
        if (!MUSIC_TRACKS || MUSIC_TRACKS.length === 0) return;
        
        if (playlistMode === "auto") {
            // Auto mode: phát bài đầu tiên
            playTrack(0);
        } else if (playlistMode === "random") {
            // Random mode: phát bài ngẫu nhiên
            const randomIdx = Math.floor(Math.random() * MUSIC_TRACKS.length);
            playTrack(randomIdx);
        }
        // Manual mode: không làm gì
    }

    if (musicBtn && musicPanel) {
        musicBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            const willOpen = !musicPanel.classList.contains("open");
            if (willOpen) {
                initMusicPlayer();
                // Scroll tới bài đang phát khi MỞ LẠI panel
                if (currentIndex !== -1) {
                    scrollToActiveTrack();
                }
            }
            musicPanel.classList.toggle("open", willOpen);
            musicBtn.classList.toggle("active", willOpen);
        });
    }

    if (closeBtn && musicPanel && musicBtn) {
        closeBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            musicPanel.classList.remove("open");
            musicBtn.classList.remove("active");
        });
    }

    document.addEventListener("click", function(e) {
        if (!musicPanel || !musicBtn) return;
        
        // Kiểm tra xem có click vào volume slider không
        const volumeSliderContainer = document.getElementById("volumeSliderContainer");
        const volumeBtn = document.getElementById("volumeBtn");
        
        const clickedVolume = volumeSliderContainer && volumeSliderContainer.contains(e.target);
        const clickedVolumeBtn = volumeBtn && volumeBtn.contains(e.target);
        
        if (!musicPanel.contains(e.target) && 
            !musicBtn.contains(e.target) && 
            !clickedVolume && 
            !clickedVolumeBtn) {
            musicPanel.classList.remove("open");
            musicBtn.classList.remove("active");
        }
    });

    // Playlist mode dropdown
    const playlistModeBtn = document.getElementById("playlistModeBtn");
    const playlistModeDropdown = document.getElementById("playlistModeDropdown");
    
    if (playlistModeBtn && playlistModeDropdown) {
        playlistModeBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            
            // Tính vị trí của button
            const rect = playlistModeBtn.getBoundingClientRect();
            
            // Đặt dropdown ngay dưới button, căn giữa
            playlistModeDropdown.style.top = (rect.bottom + 8) + 'px';
            playlistModeDropdown.style.left = (rect.left + rect.width / 2 - 90) + 'px'; // 90 = 180/2 (min-width/2)
            
            playlistModeDropdown.classList.toggle("show");
        });
        
        const modeOptions = playlistModeDropdown.querySelectorAll(".mode-option");
        modeOptions.forEach(function(option) {
            option.addEventListener("click", function(e) {
                e.stopPropagation();
                const mode = this.dataset.mode;
                setPlaylistMode(mode);
            });
        });
    }
    
    // Đóng dropdown khi click bên ngoài
    document.addEventListener("click", function(e) {
        if (playlistModeDropdown && !playlistModeBtn.contains(e.target)) {
            playlistModeDropdown.classList.remove("show");
        }
    });

    // Volume Control Feature
    const volumeBtn = document.getElementById("volumeBtn");
    const volumeSliderContainer = document.getElementById("volumeSliderContainer");
    const volumeSlider = document.getElementById("volumeSlider");
    const volumePercent = document.getElementById("volumePercent");

    // Mở volume slider
    if (volumeBtn && volumeSliderContainer) {
        volumeBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            
            // Tính vị trí của button
            const rect = volumeBtn.getBoundingClientRect();
            
            // Đặt slider bên phải button
            volumeSliderContainer.style.top = (rect.top + rect.height / 2 - 90) + 'px';
            volumeSliderContainer.style.left = (rect.right + 12) + 'px';
            
            volumeSliderContainer.classList.toggle("show");
        });
    }

    // Đóng volume slider khi click bên ngoài
    document.addEventListener("click", function(e) {
        if (volumeSliderContainer && volumeBtn && 
            !volumeSliderContainer.contains(e.target) && 
            !volumeBtn.contains(e.target)) {
            volumeSliderContainer.classList.remove("show");
        }
    });

    // Xử lý thay đổi âm lượng
    if (volumeSlider && audioEl) {
        volumeSlider.addEventListener("input", function() {
            const volume = volumeSlider.value / 100;
            audioEl.volume = volume;
            
            // Cập nhật hiển thị %
            if (volumePercent) {
                volumePercent.textContent = volumeSlider.value + "%";
            }
            
            // Cập nhật gradient
            volumeSlider.style.setProperty('--volume-percent', volumeSlider.value + '%');
            
            // Cập nhật icon loa TRONG SLIDER
            const volumeIcon = document.querySelector(".volume-icon");
            if (volumeIcon) {
                if (volume === 0) {
                    volumeIcon.textContent = "🔇";
                } else if (volume < 0.5) {
                    volumeIcon.textContent = "🔉";
                } else {
                    volumeIcon.textContent = "🔊";
                }
            }
        });
        
        // Set volume mặc định
        audioEl.volume = 1;
    }

})();
</script>
"""
    return base_html.replace("__MUSIC_TRACKS_PLACEHOLDER__", tracks_json)