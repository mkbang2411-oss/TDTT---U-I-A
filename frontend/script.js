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
  default: L.icon({
    iconUrl: "icons/default.png",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  }),
};

// =========================
// 🧠 XÁC ĐỊNH LOẠI QUÁN (đồng bộ với icons)
// =========================
function detectCategory(name = "") {
  name = name.toLowerCase();
  if (name.includes("phở") || name.includes("pho")) return "pho";
  if (name.includes("cà phê") || name.includes("coffee")) return "cafe";
  if (name.includes("trà sữa") || name.includes("milk tea") || name.includes("bubble tea")) return "tra_sua";
  if (name.includes("bún") || name.includes("bun bo") || name.includes("bò huế")) return "bun";
  if (name.includes("bánh mì") || name.includes("banh mi")) return "banh_mi";
  if (name.includes("bánh ngọt") || name.includes("banh ngot") || name.includes("cake") || name.includes("dessert")) return "banh_ngot";
  if (name.includes("mì cay") || name.includes("mi cay") || name.includes("spicy noodles") || name.includes("ramen")) return "my_cay";
  if (name.includes("cơm") || name.includes("com") || name.includes("rice")) return "com";
  if (name.includes("bánh kem") || name.includes("banh kem") || name.includes("cake") || name.includes("birthday cake")) return "banh_kem";
  return "default";
}

// =========================
// 💬 HIỂN THỊ REVIEW GIỐNG GOOGLE MAPS
// =========================
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
              <div class="review-time">${r.date || ""}</div>
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
        <p><i class="fa-regular fa-clock"></i> ${p.gio_mo_cua || "Không rõ"}</p>
        <p><i class="fa-solid fa-coins"></i> ${p.gia_trung_binh || "Không có"}</p>
      `;

      const thucdonHTML = `
  ${
    p.thuc_don
      ? p.thuc_don
          .split(/[;,]+/)
          .map(
            (img) =>
              `<img src="${img.trim()}" class="menu-img" alt="Thực đơn">`
          )
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

      // 🎯 Xử lý chuyển tab
      const tabs = sidebarContent.querySelectorAll(".tab-btn");
      const tabContents = sidebarContent.querySelectorAll(".tab-content");

      tabs.forEach((btn) => {
        btn.addEventListener("click", () => {
          tabs.forEach((b) => b.classList.remove("active"));
          tabContents.forEach((c) => c.classList.remove("active"));
          btn.classList.add("active");
          document
            .getElementById(`tab-${btn.dataset.tab}`)
            .classList.add("active");
        });
      });

      // 🎯 Xử lý gửi đánh giá
      // ⭐ Xử lý chọn sao + gửi đánh giá
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
  };

  if (!review.ten || !review.comment || review.rating === 0) {
    alert("Vui lòng nhập tên, nội dung và chọn số sao!");
    return;
  }

  await fetch(`/api/reviews/${place_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });

  alert("✅ Cảm ơn bạn đã gửi đánh giá!");
  marker.fire("click");
});
    });

    markers.push(marker);
  });

  const group = new L.featureGroup(markers);
  map.fitBounds(group.getBounds().pad(0.2));
}




// =========================
// 📡 GỌI API LẤY DỮ LIỆU CSV
// =========================
async function fetchPlaces(query = "") {
  try {
    const res = await fetch("/api/places");
    const data = await res.json();

    const filtered = query
      ? data.filter(
          (p) =>
            p.ten_quan &&
            p.ten_quan.toLowerCase().includes(query.toLowerCase())
        )
      : data;

    displayPlaces(filtered);
  } catch (err) {
    console.error("❌ Lỗi khi tải dữ liệu:", err);
    alert("Không thể tải dữ liệu từ server!");
  }
}

// =========================
// 🎯 TÌM KIẾM
// =========================
document.getElementById("btnSearch").addEventListener("click", () => {
  const query = document.getElementById("query").value.trim();
  fetchPlaces(query);
});

fetchPlaces();

// =========================
// 📍 GPS NGƯỜI DÙNG
// =========================
const locateBtn = document.getElementById("locate-btn");
let userMarker = null;
let accuracyCircle = null;

locateBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Trình duyệt của bạn không hỗ trợ định vị GPS!");
    return;
  }

  locateBtn.innerHTML = "⏳";
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const accuracy = pos.coords.accuracy;

      if (userMarker) map.removeLayer(userMarker);
      if (accuracyCircle) map.removeLayer(accuracyCircle);

      userMarker = L.marker([lat, lon], {
        icon: L.divIcon({
          className: "user-marker",
          html: '<div style="width:14px;height:14px;background:#0078ff;border-radius:50%;border:3px solid white;"></div>',
        }),
      }).addTo(map);

      accuracyCircle = L.circle([lat, lon], {
        radius: accuracy,
        color: "#0078ff",
        fillColor: "#0078ff",
        fillOpacity: 0.1,
      }).addTo(map);

      map.setView([lat, lon], 16, { animate: true });
      locateBtn.innerHTML = "📍";
    },
    (err) => {
      console.error("Lỗi GPS:", err);
      alert("Không thể lấy vị trí hiện tại!");
      locateBtn.innerHTML = "📍";
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

// =========================
// 🔒 ĐÓNG SIDEBAR
// =========================
document
  .getElementById("closeSidebar")
  .addEventListener("click", () => {
    document.getElementById("sidebar").classList.remove("show");
  });

// =====================
// 📸 Zoom ảnh thực đơn
// =====================
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("menu-img")) {
    const imgSrc = e.target.getAttribute("src");

    // Tạo overlay
    const overlay = document.createElement("div");
    overlay.classList.add("img-overlay");

    // Tạo ảnh phóng to
    const zoomedImg = document.createElement("img");
    zoomedImg.src = imgSrc;
    zoomedImg.classList.add("zoomed-img");

    // Đóng khi click ra ngoài ảnh
    overlay.addEventListener("click", () => {
      overlay.remove();
    });

    overlay.appendChild(zoomedImg);
    document.body.appendChild(overlay);
  }
});
