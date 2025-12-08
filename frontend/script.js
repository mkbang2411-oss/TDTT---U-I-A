// =========================
// 🗺️ CẤU HÌNH MAP
// =========================
const vietnamBounds = [
  [8.179066, 102.14441],   // SW
  [23.393395, 109.46972]   // NE
];

const map = L.map("map",{
  zoomControl: false,  // ← THÊM DÒNG NÀY để tắt nút +/-
  maxBounds: vietnamBounds,
  maxBoundsViscosity: 1.0
}).setView([10.76298, 106.68246], 18);

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
  minZoom: 6.5,
  maxZoom: 19,
  attribution: '&copy; CARTO',
  className: 'map-pastel'
}).addTo(map);

// Cho file khác (mini_game.js) dùng được
window.map = map;
// Map place_id -> marker
window.placeMarkersById = {};

let markers = [];

window.markerClusterGroup = L.markerClusterGroup({
    iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        let size = 'small';
        let colorClass = 'cluster-small';
        
        if (count > 100) {
            size = 'large';
            colorClass = 'cluster-large';
        } else if (count > 50) {
            size = 'medium';
            colorClass = 'cluster-medium';
        }
        
        return L.divIcon({
            html: `<div class="cluster-inner ${colorClass}"><span>${count}</span></div>`,
            className: `marker-cluster marker-cluster-${size}`,
            iconSize: L.point(50, 50)
        });
    },
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    maxClusterRadius: 80,
    disableClusteringAtZoom: 16,
    animate: false,
    animateAddingMarkers: false,
    spiderfyDistanceMultiplier: 1.5
});

const markerClusterGroup = window.markerClusterGroup; // alias


let allPlacesData = [];
let visibleMarkers = new Set();
let isLoadingMarkers = false;
let currentRouteLine = null;
let routeControl = null;



