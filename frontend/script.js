// =========================
// 🗺️ CẤU HÌNH MAP
// =========================
const map = L.map('map').setView([10.7769, 106.7009], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

let markers = [];

// =========================
// 🍴 BỘ SƯU TẬP ICON THEO LOẠI QUÁN
// =========================
const icons = {
  pho: L.icon({
    iconUrl: "icons/pho.png", // tô phở
     iconSize: [26, 26],     
    iconAnchor: [13, 26],   
    popupAnchor: [0, -25]   
  }),
  cafe: L.icon({
    iconUrl: "icons/coffee.png", // tách cà phê
     iconSize: [26, 26],     
    iconAnchor: [13, 26],   
    popupAnchor: [0, -25]   
  }),
  tra_sua: L.icon({
    iconUrl: "icons/tra_sua.png", // ly trà sữa
     iconSize: [26, 26],     
    iconAnchor: [13, 26],   
    popupAnchor: [0, -25]   
  }),
  bun: L.icon({
    iconUrl: "icons/pho.png", // tô bún
     iconSize: [26, 26],    
    iconAnchor: [13, 26],   
    popupAnchor: [0, -25]   
  }),
  com: L.icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/3174/3174880.png", // chén cơm
     iconSize: [26, 26],    
    iconAnchor: [13, 26],   
    popupAnchor: [0, -25]   
  }),
  default: L.icon({
    iconUrl: "icons/default.png", // dao nĩa mặc định
     iconSize: [26, 26],     
    iconAnchor: [13, 26],   
    popupAnchor: [0, -25]   
  })
};

// =========================
// 🧠 HÀM XÁC ĐỊNH LOẠI QUÁN TỪ TÊN
// =========================
function detectCategory(name = "") {
  name = name.toLowerCase();
  if (name.includes("phở")) return "pho";
  if (name.includes("cà phê") || name.includes("coffee")) return "cafe";
  if (name.includes("trà sữa")) return "tra_sua";
  if (name.includes("bún") || name.includes("bánh canh") || name.includes("bò huế")) return "bun";
  if (name.includes("cơm") || name.includes("com")) return "com";
  return "default";
}

// =========================
// 🔍 HÀM HIỂN THỊ MARKER
// =========================
function displayPlaces(places) {
  // Xoá marker cũ
  markers.forEach(m => map.removeLayer(m));
  markers = [];

  console.log("📂 Dữ liệu nhận được:", places);

  if (!places || places.length === 0) {
    alert("Không tìm thấy quán nào!");
    return;
  }

  // Duyệt qua từng địa điểm
  places.forEach(p => {
    const lat = parseFloat(p.lat);
    const lon = parseFloat(p.lon);
    if (isNaN(lat) || isNaN(lon)) return;

    // Xác định icon theo loại quán
    const category = detectCategory(p.ten_quan);
    const icon = icons[category] || icons.default;

    const marker = L.marker([lat, lon], { icon }).addTo(map);

    const popupContent = `
      <div style="min-width:220px; font-family:sans-serif;">
        <h4 style="margin:0 0 5px 0;">${p.ten_quan || "Không tên"}</h4>
        ${p.hinh_anh ? `<img src="${p.hinh_anh}" width="200" style="border-radius:8px;margin-bottom:5px">` : ""}
        <p><b>Địa chỉ:</b> ${p.dia_chi || "Không rõ"}</p>
        <p><b>Điện thoại:</b> ${p.so_dien_thoai || "Không có"}</p>
        <p><b>Đánh giá:</b> ⭐ ${p.rating || "Chưa có"}</p>
        <p><b>Giờ mở cửa:</b> ${p.gio_mo_cua || "Không rõ"}</p>
        <p><b>Giá trung bình:</b> ${p.gia_trung_binh || "?"}</p>
      </div>
    `;

    marker.bindPopup(popupContent);

// 🧭 Khi click vào marker -> zoom đến marker đó
    marker.on("click", () => {
    map.setView([lat, lon], 17, { animate: true }); // zoom level 17, có animation
});

    markers.push(marker);

  });

  // Zoom khung bản đồ vừa đủ chứa tất cả marker
  const group = new L.featureGroup(markers);
  map.fitBounds(group.getBounds().pad(0.2));
}

// =========================
// 📡 GỌI API LẤY DỮ LIỆU TỪ CSV
// =========================
async function fetchPlaces(query = "") {
  try {
    const url = "/api/places";
    const res = await fetch(url);
    const data = await res.json();

    const filtered = query
      ? data.filter(p => p.ten_quan && p.ten_quan.toLowerCase().includes(query.toLowerCase()))
      : data;

    displayPlaces(filtered);
  } catch (err) {
    console.error("Lỗi khi tải dữ liệu:", err);
    alert("Không thể tải dữ liệu từ server!");
  }
}

// =========================
// 🎯 SỰ KIỆN NÚT "TÌM"
// =========================
document.getElementById("btnSearch").addEventListener("click", () => {
  const query = document.getElementById("query").value.trim();
  fetchPlaces(query);
});

// ✅ Tự động hiển thị tất cả quán khi mở trang
fetchPlaces();

// =========================
// ✨ GỢI Ý TỰ ĐỘNG & ENTER SEARCH
// =========================
const queryInput = document.getElementById("query");
const suggestionsBox = document.getElementById("suggestions");
let allPlaces = [];

// Lấy toàn bộ dữ liệu để phục vụ autocomplete
async function preloadPlaces() {
  try {
    const res = await fetch("/api/places");
    allPlaces = await res.json();
  } catch (err) {
    console.error("Không thể tải dữ liệu autocomplete:", err);
  }
}

// Hiển thị gợi ý theo từ khóa nhập
queryInput.addEventListener("input", () => {
  const keyword = queryInput.value.trim().toLowerCase();
  suggestionsBox.innerHTML = "";

  if (!keyword) {
    suggestionsBox.classList.remove("show");
    return;
  }

  const matched = allPlaces
    .filter(p => p.ten_quan && p.ten_quan.toLowerCase().includes(keyword))
    .slice(0, 5);

  if (matched.length === 0) {
    suggestionsBox.classList.remove("show");
    return;
  }

  matched.forEach(p => {
    const div = document.createElement("div");
    div.textContent = p.ten_quan;
    div.addEventListener("click", () => {
      queryInput.value = p.ten_quan;
      suggestionsBox.classList.remove("show");
      fetchPlaces(p.ten_quan);
    });
    suggestionsBox.appendChild(div);
  });

  suggestionsBox.classList.add("show");
});

// Gọi trước để load dữ liệu autocomplete
preloadPlaces();

// =========================
// 📍 ĐỊNH VỊ GPS NGƯỜI DÙNG
// =========================
const locateBtn = document.getElementById("locate-btn");
let userMarker = null;
let accuracyCircle = null;

locateBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Trình duyệt của bạn không hỗ trợ định vị GPS!");
    return;
  }

  locateBtn.innerHTML = "⏳"; // loading icon
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const accuracy = pos.coords.accuracy;

      // Xoá marker cũ nếu có
      if (userMarker) map.removeLayer(userMarker);
      if (accuracyCircle) map.removeLayer(accuracyCircle);

      // Tạo marker người dùng
      userMarker = L.marker([lat, lon], {
        title: "Vị trí của bạn",
        icon: L.divIcon({
          className: "user-marker",
          html: '<div style="width:14px;height:14px;background:#0078ff;border-radius:50%;border:3px solid white;box-shadow:0 0 4px rgba(0,0,0,0.4);"></div>',
        }),
      }).addTo(map);

      // Tạo vòng tròn sai số
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
