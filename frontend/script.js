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
        </div>`)
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
          sidebar.classList.remove("show");

          // Nếu đang có route hiển thị, xóa luôn
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
      
      routeBtn.addEventListener("click", () => {
        if (!navigator.geolocation) {
          alert("Trình duyệt không hỗ trợ định vị!");
          return;
        }

        navigator.geolocation.getCurrentPosition(
  (pos) => {
    const userLat = pos.coords.latitude;
    const userLon = pos.coords.longitude;

    // 🧭 Thêm marker vị trí người dùng
    L.marker([userLat, userLon], {
      icon: L.icon({
        iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
        iconSize: [28, 28],
        iconAnchor: [14, 28],
      }),
    })
      .addTo(map)
      .bindPopup("📍 Vị trí của bạn")
      .openPopup();

    // 🔹 Xóa routeControl cũ nếu có
    if (routeControl) {
      map.removeControl(routeControl);
      routeControl = null;
    }

    // 🚗 Tạo route mới
    routeControl = L.Routing.control({
      waypoints: [
        L.latLng(userLat, userLon),
        L.latLng(lat, lon)
      ],
      lineOptions: {
        styles: [{ color: "blue", weight: 5, opacity: 0.7 }]
      },
      show: false,
      addWaypoints: false,
      routeWhileDragging: false,
      createMarker: (i, wp) => {
        return L.marker(wp.latLng, {
          icon: i === 0
            ? L.icon({
                iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
                iconSize: [24, 24],
                iconAnchor: [12, 24]
              })
            : L.icon({
                iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
                iconSize: [24, 24],
                iconAnchor: [12, 24]
              })
        });
      }
    }).addTo(map);


            // Khi tuyến được tìm thấy, hiển thị info và zoom
            routeControl.on("routesfound", (e) => {
              const route = e.routes[0];
              const bounds = L.latLngBounds(route.coordinates);
              map.fitBounds(bounds, { padding: [50, 50] });

              const distanceKm = (route.summary.totalDistance / 1000).toFixed(1); // km
              const durationMin = Math.ceil(route.summary.totalTime / 60); // phút

              let infoEl = tongquanTab.querySelector(".route-info");
              if (!infoEl) {
                infoEl = document.createElement("p");
                infoEl.className = "route-info";
                tongquanTab.appendChild(infoEl);
              }
              infoEl.innerHTML = `🛣️ Quãng đường: ${distanceKm} km<br>⏱️ Thời gian: ${durationMin} phút`;
            });
          },
          () => alert("Không thể lấy vị trí hiện tại!")
        );

      });
sidebar.classList.add("show");

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
// 📡 LẤY DỮ LIỆU CSV
// =========================
async function fetchPlaces(query = "") {
  try {
    const res = await fetch("/api/places");
    const data = await res.json();

    const filtered = query
      ? data.filter((p) => p.ten_quan && p.ten_quan.toLowerCase().includes(query.toLowerCase()))
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
// 📍 NÚT ĐỊNH VỊ GPS TRÊN GIAO DIỆN CHÍNH
// =========================
document.getElementById("locate-btn").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Trình duyệt của bạn không hỗ trợ định vị GPS!");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const userLat = pos.coords.latitude;
      const userLon = pos.coords.longitude;

      // 🔹 Thêm marker vị trí người dùng
      L.marker([userLat, userLon], {
        icon: L.icon({
          iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
          iconSize: [28, 28],
          iconAnchor: [14, 28],
        }),
      })
        .addTo(map)
        .bindPopup("📍 Vị trí của bạn")
        .openPopup();

      // 🔹 Zoom vào vị trí người dùng
      map.setView([userLat, userLon], 15);
    },
    (err) => {
      alert("Không thể lấy vị trí của bạn: " + err.message);
    }
  );
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
