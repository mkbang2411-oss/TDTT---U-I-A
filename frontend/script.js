// =========================
// 🗺️ CẤU HÌNH MAP
// =========================
const map = L.map("map").setView([10.7769, 106.7009], 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
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
  }),
  cafe: L.icon({
    iconUrl: "icons/coffee.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  tra_sua: L.icon({
    iconUrl: "icons/tra_sua.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  bun: L.icon({
    iconUrl: "icons/bun.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  banh_mi: L.icon({
    iconUrl: "icons/banh_mi.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  banh_ngot: L.icon({
    iconUrl: "icons/banh_ngot.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  my_cay: L.icon({
    iconUrl: "icons/my_cay.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  com: L.icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/3174/3174880.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  banh_kem: L.icon({
    iconUrl: "icons/banh_kem.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
  
  kem: L.icon({
    iconUrl: "icons/kem.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),

  lau: L.icon({
    iconUrl: "icons/lau.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
    mi: L.icon({
    iconUrl: "icons/ramen.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }), 
  default: L.icon({
    iconUrl: "icons/default.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
};

// =========================
// 🧠 XÁC ĐỊNH LOẠI QUÁN
// =========================
function detectCategory(name = "") {
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




function renderReviews(googleReviews, userReviews) {
  const allReviews = [...googleReviews, ...userReviews];
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
              }%"></div>
            </div>
            <span>${starCount[i]}</span>
          </div>
        `
          )
          .join("")}
      </div>
    </div>

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
              r.avatar ||
              "https://cdn-icons-png.flaticon.com/512/847/847969.png"
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
// 🔍 HIỂN THỊ MARKER + THÔNG TIN CHI TIẾT
// =========================
function displayPlaces(places) {
  markers.forEach((m) => map.removeLayer(m));
  markers = [];

  if (!places || places.length === 0) {
    alert("Không tìm thấy quán nào!");
    return;
  }

  places.forEach((p) => {
    const lat = parseFloat(p.lat);
    const lon = parseFloat(p.lon);
    if (isNaN(lat) || isNaN(lon)) return;

    const category = detectCategory(p.ten_quan);
    const icon = icons[category] || icons.default;
    const marker = L.marker([lat, lon], { icon }).addTo(map);

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

      try {
        const res = await fetch(`/api/reviews/${place_id}`);
        if (res.ok) {
          const reviewData = await res.json();
          googleReviews = reviewData.google || [];
          userReviews = reviewData.user || [];
        }
      } catch (err) {
        console.error("❌ Lỗi khi tải review:", err);
      }

      const tongquanHTML = `
        <h2>${p.ten_quan || "Không tên"}</h2>
        ${
          p.hinh_anh
            ? `<img src="${p.hinh_anh}" style="width:100%;border-radius:10px;margin-bottom:10px;">`
            : ""
        }
        <p><i class="fa-solid fa-location-dot"></i> ${p.dia_chi || "Không rõ"}</p>
<p><i class="fa-solid fa-phone"></i> ${p.so_dien_thoai || "Không có"}</p>
<p><i class="fa-solid fa-star"></i> ${p.rating || "Chưa có"}</p>
<p><i class="fa-regular fa-clock"></i> ${getRealtimeStatus(p.gio_mo_cua)}</p>
<p><i class="fa-solid fa-coins"></i> ${p.gia_trung_binh || "Không có"}</p>
<p><i class="fa-solid fa-utensils"></i> ${p.khau_vi || "Không xác định"}</p>
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

      const danhgiaHTML = `
  <div class="review-section">
    ${renderReviews(googleReviews, userReviews)}

    <div class="review-form">
      <h3>📝 Thêm đánh giá của bạn</h3>
      <input type="text" id="reviewName" placeholder="Tên của bạn" />

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
  </div>
`;

      const contentHTML = `
  <div class="sidebar-header">
    <h2>Thông tin chi tiết</h2>
    <button id="closeSidebar" class="close-btn">×</button>
  </div>

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
      // NÚT ĐÓNG SIDEBAR
      const closeBtn = document.getElementById("closeSidebar");
      closeBtn.addEventListener("click", () => {
  sidebar.classList.add("hidden"); // 👉 Ẩn sidebar

  if (routeControl) {
    map.removeControl(routeControl);
    routeControl = null;
  }
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

        // 🔹 Nếu người dùng đã định vị GPS trước đó
        if (inputValue === "Vị trí hiện tại của tôi" && window.currentUserCoords) {
          const { lat: userLat, lon: userLon } = window.currentUserCoords;

          // Xóa route cũ nếu có
          if (routeControl) {
            map.removeControl(routeControl);
            routeControl = null;
          }

          drawRoute(userLat, userLon, lat, lon, tongquanTab);
          return;
        }

        // 🔹 Nếu người dùng nhập địa chỉ chữ → dùng geocode
        if (inputValue) {
          const coords = await geocodeAddress(inputValue);
          if (!coords) return;

          const userLat = coords.lat;
          const userLon = coords.lon;

          if (routeControl) {
            map.removeControl(routeControl);
            routeControl = null;
          }

          drawRoute(userLat, userLon, lat, lon, tongquanTab);
        } 
        else {
          // 🔹 Nếu không nhập gì và chưa có GPS
           alert("⚠️ Vui lòng nhập địa điểm hoặc bật định vị GPS trước khi tìm đường!");
        }
      });

sidebar.classList.remove("hidden"); // 👉 Hiện sidebar

      // =========================
      // ✓ NÚT CHỌN QUÁN CHO FOOD PLANNER
      // =========================
      if (window.foodPlannerState && 
          window.foodPlannerState.isEditMode && 
          window.foodPlannerState.isEditMode() && 
          window.foodPlannerState.isWaitingForPlaceSelection && 
          window.foodPlannerState.isWaitingForPlaceSelection()) {
        
        const selectPlaceBtn = document.createElement("button");
        selectPlaceBtn.textContent = "✓ Chọn quán này";
        selectPlaceBtn.className = "route-btn";
        selectPlaceBtn.style.marginTop = "10px";
        selectPlaceBtn.style.background = "linear-gradient(135deg, #4caf50 0%, #45a049 100%)";
        selectPlaceBtn.style.color = "white";
        selectPlaceBtn.style.border = "none";
        selectPlaceBtn.style.fontWeight = "600";
        tongquanTab.appendChild(selectPlaceBtn);
        
        selectPlaceBtn.addEventListener("click", () => {
          const placeData = {
            ten_quan: p.ten_quan,
            dia_chi: p.dia_chi,
            rating: p.rating || 0,
            lat: lat,
            lon: lon,
            data_id: p.data_id || p.ten_quan,
            hinh_anh: p.hinh_anh || '',
            gia_trung_binh: p.gia_trung_binh || '',
            khau_vi: p.khau_vi || ''
          };
          
          if (window.foodPlannerState.selectPlace && 
              window.foodPlannerState.selectPlace(placeData)) {
            sidebar.classList.remove("show");
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
              iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
              iconSize: [30, 30],
              iconAnchor: [15, 30],
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
    const bounds = L.latLngBounds(route.coordinates);
    map.fitBounds(bounds, { padding: [50, 50] });

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

      document.getElementById("submitReview").addEventListener("click", async () => {
       const review = {
  ten: document.getElementById("reviewName").value.trim(),
  rating: selectedRating,
  comment: document.getElementById("reviewComment").value.trim(),
  date: new Date().toLocaleString("sv-SE")
};



        if (!review.ten || !review.comment || review.rating === 0) {
          showToast("Vui lòng nhập tên, nội dung và chọn số sao!", "error");
          return;
        }

        await fetch(`/api/reviews/${place_id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(review),
        });
        showToast("✅ Cảm ơn bạn đã gửi đánh giá!", "success");
        marker.fire("click");
      });
    });

    markers.push(marker);
  });

  const group = new L.featureGroup(markers);
  map.fitBounds(group.getBounds().pad(0.2));
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
  if (!priceStr || priceStr.toLowerCase().includes("không")) return null;

  let cleaned = priceStr.toLowerCase().replace(/\s/g, ""); // bỏ khoảng trắng

  let multiplier = 1;

  // nếu có N / nghìn / k → nhân 1000
  if (/n|k|nghin/.test(cleaned)) multiplier = 1000;

  // loại bỏ chữ cái và dấu ₫
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
async function fetchPlaces(query = "", flavors = [], budget = "", radius = "") {
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
        return flavors.some(f => norm.includes(normalize(f)));
      });
    }

    // ========== 3️⃣ Lọc giá ==========
   if (budget !== "") {
  const [budgetMin, budgetMax] = budget.split("-").map(n => parseInt(n));

  filtered = filtered.filter((p) => {
    const range = parsePriceRange(p.gia_trung_binh);
    if (!range) return false;

    const [minP, maxP] = range;

    // ✅ Kiểm tra giao nhau giữa 2 khoảng
    return minP >= budgetMin && maxP <= budgetMax;
  });
}



// ========== 4️⃣ Lọc bán kính ==========
if (radius !== "") {
  const r = parseFloat(radius); // km

  if (!window.currentUserCoords || !window.currentUserCoords.lat || !window.currentUserCoords.lon) {
    alert("Vui lòng chọn vị trí xuất phát (GPS hoặc nhập địa chỉ) trước khi lọc bán kính!");
  } else {
    const userLat = parseFloat(window.currentUserCoords.lat);
    const userLon = parseFloat(window.currentUserCoords.lon);

    filtered = filtered.filter((p) => {
      if (!p.lat || !p.lon) return false;

      const plat = parseFloat(p.lat.toString().replace(",", "."));
      const plon = parseFloat(p.lon.toString().replace(",", "."));
      if (isNaN(plat) || isNaN(plon)) return false;

      const d = distance(userLat, userLon, plat, plon);

      // ==== 🔹 Debug khoảng cách từng quán ====
      if (d > r) {
        console.warn(`❌ ${p.ten_quan} cách ${d.toFixed(2)} km, vượt radius ${r} km`);
      } else {
        console.log(`✅ ${p.ten_quan} cách ${d.toFixed(2)} km, trong radius ${r} km`);
      }

      return d <= r; // lọc quán theo radius
    });
  }
}




    displayPlaces(filtered);
  } catch (err) {
    console.error("❌ Lỗi khi tải dữ liệu:", err);
    alert("Không thể tải dữ liệu từ server!");
  }
}