// 👉 Biến trạng thái cho nút "Quán yêu thích"
let isFavoriteMode = false;
let lastSearchParams = {
  query: "",
  flavors: [],
  budget: "",
  radius: ""
};
// ==========================================================
// 🔔 CUSTOM ALERT - THÊM ĐOẠN NÀY VÀO SAU PHẦN KHAI BÁO BIẾN
// ==========================================================
function showCustomAlert(message, type = 'info') {
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.3s ease;
  `;

  const popup = document.createElement('div');
  popup.style.cssText = `
    background: #fff5f0;
    border-radius: 20px;
    padding: 30px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    animation: slideDown 0.3s ease;
    position: relative;
  `;

  let icon = '🔔';
  let iconColor = '#ff9966';
  if (type === 'success') {
    icon = '✅';
    iconColor = '#4caf50';
  } else if (type === 'error') {
    icon = '❌';
    iconColor = '#f44336';
  } else if (type === 'warning') {
    icon = '⚠️';
    iconColor = '#ff9800';
  }

  popup.innerHTML = `
    <div style="display: flex; align-items: start; gap: 15px;">
      <div style="font-size: 32px;">${icon}</div>
      <div style="flex: 1;">
        <h3 style="margin: 0 0 10px 0; color: ${iconColor}; font-size: 20px; font-weight: 600;">Thông báo</h3>
        <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.6;">${message}</p>
      </div>
      <button id="closeAlertBtn" style="background: none; border: none; font-size: 24px; color: #999; cursor: pointer; padding: 0; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: all 0.2s;">×</button>
    </div>
    <button id="okAlertBtn" style="margin-top: 20px; width: 100%; padding: 12px; background: linear-gradient(135deg, ${iconColor} 0%, ${iconColor}dd 100%); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s;">OK</button>
  `;

  overlay.appendChild(popup);
  document.body.appendChild(overlay);

  const closeBtn = popup.querySelector('#closeAlertBtn');
  closeBtn.addEventListener('mouseenter', () => { closeBtn.style.background = '#f0f0f0'; });
  closeBtn.addEventListener('mouseleave', () => { closeBtn.style.background = 'none'; });

  const okBtn = popup.querySelector('#okAlertBtn');
  okBtn.addEventListener('mouseenter', () => { okBtn.style.transform = 'scale(1.02)'; });
  okBtn.addEventListener('mouseleave', () => { okBtn.style.transform = 'scale(1)'; });

  const closePopup = () => {
    overlay.style.animation = 'fadeOut 0.3s ease';
    popup.style.animation = 'slideUp 0.3s ease';
    setTimeout(() => overlay.remove(), 300);
  };

  closeBtn.addEventListener('click', closePopup);
  okBtn.addEventListener('click', closePopup);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closePopup(); });
}

if (!document.getElementById('custom-alert-style')) {
  const style = document.createElement('style');
  style.id = 'custom-alert-style';
  style.textContent = `
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
    @keyframes slideDown { from { transform: translateY(-50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    @keyframes slideUp { from { transform: translateY(0); opacity: 1; } to { transform: translateY(-50px); opacity: 0; } }
  `;
  document.head.appendChild(style);
}
// =========================
// 🍴 ICON TƯƠNG ỨNG LOẠI QUÁN
// =========================
const icons = {
  default: L.icon({
    iconUrl: "https://res.cloudinary.com/dbmq2hme4/image/upload/icons/icon.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  michelin: L.icon({
    iconUrl: "https://res.cloudinary.com/dbmq2hme4/image/upload/icons/star.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  })
};

// =========================
// 🧠 XÁC ĐỊNH LOẠI QUÁN
// =========================
function detectCategory(name = "") {
  // Tất cả quán đều dùng icon mặc định
  return "default";
}

// =========================
// 💬 HIỂN THỊ REVIEW GIỐNG GOOGLE MAPS
// =========================
function timeAgo(dateString) {
  if (!dateString) return "";

  // Nếu là chuỗi kiểu "2 weeks ago" của Google thì giữ nguyên
  if (isNaN(Date.parse(dateString)) && isNaN(Number(dateString))) {
    return dateString;
  }

  const now = new Date();
  const past = new Date(dateString);
  if (isNaN(past)) return "";

  // ⚙️ Sửa lỗi lệch múi giờ (UTC → local)
  const localPast = new Date(past.getTime() + past.getTimezoneOffset() * 60000);
  const diff = Math.floor((now - localPast) / 1000);

  const minutes = Math.floor(diff / 60);
  const hours = Math.floor(diff / 3600);
  const days = Math.floor(diff / 86400);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);

  if (diff < 60) return "vừa xong";
  if (minutes < 60) return `${minutes} phút trước`;
  if (hours < 24) return `${hours} giờ trước`;
  if (days < 30) return `${days} ngày trước`;
  if (months < 12) return `${months} tháng trước`;
  return `${years} năm trước`;
}

// 🕓 Format thời gian từ "2025-11-05T10:20:30.137452" → "5/11/2025 12:15 PM"
function formatDate(dateString) {
  if (!dateString) return "";

  const date = new Date(dateString);
  if (isNaN(date)) return dateString; // nếu không parse được, giữ nguyên

  const day = date.getDate();
  const month = date.getMonth() + 1;
  const year = date.getFullYear();

  let hours = date.getHours();
  const minutes = date.getMinutes().toString().padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12 || 12;

  return `${day}/${month}/${year} ${hours}:${minutes} ${ampm}`;
}

// =========================
// 🍪 LẤY CSRF COOKIE CỦA DJANGO
// =========================
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Kiểm tra xem cookie có bắt đầu bằng tên chúng ta muốn không
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function renderReviewSummary(googleReviews, userReviews) {
  const allReviews = [...userReviews, ...googleReviews];
  const avgRating =
    allReviews.length > 0
      ? (
          allReviews.reduce((sum, r) => sum + (r.rating || 0), 0) /
          allReviews.length
        ).toFixed(1)
      : "Chưa có";

  const starCount = [5, 4, 3, 2, 1].map(
    (s) => allReviews.filter((r) => r.rating === s).length
  );

  const maxCount = Math.max(...starCount, 1);

  return `
    <div class="review-summary">
      <div class="review-average">
        <div class="review-score">${avgRating}</div>
        <div class="review-stars">${"⭐".repeat(
          Math.round(avgRating) || 0
        )}</div>
        <div class="review-total">${allReviews.length} đánh giá</div>
      </div>

      <div class="review-bars">
        ${[5, 4, 3, 2, 1]
          .map(
            (s, i) => `
          <div class="bar-row">
            <span>${s}⭐</span>
              <div class="bar">
                <div class="fill" style="width:${
                  (starCount[i] / maxCount) * 100
                }%">
                </div>
              </div>
            <span>${starCount[i]}</span>
          </div>
        `
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderReviewList(googleReviews, userReviews) {
  const allReviews = [...userReviews, ...googleReviews]; // User reviews lên trước

  return `
    <div class="review-list">
      <div class="review-list">
      ${
        allReviews.length === 0
          ? "<p>Chưa có đánh giá nào.</p>"
          : allReviews
              .map(
                (r) => `
        <div class="review-card">
          <div class="review-header">
            <img src="${
              r.avatar || // Avatar đã lưu trong file JSON (ưu tiên 1)
              "https://cdn-icons-png.flaticon.com/512/847/847969.png" // Avatar mặc định (ưu tiên 2)
            }" class="review-avatar">
            <div>
              <div class="review-author">${r.user || r.ten || "Ẩn danh"}</div>
              <div class="review-stars">${"⭐".repeat(r.rating || 0)}</div>
              <div class="review-time">${
                formatDate(r.date) || timeAgo(r.relative_time_description)
              }</div>
            </div>
          </div>
          <div class="review-text">${r.comment || ""}</div>
        </div>`
              )
              .join("")
      }
    </div>
  `;
}

function formatVietnamTime(h, m) {
  if (h === 0 && m === 0) return "12:00 khuya";
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function convertToMinutes(h, m) {
  // ✅ Nếu 0:00 → tính là 24:00 (cuối ngày), không phải đầu ngày
  if (h === 0 && m === 0) return 24 * 60;
  return h * 60 + m;
}

function getRealtimeStatus(hoursStr) {
  if (!hoursStr) return "Không rõ";

  hoursStr = hoursStr.toLowerCase().trim();
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  // ✅ 24h
  if (hoursStr.includes("mở cả ngày")) {
    return "✅ Đang mở cửa (24h)";
  }

  // ✅ "Đang mở cửa ⋅ Đóng cửa lúc XX:XX"
  if (hoursStr.includes("đang mở cửa")) {
    const match = hoursStr.match(/đóng cửa lúc\s*(\d{1,2}):(\d{2})/);
    if (match) {
      const h = parseInt(match[1]);
      const m = parseInt(match[2]);
      const closeMinutes = convertToMinutes(h, m);
      const closeFormatted = formatVietnamTime(h, m);

      if (currentMinutes < closeMinutes) {
        return `✅ Đang mở cửa (Đóng lúc ${closeFormatted})`;
      } else {
        return `❌ Đã đóng cửa (Đóng lúc ${closeFormatted})`;
      }
    }
  }

  // ✅ "Đóng cửa ⋅ Mở cửa lúc XX:XX"
  if (hoursStr.includes("đóng cửa")) {
    const match = hoursStr.match(/mở cửa lúc\s*(\d{1,2}):(\d{2})/);
    if (match) {
      const h = parseInt(match[1]);
      const m = parseInt(match[2]);
      const openMinutes = convertToMinutes(h, m);
      const openFormatted = formatVietnamTime(h, m);

      if (currentMinutes >= openMinutes) {
        return `✅ Đang mở cửa (Mở lúc ${openFormatted})`;
      } else {
        return `❌ Đã đóng cửa (Mở lúc ${openFormatted})`;
      }
    }
  }

  return hoursStr;
}

// =========================
// 🤖 HÀM MỞ CHATBOX TỰ ĐỘNG
// =========================
function openChatboxAutomatically() {
  console.log("🚨 Mở chatbox tự động sau 3 lần search thất bại");

  // 🔍 LẤY TEXT TỪ Ô SEARCH QUÁN
  const searchInput = document.getElementById("query");
  const searchText = searchInput ? searchInput.value.trim() : "";
  
  console.log("📝 Text user đã search:", searchText);

  // Tìm các elements của chatbox
  const chatWindow = document.getElementById("chatWindow");
  const chatbotBtn = document.getElementById("chatbotBtn");
  const speechBubble = document.getElementById("speechBubble");

  if (!chatWindow || !chatbotBtn) {
    console.error("❌ Không tìm thấy chatbox elements!");
    alert("🤖 Bạn có thể thử hỏi chatbot UIAboss để tìm món ăn phù hợp hơn nhé!");
    return;
  }

  // ✅ Mở chatbox
  chatWindow.style.display = "flex";
  chatWindow.classList.add("open");
  chatbotBtn.style.display = "none";
  chatbotBtn.classList.add("hidden");
  speechBubble.style.display = "none";
  speechBubble.classList.add("hidden");

  // ✅ XỬ LÝ TỰ ĐỘNG GỬI TEXT CHO GEMINI
  setTimeout(() => {
    const messagesArea = document.getElementById("messagesArea");
    
    if (!messagesArea) return;

    // 🔥 NẾU CÓ TEXT SEARCH → GỬI TRỰC TIẾP CHO GEMINI
    if (searchText && searchText.length > 0) {
      console.log("🤖 Gửi text cho Gemini xử lý:", searchText);
      
      // ✅ Tạo message đặc biệt với prefix [SEARCH_CORRECTION]
      const correctionMessage = `[SEARCH_CORRECTION] ${searchText}`;
      
      // ✅ Hiển thị typing indicator
      showTyping();
      
      // ✅ GỌI GEMINI API TRỰC TIẾP (KHÔNG HIỂN thị tin nhắn user)
      callGeminiAPI(correctionMessage);
      
    } else {
      // 🔥 KHÔNG CÓ TEXT → HIỂN THỊ TIN NHẮN MẶC ĐỊNH
      const autoMessage = `
        <div class="message bot">
          <div class="message-avatar">🍜</div>
          <div class="message-content">
            <div class="message-text">
              <p>Ối! Có vẻ bạn đang gặp khó khăn tìm quán nè 😅</p>
              <p>Để mình giúp bạn nhé! Bạn muốn ăn gì, ở khu vực nào, ngân sách bao nhiêu? Cứ nói mình nghe nha~ 💕</p>
            </div>
            <div class="message-time">${new Date().toLocaleTimeString("vi-VN", {
              hour: "2-digit",
              minute: "2-digit",
            })}</div>
          </div>
        </div>
      `;
      messagesArea.innerHTML += autoMessage;
      messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    // Focus vào input
    const messageInput = document.getElementById("messageInput");
    if (messageInput) {
      messageInput.focus();
    }
  }, 500);
}

// =========================
// 🔍 HIỂN THỊ MARKER + THÔNG TIN CHI TIẾT
// =========================
function displayPlaces(places, shouldZoom = true) {
 console.log('🎯 displayPlaces được gọi với', places ? places.length : 0, 'quán');
  console.log('📊 shouldZoom:', shouldZoom);
  console.log('📊 isFavoriteMode:', isFavoriteMode);
  
  
  allPlacesData = places || [];
  visibleMarkers.clear();

  if (!places || places.length === 0) {
    alert("Không tìm thấy quán nào!");
    return false;
  }
// 👉 THÊM DÒNG NÀY
  const isSinglePlaceMode = !isFavoriteMode && places.length === 1;

  // 🔥🔥🔥 THÊM ĐOẠN NÀY 🔥🔥🔥
  // ✅ XÓA SẠCH TẤT CẢ MARKER CŨ TRƯỚC KHI VẼ MỚI
  
  // 1️⃣ Xóa cluster LOCAL
  if (typeof markerClusterGroup !== 'undefined' && markerClusterGroup) {
    if (map.hasLayer(markerClusterGroup)) {
      map.removeLayer(markerClusterGroup);
      console.log('🧹 [displayPlaces] Removed LOCAL cluster');
    }
    markerClusterGroup.clearLayers(); // ⬅️ THÊM DÒNG NÀY
  }
  
  // 2️⃣ Xóa cluster GLOBAL
  if (window.markerClusterGroup) {
    if (map.hasLayer(window.markerClusterGroup)) {
      map.removeLayer(window.markerClusterGroup);
      console.log('🧹 [displayPlaces] Removed GLOBAL cluster');
    }
    window.markerClusterGroup.clearLayers(); // ⬅️ THÊM DÒNG NÀY
  }

  // 3️⃣ Reset các biến toàn cục
  markers = []; // ⬅️ THÊM DÒNG NÀY
  window.placeMarkersById = {}; // ⬅️ THÊM DÒNG NÀY
  visibleMarkers.clear(); // ⬅️ ĐÃ CÓ NHƯNG ĐẢM BẢO NÓ Ở ĐÂY
  
  // 🔥🔥🔥 HẾT ĐOẠN THÊM 🔥🔥🔥

  // 👉 Gắn cluster vào map trước (code cũ của bạn tiếp tục)
    // 👉 Gắn cluster vào map nếu KHÔNG phải 1-quán-mode
  if (!isSinglePlaceMode) {
    map.addLayer(markerClusterGroup);
  }


// ✅ TẮT lazy load cũ

map.off("moveend", loadMarkersInViewport);
console.log('⚠️ [displayPlaces] Removed old lazy load listener');

// 🔥 NẾU LÀ FAVORITE MODE: LOAD TẤT CẢ MARKERS NGAY
  // 🔥 NẾU LÀ FAVORITE MODE HOẶC KẾT QUẢ ÍT → LOAD TẤT CẢ MARKERS NGAY
  clearAllMarkers(); // ⬅️ XÓA SẠCH TẤT CẢ MARKER CŨ

  // 👇 THÊM DÒNG NÀY: search ít quán thì vẽ luôn, không lazy-load
    const shouldLoadAllNow = isFavoriteMode || places.length <= 200;

  if (shouldLoadAllNow) {
    console.log('🔥 [displayPlaces] Loading ALL markers immediately...', {
      favoriteMode: isFavoriteMode,
      total: places.length,
      singleMode: isSinglePlaceMode,
    });

    places.forEach((p) => {
      const lat = parseFloat(p.lat?.toString().replace(",", "."));
      const lon = parseFloat(p.lon?.toString().replace(",", "."));
      
      if (isNaN(lat) || isNaN(lon)) return;
      
      const placeId = p.data_id || p.ten_quan;
      
      // Tạo marker
      const marker = createMarker(p, lat, lon);
      markers.push(marker);
      visibleMarkers.add(placeId);

      if (isSinglePlaceMode) {
        // ✅ CASE CHỈ 1 QUÁN: add thẳng vào map, không dùng cluster
        marker.addTo(map);
        console.log('✅ [displayPlaces] Single-place mode: marker add trực tiếp vào map');
      } else {
        // ✅ Nhiều quán: dùng cluster như cũ
        markerClusterGroup.addLayer(marker);
      }
    });



    console.log(`✅ [displayPlaces] Loaded ${markers.length} markers (immediate mode)`);

    // ❗ QUAN TRỌNG: KHÔNG BẬT LẠI lazy load trong mode này
    // (Không cần map.on("moveend", loadMarkersInViewport);)

  } else {
    // CHẾ ĐỘ BÌNH THƯỜNG: Bật lại lazy load
    map.on("moveend", loadMarkersInViewport);
    console.log('✅ [displayPlaces] Re-enabled lazy load (normal mode)');
  }


  if (shouldZoom && places.length > 0) {
 
    // 🔍 Tính bounds theo TOÀN BỘ các quán đã lọc
    const bounds = L.latLngBounds([]);

    places.forEach((p) => {
      const lat = parseFloat(p.lat?.toString().replace(",", "."));
      const lon = parseFloat(p.lon?.toString().replace(",", "."));
      if (!isNaN(lat) && !isNaN(lon)) {
        bounds.extend([lat, lon]);
      }
    });

    if (bounds.isValid()) {
      // 🔥 FIX: Nếu chỉ có 1 quán, load marker ngay không cần chờ moveend
      if (places.length === 1) {
  const p = places[0];
  const lat = parseFloat(p.lat?.toString().replace(",", "."));
  const lon = parseFloat(p.lon?.toString().replace(",", "."));
  
  if (!isNaN(lat) && !isNaN(lon)) {
    console.log('🔥 [1 QUÁN] Bắt đầu xử lý marker duy nhất...');
    
    // ✅ QUAN TRỌNG: Đảm bảo cluster đã được add vào map
    if (!map.hasLayer(markerClusterGroup)) {
      console.warn('⚠️ Cluster chưa có trên map, thêm lại...');
      map.addLayer(markerClusterGroup);
    }
    
    // Zoom trước
    map.setView([lat, lon], 17, { animate: true });
    
    // Load marker sau khi zoom xong
    setTimeout(() => {
      const placeId = p.data_id || p.ten_quan;
      
      if (!visibleMarkers.has(placeId)) {
        console.log('🏗️ [1 QUÁN] Tạo marker mới...');
        
        const marker = createMarker(p, lat, lon);
        markers.push(marker);
        markerClusterGroup.addLayer(marker);
        visibleMarkers.add(placeId);
        
        // 🔥 ĐẢM BẢO CLUSTER REFRESH
        markerClusterGroup.refreshClusters();
        
        console.log('✅ [1 QUÁN] Marker đã được tạo và thêm vào cluster');
        console.log('✅ [1 QUÁN] Tổng markers:', markers.length);
        console.log('✅ [1 QUÁN] Cluster có layer không?', markerClusterGroup.hasLayer(marker));
        
        // Click vào marker để mở sidebar
        setTimeout(() => {
          console.log('🔥 [1 QUÁN] Click vào marker');
          marker.fire('click');
        }, 300);
      } else {
        console.warn('⚠️ [1 QUÁN] Marker đã tồn tại, không tạo mới');
      }
    }, 500); // Tăng timeout lên 500ms để chắc chắn zoom xong
  }
} else {
        // Nhiều quán → fit bounds bình thường, moveend sẽ trigger lazy load
        map.fitBounds(bounds.pad(0.2));
      }
    } else {
      // fallback nếu dữ liệu không có lat/lon
      loadMarkersInViewport();
    }
 } else {
    // 🔥 QUAN TRỌNG: Dù không zoom, vẫn phải load marker + BẬT lazy load
    console.log('⚠️ Không zoom nhưng vẫn cần load marker');
    loadMarkersInViewport();
  }
  
  // 🔥 BẬT LẠI LAZY LOAD CHO MỌI TRƯỜNG HỢP (TRỪ FAVORITE MODE)
  if (!shouldLoadAllNow) {
    console.log('✅ Bật lại lazy load sau khi display xong');
    map.off("moveend", loadMarkersInViewport); // Tắt cái cũ trước
    map.on("moveend", loadMarkersInViewport);  // Bật lại
  }

  window.allMarkers = markers;
  return true;
}

// =========================
// 🚀 HÀM LAZY LOADING
// =========================
function loadMarkersInViewport() {
  // ✅ THÊM CHECK NÀY
  if (isFavoriteMode) {
    console.log('🚫 Lazy load bị chặn vì đang ở favorite mode');
    return;
  }
  
  if (isLoadingMarkers) return;
  isLoadingMarkers = true;

  const bounds = map.getBounds();
  const zoom = map.getZoom();
  
  let maxMarkersToLoad = zoom > 14 ? 200 : zoom > 12 ? 100 : 50;
  let loadedCount = 0;

  const markersToAdd = [];

  allPlacesData.forEach((p) => {
    const placeId = p.data_id || p.ten_quan;
    if (visibleMarkers.has(placeId)) return;
    if (loadedCount >= maxMarkersToLoad) return;

    const lat = parseFloat(p.lat);
    const lon = parseFloat(p.lon);
    if (isNaN(lat) || isNaN(lon)) return;

    if (!bounds.contains([lat, lon])) return;

    const marker = createMarker(p, lat, lon);
    markers.push(marker);
    markersToAdd.push(marker);
    visibleMarkers.add(placeId);
    loadedCount++;
  });

  markerClusterGroup.addLayers(markersToAdd);
  
  isLoadingMarkers = false;
  console.log(`✅ Đã load ${loadedCount} markers`);
}


// =========================
function createMarker(p, lat, lon) {
  // 🎯 Chọn icon phù hợp
let icon;

if (p.mo_ta && p.mo_ta.toLowerCase().includes("michelin")) {
  icon = icons.michelin;  // ⭐ Chỉ quán Michelin dùng icon sao
} else {
  icon = icons.default;   // 🍽️ Tất cả quán khác dùng icon chung
}

  // 🎯 Tạo marker (KHÔNG dùng .addTo(map) nữa)
  const marker = L.marker([lat, lon], { 
    icon,
    placeData: p // ✅ Lưu thông tin quán vào marker
  });
// Lưu marker theo id để có thể focus từ mini_game.js
const placeId = p.data_id || p.ten_quan;
if (placeId) {
  if (!window.placeMarkersById) window.placeMarkersById = {};
  window.placeMarkersById[placeId] = marker;
}

  // ⭐ Thêm hiệu ứng glow cho Michelin
  if (p.mo_ta && p.mo_ta.toLowerCase().includes("michelin")) {
    setTimeout(() => {
      if (marker._icon) {
        marker._icon.classList.add("michelin-glow");
      }
    }, 100);
  }

  // 🟢 TOOLTIP khi rê chuột vào marker
  const tooltipHTML = `
    <div style="text-align:center;min-width:180px;">
      <strong>${p.ten_quan || "Không tên"}</strong><br>
      ${p.hinh_anh 
        ? `<img src="${p.hinh_anh}" style="width:100px;height:70px;object-fit:cover;border-radius:6px;margin-top:4px;">` 
        : ""}
      <div style="font-size:13px;margin-top:4px;">
        <i class="fa-regular fa-clock"></i> ${p.gio_mo_cua || "Không rõ"}<br>
        <i class="fa-solid fa-coins"></i> ${p.gia_trung_binh || "Không có"}
      </div>
    </div>
  `;

  marker.bindTooltip(tooltipHTML, {
    direction: "top",
    offset: [0, -10],
    opacity: 0.95,
    sticky: true,
    className: "custom-tooltip"
  });

  // 🎯 SỰ KIỆN CLICK VÀO MARKER
  marker.on("click", async () => {
    const place_id = p.data_id || p.ten_quan;
    map.setView([lat, lon], 17, { animate: true });
    const sidebar = document.getElementById("sidebar");
    const sidebarContent = document.getElementById("sidebar-content");

    sidebar.dataset.placeId = place_id;

    let googleReviews = [];
    let userReviews = [];
    let currentUser = null;
    let isFavorite = false;

    // 📡 Tải reviews từ API
    try {
      const res = await fetch(`/api/reviews/${place_id}`, {
        credentials: "include",
      });

      if (res.ok) {
        const responseData = await res.json();
        const reviewData = responseData.reviews;
        currentUser = responseData.user;
        isFavorite = responseData.is_favorite;
        googleReviews = reviewData.google || [];
        userReviews = reviewData.user || [];
      }
    } catch (err) {
      console.error("❌ Lỗi khi tải review:", err);
    }

    // 📝 TAB TỔNG QUAN
    const tongquanHTML = `
      <div class="place-header" style="display:flex;align-items:center;justify-content:space-between;">
        <h2 style="margin:0;">${p.ten_quan || "Không tên"}</h2>
        <!-- ❤️ Nút yêu thích -->
        <button id="favoriteBtn" class="action-btn" style="padding:8px 10px;min-width:auto;border:none;background:none;">
          <i class="fa-regular fa-heart" style="font-size:22px;"></i>
        </button>
      </div>

      ${p.hinh_anh 
        ? `<img src="${p.hinh_anh}" style="width:100%;border-radius:10px;margin:10px 0;">` 
        : ""}

      ${p.mo_ta && p.mo_ta.toLowerCase().includes("khu ẩm thực")
        ? `<p style="color:#ff6600;font-weight:bold;">🔥 Đây là khu ẩm thực sầm uất, có nhiều món ăn và hoạt động về đêm.</p>`
        : ""}

      <p><i class="fa-solid fa-location-dot"></i> ${p.dia_chi || "Không rõ"}</p>
      <p><i class="fa-solid fa-phone"></i> ${p.so_dien_thoai || "Không có"}</p>
      <p><i class="fa-solid fa-star"></i> ${p.rating || "Chưa có"}</p>
      <p><i class="fa-regular fa-clock"></i> ${p.gio_mo_cua || "Không rõ"}</p>
      <p><i class="fa-solid fa-coins"></i> ${p.gia_trung_binh || "Không có"}</p>
      <p><i class="fa-solid fa-utensils"></i> ${p.khau_vi || "Không xác định"}</p>

      <!-- 🔖 Nút lưu quán (ẩn) -->
      <div style="margin-top:10px;display:flex;justify-content:center;">
        <button id="saveBtn" class="action-btn" style="display:none;">
          <i class="fa-regular fa-bookmark"></i>
          <span>Lưu quán</span>
        </button>
      </div>
    `;

    // 📝 TAB THỰC ĐƠN
    const thucdonHTML = `
      ${p.thuc_don
        ? p.thuc_don.split(/[;,]+/).map(img => 
            `<img src="${img.trim()}" class="menu-img" alt="Thực đơn">`
          ).join("")
        : "<p>Không có hình thực đơn.</p>"}
    `;

    // 📝 TAB ĐÁNH GIÁ - Form nhập review
    let reviewFormHTML = "";
    if (currentUser && currentUser.is_logged_in) {
      reviewFormHTML = `
        <div class="review-form logged-in">
          <h3 class="form-title">📝 Thêm đánh giá của bạn</h3>
          <div class="form-header">
            <img src="${currentUser.avatar}" class="user-avatar-form" alt="Avatar">
            <span class="user-name">${currentUser.username}</span>
          </div>
          <div class="star-rating" id="starRating">
            <span class="star" data-value="1">★</span>
            <span class="star" data-value="2">★</span>
            <span class="star" data-value="3">★</span>
            <span class="star" data-value="4">★</span>
            <span class="star" data-value="5">★</span>
          </div>
          <textarea id="reviewComment" placeholder="Cảm nhận của bạn..."></textarea>
          <button id="submitReview">Gửi đánh giá</button>
        </div>
      `;
    } else {
      reviewFormHTML = `
        <div class="review-form">
          <h3>📝 Thêm đánh giá của bạn</h3>
          <p>Vui lòng <a href="/accounts/login/" target="_blank">đăng nhập</a> để gửi đánh giá.</p>
        </div>
      `;
    }

    const danhgiaHTML = `
      <div class="review-section">
        ${renderReviewSummary(googleReviews, userReviews)} 
        ${reviewFormHTML}
        ${renderReviewList(googleReviews, userReviews)}
      </div>
    `;

    // 📝 NỘI DUNG SIDEBAR HOÀN CHỈNH
    const contentHTML = `
      <div class="tab-bar">
        <button class="tab-btn active" data-tab="tongquan">Tổng quan</button>
        <button class="tab-btn" data-tab="thucdon">Thực đơn</button>
        <button class="tab-btn" data-tab="danhgia">Đánh giá</button>
      </div>

      <div id="tab-tongquan" class="tab-content active">${tongquanHTML}</div>
      <div id="tab-thucdon" class="tab-content">${thucdonHTML}</div>
      <div id="tab-danhgia" class="tab-content">${danhgiaHTML}</div>
    `;

    sidebarContent.innerHTML = contentHTML;
    sidebar.classList.add("show");
    document.getElementById('sidebar-title').textContent = "Thông tin chi tiết";

    // ❤️ XỬ LÝ NÚT YÊU THÍCH
    const favoriteBtn = document.getElementById("favoriteBtn");
    if (isFavorite) {
      favoriteBtn.classList.add("active");
      const icon = favoriteBtn.querySelector("i");
      icon.classList.replace("fa-regular", "fa-solid");
      icon.style.color = "red";
    }

    favoriteBtn.addEventListener("click", async () => {
      try {
        const response = await fetch(`/api/favorite/${place_id}/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "include",
        });

        if (response.status === 403 || response.status === 401) {
          alert("Vui lòng đăng nhập để lưu quán!");
          window.location.href = "/accounts/login/";
          return;
        }

        const data = await response.json();

        if (data.status === "added") {
          favoriteBtn.classList.add("active");
          favoriteBtn.querySelector("i").classList.remove("fa-regular");
          favoriteBtn.querySelector("i").classList.add("fa-solid");
          favoriteBtn.querySelector("i").style.color = "red";
          alert("❤️ Đã thêm vào yêu thích!");
        } else if (data.status === "removed") {
          favoriteBtn.classList.remove("active");
          favoriteBtn.querySelector("i").classList.remove("fa-solid");
          favoriteBtn.querySelector("i").classList.add("fa-regular");
          favoriteBtn.querySelector("i").style.color = "";
          alert("💔 Đã xóa khỏi yêu thích!");
        }
      } catch (error) {
        console.error("Lỗi:", error);
        alert("Có lỗi xảy ra, vui lòng thử lại.");
      }
    });

    // 🔖 XỬ LÝ NÚT LƯU QUÁN (nếu cần)
    const saveBtn = document.getElementById("saveBtn");
    if (saveBtn) {
      let clickCount = 0;
      saveBtn.addEventListener("click", () => {
        clickCount++;
        if (clickCount % 2 === 1) {
          saveBtn.classList.add("active");
          saveBtn.querySelector("i").classList.replace("fa-regular", "fa-solid");
        } else {
          saveBtn.classList.remove("active");
          saveBtn.querySelector("i").classList.replace("fa-solid", "fa-regular");
        }
      });
    }

    // 🎯 XỬ LÝ CHUYỂN TAB
    const tabs = sidebarContent.querySelectorAll(".tab-btn");
    const tabContents = sidebarContent.querySelectorAll(".tab-content");
    tabs.forEach((btn) => {
      btn.addEventListener("click", () => {
        tabs.forEach((b) => b.classList.remove("active"));
        tabContents.forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
      });
    });

    // ⭐ XỬ LÝ ĐÁNH GIÁ SAO
    let selectedRating = 0;
    document.querySelectorAll("#starRating .star").forEach((star) => {
      star.addEventListener("click", () => {
        selectedRating = parseInt(star.dataset.value);
        document.querySelectorAll("#starRating .star").forEach((s, i) => {
          s.classList.toggle("active", i < selectedRating);
        });
      });
    });

    // 📤 GỬI ĐÁNH GIÁ
    const submitBtn = document.getElementById("submitReview");
if (submitBtn) {
  submitBtn.addEventListener("click", async () => {
    const review = {
      rating: selectedRating,
      comment: document.getElementById("reviewComment").value.trim(),
    };

    if (!review.comment || review.rating === 0) {
      alert("Vui lòng nhập nội dung và chọn số sao!");
      return;
    }

    // 🔄 Hiển thị loading
    submitBtn.disabled = true;
    submitBtn.textContent = "🔄 Đang kiểm tra...";

    try {
      const response = await fetch(`/api/reviews/${place_id}/`, {  // ← THÊM DẤU /
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(review),
        credentials: "include",
      });

      const result = await response.json();

      if (response.ok && result.success) {
        alert(result.message || "✅ Cảm ơn bạn đã gửi đánh giá!");
        marker.fire("click");
      } else {
        // ❌ Nội dung không hợp lệ
        let errorMsg = result.message || "Lỗi khi gửi đánh giá";
        
        // Nếu có gợi ý nội dung tốt hơn
        if (result.suggested_content) {
          const useSuggestion = confirm(
            `${errorMsg}\n\n💡 Bạn có muốn dùng nội dung gợi ý không?`
          );
          
          if (useSuggestion) {
            document.getElementById("reviewComment").value = result.suggested_content;
            submitBtn.disabled = false;
            submitBtn.textContent = "Gửi đánh giá";
            return;
          }
        }
        
        alert(errorMsg);
      }
    } catch (err) {
      console.error("Lỗi fetch API:", err);
      alert("Lỗi kết nối. Không thể gửi đánh giá.");
    } finally {
      // ✅ Reset button
      submitBtn.disabled = false;
      submitBtn.textContent = "Gửi đánh giá";
    }
  });
}

    // 🚗 NÚT TÌM ĐƯỜNG ĐI
    const tongquanTab = sidebarContent.querySelector("#tab-tongquan");
    const routeBtn = document.createElement("button");

    // ✅ Kiểm tra xem có đang chỉ đường đến quán này không
    const isCurrentPlaceRouted = (routeControl && currentPlaceId === place_id);

    if (isCurrentPlaceRouted) {
      // ✅ Đang chỉ đường đến quán này → Hiển thị nút "Tắt chỉ đường"
      routeBtn.textContent = "📍 Tắt chỉ đường";
      routeBtn.style.background = "linear-gradient(135deg, #ffa726 0%, #ff9800 100%)";
    } else {
      // ✅ Chưa chỉ đường hoặc đang chỉ đường quán khác → Hiển thị "Tìm đường đi"
      routeBtn.textContent = "🔍 Tìm đường đi";
      routeBtn.style.background = "";
    }

    routeBtn.className = "route-btn";
    tongquanTab.appendChild(routeBtn);

    routeBtn.addEventListener("click", async () => {
      const gpsInput = document.getElementById("gpsInput");
      const inputValue = gpsInput ? gpsInput.value.trim() : "";

      // ✅ TRƯỜNG HỢP 1: Đang chỉ đường đến quán này → Tắt đường đi
      if (routeControl && currentPlaceId === place_id) {
        map.removeControl(routeControl);
        routeControl = null;
        currentPlaceId = null;

        const infoEl = tongquanTab.querySelector(".route-info");
        if (infoEl) infoEl.remove();

        // Đổi lại nút
        routeBtn.textContent = "🔍 Tìm đường đi";
        routeBtn.style.background = "";
        return;
      }

      // ✅ TRƯỜNG HỢP 2: Chưa có đường hoặc đang chỉ quán khác → Xóa đường cũ và vẽ đường mới

      // Kiểm tra vị trí xuất phát
      if (!inputValue && !window.currentUserCoords) {
        alert("⚠️ Vui lòng nhập địa điểm hoặc bật định vị GPS trước khi tìm đường!");
        return;
      }

      let userLat, userLon;

      if (inputValue === "Vị trí hiện tại của tôi" && window.currentUserCoords) {
        userLat = window.currentUserCoords.lat;
        userLon = window.currentUserCoords.lon;
      } else if (inputValue) {
        const coords = await geocodeAddress(inputValue);
        if (!coords) return;
        userLat = coords.lat;
        userLon = coords.lon;
      } else if (window.currentUserCoords) {
        userLat = window.currentUserCoords.lat;
        userLon = window.currentUserCoords.lon;
      } else {
        alert("⚠️ Vui lòng nhập địa điểm hoặc bật định vị GPS trước khi tìm đường!");
        return;
      }

      // ✅ Xóa đường cũ nếu có (đang chỉ quán khác)
      if (routeControl) {
        map.removeControl(routeControl);
        routeControl = null;
      }

      // ✅ Vẽ đường mới
      drawRoute(userLat, userLon, lat, lon, tongquanTab);
      currentPlaceId = place_id;

      // ✅ Đổi nút thành "Tắt chỉ đường"
      routeBtn.textContent = "📍 Tắt chỉ đường";
      routeBtn.style.background = "linear-gradient(135deg, #ffa726 0%, #ff9800 100%)";
    });

    sidebar.classList.remove("hidden");

    // ✓ NÚT CHỌN QUÁN CHO FOOD PLANNER
    if (window.foodPlannerState && 
        typeof window.foodPlannerState.isWaitingForPlaceSelection === "function" &&
        window.foodPlannerState.isWaitingForPlaceSelection()) {
      
      const selectPlaceBtn = document.createElement("button");
      selectPlaceBtn.textContent = "✓ Chọn quán này";
      selectPlaceBtn.className = "route-btn";
      selectPlaceBtn.style.marginTop = "10px";
      selectPlaceBtn.style.background = "linear-gradient(135deg, #4caf50 0%, #45a049 100%)";
      selectPlaceBtn.style.color = "white";
      selectPlaceBtn.style.border = "none";
      selectPlaceBtn.style.fontWeight = "600";
      selectPlaceBtn.style.fontSize = "14px";
      selectPlaceBtn.style.padding = "10px 20px";
      selectPlaceBtn.style.borderRadius = "8px";
      selectPlaceBtn.style.cursor = "pointer";
      tongquanTab.appendChild(selectPlaceBtn);

      selectPlaceBtn.addEventListener("click", () => {
        const placeData = {
          ten_quan: p.ten_quan,
          dia_chi: p.dia_chi,
          rating: parseFloat(p.rating) || 0,
          lat: lat,
          lon: lon,
          data_id: p.data_id || p.ten_quan,
          hinh_anh: p.hinh_anh || "",
          gia_trung_binh: p.gia_trung_binh || "",
          khau_vi: p.khau_vi || "",
          gio_mo_cua: p.gio_mo_cua || ""
        };

        if (typeof window.foodPlannerState.selectPlace === "function") {
          const success = window.foodPlannerState.selectPlace(placeData);
          if (success) {
            sidebar.classList.remove("show");
            alert("Đã chọn quán: " + placeData.ten_quan);
          } else {
            alert("Không thể chọn quán. Vui lòng thử lại!");
          }
        }
      });
    }

    // 🚗 HÀM VẼ ĐƯỜNG ĐI
    function drawRoute(userLat, userLon, destLat, destLon, tongquanTab) {
      routeControl = L.Routing.control({
        waypoints: [L.latLng(userLat, userLon), L.latLng(destLat, destLon)],
        lineOptions: {
          styles: [
            { color: "white", weight: 5, opacity: 1 },
            { color: "#34A853", weight: 6, opacity: 1 }
          ],
        },
        show: false,
        addWaypoints: false,
        routeWhileDragging: false,
        containerClassName: 'hidden-routing-control',
        createMarker: (i, wp) => {
          return L.marker(wp.latLng, {
            icon: i === 0
              ? L.icon({
                  iconUrl: "Picture/home.gif",
                  iconSize: [120, 100],
                  iconAnchor: [60, 100],
                })
              : L.icon({
                  iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
                  iconSize: [30, 30],
                  iconAnchor: [15, 30],
                }),
          });
        },
      }).addTo(map);

      routeControl.on("routesfound", (e) => {
        const route = e.routes[0];
        const coords = route.coordinates;

        if (coords && coords.length > 1) {
          const bounds = L.latLngBounds(coords);
          map.fitBounds(bounds, { padding: [50, 50] });
        }

        const distanceKm = (route.summary.totalDistance / 1000).toFixed(1);
        const durationMin = Math.ceil(route.summary.totalTime / 60);

        let infoEl = tongquanTab.querySelector(".route-info");
        if (!infoEl) {
          infoEl = document.createElement("p");
          infoEl.className = "route-info";
          tongquanTab.appendChild(infoEl);
        }
        infoEl.innerHTML = `🛣️ Quãng đường: ${distanceKm} km<br>⏱️ Thời gian: ${durationMin} phút`;
      });
    }
  });

  // ✅ RETURN marker
  return marker;
}

// =========================
// 💖 HIỂN THỊ CÁC QUÁN YÊU THÍCH CỦA USER
// =========================
async function showFavoritePlaces() {
  try {
    console.log('🍕 [SHOW FAVORITES] Step 1: Calling API...');
    
    const res = await fetch("/api/get-favorites/", {
      method: "GET",
      credentials: "include",
    });

    console.log('🍕 [SHOW FAVORITES] Step 2: Response status:', res.status);

    if (res.status === 401 || res.status === 403) {
      alert("Vui lòng đăng nhập để xem danh sách quán yêu thích!");
      return false;
    }

    const data = await res.json();
    const favorites = data.favorites || [];

    console.log('🍕 [SHOW FAVORITES] Step 3: Received data');
    console.log('   📊 Count:', favorites.length);
    console.log('   📦 Data:', favorites);

    if (!favorites.length) {
      showWarningToast("Bạn chưa lưu quán nào vào danh sách quán yêu thích.");
      return false;
    }

    console.log('🍕 [SHOW FAVORITES] Step 4: Calling displayPlaces()...');
    
    // ✅✅✅ SET isFavoriteMode = true TRƯỚC ✅✅✅
    isFavoriteMode = true;
    
    // 🔥🔥🔥 QUAN TRỌNG: XÓA TẤT CẢ CLUSTER CŨ 🔥🔥🔥
    
    // 1️⃣ Xóa cluster local (nếu có)
    if (typeof markerClusterGroup !== 'undefined' && markerClusterGroup) {
      if (map.hasLayer(markerClusterGroup)) {
        map.removeLayer(markerClusterGroup);
        console.log('🧹 Removed LOCAL cluster');
      }
    }
    
    // 2️⃣ Xóa cluster global (nếu có)
    if (window.markerClusterGroup) {
      if (map.hasLayer(window.markerClusterGroup)) {
        map.removeLayer(window.markerClusterGroup);
        console.log('🧹 Removed GLOBAL cluster');
      }
    }
    
    // 3️⃣ TẮT lazy load
    map.off("moveend", loadMarkersInViewport);
    console.log('   ⚠️ Disabled lazy load');
    
    // 4️⃣ Reset biến toàn cục
    allPlacesData = [];
    visibleMarkers.clear();
    markers = [];
    window.placeMarkersById = {};
    console.log('🧹 Cleared all global variables');
    
    // 5️⃣ GỌI displayPlaces()
    clearAllMarkers();
    displayPlaces(favorites, true);
    
    console.log('🍕 [SHOW FAVORITES] Step 5: Done!');
    console.log('   🗺️ Total markers after display:', markers.length);
    
    return true;
  } catch (err) {
    console.error("❌ [FAVORITES ERROR]:", err);
    showWarningToast("Không thể tải danh sách quán yêu thích. Vui lòng thử lại sau.");
    return false;
  }
}


// 📡 LẤY DỮ LIỆU CSV + LỌC THEO KHẨU VỊ
// =========================
// =========================
// 📡 LẤY DỮ LIỆU CSV + TÌM GẦN ĐÚNG (FUZZY SEARCH)
// =========================
// =========================
// 📡 LẤY DỮ LIỆU CSV + TÌM GẦN ĐÚNG (FUZZY SEARCH, BỎ DẤU)
// =========================
function parsePriceRange(priceStr) {
  if (!priceStr) return null;

  let s = priceStr.toLowerCase().trim();

  // ❌ Nếu chứa “không”, bỏ qua
  if (s.includes("không")) return null;

  // 👉 Nếu dạng “Trên …”
  if (s.includes("trên") || s.includes("tren") || s.startsWith(">")) {
    // Lấy ra số đầu tiên
    let num = s.replace(/[^\d\.]/g, ""); // giữ lại số và dấu .
    let value = parseInt(num.replace(/\./g, "")); // bỏ dấu chấm ngăn cách

    if (s.includes("k") || s.includes("nghìn") || s.includes("nghin"))
      value *= 1000;

    if (s.includes("triệu") || s.includes("million")) value *= 1000000;

    return [value, Infinity]; // giá từ X trở lên
  }

  // ==========================================
  // ⬇️ XỬ LÝ BÌNH THƯỜNG: "20k - 30k", "50.000 - 70.000"
  // ==========================================

  let cleaned = s.replace(/\s/g, "");

  let multiplier = 1;

  // nếu có kí hiệu nghìn
  if (/k|n|nghin|nghìn/.test(cleaned)) multiplier = 1000;

  cleaned = cleaned.replace(/[^\d\-]/g, "");

  const parts = cleaned.split("-");

  const minP = (parseInt(parts[0]) || 0) * multiplier;
  const maxP = (parseInt(parts[1]) || minP) * multiplier;

  return [minP, maxP];
}

// =======================================================
// ✅ HÀM TÍNH KHOẢNG CÁCH (Km)
// =======================================================
function distance(lat1, lon1, lat2, lon2) {
  const R = 6371; // km

  const plat1 = parseFloat(lat1);
  const plon1 = parseFloat(lon1);
  const plat2 = parseFloat(lat2);
  const plon2 = parseFloat(lon2);

  if (isNaN(plat1) || isNaN(plon1) || isNaN(plat2) || isNaN(plon2))
    return Infinity;

  const dLat = ((plat2 - plat1) * Math.PI) / 180;
  const dLon = ((plon2 - plon1) * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((plat1 * Math.PI) / 180) *
      Math.cos((plat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // km
}
function clearAllMarkers() {
    // ✅ Xóa toàn bộ markers NHƯNG GIỮ LẠI marker GPS
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            // 🔥 KHÔNG XÓA marker GPS (startMarker)
            if (window.startMarker && layer === window.startMarker) {
                console.log('🔒 Giữ lại marker GPS');
                return;
            }
            map.removeLayer(layer);
        }
    });

    // Xóa tất cả cluster (dù là biến nào)
    if (markerClusterGroup) markerClusterGroup.clearLayers();
    if (window.markerClusterGroup) window.markerClusterGroup.clearLayers();

    // Reset data
    markers = [];
    visibleMarkers.clear();
    window.placeMarkersById = {};
}


// =======================================================
// ✅ FETCH + LỌC DỮ LIỆU (FIXED VERSION)
// =======================================================

async function fetchPlaces(query = "", flavors = [], budget = "", radius = "", shouldZoom = true) {
  try {
    // 🔥 THÊM ĐOẠN NÀY Ở ĐẦU HÀM
    if (window.permanentMarker) {
      if (window.markerClusterGroup) {
        window.markerClusterGroup.removeLayer(window.permanentMarker);
      } else if (map.hasLayer(window.permanentMarker)) {
        map.removeLayer(window.permanentMarker);
      }
      window.permanentMarker = null;
      window.permanentMarkerData = null;
      console.log("🗑️ [FETCH] Cleared permanent marker");
    }
    
    // ✅ RESET TRẠNG THÁI TRƯỚC KHI FETCH MỚI
    allPlacesData = [];
    visibleMarkers.clear();
    
    // Tắt lazy load cũ (nếu có)
    map.off("moveend", loadMarkersInViewport);
    
    const res = await fetch("/api/places");
    let data = await res.json();


    // ⭐ NORMALIZE GIỮNGUYÊN DẤU THANH (chỉ bỏ dấu phụ như ă, ơ, ê)
    function normalizeKeepTone(str) {
      return str
        .toLowerCase()
        .trim()
        // Chỉ chuẩn hóa đ → d
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D");
    }

    // ⭐ NORMALIZE BỎ HOÀN TOÀN DẤU (dùng cho fuzzy search)
    function normalizeRemoveAll(str) {
      return str
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase()
        .trim();
    }

    // ⭐ ESCAPE REGEX đặc biệt characters
    function escapeRegex(str) {
      return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

     let filtered = data;

    // ========== 1️⃣ Tìm theo tên (có rút ngắn dần) ==========
    if (query) {
      const queryKeepTone = normalizeKeepTone(query);
      const queryNoTone = normalizeRemoveAll(query);

      // --- Bước 1: thử exact-match với chuỗi đầy đủ (giữ dấu thanh) ---
      const exactMatches = data.filter((p) => {
        const nameKeepTone = normalizeKeepTone(p.ten_quan || "");
        return nameKeepTone.includes(queryKeepTone);
      });

      if (exactMatches.length > 0) {
        filtered = exactMatches;
        console.log("✅ Exact match found:", exactMatches.length);
      } else {
        // --- Chuẩn bị query không dấu + xử lý trường hợp người dùng gõ liền chữ ---
        let normalizedQuery = queryNoTone;

        // Giữ logic cũ: tự chèn khoảng trắng nếu user gõ liền (vd: "bundaubac")
        if (!normalizedQuery.includes(" ")) {
          const possibleMatches = data.map((p) =>
            normalizeRemoveAll(p.ten_quan || "")
          );
          const splitVariants = [];

          for (let i = 1; i < normalizedQuery.length; i++) {
            splitVariants.push(
              normalizedQuery.slice(0, i) + " " + normalizedQuery.slice(i)
            );
          }
          for (const variant of splitVariants) {
            if (possibleMatches.some((name) => name.includes(variant))) {
              normalizedQuery = variant;
              break;
            }
          }
        }

        // Chuẩn bị dữ liệu cho Fuse chỉ 1 lần
        const fuse = new Fuse(
          data.map((p) => ({
            ...p,
            ten_quan_no_dau: normalizeRemoveAll(p.ten_quan || ""),
          })),
          {
            keys: ["ten_quan_no_dau"],
            threshold: 0.35,   // khá strict
            ignoreLocation: true,
            includeScore: true,
          }
        );

        // Hàm chạy fuzzy + lọc cho 1 câu query đã normalize (không dấu)
        function runFuzzy(normQ) {
          const fuzzyResults = fuse.search(normQ);
          const queryWords = normQ.split(" ").filter(Boolean);

          return fuzzyResults
            .map((r) => r.item)
            .filter((p) => {
              const nameNoTone = normalizeRemoveAll(p.ten_quan || "");
              const hasPhrase = nameNoTone.includes(normQ);
              const hasAllWords = queryWords.every((w) =>
                nameNoTone.includes(w)
              );

              // Query nhiều từ: cho pass nếu chứa cụm hoặc đủ các từ
              if (queryWords.length >= 2) {
                return hasPhrase || hasAllWords;
              }
              // Query 1 từ: chỉ cần chứa từ đó
              return hasPhrase;
            });
        }

        // --- Bước 2: thử với chuỗi đầy đủ ---
        let currentNorm = normalizedQuery;
        let currentWords = currentNorm.split(" ").filter(Boolean);
        let results = runFuzzy(currentNorm);
        console.log(
          `🔍 Fuzzy với "${currentNorm}" =>`,
          results.length,
          "kết quả"
        );

        // --- Bước 3: nếu không ra kết quả thì rút bớt từ cuối dần ---
        // VD: "bun thit nuong cha gio" -> "bun thit nuong cha" -> "bun thit nuong" -> ...
        while (results.length === 0 && currentWords.length > 1) {
          currentWords.pop(); // bỏ bớt 1 từ cuối
          currentNorm = currentWords.join(" ");
          results = runFuzzy(currentNorm);
          console.log(
            `🔁 Thử lại với "${currentNorm}" =>`,
            results.length,
            "kết quả"
          );
        }

        filtered = results;
        console.log(
          "✅ Query cuối cùng dùng để filter:",
          `"${currentNorm}"`,
          "=>",
          filtered.length,
          "kết quả"
        );
      }
    }

    // ========== 2️⃣ Lọc khẩu vị ==========
    if (flavors.length > 0) {
      filtered = filtered.filter((p) => {
        if (!p.khau_vi) return false;
        const norm = normalizeRemoveAll(p.khau_vi);
        return flavors.some((f) => norm.includes(normalizeRemoveAll(f)));
      });
    }

    // ========== 3️⃣ Lọc giá ==========
    if (budget !== "") {
      const [budgetMin, budgetMaxRaw] = budget.split("-").map((n) => n.trim());
      const budgetMinNum = parseInt(budgetMin);
      const budgetMax =
        budgetMaxRaw === "Infinity" ? Infinity : parseInt(budgetMaxRaw);

      filtered = filtered.filter((p) => {
        const range = parsePriceRange(p.gia_trung_binh);
        if (!range) return false;

        const [minP, maxP] = range;

        if (budgetMax === Infinity) {
          return minP >= budgetMinNum;
        }

        return minP >= budgetMinNum && maxP <= budgetMax;
      });
    }

// ========== 4️⃣ Lọc bán kính ==========
if (radius && radius !== "" && radius !== "all") {
  const r = parseFloat(radius);
  
  if (isNaN(r) || r <= 0) {
    // Bán kính không hợp lệ → bỏ qua filter này
  } else {
    // ⭐ CHỈ KIỂM TRA TỌA ĐỘ KHI ĐÃ CHỌN BÁN KÍNH HỢP LỆ
    if (
      !window.currentUserCoords ||
      !window.currentUserCoords.lat ||
      !window.currentUserCoords.lon
    ) {
      showWarningToast(
        "Vui lòng chọn vị trí xuất phát (GPS hoặc nhập địa chỉ) trước khi lọc bán kính!"
      );
      return false; // ⭐⭐⭐ DỪNG HÀM fetchPlaces(), không filter nữa
    }

    const userLat = parseFloat(window.currentUserCoords.lat);
    const userLon = parseFloat(window.currentUserCoords.lon);

    filtered = filtered.filter((p) => {
      if (!p.lat || !p.lon) return false;

      const plat = parseFloat(p.lat.toString().replace(",", "."));
      const plon = parseFloat(p.lon.toString().replace(",", "."));
      if (isNaN(plat) || isNaN(plon)) return false;

      const d = distance(userLat, userLon, plat, plon);
      return d <= r;
    });
  }
}

    const ok = displayPlaces(filtered, shouldZoom);
    return ok;
  } catch (err) {
    console.error("❌ Lỗi khi tải dữ liệu:", err);
    showWarningToast("Không thể tải dữ liệu từ server!");
    return false;
  }
}
let notFoundCount = 0;
// =============================
// 🔍 NÚT TÌM KIẾM
// =============================
document.getElementById("btnSearch").addEventListener("click", async () => {
  const gpsInputValue = document.getElementById("gpsInput").value.trim();
  const query = document.getElementById("query").value.trim();

  // ✅ XÓA MARKER GPS NẾU USER XÓA INPUT
if (!gpsInputValue || gpsInputValue === "") {
  // Xóa marker GPS khỏi map
  if (window.startMarker) {
    map.removeLayer(window.startMarker);
    window.startMarker = null;
    console.log('🧹 Đã xóa marker GPS vì input rỗng');
  }
  
  // Reset tọa độ GPS
  window.currentUserCoords = null;
  console.log('🧹 Đã reset currentUserCoords');
}

  const selectedFlavors = Array.from(
    document.querySelectorAll("#flavorDropdown input:checked")
  ).map((c) => c.value);

  const budget = document.getElementById("budget").value;
  let radius = document.getElementById("radius").value; // ⬅ LẤY GIÁ TRỊ

  // ✅ ✅ ✅ FIX CHÍNH Ở ĐÂY ✅ ✅ ✅
  // Nếu user KHÔNG TỰ CHỌN bán kính (radio không được check) → XÓA giá trị
  const radiusChecked = document.querySelector('input[name="radius"]:checked');
  if (!radiusChecked) {
    radius = ""; // ⬅ XÓA giá trị để KHÔNG LỌC bán kính
    document.getElementById("radius").value = ""; // ⬅ Reset luôn hidden input
  }
  // ✅ ✅ ✅ HẾT FIX ✅ ✅ ✅

  // 🔁 Mỗi lần tìm kiếm mới thì tắt chế độ "Quán yêu thích"
  isFavoriteMode = false;
  const favoriteModeBtnEl = document.getElementById("favoriteModeBtn");
  if (favoriteModeBtnEl) favoriteModeBtnEl.classList.remove("active");

  // 💾 Lưu lại tham số tìm kiếm cuối cùng
  lastSearchParams = {
    query: query,
    flavors: selectedFlavors,
    budget: budget,
    radius: radius,
  };

  let result = true; // true = có quán, false = không
  // 👉 TRUE nếu đây chỉ là filter bằng 3 thanh phụ
  const isFilterOnlySearch =
    (!gpsInputValue || gpsInputValue === "Vị trí hiện tại của tôi") && !query;

  // =============================
  // 📌 CASE 1 — Có nhập địa điểm (khác "Vị trí hiện tại của tôi")
  // =============================
  if (gpsInputValue && gpsInputValue !== "Vị trí hiện tại của tôi") {
    const coords = await geocodeAddress(gpsInputValue);
    if (!coords) return;

    if (window.startMarker) map.removeLayer(window.startMarker);

    window.startMarker = L.marker([coords.lat, coords.lon], {
      icon: L.icon({
          iconUrl: "Picture/home.gif",
          iconSize: [120, 100],
          iconAnchor: [60, 100],
      }),
    }).addTo(map)

    window.currentUserCoords = { lat: coords.lat, lon: coords.lon };

    map.setView([coords.lat, coords.lon], 16);

    // Có filter → mới tìm quán
   // ✅ LUÔN LUÔN gọi fetchPlaces khi có GPS
// Nếu không có filter gì thì fetchPlaces sẽ hiện tất cả quán gần đó
result = await fetchPlaces(query, selectedFlavors, budget, radius, false);
  }

  // =============================
  // 📌 CASE 2 — Không nhập địa điểm
  //      (hoặc "Vị trí hiện tại của tôi")
  // =============================
  else {
    result = await fetchPlaces(query, selectedFlavors, budget, radius, true);
  }

  // =============================
  // 🚨 ĐẾM 3 LẦN THẤT BẠI LIÊN TIẾP (CHỈ TÍNH MAIN SEARCH)
  // =============================
  if (!isFilterOnlySearch) {
    if (result === false) {
      // ❌ Tìm kiếm chính thất bại
      notFoundCount++;
      console.log(
        "⚠️ Không tìm thấy quán (main search):",
        notFoundCount,
        "lần liên tiếp"
      );

      if (notFoundCount >= 3) {
        notFoundCount = 0;
        openChatboxAutomatically();
      }
    } else if (result === true) {
      // ✅ Tìm kiếm chính thành công → reset chuỗi thất bại
      notFoundCount = 0;
    }
  }

  // Nếu là filter-only search → không đụng tới notFoundCount
});


// ✅ NÚT YÊU THÍCH Ở HEADER (ICON TRÁI TIM)
const favoriteModeBtnHeader = document.getElementById("favoriteModeBtnHeader");

if (favoriteModeBtnHeader) {
  favoriteModeBtnHeader.addEventListener("click", async () => {
    console.log('🔴 [FAVORITE BTN] Clicked!');
    console.log('🔴 [FAVORITE BTN] Current mode:', isFavoriteMode);
    
    if (!isFavoriteMode) {
      // ✅ BẬT FAVORITE MODE
      favoriteModeBtnHeader.classList.add("active");

      console.log('🔴 [FAVORITE BTN] Calling showFavoritePlaces()...');
      
      const ok = await showFavoritePlaces();
      
      console.log('🔴 [FAVORITE BTN] Result:', ok);
      console.log('🔴 [FAVORITE BTN] Total markers on map:', markers.length);
      
      if (!ok) {
        // ✅ NẾU THẤT BẠI THÌ TẮT LẠI
        isFavoriteMode = false;
        favoriteModeBtnHeader.classList.remove("active");
      }
    }
    else {
      // ✅ TẮT FAVORITE MODE
      console.log('🟢 [FAVORITE BTN] Turning OFF favorite mode');
      
      isFavoriteMode = false;
      favoriteModeBtnHeader.classList.remove("active");

      // ✅ TẮT lazy load cũ trước
      map.off("moveend", loadMarkersInViewport);
      
      await fetchPlaces(
        lastSearchParams.query,
        lastSearchParams.flavors,
        lastSearchParams.budget,
        lastSearchParams.radius,
        true
      );
      
      console.log('🟢 [FAVORITE BTN] Restored to last search');
    }
  });
}

// =======================================================
// ✅ MULTI-SELECT KHẨU VỊ
// =======================================================
const flavorBtn = document.getElementById("flavorBtn");
const flavorDropdown = document.getElementById("flavorDropdown");
const selectedFlavorsEl = flavorBtn.querySelector(".selected-flavors");
const flavorSelector = document.getElementById("flavorSelector"); // FIX BUG

flavorBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  flavorDropdown.classList.toggle("show");
});

// Ẩn dropdown khi click ra ngoài
document.addEventListener("click", (e) => {
  if (!flavorSelector.contains(e.target)) {
    flavorDropdown.classList.remove("show");
  }
});

// Cập nhật text hiển thị
const checkboxes = flavorDropdown.querySelectorAll("input[type='checkbox']");
checkboxes.forEach((cb) => {
  cb.addEventListener("change", () => {
    const selected = Array.from(checkboxes)
      .filter((c) => c.checked)
      .map((c) => c.value);

    if (selected.length === 0) {
      selectedFlavorsEl.textContent = "Chọn khẩu vị";
      selectedFlavorsEl.classList.add("empty");
    } else {
      selectedFlavorsEl.textContent = selected.join(", ");
      selectedFlavorsEl.classList.remove("empty");
    }
  });
});

// =======================================================
// ✅ TẢI LẦN ĐẦU
// =======================================================
window.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  
  // ✅ Chỉ load quán mặc định khi KHÔNG phải chế độ xem quán bạn bè
  if (urlParams.get('view') !== 'friend-favorites') {
    fetchPlaces("", [], "", "", false);
  }
  // Nếu là chế độ bạn bè thì logic phía dưới sẽ xử lý
});

// =========================
// 💰 BUDGET DROPDOWN
// =========================
const budgetBtn = document.getElementById('budgetBtn');
const budgetDropdown = document.getElementById('budgetDropdown');
const budgetRadios = document.querySelectorAll('input[name="budget"]');
const budgetHidden = document.querySelector('.budget-selector input[type="hidden"]');

budgetBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    budgetDropdown.classList.toggle('show');
    
    // Đóng radius dropdown nếu đang mở
    const radiusDropdown = document.getElementById('radiusDropdown');
    if (radiusDropdown) radiusDropdown.classList.remove('show');
});

budgetRadios.forEach(radio => {
    radio.addEventListener('change', () => {
        const label = document.querySelector(`label[for="${radio.id}"]`).textContent;
        budgetBtn.querySelector('.selected-flavors').textContent = label;
        budgetBtn.querySelector('.selected-flavors').classList.remove('empty');
        
        // ✅ Cập nhật hidden input
        budgetHidden.value = radio.value;
        
        budgetDropdown.classList.remove('show');
    });
});

// =========================
// 📏 RADIUS DROPDOWN
// =========================
const radiusBtn = document.getElementById('radiusBtn');
const radiusDropdown = document.getElementById('radiusDropdown');
const radiusRadios = document.querySelectorAll('input[name="radius"]');
const radiusHidden = document.querySelector('.radius-selector input[type="hidden"]');

radiusBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    radiusDropdown.classList.toggle('show');
    
    // Đóng budget dropdown nếu đang mở
    budgetDropdown.classList.remove('show');
});

radiusRadios.forEach(radio => {
    radio.addEventListener('change', () => {
        const label = document.querySelector(`label[for="${radio.id}"]`).textContent;
        radiusBtn.querySelector('.selected-flavors').textContent = label;
        radiusBtn.querySelector('.selected-flavors').classList.remove('empty');
        
        // ✅ Cập nhật hidden input
        radiusHidden.value = radio.value;
        
        radiusDropdown.classList.remove('show');
    });
});

// Đóng dropdown khi click ra ngoài
document.addEventListener('click', (e) => {
    const budgetSelector = document.getElementById('budgetSelector');
    const radiusSelector = document.getElementById('radiusSelector');
    
    if (budgetSelector && !budgetSelector.contains(e.target)) {
        budgetDropdown.classList.remove('show');
    }
    if (radiusSelector && !radiusSelector.contains(e.target)) {
        radiusDropdown.classList.remove('show');
    }
});


// ========== LƯU BÁN KÍNH VÀO GLOBAL STATE ==========
// =========================
// 🧹 RESET BÁN KÍNH KHI PAGE LOAD (QUAN TRỌNG!)
// =========================
document.addEventListener("DOMContentLoaded", function () {
  console.log("🧹 Đang reset bán kính về mặc định...");
  
  // ✅ Xóa giá trị hidden input
  const radiusInput = document.getElementById('radius');
  if (radiusInput) {
    radiusInput.value = '';
    console.log("✅ Đã xóa giá trị #radius");
  }
  
  // ✅ Bỏ check tất cả radio buttons
  const radiusRadios = document.querySelectorAll('input[name="radius"]');
  radiusRadios.forEach(r => {
    r.checked = false;
  });
  console.log("✅ Đã uncheck tất cả radio buttons");
  
  // ✅ Reset text hiển thị trên nút dropdown
  const radiusBtn = document.getElementById('radiusBtn');
  if (radiusBtn) {
    const radiusText = radiusBtn.querySelector('.selected-flavors');
    if (radiusText) {
      radiusText.textContent = 'Bán kính tìm kiếm';
      radiusText.classList.add('empty');
    }
    console.log("✅ Đã reset text nút bán kính");
  }
  
  // ✅ Làm tương tự cho budget (nếu cần)
  const budgetInput = document.getElementById('budget');
  if (budgetInput) {
    budgetInput.value = '';
  }
  
  const budgetRadios = document.querySelectorAll('input[name="budget"]');
  budgetRadios.forEach(b => {
    b.checked = false;
  });
  
  const budgetBtn = document.getElementById('budgetBtn');
  if (budgetBtn) {
    const budgetText = budgetBtn.querySelector('.selected-flavors');
    if (budgetText) {
      budgetText.textContent = 'Ngân sách mặc định ▼';
      budgetText.classList.add('empty');
    }
  }
  
  console.log("✅ Hoàn tất reset filter mặc định!");
});
// =========================
// 💡 GỢI Ý TÌM KIẾM (AUTOCOMPLETE) - SỬ DỤNG #suggestions HIỆN CÓ TRONG HTML
// =========================
const input = document.getElementById("query");
const suggestionsEl = document.getElementById("suggestions");
let allPlacesCache = [];

// Tải toàn bộ danh sách quán (1 lần)
(async () => {
  try {
    const res = await fetch("/api/places");
    allPlacesCache = await res.json();
  } catch (err) {
    console.error("❌ Lỗi tải dữ liệu gợi ý:", err);
  }
})();

input.addEventListener("input", () => {
  const text = input.value.trim().toLowerCase();
  suggestionsEl.innerHTML = "";

  if (text.length === 0) {
    suggestionsEl.classList.remove("show");
    return;
  }

  const filtered = allPlacesCache
    .filter((p) => p.ten_quan && p.ten_quan.toLowerCase().includes(text))
    .slice(0, 8);

  if (filtered.length === 0) {
    suggestionsEl.classList.remove("show");
    return;
  }

  filtered.forEach((p) => {
    const div = document.createElement("div");
    const cat = detectCategory(p.ten_quan);
    const iconUrl = icons[cat]
      ? icons[cat].options.iconUrl
      : icons.default.options.iconUrl;

    const name = p.ten_quan;
    const idx = name.toLowerCase().indexOf(text);
    let displayName = name;
    if (idx >= 0) {
      displayName = `${name.slice(0, idx)}<strong>${name.slice(
        idx,
        idx + text.length
      )}</strong>${name.slice(idx + text.length)}`;
    }

    div.innerHTML = `<img src="${iconUrl}" style="width:20px;height:20px;margin-right:8px;object-fit:contain;"> <div style="flex:1">${displayName}</div>`;
    
    // 🔥🔥🔥 LOGIC MỚI BẮT ĐẦU TỪ ĐÂY 🔥🔥🔥
   div.addEventListener("click", async () => {
  input.value = p.ten_quan;
  suggestionsEl.classList.remove("show");

  const lat = parseFloat(p.lat?.toString().replace(",", "."));
  const lon = parseFloat(p.lon?.toString().replace(",", "."));

  if (isNaN(lat) || isNaN(lon)) {
    alert("⚠️ Quán này không có tọa độ!");
    return;
  }

  console.log("🎯 [AUTOCOMPLETE] Clicked:", p.ten_quan);

  // // 🔥 BƯỚC 1: TẮT lazy load HOÀN TOÀN

  // 🔥 BƯỚC 2: XÓA TẤT CẢ MARKER CŨ
  clearAllMarkers();
  console.log("🧹 [AUTOCOMPLETE] Cleared all old markers");

  // 🔥 BƯỚC 3: Reset biến toàn cục
  allPlacesData = [p]; // ⬅️ CHỈ GIỮ LẠI QUÁN NÀY
  visibleMarkers.clear();
  markers = [];
  window.placeMarkersById = {};

  // 🔥 BƯỚC 4: Zoom đến quán
  map.setView([lat, lon], 17);
  console.log("📍 [AUTOCOMPLETE] Zoomed to:", lat, lon);

  // 🔥 BƯỚC 5: Tạo marker SAU KHI ZOOM XONG
 setTimeout(() => {
  console.log("🏗️ [AUTOCOMPLETE] Creating marker...");

  const marker = createMarker(p, lat, lon);
  markers.push(marker);

  // ❗ FIX: marker autocomplete luôn nằm trực tiếp trên map
  marker.addTo(map);

  const placeId = p.data_id || p.ten_quan;
  window.placeMarkersById[placeId] = marker;
  visibleMarkers.add(placeId);

  console.log("✅ [AUTOCOMPLETE] Marker created");

  window.permanentMarker = marker;
  window.permanentMarkerData = p;

   // 🔥 BẬT LẠI LAZY LOAD NHƯNG VỚI LOGIC KHÁC
map.on("moveend", () => {
  // 🔒 Nếu không còn permanentMarker (đã bị xoá khi search mới) thì thoát luôn
  if (!window.permanentMarker) return;

  let markerExists = false;
  
  if (window.markerClusterGroup && window.markerClusterGroup.hasLayer(window.permanentMarker)) {
    markerExists = true;
  }
  
  if (map.hasLayer(window.permanentMarker)) {
    markerExists = true;
  }
  
  if (!markerExists) {
    console.log("🔄 [AUTOCOMPLETE] Re-adding permanent marker");
    
    if (window.markerClusterGroup) {
      window.markerClusterGroup.addLayer(window.permanentMarker);
    } else {
      window.permanentMarker.addTo(map);
    }
    
    const placeId = window.permanentMarkerData.data_id || window.permanentMarkerData.ten_quan;
    if (placeId) {
      window.placeMarkersById[placeId] = window.permanentMarker;
      visibleMarkers.add(placeId);
    }
  }
});


    // 🔥 CLICK VÀO MARKER
    setTimeout(() => {
      marker.fire("click");
      console.log("🔥 [AUTOCOMPLETE] Marker clicked");
    }, 300);

  }, 700);
});
    // 🔥🔥🔥 LOGIC MỚI KẾT THÚC 🔥🔥🔥

    suggestionsEl.appendChild(div);
  });

  suggestionsEl.classList.add("show");
});

// ẩn gợi ý khi click ra ngoài hộp tìm kiếm
document.addEventListener("click", (e) => {
  const searchBox = document.querySelector(".search-box");
  if (!searchBox.contains(e.target)) {
    suggestionsEl.classList.remove("show");
  }
});

// =========================
// 🖼️ CLICK ẢNH -> PHÓNG TO
// =========================
document.addEventListener("click", (e) => {
  // ✅ LOẠI TRỪ ẢNH TRONG MINI GAME
  const isInMiniGame = e.target.closest('.mini-game-overlay');
  const isInMapSelector = e.target.closest('.map-selector');
  const isInAchievements = e.target.closest('.achievements-container');
  const isInMapOption = e.target.closest('.map-option');
  const isInAchievementCard = e.target.closest('.achievement-card');
  
  // Chỉ xử lý ảnh trong sidebar (tab-content), KHÔNG phải mini game
  if (e.target.tagName === "IMG" && 
      e.target.closest(".tab-content") &&
      !isInMiniGame && 
      !isInMapSelector && 
      !isInAchievements &&
      !isInMapOption &&
      !isInAchievementCard) {
    
    const src = e.target.src;
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImg");
    modalImg.src = src;
    modal.style.display = "flex";
  }
});

document.getElementById("closeModal").addEventListener("click", () => {
  document.getElementById("imageModal").style.display = "none";
});

document.getElementById("imageModal").addEventListener("click", (e) => {
  if (e.target.id === "imageModal") {
    e.currentTarget.style.display = "none";
  }
});

// =========================
// 🌍 CHUYỂN ĐỊA ĐIỂM CHỮ → TỌA ĐỘ (OSM API)
// =========================

async function geocodeAddress(address) {
  const url = `/api/accounts/geocode/?address=${encodeURIComponent(address)}`;
  
  try {
    const res = await fetch(url);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    
    const data = await res.json();

    if (data.lat && data.lon) {
      return {
        lat: parseFloat(data.lat),
        lon: parseFloat(data.lon),
      };
    }

    showWarningToast("❌ Không tìm thấy địa điểm này!");
    return null;
    
  } catch (err) {
    console.error("Lỗi khi geocode:", err);
    showWarningToast("❌ Lỗi khi tìm địa điểm: " + err.message);
    return null;
  }
}

// =========================
// 📍 NÚT GPS: tự động định vị bản thân
// =========================
document.getElementById("gpsLocateBtn").addEventListener("click", async () => {
  if (!navigator.geolocation) {
    showWarningToast("Trình duyệt không hỗ trợ định vị GPS!");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const userLat = pos.coords.latitude;
      const userLon = pos.coords.longitude;

      // ✅ Điền text vào ô nhập (để người dùng biết là đang dùng GPS)
      const gpsInput = document.getElementById("gpsInput");
      gpsInput.value = "Vị trí hiện tại của tôi";

      // ✅ Lưu lại tọa độ thật để khi nhấn “Tìm đường đi” dùng đúng vị trí này
      window.currentUserCoords = { lat: userLat, lon: userLon };

      // ✅ Xóa marker xuất phát cũ (dù là GPS hay nhập tay)
      if (window.startMarker) {
        map.removeLayer(window.startMarker);
      }

      // ✅ Thêm marker mới cho điểm xuất phát
      window.startMarker = L.marker([userLat, userLon], {
        icon: L.icon({
          iconUrl: "Picture/home.gif",
          iconSize: [120, 100],
          iconAnchor: [60, 100],
        }),
      }).addTo(map)

      map.setView([userLat, userLon], 16);
    },
    (err) => {
      showWarningToast("Không thể lấy vị trí của bạn: " + err.message);
    }
  );
});

// =========================
// ⌨️ ENTER chạy nút TÌM cho cả 2 ô input
// =========================
document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        const active = document.activeElement;

        // Nếu đang focus vào ô địa điểm hoặc ô tìm món → chạy Search
        if (active && (active.id === "gpsInput" || active.id === "query")) {
            e.preventDefault();
            document.getElementById("btnSearch").click();
        }
    }
});

// =====================================================
// 🚀 TỰ ĐỘNG MỞ QUÁN TỪ TRANG ACCOUNT (Deep Linking)
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
    // 1. Đọc tham số trên thanh địa chỉ (Ví dụ: ?search=Phở+Hòa)
    const urlParams = new URLSearchParams(window.location.search);
    const searchName = urlParams.get('search');

    // 2. Nếu tìm thấy tên quán
    if (searchName) {
        console.log("🌍 Đang tự động tìm quán:", searchName);
        
        const searchInput = document.getElementById("query");
        const searchBtn = document.getElementById("btnSearch");

        if (searchInput && searchBtn) {
            // A. Điền tên quán vào ô nhập
            searchInput.value = searchName;
            
            // ✅ XÓA BÁN KÍNH VÀ GPS ĐỂ TRÁNH BẮT NHẬP VỊ TRÍ
            const radiusInput = document.getElementById('radius');
            const budgetInput = document.getElementById('budget');
            const gpsInput = document.getElementById('gpsInput');
            
            if (radiusInput) radiusInput.value = '';
            if (budgetInput) budgetInput.value = '';
            if (gpsInput) gpsInput.value = '';
            
            // ✅ Reset radio buttons
            const radiusRadios = document.querySelectorAll('input[name="radius"]');
            radiusRadios.forEach(r => r.checked = false);
            
            const budgetRadios = document.querySelectorAll('input[name="budget"]');
            budgetRadios.forEach(b => b.checked = false);
            
            // ✅ Reset text hiển thị trên nút dropdown
            const radiusBtn = document.getElementById('radiusBtn');
            const budgetBtn = document.getElementById('budgetBtn');
            
            if (radiusBtn) {
                const radiusText = radiusBtn.querySelector('.selected-flavors');
                if (radiusText) {
                    radiusText.textContent = 'Bán kính tìm kiếm';
                    radiusText.classList.add('empty');
                }
            }
            
            if (budgetBtn) {
                const budgetText = budgetBtn.querySelector('.selected-flavors');
                if (budgetText) {
                    budgetText.textContent = 'Ngân sách mặc định ▼';
                    budgetText.classList.add('empty');
                }
            }
            
            // B. Đợi 1 chút cho bản đồ load xong thì tự bấm nút tìm
            setTimeout(() => {
                searchBtn.click();
                console.log('🔍 Auto-search triggered for:', searchName);
            }, 500); // Đợi 0.5 giây
        }
    }
});



// Xử lý nút đóng sidebar
const closeSidebarBtn = document.getElementById('closeSidebar');
if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('show');
        }
    });
}

// Đóng sidebar khi click vào overlay (nếu có)
const sidebar = document.getElementById('sidebar');
if (sidebar) {
    sidebar.addEventListener('click', (e) => {
        // Chỉ đóng khi click vào chính sidebar (không phải nội dung bên trong)
        if (e.target === sidebar) {
            sidebar.classList.remove('show');
        }
    });
}

// =========================
// 🎯 Cho mini_game.js gọi khi click vào quán trong Album
// =========================
window.focusPlaceOnMap = function ({ lat, lon, placeId, name, address }) {
  if (!window.map) return;

  // 1️⃣ Ưu tiên dùng marker có sẵn theo id
  if (placeId && window.placeMarkersById && window.placeMarkersById[placeId]) {
    const mk = window.placeMarkersById[placeId];
    const pos = mk.getLatLng();

    // zoom tới & tái sử dụng logic click marker (mở sidebar, review, route,…)
    map.setView(pos, 17, { animate: true });
    mk.fire("click");
    return;
  }

  // 2️⃣ Fallback: dùng toạ độ
  const latNum = parseFloat(lat);
  const lonNum = parseFloat(lon);
  if (!isNaN(latNum) && !isNaN(lonNum)) {
    const pos = [latNum, lonNum];
    map.setView(pos, 17, { animate: true });

    L.popup()
      .setLatLng(pos)
      .setContent(`<b>${name || ""}</b><br>${address || ""}`)
      .openOn(map);
  }
};

// =========================
// 🎯 Cho mini_game (Album) gọi
// =========================
window.focusPlaceOnMap = function ({
  lat,
  lon,
  placeId,
  name,
  address,
  placeData
}) {
  if (!window.map) return;

  let marker = null;

  // 1️⃣ Ưu tiên dùng marker đã tồn tại
  if (placeId && window.placeMarkersById && window.placeMarkersById[placeId]) {
    marker = window.placeMarkersById[placeId];
  }

  // 2️⃣ Nếu chưa có marker mà có placeData → tạo luôn marker
  if (!marker && placeData) {
    const plat = parseFloat(placeData.lat ?? lat);
    const plon = parseFloat(placeData.lon ?? lon);
    if (!isNaN(plat) && !isNaN(plon)) {
      marker = createMarker(placeData, plat, plon);

      if (window.markerClusterGroup) {
        window.markerClusterGroup.addLayer(marker);
      } else {
        marker.addTo(map);
      }

      // lưu lại để lần sau dùng
      const id = placeId || placeData.data_id || placeData.ten_quan;
      if (!window.placeMarkersById) window.placeMarkersById = {};
      if (id) window.placeMarkersById[id] = marker;

      if (id && window.visibleMarkers) {
        visibleMarkers.add(id); // tránh tạo trùng trong lazy-load
      }
    }
  }

  // 3️⃣ Nếu đã có marker → zoom + giả lập click để mở sidebar
  if (marker) {
    const pos = marker.getLatLng();
    map.setView(pos, 17, { animate: true });
    marker.fire("click");           // ⬅ chạy y như user click trên map
    return;
  }

  // 4️⃣ Fallback cuối: chỉ pan + popup đơn giản
  const plat = parseFloat(lat);
  const plon = parseFloat(lon);
  if (!isNaN(plat) && !isNaN(plon)) {
    const pos = [plat, plon];
    map.setView(pos, 17, { animate: true });
    L.popup()
      .setLatLng(pos)
      .setContent(`<b>${name || ""}</b><br>${address || ""}`)
      .openOn(map);
  }
};

// ==========================================================
// 🗺️ HIỂN THỊ QUÁN YÊU THÍCH CỦA BẠN BÈ
// ==========================================================
// ==========================================================
// 🗺️ HIỂN THỊ QUÁN YÊU THÍCH CỦA BẠN BÈ
// ==========================================================
window.addEventListener('DOMContentLoaded', () => {
    console.log('🔍 Checking for friend favorites view...');
    
    const urlParams = new URLSearchParams(window.location.search);
    console.log('🔍 URL params:', urlParams.toString());
    
    if (urlParams.get('view') === 'friend-favorites') {
        console.log('✅ Friend favorites mode detected');
        
        const friendData = localStorage.getItem('friendFavorites');
        console.log('💾 LocalStorage data:', friendData);
        
        if (friendData) {
            const { friendName, places } = JSON.parse(friendData);
            console.log('👤 Friend:', friendName);
            console.log('🍽️ Places count:', places.length);
            console.log('📦 Places data:', places);
            
            // ✅ Kiểm tra dữ liệu có hợp lệ không
            if (!places || places.length === 0) {
                showWarningToast(`${friendName} chưa có quán yêu thích nào`);
                localStorage.removeItem('friendFavorites');
                return;
            }
            
            // ✅ Log chi tiết từng quán
            places.forEach((place, i) => {
                console.log(`\nQuán ${i+1}:`);
                console.log(`  - Tên: ${place.ten_quan}`);
                console.log(`  - lat: ${place.lat}`);
                console.log(`  - lon: ${place.lon}`);
            });
            
            localStorage.removeItem('friendFavorites');
            
            // ✅ QUAN TRỌNG: Đợi 500ms để đảm bảo map đã load xong
            setTimeout(() => {
                showCustomAlert(`Đang hiển thị ${places.length} quán yêu thích của ${friendName}`);
                
                // ✅ Xóa TẤT CẢ marker cũ trước khi hiển thị
                if (window.markerClusterGroup) {
                    map.removeLayer(window.markerClusterGroup);
                }
                
                // ✅ Tạo cluster mới
                window.markerClusterGroup = L.markerClusterGroup({
                    maxClusterRadius: 50,
                    spiderfyOnMaxZoom: true,
                    showCoverageOnHover: false
                });
                map.addLayer(window.markerClusterGroup);
                
                // ✅ Reset biến toàn cục
                window.allPlacesData = places;
                window.visibleMarkers = new Set();
                
                // ✅ Hiển thị chỉ 7 quán của bạn bè
                displayPlaces(places, true);
                
                console.log('✅ Đã gọi displayPlaces với', places.length, 'quán');
            }, 500);
            
        } else {
            console.warn('⚠️ No data in localStorage');
        }
    } else {
        console.log('ℹ️ Not in friend favorites view mode');
    }
});
// Hàm toast
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => {
            toast.className = 'toast';
        }, 3000);
    }
}
// Thêm vào cuối file, sau phần xử lý friend favorites

// ==========================================================
// 🚪 NÚT THOÁT KHỎI CHẾ ĐỘ XEM QUÁN BẠN BÈ
// ==========================================================
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('view') === 'friend-favorites') {
        // ✅ Tạo nút thoát
        const exitBtn = document.createElement('button');
        exitBtn.innerHTML = 'X';
        exitBtn.style.cssText = `
            position: fixed;
            top: 180px;
            left: 20px;
            z-index: 10000;
            padding: 12px 24px;
            background: linear-gradient(135deg, #bc2a21 0%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        
        // ✅ Hover effect
        exitBtn.addEventListener('mouseenter', () => {
            exitBtn.style.transform = 'translateY(-2px)';
            exitBtn.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
        });
        
        exitBtn.addEventListener('mouseleave', () => {
            exitBtn.style.transform = 'translateY(0)';
            exitBtn.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
        });
        
        // ✅ Click để thoát
        exitBtn.addEventListener('click', () => {
            // Xóa tham số view khỏi URL
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);
            
            // Reload lại trang để hiển thị bản đồ bình thường
            window.location.reload();
        });
        
        // ✅ Thêm nút vào body
        document.body.appendChild(exitBtn);
        
        console.log('✅ Đã thêm nút thoát khỏi chế độ bạn bè');
    }
});

//Hàm click lại marker
window.refreshCurrentSidebar = function() {
  const sidebar = document.getElementById('sidebar');
  
  if (!sidebar || !sidebar.classList.contains('show')) {
    return;
  }
  
  const placeId = sidebar.dataset.placeId;
  
  if (!placeId) {
    return;
  }
  
  if (!window.placeMarkersById || !window.placeMarkersById[placeId]) {
    return;
  }
  
  window.placeMarkersById[placeId].fire('click');
};

// ==========================================================
// 🍽️ HÀM RIÊNG CHO FOOD PLANNER - FLY TO PLACE WITH AUTO MARKER
// ==========================================================
window.flyToPlaceFromPlanner = function(lat, lon, placeId, placeName) {
  if (typeof map === 'undefined') {
    console.error('❌ Map chưa được khởi tạo');
    return;
  }

  console.log('🎯 flyToPlaceFromPlanner được gọi:', { lat, lon, placeId, placeName });

  // ✅ ZOOM ĐẾN VỊ TRÍ QUÁN
  map.setView([lat, lon], 17, { animate: true });

  // ✅ HÀM ĐỢI MAP ZOOM XONG
  function waitForMapReady() {
    return new Promise((resolve) => {
      if (!map._animatingZoom) {
        setTimeout(resolve, 500);
        return;
      }
      
      map.once('moveend', () => {
        setTimeout(resolve, 800);
      });
    });
  }

  // ✅ HÀM KIỂM TRA CÓ PHẢI MARKER CỦA ROUTES KHÔNG
  function isRouteMarker(layer) {
    if (!layer.options || !layer.options.icon) return false;
    
    const iconUrl = layer.options.icon.options?.iconUrl || '';
    
    // 🔥 BỎ QUA MARKER HOME (điểm xuất phát) và MARKER ĐÍCH (quán ăn trên route)
    if (iconUrl.includes('home.gif') || 
        iconUrl.includes('684908.png') ||
        iconUrl.includes('marker-icon.png')) {
      return true;
    }
    
    // 🔥 BỎ QUA MARKER SỐ (1, 2, 3...) trên route
    if (layer.options.icon.options?.className?.includes('route-number-marker')) {
      return true;
    }
    
    return false;
  }

  // ✅ HÀM TÌM MARKER HIỆN CÓ (BỎ QUA MARKER ROUTES)
  function findExistingMarker() {
    let targetMarker = null;

    // 🔥 BƯỚC 1: TÌM MARKER THEO ID
    if (placeId && window.placeMarkersById && window.placeMarkersById[placeId]) {
      targetMarker = window.placeMarkersById[placeId];
      
      // ✅ KIỂM TRA MARKER CÓ ĐANG TRÊN MAP KHÔNG
      if (map.hasLayer(targetMarker)) {
        console.log('✅ Tìm thấy marker theo ID (đang hiển thị):', placeId);
        return targetMarker;
      } else {
        console.warn('⚠️ Marker tồn tại nhưng không hiển thị trên map');
        targetMarker = null;
      }
    }

    // 🔥 BƯỚC 2: TÌM THEO TÊN QUÁN
    if (placeName) {
      let foundByName = false;
      
      map.eachLayer((layer) => {
        if (foundByName) return;
        
        if (layer instanceof L.Marker) {
          // 🔥 BỎ QUA MARKER CỦA ROUTES
          if (isRouteMarker(layer)) {
            return;
          }
          
          const data = layer.options.placeData || layer.placeData;
          if (data && data.ten_quan === placeName) {
            targetMarker = layer;
            foundByName = true;
            console.log('✅ Tìm thấy marker theo tên:', placeName);
          }
        }
      });
    }

    if (targetMarker) return targetMarker;

    // 🔥 BƯỚC 3: TÌM THEO TỌA ĐỘ
    let minDistance = Infinity;
    
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        // 🔥 BỎ QUA MARKER CỦA ROUTES
        if (isRouteMarker(layer)) {
          return;
        }
        
        const markerLatLng = layer.getLatLng();
        
        const dLat = markerLatLng.lat - lat;
        const dLng = markerLatLng.lng - lon;
        const distance = Math.sqrt(dLat * dLat + dLng * dLng);
        
        if (distance < 0.00001 && distance < minDistance) {
          minDistance = distance;
          targetMarker = layer;
        }
      }
    });
    
    if (targetMarker) {
      console.log('✅ Tìm thấy marker theo tọa độ, khoảng cách:', minDistance.toFixed(8));
    }

    return targetMarker;
  }

  // ✅ HÀM TÌM DATA QUÁN
  function findPlaceData() {
    console.log('🔍 Tìm data quán trong allPlacesData...');
    
    if (typeof allPlacesData === 'undefined' || !allPlacesData || allPlacesData.length === 0) {
      console.error('❌ allPlacesData không tồn tại hoặc rỗng');
      return null;
    }

    let foundPlace = null;

    // Tìm theo ID
    if (placeId) {
      foundPlace = allPlacesData.find(p => p.data_id === placeId);
      if (foundPlace) {
        console.log('✅ Tìm thấy data theo ID:', placeId);
        return foundPlace;
      }
    }

    // Tìm theo tên
    if (placeName) {
      foundPlace = allPlacesData.find(p => p.ten_quan === placeName);
      if (foundPlace) {
        console.log('✅ Tìm thấy data theo tên:', placeName);
        return foundPlace;
      }
    }

    // Tìm theo tọa độ
    foundPlace = allPlacesData.find(p => {
      const pLat = parseFloat(p.lat);
      const pLon = parseFloat(p.lon);
      if (isNaN(pLat) || isNaN(pLon)) return false;
      
      const dist = Math.sqrt(
        Math.pow(pLat - lat, 2) + 
        Math.pow(pLon - lon, 2)
      );
      return dist < 0.00001;
    });

    if (foundPlace) {
      console.log('✅ Tìm thấy data theo tọa độ');
    }

    return foundPlace;
  }

  // ✅ HÀM TẠO MARKER MỚI
  function createNewMarker(placeData) {
    console.log('🏗️ Tạo marker mới cho:', placeData?.ten_quan || placeName);

    // Nếu không có data, tạo data tối thiểu
    if (!placeData) {
      placeData = {
        ten_quan: placeName || 'Quán ăn',
        dia_chi: 'Đang cập nhật...',
        lat: lat,
        lon: lon,
        data_id: placeId || `temp_${Date.now()}`,
        rating: 0,
        gio_mo_cua: 'Không rõ',
        gia_trung_binh: 'Không có',
        khau_vi: '',
        hinh_anh: '',
        so_dien_thoai: '',
        thuc_don: '',
        mo_ta: ''
      };
      console.log('⚠️ Tạo data tối thiểu cho marker');
    }

    // Kiểm tra hàm createMarker có tồn tại không
    if (typeof createMarker !== 'function') {
      console.error('❌ Hàm createMarker không tồn tại');
      return null;
    }

    const newMarker = createMarker(placeData, lat, lon);

    // 🔥 ĐẢM BẢO MARKER ĐƯỢC THÊM VÀO MAP
    if (window.markerClusterGroup) {
      window.markerClusterGroup.addLayer(newMarker);
      console.log('✅ Đã thêm marker vào cluster');
      
      // 🔥 FORCE REFRESH CLUSTER
      window.markerClusterGroup.refreshClusters();
    } else {
      newMarker.addTo(map);
      console.log('✅ Đã thêm marker vào map');
    }

    // Lưu vào index
    const id = placeData.data_id || placeId || `temp_${Date.now()}`;
    if (!window.placeMarkersById) window.placeMarkersById = {};
    window.placeMarkersById[id] = newMarker;
    console.log('✅ Đã lưu marker vào placeMarkersById với ID:', id);

    // Đánh dấu visible
    if (window.visibleMarkers) {
      window.visibleMarkers.add(id);
    }

    return newMarker;
  }

  // ✅ LOGIC CHÍNH
  waitForMapReady().then(() => {
    console.log('🎬 Bắt đầu tìm/tạo marker...');
    
    // 1️⃣ Tìm marker hiện có
    let marker = findExistingMarker();

    if (marker) {
      console.log('✅ Sử dụng marker hiện có');
      
      // 🔥 ĐẢM BẢO MARKER VẪN CÒN TRÊN MAP
      if (!map.hasLayer(marker)) {
        console.warn('⚠️ Marker không còn trên map, thêm lại...');
        if (window.markerClusterGroup) {
          window.markerClusterGroup.addLayer(marker);
        } else {
          marker.addTo(map);
        }
      }
      
      marker.fire('click');
      return;
    }

    // 2️⃣ Không tìm thấy marker → Tạo mới
    console.log('⚠️ Không tìm thấy marker, tiến hành tạo mới...');

    // 3️⃣ Tìm data quán
    const placeData = findPlaceData();

    // 4️⃣ Tạo marker mới (dù có data hay không)
    const newMarker = createNewMarker(placeData);

    if (!newMarker) {
      console.error('❌ Không thể tạo marker');
      
      // Fallback: Tạo popup đơn giản
      L.popup()
        .setLatLng([lat, lon])
        .setContent(`
          <div style="text-align:center;padding:10px;">
            <strong style="color:#FF6B35;">${placeName || 'Quán ăn'}</strong><br>
            <em style="color:#999;font-size:12px;">Không tìm thấy thông tin chi tiết</em>
          </div>
        `)
        .openOn(map);
      
      return;
    }

    // 5️⃣ Click vào marker mới sau 600ms
    setTimeout(() => {
      console.log('🔥 Click vào marker mới');
      
      // 🔥 KIỂM TRA LẠI MARKER VẪN CÒN TRÊN MAP
      if (!map.hasLayer(newMarker)) {
        console.error('❌ Marker mới đã bị xóa khỏi map!');
        if (window.markerClusterGroup) {
          window.markerClusterGroup.addLayer(newMarker);
        } else {
          newMarker.addTo(map);
        }
      }
      
      newMarker.fire('click');
    }, 600);
  });
};

// ==========================================================
// 🍽️ CHỈ HIỂN THỊ MARKER CỦA QUÁN TRONG LỊCH TRÌNH (FOOD PLANNER)
// ==========================================================
showMarkersForPlaceIds = function (plan) {
  try {
    if (!window.map || !plan) return;

    // 🔍 Gom tất cả quán có trong plan
    const placesInPlan = [];
    for (const key in plan) {
      if (!Object.prototype.hasOwnProperty.call(plan, key)) continue;
      if (key === "_order") continue;

      const item = plan[key];
      if (!item || !item.place) continue;

      const place = item.place;
      const id = place.data_id || place.ten_quan;
      if (!id) continue;

      // tránh trùng
      if (placesInPlan.some(p => p.id === id)) continue;

      placesInPlan.push({ id, place });
    }

    if (placesInPlan.length === 0) {
      console.log("⚠️ Plan không có quán nào để vẽ marker.");
      return;
    }

    // 🎯 Tập ID quán cần GIỮ LẠI trên map
    const idsTrongPlan = new Set(placesInPlan.map(p => p.id));

    // 🔌 Tắt lazy-load: không tự load thêm quán khác nữa
    if (typeof loadMarkersInViewport === "function") {
      map.off("moveend", loadMarkersInViewport);
    }

    // 🧩 Gom tất cả cluster đang có (cluster mặc định + cluster global)
    const clusters = [];

    // cluster mặc định dùng cho search/lazy-load
    try {
      if (typeof markerClusterGroup !== "undefined" && markerClusterGroup && map.hasLayer(markerClusterGroup)) {
        clusters.push(markerClusterGroup);
      }
    } catch (e) {
      // bỏ qua nếu biến không tồn tại
    }

    // cluster global (friend view / planner / mini game)
    if (window.markerClusterGroup && map.hasLayer(window.markerClusterGroup)) {
      if (!clusters.includes(window.markerClusterGroup)) {
        clusters.push(window.markerClusterGroup);
      }
    }

    // Nếu chưa có cluster nào → tạo một cái để dùng cho lịch trình
    if (clusters.length === 0) {
      const tempCluster = L.markerClusterGroup({
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 80,
        disableClusteringAtZoom: 16
      });
      map.addLayer(tempCluster);
      clusters.push(tempCluster);

      // cập nhật lại 2 biến global nếu có
      window.markerClusterGroup = tempCluster;
      try { markerClusterGroup = tempCluster; } catch (e) {}
    }

    // Đảm bảo map place_id -> marker tồn tại
    if (!window.placeMarkersById) {
      window.placeMarkersById = {};
    }

    // 🧹 XÓA TẤT CẢ marker KHÔNG NẰM TRONG LỊCH TRÌNH (cả trong cluster lẫn trên map)
    for (const [id, marker] of Object.entries(window.placeMarkersById)) {
      if (!marker || typeof marker.getLatLng !== "function") continue;

      if (!idsTrongPlan.has(id)) {
        // gỡ khỏi mọi cluster hiện có
        clusters.forEach(c => {
          if (c && c.hasLayer && c.hasLayer(marker)) {
            c.removeLayer(marker);
          }
        });

        // gỡ khỏi map
        if (typeof marker.remove === "function") {
          marker.remove();
        } else if (map.hasLayer(marker)) {
          map.removeLayer(marker);
        }
      }
    }

    // 🧽 Clear toàn bộ layer trong các cluster hiện tại
    clusters.forEach(c => {
      if (c && c.clearLayers) c.clearLayers();
    });

    // 🔄 Reset visibleMarkers (cả bản local và bản window)
    if (typeof visibleMarkers !== "undefined" && visibleMarkers instanceof Set) {
      visibleMarkers.clear();
    }
    if (!window.visibleMarkers || !(window.visibleMarkers instanceof Set)) {
      window.visibleMarkers = new Set();
    } else {
      window.visibleMarkers.clear();
    }

    const bounds = L.latLngBounds([]);

    // 🔁 Tạo / dùng lại marker chỉ cho những quán trong plan
    placesInPlan.forEach(({ id, place }) => {
      const lat = parseFloat(place.lat?.toString().replace(",", "."));
      const lon = parseFloat(place.lon?.toString().replace(",", "."));
      if (isNaN(lat) || isNaN(lon)) return;

      let marker = window.placeMarkersById[id];

      // nếu chưa có thì tạo marker mới từ createMarker
      if (!marker && typeof createMarker === "function") {
        marker = createMarker(place, lat, lon);
        if (marker) {
          window.placeMarkersById[id] = marker;
        }
      }

      if (!marker) return;

      // Thêm marker vào các cluster đang dùng
      clusters.forEach(c => {
        if (c && c.addLayer) c.addLayer(marker);
      });

      // Đánh dấu visible
      if (typeof visibleMarkers !== "undefined" && visibleMarkers instanceof Set) {
        visibleMarkers.add(id);
      }
      window.visibleMarkers.add(id);

      const pos = marker.getLatLng && marker.getLatLng();
      if (pos) bounds.extend(pos);
    });

    // Fit map tới các quán trong lịch trình
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.25));
    }
  } catch (err) {
    console.error("❌ Lỗi khi showMarkersForPlaceIds:", err);
  }
};

// Thay thế alert() bằng showWarningToast()
function showWarningToast(message) {
  const toast = document.createElement('div');
  toast.className = 'warning-toast';
  toast.innerHTML = `
    <i class="fa-solid fa-triangle-exclamation"></i>
    <span>${message}</span>
  `;
  toast.style.cssText = `
    position: fixed;
    top: 100px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    color: white;
    padding: 15px 25px;
    border-radius: 12px;
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
    z-index: 10000;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: slideDown 0.3s ease;
  `;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideUp 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Thêm CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideDown {
    from { transform: translate(-50%, -100%); opacity: 0; }
    to { transform: translate(-50%, 0); opacity: 1; }
  }
  @keyframes slideUp {
    from { transform: translate(-50%, 0); opacity: 1; }
    to { transform: translate(-50%, -100%); opacity: 0; }
  }
`;
document.head.appendChild(style);
