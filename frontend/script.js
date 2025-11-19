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

let markers = [];
let currentRouteLine = null;
let routeControl = null;

// =========================
// 🍴 ICON TƯƠNG ỨNG LOẠI QUÁN
// =========================
const icons = {
  pho: L.icon({
    iconUrl: "icons/pho.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  cafe: L.icon({
    iconUrl: "icons/coffee.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  tra_sua: L.icon({
    iconUrl: "icons/tra_sua.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  bun: L.icon({
    iconUrl: "icons/bun.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  banh_mi: L.icon({
    iconUrl: "icons/banh_mi.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  banh_ngot: L.icon({
    iconUrl: "icons/banh_ngot.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  my_cay: L.icon({
    iconUrl: "icons/my_cay.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  com: L.icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/3174/3174880.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  banh_kem: L.icon({
    iconUrl: "icons/banh_kem.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  
  kem: L.icon({
    iconUrl: "icons/kem.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),

  lau: L.icon({
    iconUrl: "icons/lau.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
    mi: L.icon({
    iconUrl: "icons/ramen.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }), 
  khu_am_thuc: L.icon({
  iconUrl: "icons/street_food.png", // 👉 Bạn đặt file này trong thư mục /icons
  iconSize: [26, 26],
  iconAnchor: [13, 26],
  className: 'fixed-size-icon'  
  }),
  default: L.icon({
    iconUrl: "icons/default.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    className: 'fixed-size-icon'  
  }),
  michelin: L.icon({
  iconUrl: "icons/star.png", // đặt file PNG vào thư mục /icons
  iconSize: [26, 26],
  iconAnchor: [13, 26],
  className: 'fixed-size-icon'  
}),
};

// =========================
// 🧠 XÁC ĐỊNH LOẠI QUÁN
// =========================
function detectCategory(name = "") 
{
  name = name.toLowerCase();

  // 🥣 Phở
  if (name.includes("phở") || name.includes("pho")) return "pho";

  // ☕ Cà phê
  if (name.includes("cà phê") || name.includes("coffee")) return "cafe";

  // 🧋 Trà sữa
  if (name.includes("trà sữa") || name.includes("milktea") ||name.includes("milk tea") || name.includes("bubble tea")) return "tra_sua";

  // 🍜 Bún / Bún bò
  if (name.includes("bún") || name.includes("bun bo") || name.includes("bò huế")) return "bun";

  // 🥖 Bánh mì
  if (name.includes("bánh mì") || name.includes("banh mi")) return "banh_mi";

  // 🍰 Bánh ngọt / Bakery / Dessert
  if (
    name.includes("bánh ngọt") ||
    name.includes("banh ngot") ||
    name.includes("cake") ||
    name.includes("tiệm bánh") ||
    name.includes("dessert") ||
    name.includes("bakery")
  )
    return "banh_ngot";

  // 🍜 Mì cay
  if (
    name.includes("mì cay") ||
    name.includes("mi cay") ||
    name.includes("spicy noodles") ||
    name.includes("ramen")
  )
    return "my_cay";

  // 🍚 Cơm
  if (name.includes("cơm") || name.includes("com") || name.includes("rice")) return "com";

  // 🎂 Bánh kem / Cake sinh nhật
  if (
    name.includes("bánh kem") ||
    name.includes("banh kem") ||
    name.includes("birthday cake")
  )
    return "banh_kem";

  // 🍦 Kem
  if (
    name.includes("kem") ||
    name.includes("ice cream") ||
    name.includes("gelato") ||
    name.includes("snow ice") ||
    name.includes("frozen")
  )
    return "kem";

  // 🔥 Lẩu
  if (
    name.includes("lẩu") ||
    name.includes("lau") ||
    name.includes("hotpot") ||
    name.includes("hot pot") ||
    name.includes("thái") ||
    name.includes("suki")
  )
    return "lau";

  // 🍜 Mì (chung)
  if (
    (name.includes("mì") || name.includes("my") || name.includes("mỳ")) &&
    !name.includes("cay") // tránh trùng với "mì cay"
  )
    return "mi";

  // ⚙️ Mặc định
  return "default";
}




// =========================
// 💬 HIỂN THỊ REVIEW GIỐNG GOOGLE MAPS
// =========================
function timeAgo(dateString) 
{
  if (!dateString) return "";

  // Nếu là chuỗi kiểu "2 weeks ago" của Google thì giữ nguyên
  if (isNaN(Date.parse(dateString)) && isNaN(Number(dateString))) 
  {
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
function getCookie(name) 
{
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') 
  {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) 
    {
      const cookie = cookies[i].trim();
      // Kiểm tra xem cookie có bắt đầu bằng tên chúng ta muốn không
      if (cookie.substring(0, name.length + 1) === (name + '=')) 
      {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function renderReviewSummary(googleReviews, userReviews) 
{
  const allReviews = [...userReviews,...googleReviews ];
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
        <div class="review-stars">${"⭐".repeat(Math.round(avgRating) || 0)}</div>
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
              <div class="review-time">${formatDate(r.date) || timeAgo(r.relative_time_description)}</div>
            </div>
          </div>
          <div class="review-text">${r.comment || ""}</div>
        </div>`)
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

  // Tìm các elements của chatbox
  const chatWindow = document.getElementById("chatWindow");
  const chatbotBtn = document.getElementById("chatbotBtn");
  const speechBubble = document.getElementById("speechBubble");

  if (!chatWindow || !chatbotBtn) {
    console.error("❌ Không tìm thấy chatbox elements!");
    alert("🤖 Bạn có thể thử hỏi chatbot UIAboss để tìm món ăn phù hợp hơn nhé!");
    return;
  }

  // ✅ Mở chatbox (giống logic openChatWindow trong chatbot)
  chatWindow.style.display = "flex";
  chatWindow.classList.add("open");
  chatbotBtn.style.display = "none";
  chatbotBtn.classList.add("hidden");
  speechBubble.style.display = "none";
  speechBubble.classList.add("hidden");

  // ✅ Tự động gửi tin nhắn gợi ý
  setTimeout(() => {
    const messagesArea = document.getElementById("messagesArea");
    if (messagesArea) {
      // Thêm tin nhắn bot
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

      // Focus vào input để user nhập liền
      const messageInput = document.getElementById("messageInput");
      if (messageInput) {
        messageInput.focus();
      }
    }
  }, 500);
}

// =========================
// 🔍 HIỂN THỊ MARKER + THÔNG TIN CHI TIẾT
// =========================
function displayPlaces(places, shouldZoom = true) {
  markers.forEach((m) => map.removeLayer(m));
  markers = [];

  if (!places || places.length === 0) {
    alert("Không tìm thấy quán nào!");
    return false;
}

  places.forEach((p) => {
    const lat = parseFloat(p.lat);
    const lon = parseFloat(p.lon);
    if (isNaN(lat) || isNaN(lon)) return;

    let icon;

if (p.mo_ta && p.mo_ta.toLowerCase().includes("michelin")) {
    icon = icons.michelin; // ⭐ ICON RIÊNG MICHELIN
}
else if (p.mo_ta && p.mo_ta.toLowerCase().includes("khu ẩm thực")) {
    icon = icons.khu_am_thuc;
}
else {
    const category = detectCategory(p.ten_quan);
    icon = icons[category] || icons.default;
}

    const marker = L.marker([lat, lon], { icon }).addTo(map);

    if (p.mo_ta && p.mo_ta.toLowerCase().includes("michelin")) {
    marker._icon.classList.add("michelin-glow");
    }

      // 🟢 TOOLTIP khi rê chuột vào marker
  const tooltipHTML = `
    <div style="text-align:center;min-width:180px;">
      <strong>${p.ten_quan || "Không tên"}</strong><br>
      ${
        p.hinh_anh
          ? `<img src="${p.hinh_anh}" style="width:100px;height:70px;object-fit:cover;border-radius:6px;margin-top:4px;">`
          : ""
      }
      <div style="font-size:13px;margin-top:4px;">
        <i class="fa-regular fa-clock"></i> ${p.gio_mo_cua || "Không rõ"}<br>
        <i class="fa-solid fa-coins"></i> ${p.gia_trung_binh || "Không có"}
      </div>
    </div>
  `;

  // Gắn tooltip vào marker
  marker.bindTooltip(tooltipHTML, {
    direction: "top",   // vị trí tooltip
    offset: [0, -10],   // đẩy tooltip lên một chút
    opacity: 0.95,
    sticky: true,       // theo chuột
    className: "custom-tooltip" // dùng để CSS đẹp hơn
  });

    marker.on("click", async () => {
      map.setView([lat, lon], 17, { animate: true });
      const sidebar = document.getElementById("sidebar");
      const sidebarContent = document.getElementById("sidebar-content");
    
      const place_id = p.data_id || p.ten_quan;
      let googleReviews = [];
      let userReviews = [];
      let currentUser = null; // Biến lưu thông tin user

      try {
        const res = await fetch(`http://127.0.0.1:8000/api/reviews/${place_id}`, {
            credentials: 'include' //gửi cookie đăng nhập
        });
        
        if (res.ok) {
          const responseData = await res.json();
          
          const reviewData = responseData.reviews; // Lấy object reviews
          currentUser = responseData.user;       // Lấy object user
          
          googleReviews = reviewData.google || [];
          userReviews = reviewData.user || [];
        }
      } catch (err) {
        console.error("❌ Lỗi khi tải review:", err);
      }

      const tongquanHTML = `
  <div class="place-header" style="display:flex;align-items:center;justify-content:space-between;">
    <h2 style="margin:0;">${p.ten_quan || "Không tên"}</h2>
    <!-- ❤️ Nút yêu thích bên phải tên -->
    <button id="favoriteBtn" class="action-btn" style="padding:8px 10px;min-width:auto;border:none;background:none;">
      <i class="fa-regular fa-heart" style="font-size:22px;"></i>
    </button>
  </div>

  ${
    p.hinh_anh
      ? `<img src="${p.hinh_anh}" style="width:100%;border-radius:10px;margin:10px 0;">`
      : ""
  }

  ${p.mo_ta && p.mo_ta.toLowerCase().includes("khu ẩm thực")
    ? `<p style="color:#ff6600;font-weight:bold;">🔥 Đây là khu ẩm thực sầm uất, có nhiều món ăn và hoạt động về đêm.</p>`
    : ""}

  <p><i class="fa-solid fa-location-dot"></i> ${p.dia_chi || "Không rõ"}</p>
  <p><i class="fa-solid fa-phone"></i> ${p.so_dien_thoai || "Không có"}</p>
  <p><i class="fa-solid fa-star"></i> ${p.rating || "Chưa có"}</p>
  <p><i class="fa-regular fa-clock"></i> ${p.gio_mo_cua || "Không rõ"}</p>
  <p><i class="fa-solid fa-coins"></i> ${p.gia_trung_binh || "Không có"}</p>
  <p><i class="fa-solid fa-utensils"></i> ${p.khau_vi || "Không xác định"}</p>

    <!-- 🔖 Nút lưu quán (đang ẩn bằng CSS) -->
  <div style="margin-top:10px;display:flex;justify-content:center;">
    <button id="saveBtn" class="action-btn" style="display:none;">
      <i class="fa-regular fa-bookmark"></i>
      <span>Lưu quán</span>
    </button>
  </div>
`;




      const thucdonHTML = `
  ${
    p.thuc_don
      ? p.thuc_don
          .split(/[;,]+/)
          .map((img) => `<img src="${img.trim()}" class="menu-img" alt="Thực đơn">`)
          .join("")
      : "<p>Không có hình thực đơn.</p>"
  }
`;

      let reviewFormHTML = "";
      // Nếu user TỒN TẠI và ĐÃ ĐĂNG NHẬP
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
      } 
      // Nếu CHƯA ĐĂNG NHẬP
      else {
          reviewFormHTML = `
            <div class="review-form">
              <h3>📝 Thêm đánh giá của bạn</h3>
              <p>Vui lòng <a href="http://127.0.0.1:8000/accounts/login/" target="_blank">đăng nhập</a> để gửi đánh giá.</p>
            </div>
          `;
      }

      // Nó sẽ tự động dùng reviewFormHTML vừa tạo
      const danhgiaHTML = `
        <div class="review-section">
          ${renderReviewSummary(googleReviews, userReviews)} 
          ${reviewFormHTML}
          ${renderReviewList(googleReviews, userReviews)}
        </div>
      `;

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
// ✅ Cập nhật tiêu đề header (không tạo lại header)
document.getElementById('sidebar-title').textContent = "Thông tin chi tiết";


      // 👉 Sau khi render xong, gắn sự kiện cho nút
const favoriteBtn = document.getElementById("favoriteBtn");
const saveBtn = document.getElementById("saveBtn");

let clickCount = 0; // Đếm số lần click để xử lý chẵn/lẻ

favoriteBtn.addEventListener("click", () => {
  clickCount++;
  if (clickCount % 2 === 1) {
    favoriteBtn.classList.add("active");
    favoriteBtn.querySelector("i").classList.replace("fa-regular", "fa-solid");
  } else {
    favoriteBtn.classList.remove("active");
    favoriteBtn.querySelector("i").classList.replace("fa-solid", "fa-regular");
  }
});

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
      // NÚT ĐÓNG SIDEBAR
      const closeBtn = document.getElementById("closeSidebar");
      closeBtn.addEventListener("click", () => {
  sidebar.classList.remove("show"); // 👉 Ẩn sidebar
});

      // =========================
      // 🚗 NÚT TÌM ĐƯỜNG ĐI
      // =========================
      const tongquanTab = sidebarContent.querySelector("#tab-tongquan");
      const routeBtn = document.createElement("button");
      routeBtn.textContent = "📍 Tìm đường đi";
      routeBtn.className = "route-btn";
      tongquanTab.appendChild(routeBtn);
      
      routeBtn.addEventListener("click", async () => {
        const gpsInput = document.getElementById("gpsInput");
        const inputValue = gpsInput ? gpsInput.value.trim() : "";

        // ✅ Nếu đang chỉ đường cho cùng quán này → XÓA ĐƯỜNG (toggle off)
        if (routeControl && currentPlaceId === place_id) {
          map.removeControl(routeControl);
          routeControl = null;
          currentPlaceId = null;

          // ✅ XÓA THÔNG TIN QUÃNG ĐƯỜNG
          const infoEl = tongquanTab.querySelector(".route-info");
          if (infoEl) {
            infoEl.remove();
          }
          
          return; // Dừng lại, không vẽ lại
        }

        // ✅ Nếu có đường cũ (dù quán nào) → XÓA trước khi vẽ mới
        if (routeControl) {
          map.removeControl(routeControl);
          routeControl = null;
          currentPlaceId = null;
        }

        // 🔹 Kiểm tra xem có vị trí xuất phát không
        if (!inputValue && !window.currentUserCoords) {
          alert("⚠️ Vui lòng nhập địa điểm hoặc bật định vị GPS trước khi tìm đường!");
          return;
        }

        let userLat, userLon;

        // 🔹 Nếu người dùng đã định vị GPS trước đó
        if (inputValue === "Vị trí hiện tại của tôi" && window.currentUserCoords) {
          userLat = window.currentUserCoords.lat;
          userLon = window.currentUserCoords.lon;
        } 
        // 🔹 Nếu người dùng nhập địa chỉ chữ → dùng geocode
        else if (inputValue) {
          const coords = await geocodeAddress(inputValue);
          if (!coords) return;
          userLat = coords.lat;
          userLon = coords.lon;
        }
        // 🔹 Nếu không nhập gì nhưng có GPS đã lưu
        else if (window.currentUserCoords) {
          userLat = window.currentUserCoords.lat;
          userLon = window.currentUserCoords.lon;
        }
        else {
          alert("⚠️ Vui lòng nhập địa điểm hoặc bật định vị GPS trước khi tìm đường!");
          return;
        }

        // ✅ Vẽ đường mới
        drawRoute(userLat, userLon, lat, lon, tongquanTab);
        currentPlaceId = place_id; // Lưu ID quán hiện tại
      });

      // Khi mở quán mới → luôn xóa route cũ để tránh tự zoom lỗi
if (routeControl) {
  map.removeControl(routeControl);
  routeControl = null;
  currentPlaceId = null;
}


sidebar.classList.remove("hidden"); // 👉 Hiện sidebar

        // =========================
        // ✓ NÚT CHỌN QUÁN CHO FOOD PLANNER
        // =========================
        if (window.foodPlannerState && 
            typeof window.foodPlannerState.isWaitingForPlaceSelection === 'function' &&
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
            hinh_anh: p.hinh_anh || '',
            gia_trung_binh: p.gia_trung_binh || '',
            khau_vi: p.khau_vi || ''
          };
          
          console.log("Chon quan:", placeData.ten_quan);
          
          if (typeof window.foodPlannerState.selectPlace === 'function') {
            const success = window.foodPlannerState.selectPlace(placeData);
            if (success) {
              sidebar.classList.remove("show");
              alert("Da chon quan: " + placeData.ten_quan);
            } else {
              alert("Khong the chon quan. Vui long thu lai!");
            }
          }
        });
      }

function drawRoute(userLat, userLon, destLat, destLon, tongquanTab) {
  routeControl = L.Routing.control({
    waypoints: [L.latLng(userLat, userLon), L.latLng(destLat, destLon)],
    lineOptions: {
      styles: [
        { color: "white", weight: 5, opacity: 1 },     // viền trắng ngoài cho nổi bật
        { color: "#34A853", weight: 6, opacity: 1 }    // xanh lá chuẩn Google Maps
      ],
    },
    show: false,
    addWaypoints: false,
    routeWhileDragging: false,
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

// Nếu route hợp lệ mới fitBounds
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


// Gắn sự kiện sau khi phần tử đã render vào DOM
setTimeout(() => {
  const closeBtn = document.getElementById("closeSidebar");
  if (closeBtn) {
    closeBtn.onclick = () => {
      sidebar.classList.remove("show");
    };
  }
}, 0);

      // 🎯 Chuyển tab
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

      // ⭐ Gửi đánh giá
      let selectedRating = 0;
      document.querySelectorAll("#starRating .star").forEach((star) => {
        star.addEventListener("click", () => {
          selectedRating = parseInt(star.dataset.value);
          document.querySelectorAll("#starRating .star").forEach((s, i) => {
            s.classList.toggle("active", i < selectedRating);
          });
        });
      });

      document.getElementById("submitReview").addEventListener("click", async () => 
      {
        // 1. Chỉ lấy rating và comment
        const review = 
        {
          rating: selectedRating,
          comment: document.getElementById("reviewComment").value.trim(),
        };

        // 2. Cập nhật validation (bỏ 'ten')
        if (!review.comment || review.rating === 0) 
        {
          // (Giả sử bạn có hàm showToast, nếu không thì dùng alert)
           alert("Vui lòng nhập nội dung và chọn số sao!");
          // showToast("Vui lòng nhập nội dung và chọn số sao!", "error");
          return;
        }
        
        try {
          // 3. Gọi API Django (port 8000) với CSRF và credentials
          const response = await fetch(`http://127.0.0.1:8000/api/reviews/${place_id}`, {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie('csrftoken') // Lấy token từ hàm helper
            },
            body: JSON.stringify(review), // Chỉ gửi rating và comment
            credentials: 'include' // RẤT QUAN TRỌNG: để gửi cookie đăng nhập
          });

          const result = await response.json();

          if (response.ok && result.success) 
          {
            // showToast(result.message || "✅ Cảm ơn bạn đã gửi đánh giá!", "success");
            alert(result.message || "✅ Cảm ơn bạn đã gửi đánh giá!");
            
            // Tải lại sidebar để xem review mới
            marker.fire("click"); 

          } else {
            // Báo lỗi nếu API trả về lỗi (vd: chưa đăng nhập, lỗi 403)
            // showToast(result.message || "Lỗi khi gửi đánh giá. Bạn đã đăng nhập chưa?", "error");
            alert(result.message || "Lỗi khi gửi đánh giá. Bạn đã đăng nhập chưa?");
          }

        } catch (err) {
          console.error("Lỗi fetch API:", err);
          // showToast("Lỗi kết nối. Không thể gửi đánh giá.", "error");
          alert("Lỗi kết nối. Không thể gửi đánh giá.");
        }
      });
    });

    markers.push(marker);
  });

  // ✅ Chỉ zoom đến quán nếu shouldZoom = true
  if (shouldZoom && markers.length > 0) {
    const group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.2));
  }
  return true;
}

// =========================
// 📡 LẤY DỮ LIỆU CSV
// =========================
// =========================
// 📡 LẤY DỮ LIỆU CSV + LỌC THEO KHẨU VỊ
// =========================
// =========================
// 📡 LẤY DỮ LIỆU CSV + TÌM GẦN ĐÚNG (FUZZY SEARCH)
// =========================
// =========================
// 📡 LẤY DỮ LIỆU CSV + TÌM GẦN ĐÚNG (FUZZY SEARCH, BỎ DẤU)
// =========================
// =======================================================
// ✅ HÀM TÁCH GIÁ
// =======================================================
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

    if (s.includes("triệu") || s.includes("million"))
      value *= 1000000;

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

  if (isNaN(plat1) || isNaN(plon1) || isNaN(plat2) || isNaN(plon2)) return Infinity;

  const dLat = (plat2 - plat1) * Math.PI / 180;
  const dLon = (plon2 - plon1) * Math.PI / 180;

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(plat1 * Math.PI / 180) *
    Math.cos(plat2 * Math.PI / 180) *
    Math.sin(dLon / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // km
}


// =======================================================
// ✅ FETCH + LỌC DỮ LIỆU
// =======================================================
async function fetchPlaces(
  query = "",
  flavors = [],
  budget = "",
  radius = "",
  shouldZoom = true
) {
  try {
    const res = await fetch("/api/places");
    let data = await res.json();

    function normalize(str) {
      return str
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase()
        .trim();
    }

    let filtered = data;

    // ========== 1️⃣ Fuzzy Search ==========
    if (query) {
      let normalizedQuery = normalize(query);

      // chia chữ nếu user gõ liền "bundaubac..."
      if (!normalizedQuery.includes(" ")) {
        const possibleMatches = data.map((p) => normalize(p.ten_quan || ""));
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

      // Fuzzy engine
      const fuse = new Fuse(
        data.map((p) => ({ ...p, ten_quan_no_dau: normalize(p.ten_quan || "") })),
        { keys: ["ten_quan_no_dau"], threshold: 0.4, ignoreLocation: true }
      );

      const fuzzyResults = fuse.search(normalizedQuery).map((r) => r.item);

      const queryWords = normalizedQuery.split(" ").filter(Boolean);
      const normalizedPhrase = normalizedQuery.trim();

      filtered = fuzzyResults.filter((p) => {
        const name = normalize(p.ten_quan || "");
        const phraseRegex = new RegExp(`\\b${normalizedPhrase}\\b`, "i");
        const hasFullPhrase = phraseRegex.test(name);

        const hasWordMatch = queryWords.some((w) => {
          const wordRegex = new RegExp(`\\b${w}\\b`, "i");
          return wordRegex.test(name);
        });

        return queryWords.length >= 2 ? hasFullPhrase : hasFullPhrase || hasWordMatch;
      });
    }

    // ========== 2️⃣ Lọc khẩu vị ==========
    if (flavors.length > 0) {
      filtered = filtered.filter((p) => {
        if (!p.khau_vi) return false;
        const norm = normalize(p.khau_vi);
        return flavors.some((f) => norm.includes(normalize(f)));
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

        // ⭐ TH1: "300.000 trở lên"
        if (budgetMax === Infinity) {
          return minP >= budgetMinNum;
        }

        // ⭐ TH2: khoảng giá bình thường → chỉ cần giao nhau
        return minP >= budgetMinNum && maxP <= budgetMax;
      });
    }

    // ========== 4️⃣ Lọc bán kính ==========
    if (radius !== "") {
      const r = parseFloat(radius); // km

      if (
        !window.currentUserCoords ||
        !window.currentUserCoords.lat ||
        !window.currentUserCoords.lon
      ) {
        alert(
          "Vui lòng chọn vị trí xuất phát (GPS hoặc nhập địa chỉ) trước khi lọc bán kính!"
        );
        // không filter theo radius nữa, dùng filtered hiện tại
      } else {
        const userLat = parseFloat(window.currentUserCoords.lat);
        const userLon = parseFloat(window.currentUserCoords.lon);

        filtered = filtered.filter((p) => {
          if (!p.lat || !p.lon) return false;

          const plat = parseFloat(p.lat.toString().replace(",", "."));
          const plon = parseFloat(p.lon.toString().replace(",", "."));
          if (isNaN(plat) || isNaN(plon)) return false;

          const d = distance(userLat, userLon, plat, plon);

          // Debug tuỳ bạn cần hay không
          // if (d > r) {
          //   console.warn(`❌ ${p.ten_quan} cách ${d.toFixed(2)} km, vượt radius ${r} km`);
          // } else {
          //   console.log(`✅ ${p.ten_quan} cách ${d.toFixed(2)} km, trong radius ${r} km`);
          // }

          return d <= r;
        });
      }
    }

    // 🟢 Quan trọng: trả về true/false từ displayPlaces
    const ok = displayPlaces(filtered, shouldZoom);
    return ok; // <-- để btnSearch biết là có quán hay không
  } catch (err) {
    console.error("❌ Lỗi khi tải dữ liệu:", err);
    alert("Không thể tải dữ liệu từ server!");
    return false; // xem như thất bại
  }
}

let notFoundCount = 0;
// =============================
// 🔍 NÚT TÌM KIẾM
// =============================
document.getElementById("btnSearch").addEventListener("click", async () => {
  const gpsInputValue = document.getElementById("gpsInput").value.trim();
  const query = document.getElementById("query").value.trim();

  const selectedFlavors = Array.from(
    document.querySelectorAll("#flavorDropdown input:checked")
  ).map((c) => c.value);

  const budget = document.getElementById("budget").value;
  const radius = document.getElementById("radius").value;

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
    })
      .addTo(map)
      .bindPopup(`📍 ${gpsInputValue}`)
      .openPopup();

    window.currentUserCoords = { lat: coords.lat, lon: coords.lon };

    map.setView([coords.lat, coords.lon], 15);

    // Có filter → mới tìm quán
    if (query || selectedFlavors.length > 0 || budget || radius) {
      result = await fetchPlaces(query, selectedFlavors, budget, radius, false);
    }
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
checkboxes.forEach(cb => {
  cb.addEventListener("change", () => {
    const selected = Array.from(checkboxes)
      .filter(c => c.checked)
      .map(c => c.value);

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
fetchPlaces("", [], "", "", false); // shouldZoom 

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
document.addEventListener('DOMContentLoaded', function() {
    const radiusInput = document.getElementById('radius');
    
    if (radiusInput) {
        // Lưu giá trị ban đầu
        window.currentRadius = radiusInput.value;
        console.log('✅ Khởi tạo bán kính:', window.currentRadius, 'km');
        
        // Cập nhật khi thay đổi
        radiusInput.addEventListener('change', function() {
            window.currentRadius = this.value;
            console.log('🎯 Đã cập nhật bán kính:', window.currentRadius, 'km');
        });
    } else {
        console.error('⚠️ Không tìm thấy input #radius');
    }
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
  suggestionsEl.innerHTML = ""; // clear

  if (text.length === 0) {
    suggestionsEl.classList.remove("show");
    return;
  }

  // lọc, giới hạn 8 kết quả
  const filtered = allPlacesCache
    .filter((p) => p.ten_quan && p.ten_quan.toLowerCase().includes(text))
    .slice(0, 8);

  if (filtered.length === 0) {
    suggestionsEl.classList.remove("show");
    return;
  }

  // tạo các div gợi ý (tương thích với CSS .suggestions)
  filtered.forEach((p) => {
    const div = document.createElement("div");
    const cat = detectCategory(p.ten_quan);
    const iconUrl = icons[cat] ? icons[cat].options.iconUrl : icons.default.options.iconUrl;

    // highlight từ khóa trong tên (ví dụ: "phở" -> <b>phở</b>)
    const name = p.ten_quan;
    const idx = name.toLowerCase().indexOf(text);
    let displayName = name;
    if (idx >= 0) {
      displayName = `${name.slice(0, idx)}<strong>${name.slice(idx, idx + text.length)}</strong>${name.slice(idx + text.length)}`;
    }

    div.innerHTML = `<img src="${iconUrl}" style="width:20px;height:20px;margin-right:8px;object-fit:contain;"> <div style="flex:1">${displayName}</div>`;
    div.addEventListener("click", () => {
      input.value = p.ten_quan;
      suggestionsEl.classList.remove("show");
     fetchPlaces(p.ten_quan, [], "", "", true); 
    });
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
// ✅ Xử lý đóng sidebar (luôn hoạt động, dù sidebarContent bị thay đổi)
document.addEventListener("click", (e) => {
  if (e.target && e.target.id === "closeSidebar") {
    document.getElementById("sidebar").classList.remove("show");
  }
});

// =========================
// 🖼️ CLICK ẢNH -> PHÓNG TO
// =========================
document.addEventListener("click", (e) => {
  if (e.target.tagName === "IMG" && e.target.closest(".tab-content")) {
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
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
  try {
    const res = await fetch(url);
    const data = await res.json();

    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
      };
    }

    alert("❌ Không tìm thấy địa điểm này!");
    return null;
  } catch (err) {
    console.error("Lỗi khi geocode:", err);
    alert("❌ Lỗi khi tìm địa điểm!");
    return null;
  }
}

// =========================
// 📍 NÚT GPS: tự động định vị bản thân
// =========================
document.getElementById("gpsLocateBtn").addEventListener("click", async () => {
  if (!navigator.geolocation) {
    alert("Trình duyệt không hỗ trợ định vị GPS!");
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
      })
        .addTo(map)
        .bindPopup("📍 Bạn đang ở đây (tọa độ thật)")
        .openPopup();

      map.setView([userLat, userLon], 15);
    },
    (err) => {
      alert("Không thể lấy vị trí của bạn: " + err.message);
    }
  );
});

// =========================
// ⌨️ ENTER chỉ hoạt động khi người dùng đang tương tác với ô nhập địa điểm
// =========================
let isUsingGpsInput = false;

// Khi người dùng click hoặc gõ trong ô nhập
const gpsInput = document.getElementById("gpsInput");
gpsInput.addEventListener("focus", () => (isUsingGpsInput = true));
gpsInput.addEventListener("input", () => (isUsingGpsInput = true));

// Khi người dùng click ra ngoài map hoặc sidebar → tắt chế độ nhập
document.addEventListener("click", (e) => {
  const gpsBox = document.querySelector(".gps-box");
  if (!gpsBox.contains(e.target)) {
    isUsingGpsInput = false;
  }
});

// Khi nhấn Enter → chỉ hoạt động nếu đang trong chế độ nhập
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && isUsingGpsInput) {
    e.preventDefault();
    document.getElementById("gpsEnterBtn").click(); // Giả lập click nút ↩
  }
});