// =======================================================
// ✅ NÚT TÌM KIẾM
// =======================================================
document.getElementById("btnSearch").addEventListener("click", () => {
  const query = document.getElementById("query").value.trim();

  const selectedFlavors = Array.from(
    document.querySelectorAll("#flavorDropdown input:checked")
  ).map(c => c.value);

  const budget = document.getElementById("budget").value;
  const radius = document.getElementById("radius").value;

  fetchPlaces(query, selectedFlavors, budget, radius);
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
fetchPlaces();

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
      fetchPlaces(p.ten_quan);
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
// ↩ NÚT ENTER: tìm theo địa điểm người nhập
// =========================
document.getElementById("gpsEnterBtn").addEventListener("click", async () => {
  const input = document.getElementById("gpsInput").value.trim();
  if (!input) {
    alert("Vui lòng nhập địa điểm!");
    return;
  }

  const coords = await geocodeAddress(input);
  if (coords) {

    if (window.startMarker) {
      map.removeLayer(window.startMarker);
    }

     window.startMarker = L.marker([coords.lat, coords.lon], {
      icon: L.icon({
        iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
        iconSize: [30, 30],
        iconAnchor: [15, 30],
      }),
    })
      .addTo(map)
      .bindPopup(`📍 ${input}`)
      .openPopup();
    //lưu địa điểm xuất phát mới cho an toàn
    window.currentUserCoords = { lat: coords.lat, lon: coords.lon };

    map.setView([coords.lat, coords.lon], 15);
  }
});

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
          iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
          iconSize: [30, 30],
          iconAnchor: [15, 30],
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

// =========================
// 👁️‍🗨️ NÚT ẨN / HIỆN ĐƯỜNG ĐI
// =========================
const gpsHideRouteBtn = document.getElementById("gpsHideRouteBtn");

let hiddenRoute = null; // lưu tuyến đường bị ẩn

gpsHideRouteBtn.addEventListener("click", () => {
  if (routeControl) {
    hiddenRoute = routeControl;
    map.removeControl(routeControl);
    routeControl = null;
    showToast("👁️‍🗨️ Đã ẩn đường đi", "success");
  } 
  else if (hiddenRoute) {
    hiddenRoute.addTo(map);
    routeControl = hiddenRoute;
    hiddenRoute = null;
    showToast("✅ Đã hiện lại đường đi", "success");
  } 
  else {
    showToast("⚠️ Chưa có tuyến đường nào để ẩn/hiện!", "error");
  }
});