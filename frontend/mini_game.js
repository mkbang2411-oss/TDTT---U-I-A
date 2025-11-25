// ===============================
// 🌐 API CONFIGURATION
// ===============================
const API_GAME_URL = 'http://127.0.0.1:8000';
// ===============================
// 🎮 MINI GAME POPUP CONTROL
// ===============================

const miniGameBtn = document.getElementById("miniGameBtn");
const miniGamePopup = document.getElementById("miniGamePopup");
const closeMiniGame = document.getElementById("closeMiniGame");

const miniGameTabBtn = document.getElementById("miniGameTabBtn");
const miniAlbumTabBtn = document.getElementById("miniAlbumTabBtn");


function switchMiniGameTab(targetId) {
    const popup = document.getElementById("miniGamePopup");
    if (!popup) return;

    const tabContents = popup.querySelectorAll(".mini-game-tab-content");
    const tabButtons = popup.querySelectorAll(".mini-tab-btn");

    tabContents.forEach((tab) => {
        tab.classList.toggle("active", tab.id === targetId);
    });

    tabButtons.forEach((btn) => {
        const target = btn.getAttribute("data-target");
        btn.classList.toggle("active", target === targetId);
    });
}

// Gán event cho 2 nút tab
miniGameTabBtn?.addEventListener("click", () => {
    switchMiniGameTab("miniGameTab");
});

miniAlbumTabBtn?.addEventListener("click", () => {
    switchMiniGameTab("miniAlbumTab");
    loadAlbumCards();   // 🔥 mỗi lần mở tab Album thì refresh
});

if (miniGameBtn) {
    miniGameBtn.addEventListener("click", async () => {
        miniGamePopup.classList.remove("hidden");
        
        // Luôn quay lại tab chơi game khi mở popup
        switchMiniGameTab("miniGameTab");
        // 🆕 Load tiến độ game từ server
        await loadGameProgress();

        // 🔥 Load luôn album theo tiến độ mới
        await loadAlbumCards();
        
        // 🆕 Đợi DOM loaded rồi mới gọi
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                showLevelSelection();
            });
        } else {
            // DOM đã sẵn sàng, gọi luôn
            const showLevelSelectionEvent = new CustomEvent('showLevelSelection');
            document.dispatchEvent(showLevelSelectionEvent);
        }
    });
}

if (closeMiniGame) {
    closeMiniGame.addEventListener("click", () => {
        miniGamePopup.classList.add("hidden");
    });
}

// Đóng popup khi click ra ngoài
miniGamePopup?.addEventListener("click", (e) => {
    if (e.target === miniGamePopup) {
        miniGamePopup.classList.add("hidden");
    }
});

// ===============================
// 🎮 GAME PROGRESS MANAGEMENT
// ===============================

let userGameProgress = {
    current_level: 0,
    completed_levels: [],
    max_unlocked: 0
};

// Load tiến độ từ server khi mở game
async function loadGameProgress() {
    try {
        const response = await fetch(`${API_GAME_URL}/api/game/progress/`, {
            credentials: 'include'  // Gửi cookies
        });
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success') {
                userGameProgress = data;
                currentLevel = data.current_level;
                console.log('✅ Đã load game progress:', data);
            }
        }
    } catch (error) {
        console.error('❌ Không thể load game progress:', error);
    }
}

// Lưu tiến độ lên server khi hoàn thành level
async function saveGameProgress(levelCompleted) {
    try {
        // ⏱️ TÍNH THỜI GIAN HOÀN THÀNH (giây)
        const timeTaken = (Date.now() - levelStartTime) / 1000;
        
        const response = await fetch(`${API_GAME_URL}/api/game/update/`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                level_completed: levelCompleted,
                time_taken: timeTaken,      // 🆕 Gửi thời gian
                deaths: levelDeaths         // 🆕 Gửi số lần chết
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success') {
                userGameProgress = data;
                console.log('✅ Đã lưu tiến độ:', data);
                
                // 🆕 Trả về số sao để hiển thị
                return data.stars;
            }
        }
    } catch (error) {
        console.error('❌ Không thể lưu game progress:', error);
    }
    return 1; // Mặc định 1 sao nếu lỗi
}
// ===============================
// 🎴 CLICK VÀO CARD TRONG ALBUM
// ===============================
function setupAlbumCardClicks() {
    const popup = document.getElementById("miniGamePopup");
    if (!popup) return;

    const cards = popup.querySelectorAll(".album-card");
    const panel = document.getElementById("albumPlacesPanel");

    cards.forEach(card => {
        // Clear handler cũ
        card.onclick = null;

        card.addEventListener("click", () => {
            // 🔒 Nếu card chưa unlock → hiển thị thông báo
            if (!card.classList.contains("unlocked")) {
                if (panel) {
                    const levelIndex = card.getAttribute("data-level");
                    panel.innerHTML = `
                        <div class="album-places-empty">
                            🔒 Hãy hoàn thành Level ${parseInt(levelIndex) + 1} để mở khóa món này!
                        </div>
                    `;
                }
                return;
            }

            // ✅ Nếu card đã unlock → highlight card và load quán
            cards.forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");

            const districtEl = card.querySelector(".album-district");
            const district = districtEl ? districtEl.textContent.trim() : null;
            
            if (district) {
                showDistrictPlaces(district);
            }
        });
    });
}

// ===============================
// 📍 RENDER DANH SÁCH QUÁN THEO QUẬN
// ===============================
function renderPlaceSuggestions(district, places) {
    const panel = document.getElementById("albumPlacesPanel");
    if (!panel) return;

    if (!places || places.length === 0) {
        panel.innerHTML = `
            <div class="album-places-empty">
                Chưa tìm được quán nào trong dữ liệu cho <strong>${district}</strong> 😢
            </div>
        `;
        return;
    }

    const itemsHtml = places.map(p => `
        <div class="place-card">
            <div class="place-main">
                <div class="place-name">${p.ten_quan || "Quán ăn"}</div>
                <div class="place-rating">
                    ${p.rating ? `⭐ ${p.rating}` : ""}
                    ${p.gia_trung_binh ? `<span class="place-price">${p.gia_trung_binh}</span>` : ""}
                </div>
            </div>
            <div class="place-address">${p.dia_chi || ""}</div>
            ${p.khau_vi ? `<div class="place-flavor">Khẩu vị: ${p.khau_vi}</div>` : ""}
        </div>
    `).join("");

    panel.innerHTML = `
        <h4 class="album-places-title">Gợi ý quán ở ${district}</h4>
        <div class="album-places-list">
            ${itemsHtml}
        </div>
    `;
}

// ===============================
// 📍 GỌI API LẤY QUÁN THEO QUẬN
// ===============================
async function showDistrictPlaces(district) {
    const panel = document.getElementById("albumPlacesPanel");
    if (!panel) return;

    panel.innerHTML = `
        <div class="album-places-loading">
            <div class="spinner"></div>
            <p>Đang tải quán ở <strong>${district}</strong>...</p>
        </div>
    `;

    try {
        const response = await fetch(
            `${API_GAME_URL}/api/food/suggestions/?district=${encodeURIComponent(district)}`,
            { credentials: "include" }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.status !== "success") {
            throw new Error(data.message || "Lỗi server");
        }

        renderPlaceSuggestions(district, data.places);
    } catch (error) {
        console.error("Lỗi load gợi ý quán:", error);
        panel.innerHTML = `
            <div class="album-places-error">
                Không tải được danh sách quán cho <strong>${district}</strong>.<br>
                <span style="font-size: 12px; color:#999;">${error.message || ""}</span>
            </div>
        `;
    }
}
// ===============================
// 📖 ALBUM (FOOD MAP JOURNEY)
// ===============================
async function loadAlbumCards() {
    try {
        const response = await fetch(`${API_GAME_URL}/api/game/album/`, {
            credentials: 'include',
        });

        if (!response.ok) {
            console.warn('Không load được album (HTTP)', response.status);
            return;
        }

        const data = await response.json();
        if (data.status !== 'success' || !Array.isArray(data.cards)) {
            console.warn('Dữ liệu album không hợp lệ', data);
            return;
        }

        const popup = document.getElementById("miniGamePopup");
        if (!popup) return;

        data.cards.forEach(card => {
    const cardEl = popup.querySelector(`.album-card[data-level="${card.level_index}"]`);
    if (!cardEl) return;

    // 👀 trạng thái trước khi cập nhật
    const wasUnlocked = cardEl.classList.contains("unlocked");

    // locked / unlocked
    cardEl.classList.toggle("unlocked", !!card.unlocked);
    cardEl.classList.toggle("locked", !card.unlocked);

    const districtEl = cardEl.querySelector(".album-district");
    const foodEl     = cardEl.querySelector(".album-food");
    const statusEl   = cardEl.querySelector(".album-status");

    if (districtEl && card.district) {
        districtEl.textContent = card.district;
    }

    if (foodEl) {
        const icon = card.icon || "";
        const foodName = card.food_name || "";
        foodEl.textContent = `${icon ? icon + " " : ""}${foodName}`;
    }

    if (statusEl) {
        if (card.unlocked) {
            const starText = card.stars && card.stars > 0
                ? '⭐'.repeat(card.stars) + ' '
                : '';
            statusEl.textContent = `${starText}Đã mở`;
        } else if (card.available_to_play) {
            statusEl.textContent = "▶ Có thể chơi";
        } else {
            statusEl.textContent = "🔒 Chưa mở";
        }
    }

    if (card.best_time) {
        cardEl.setAttribute("data-best-time", card.best_time.toFixed(1));
    } else {
        cardEl.removeAttribute("data-best-time");
    }

    // ✨ Nếu trước đó locked, giờ thành unlocked → chạy animation
    if (card.unlocked && !wasUnlocked) {
        cardEl.classList.add("just-unlocked");
        setTimeout(() => {
            cardEl.classList.remove("just-unlocked");
        }, 650);  // thời gian ≈ animation 0.6s
    }
});
 // 🆕 Gán sự kiện click cho card
    setupAlbumCardClicks();
    } catch (error) {
        console.error('❌ Không load được album:', error);
    }
}

// ===============================
// 🎮 GLOBAL GAME VARIABLES (phải ở ngoài DOMContentLoaded)
// ===============================
let levelStartTime = Date.now();
let levelDeaths = 0;
let currentLevel = 0;
let gameLoopStarted = false;

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("gameCanvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // --------------------------
    // TILE SYSTEM
    // --------------------------
   let tileSize = 32; // khôi phục biến này

    // Map 2D (0 = floor, 1 = wall)
   const levels = [
    {
        // ⭐ LEVEL 1
        map: [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1],
            [1,0,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,1,0,1],
            [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1],
            [1,0,1,0,1,1,1,0,1,1,1,0,1,1,1,1,0,1,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,1,0,0,0,1,0,1,0,0,1,0,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,0,1,1,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,1,0,0,0,0,0,1,0,1,0,0,0,1,0,0,0,1,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ],
        playerStart: { x: 1, y: 1 },
        chestPos:    { x: 23, y: 1 },
        food: "images/pho.png"   // món ăn mở khóa level 1
    },

    {
        // ⭐ LEVEL 2 (mình tạo map mới cho bạn)
        map: [
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,1,0,1,1,1,0,0,0,1,0,1,1,1,0,1,0,0,0,1,0,1],
        [1,0,1,0,1,0,0,0,1,0,1,0,1,0,0,0,0,0,1,1,1,0,1,0,1],
        [1,0,1,0,1,1,1,0,1,0,1,0,1,1,1,0,1,0,0,0,0,0,1,0,1],
        [1,0,1,0,0,0,1,0,0,0,1,0,1,0,0,0,1,1,1,1,1,0,1,0,1],
        [1,0,1,1,1,0,1,1,1,0,1,0,1,0,1,1,1,0,0,0,1,0,1,0,1],
        [1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,1,0,0,0,1],  // ⭐ FIXED – mở đường bên phải
        [1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,0,1]
    ],
        playerStart: { x: 1, y: 1 },
        chestPos:    { x: 23, y: 7 },
        food: "images/bun_bo_hue.png"  // món ăn mở khóa level 2
    }
    ,{
    // ⭐ LEVEL 3 — chuẩn bị cho bot
     map: [
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,1,0,1,0,0,0,1,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
        [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,0,1,1,1,0,1,0,1],
        [1,0,1,0,0,0,1,0,1,0,1,0,0,0,0,0,1,0,0,0,1,0,1,0,1],
        [1,0,1,1,1,0,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,0,1,0,1],
        [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,1,0,0,0,1],
        [1,1,1,0,1,1,1,1,1,0,1,0,1,1,1,0,1,0,1,1,1,1,1,0,1],
        [1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    ],

    playerStart: { x: 1, y: 1 },
    chestPos:    { x: 23, y: 7 },
    food: "images/com_tam.png",

    // ➕ BOT XUẤT HIỆN Ở MAP 3
     bots: [
        { x: 12, y: 5, dir: "left" }
    ]
},
 {
        // ⭐ LEVEL 4 - THE BIG CHALLENGE
        map: [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,1],
            [1,0,1,1,1,0,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,0,1,1,1,0,1,0,1,1],
            [1,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1],
            [1,0,1,0,1,1,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,1,1,0,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,0,1,1],
            [1,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,1],
            [1,0,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,0,1,0,1,1,1,0,1,0,1,1],
            [1,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1],
            [1,0,1,0,1,1,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,0,1,0,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,0,1,1,1,1,1,1,1,0,1,1,1,0,1,1,1,1,1,1,1,0,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ],
        playerStart: { x: 1, y: 1 },
        chestPos:    { x: 28, y: 13 },
        food: "images/banh_mi.png",  // 🥖 Bánh mì Việt Nam
        
        // 🆕 2 BOTS
        bots: [
            { x: 15, y: 7, dir: "left" },
            { x: 10, y: 9, dir: "right" },
            { x: 6,  y: 13, dir: "left" }
        ],

          // 🧱 Moving Walls cho Level 4
        movingWalls: [
          // Tường ngang chạy qua lại ở hàng y = 5, từ x = 2 → 8
          { x: 3,  y: 5, axis: "horizontal", dir: 1, min: 2, max: 8 },

          // Tường dọc chạy lên xuống ở cột x = 21, từ y = 7 → 11
          { x: 21, y: 8, axis: "vertical",   dir: 1, min: 7, max: 11 },

          // 🆕 Tường dọc mới ở cột x = 13, quanh vị trí shield
          { x: 13, y: 5, axis: "vertical",   dir: 1, min: 3, max: 9 },

        ],
        
        // 🆕 SHIELD POWER-UP (vị trí ở giữa map)
        shieldPos: { x: 15, y: 5 }
    }
];

    // --------------------------
    // LOAD TEXTURES
    // --------------------------
    const wallImg = new Image();
    wallImg.src = "GameAssets/wall.png";

    const floorImg = new Image();
    floorImg.src = "GameAssets/floor.png";

    // ➕ THÊM VÀO
const playerSprites = {
    up: new Image(),
    down: new Image(),
    left: new Image(),
    right: new Image()
};
const playerImg = new Image();
playerImg.src = "GameAssets/player.png";

playerSprites.up.src = "GameAssets/player_up.png";
playerSprites.down.src = "GameAssets/player_down.png";
playerSprites.left.src = "GameAssets/player_left.png";
playerSprites.right.src = "GameAssets/player_right.png";

const botSprites = {
    up: new Image(),
    down: new Image(),
    left: new Image(),
    right: new Image()
};

botSprites.up.src = "GameAssets/bot_up.png";
botSprites.down.src = "GameAssets/bot_down.png";
botSprites.left.src = "GameAssets/bot_left.png";
botSprites.right.src = "GameAssets/bot_right.png";


const chestSprites = {
    closed: new Image(),
    open: new Image()
};

chestSprites.closed.src = "GameAssets/chest_closed.png";
chestSprites.open.src   = "GameAssets/chest_open.png";

// 🆕 THÊM SHIELD SPRITE
const shieldSprite = new Image();
shieldSprite.src = "GameAssets/shield.png";  // Bạn cần tạo ảnh này (hoặc dùng emoji 🛡️)



//Thêm level để tăng độ khó
let map         = levels[currentLevel].map;
let foodReward  = levels[currentLevel].food;

// cập nhật vị trí player + chest theo level
let player = { ...levels[currentLevel].playerStart };
const chest = { ...levels[currentLevel].chestPos, opened: false };

// ⭐ DANH SÁCH CÁC BOT (0, 1 hoặc nhiều con tùy level)
let bots = [];

// Khởi tạo bot lần đầu theo currentLevel (level 1–2 sẽ không có bot)
const initialBots = levels[currentLevel].bots || [];
initialBots.forEach(b => {
    bots.push({
        x: b.x,
        y: b.y,
        pixelX: b.x * tileSize,
        pixelY: b.y * tileSize,
        dir: b.dir || "left"
    });
});

// 🧱 MOVING WALLS (tường di chuyển)
let movingWalls = [];
const initialMovingWalls = levels[currentLevel].movingWalls || [];
initialMovingWalls.forEach(w => {
    movingWalls.push({
        ...w,
        pixelX: w.x * tileSize,
        pixelY: w.y * tileSize
    });
});


// 🛡️ TRẠNG THÁI SHIELD
let shield = {
    x: null,
    y: null,
    visible: false,   // có hiển thị icon trên map hay không
    active: false,    // đang miễn nhiễm hay không
    endTime: 0        // thời điểm hết hiệu lực (ms)
};

// Khởi tạo shield ban đầu theo level hiện tại (chỉ level 4 mới có)
const initialShield = levels[currentLevel].shieldPos;
if (initialShield) {
    shield.x = initialShield.x;
    shield.y = initialShield.y;
    shield.visible = true;
}

    // ➕ THÊM 2 BIẾN NÀY NGAY SAU ĐÓ
    let playerPixelX = player.x * tileSize;
    let playerPixelY = player.y * tileSize;

// ➕ THÊM CỜ KIỂM TRA ĐANG DI CHUYỂN HAY KHÔNG
    let isMoving = false;
    // ➕ THÊM DÒNG NÀY
let playerDir = "right"; // hướng mặc định
    const foods = [
        "images/pho.png",
        "images/bun_bo_hue.png",
        "images/com_tam.png"
    ];
    let randomFood = foods[Math.floor(Math.random() * foods.length)];
// 🔍 HÀM CHECK XEM Ô TILE CÓ MOVING WALL ĐỨNG KHÔNG
function isMovingWallAt(tileX, tileY) {
    return movingWalls.some(w => w.x === tileX && w.y === tileY);
}
      
  // Reset toàn bộ trạng thái game (dùng cho nút "Chơi lại")
   function resetGameState(isLevelChange = false) {  // ✅ Thêm tham số
    // ⭐ BẮT BUỘC: Tính lại kích thước canvas trước
    const container = document.getElementById("miniGameInner");
    if (!container) return;

    const tilesX = levels[currentLevel].map[0].length;
    const tilesY = levels[currentLevel].map.length;

    const availableWidth  = container.clientWidth;
    const availableHeight = container.clientHeight;

    const tileW = Math.floor(availableWidth  / tilesX);
    const tileH = Math.floor(availableHeight / tilesY);

    tileSize = Math.min(tileW, tileH);

    canvas.width  = tilesX * tileSize;
    canvas.height = tilesY * tileSize;

    // ⭐ SAU ĐÓ MỚI GÁN LẠI TRẠNG THÁI
    map        = levels[currentLevel].map;
    foodReward = levels[currentLevel].food;

    // player
    player.x = levels[currentLevel].playerStart.x;
    player.y = levels[currentLevel].playerStart.y;
    playerPixelX = player.x * tileSize;
    playerPixelY = player.y * tileSize;

    // chest
    chest.x = levels[currentLevel].chestPos.x;
    chest.y = levels[currentLevel].chestPos.y;
    chest.opened = false;

     // ⭐ RESET CÁC BOT THEO LEVEL HIỆN TẠI
    bots = [];
    const levelBots = levels[currentLevel].bots || [];
    levelBots.forEach(b => {
        bots.push({
            x: b.x,
            y: b.y,
            pixelX: b.x * tileSize,
            pixelY: b.y * tileSize,
            dir: b.dir || "left"
        });
    });

      // 🧱 RESET MOVING WALLS THEO LEVEL HIỆN TẠI
    movingWalls = [];
    const levelMovingWalls = levels[currentLevel].movingWalls || [];
    levelMovingWalls.forEach(w => {
        movingWalls.push({
            ...w,
            pixelX: w.x * tileSize,
            pixelY: w.y * tileSize
        });
    });

       // 🛡️ RESET SHIELD THEO LEVEL HIỆN TẠI
    shield.active = false;
    shield.endTime = 0;

    const levelShield = levels[currentLevel].shieldPos;
    if (levelShield) {
        shield.x = levelShield.x;
        shield.y = levelShield.y;
        shield.visible = true;   // mỗi lần chơi lại level là có shield lại
    } else {
        shield.x = null;
        shield.y = null;
        shield.visible = false;
    }
    
    // ⭐ RESET CÁC PHÍM
    keys.w = false;
    keys.a = false;
    keys.s = false;
    keys.d = false;

    isMoving = false;
    playerDir = "right";

    const winOverlay = document.getElementById("winOverlay");
    if (winOverlay) winOverlay.remove();

    canvas.style.display = "block";

    // ⏱️ CHỈ RESET DEATHS KHI CHUYỂN LEVEL
    if (isLevelChange) {
        levelDeaths = 0;  // ✅ Chỉ reset khi chuyển level mới
    }
    
    levelStartTime = Date.now();  // ✅ Luôn reset timer
    
    drawMap();
}


    // --------------------------
    // TILE RENDERING
    // --------------------------
    function drawMap() {
        for (let y = 0; y < map.length; y++) {
            for (let x = 0; x < map[y].length; x++) {

                // Draw floor
                ctx.drawImage(floorImg, x * tileSize, y * tileSize, tileSize, tileSize);

                // Draw wall
                if (map[y][x] === 1) {
                    ctx.drawImage(wallImg, x * tileSize, y * tileSize, tileSize, tileSize);
                }
            }
        }

          // 🛡️ VẼ SHIELD TRÊN MAP (nếu có và chưa nhặt)
    if (shield.visible && shield.x !== null && shield.y !== null && !shield.active) {
        if (shieldSprite.complete) {
            ctx.drawImage(
                shieldSprite,
                shield.x * tileSize,
                shield.y * tileSize,
                tileSize,
                tileSize
            );
        } else {
            // fallback: vẽ vòng tròn màu nếu ảnh chưa load
            ctx.fillStyle = "rgba(0, 150, 255, 0.6)";
            ctx.beginPath();
            ctx.arc(
                shield.x * tileSize + tileSize / 2,
                shield.y * tileSize + tileSize / 2,
                tileSize / 2 - 4,
                0, Math.PI * 2
            );
            ctx.fill();
        }
    }
    // 🧱 VẼ CÁC MOVING WALLS (dùng pixel để lướt mượt)
    movingWalls.forEach(w => {
        const px = (w.pixelX !== undefined) ? w.pixelX : w.x * tileSize;
        const py = (w.pixelY !== undefined) ? w.pixelY : w.y * tileSize;

        ctx.drawImage(
            wallImg,
            px,
            py,
            tileSize,
            tileSize
        );
    });

        // Draw player (theo hướng)
let img = playerSprites[playerDir];

if (img && img.complete) {
    ctx.drawImage(
        img,
        playerPixelX,
        playerPixelY,
        tileSize,
        tileSize
    );
} else {
    // Fallback: vẽ tạm hình tròn nếu ảnh chưa load
    ctx.fillStyle = "blue";
    ctx.beginPath();
    ctx.arc(
        playerPixelX + tileSize / 2,
        playerPixelY + tileSize / 2,
        tileSize / 2 - 4,
        0, Math.PI * 2
    );
    ctx.fill();
}

 // 🛡️ Nếu shield đang active, vẽ vòng sáng quanh nhân vật
    if (shield.active) {
        ctx.save();
        ctx.strokeStyle = "rgba(0, 200, 255, 0.9)";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(
            playerPixelX + tileSize / 2,
            playerPixelY + tileSize / 2,
            tileSize / 2,
            0, Math.PI * 2
        );
        ctx.stroke();
        ctx.restore();
    }
        // Draw chest (closed / open)
let chestImg = chest.opened ? chestSprites.open : chestSprites.closed;
// ⭐ VẼ CÁC BOT (nếu level có)
bots.forEach(bot => {
    const botImg = botSprites[bot.dir] || botSprites.down;

    if (botImg.complete) {
        ctx.drawImage(botImg, bot.pixelX, bot.pixelY, tileSize, tileSize);
    } else {
        // fallback khi sprite chưa load
        ctx.fillStyle = "red";
        ctx.fillRect(bot.pixelX, bot.pixelY, tileSize, tileSize);
    }
});


if (chestImg && chestImg.complete) {
    ctx.drawImage(
        chestImg,
        chest.x * tileSize,
        chest.y * tileSize,
        tileSize,
        tileSize
    );
}
    }
    function playChestSound() {
    const audio = document.getElementById("chestSoundAudio");
    if (!audio) return;
    audio.currentTime = 0;
    audio.play().catch(() => {});
}


    // --------------------------
    // MOVEMENT
    // --------------------------
    function move(dx, dy) {
    // Nếu đang di chuyển thì bỏ qua input mới
    if (isMoving) return;

    const targetX = player.x + dx;
    const targetY = player.y + dy;

    // Kiểm tra có đi được không (0 = đường đi)
    if (!map[targetY] || map[targetY][targetX] !== 0) {
        return;
    }

    isMoving = true;

    const startX = playerPixelX;
    const startY = playerPixelY;
    const endX = targetX * tileSize;
    const endY = targetY * tileSize;
    const duration = 150; // ms
    let startTime = null;

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);

        // Nội suy vị trí
        playerPixelX = startX + (endX - startX) * progress;
        playerPixelY = startY + (endY - startY) * progress;

        drawMap();

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            // Kết thúc di chuyển → cập nhật vị trí tile thật
            player.x = targetX;
            player.y = targetY;
            isMoving = false;

            // Vẽ lại lần cuối cho chuẩn
            drawMap();

            // Check win
            // Check chest collision
if (player.x === chest.x && player.y === chest.y) {
    chest.opened = true;
    drawMap();      // vẽ lại để thấy rương mở
    playChestSound();
    setTimeout(showFoodReward, 400); // delay nhẹ cho đẹp
}
        }
    }

    requestAnimationFrame(animate);
}

// ===============================
// 🎮 LEVEL SELECTION SCREEN
// ===============================
function showLevelSelection() {
    const miniGameInner = document.getElementById("miniGameInner");
    const canvas = document.getElementById("gameCanvas");
    if (!miniGameInner || !canvas) return;

    canvas.style.display = "none";

    // Xóa màn hình cũ nếu có
    let levelSelection = document.getElementById("levelSelection");
    if (levelSelection) {
        levelSelection.remove();
    }

    // Tạo màn hình chọn level
    levelSelection = document.createElement("div");
    levelSelection.id = "levelSelection";
    levelSelection.style.cssText = `
        padding: 20px;
        overflow-y: auto;
        max-height: 100%;
    `;

    levelSelection.innerHTML = `
        <h3 style="text-align: center; margin-bottom: 20px; font-size: 24px;">🎮 Chọn Màn Chơi</h3>
        <div id="levelGrid" style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            max-width: 600px;
            margin: 0 auto 20px;
        "></div>
        <button id="startGameBtn" style="
            display: block;
            margin: 0 auto;
            padding: 12px 30px;
            background: #5a6ff0;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        ">🎮 Bắt đầu chơi</button>
    `;

    miniGameInner.appendChild(levelSelection);

    const levelGrid = document.getElementById("levelGrid");

    // Tạo các nút level
    levels.forEach((level, index) => {
        const isCompleted = userGameProgress.completed_levels.includes(index);
        const isUnlocked = index === 0 || 
                           isCompleted || 
                           userGameProgress.completed_levels.includes(index - 1) ||
                           index <= userGameProgress.max_unlocked;

        const levelBtn = document.createElement("button");
        levelBtn.innerHTML = `
            <div style="font-size: 32px; margin-bottom: 8px;">
                ${isCompleted ? '✅' : (isUnlocked ? '🔓' : '🔒')}
            </div>
            <div style="font-weight: bold;">Level ${index + 1}</div>
            ${isCompleted ? '<div style="font-size: 12px; color: #4CAF50;">Đã hoàn thành</div>' : ''}
        `;
        levelBtn.style.cssText = `
            padding: 20px;
            border: 3px solid ${isUnlocked ? '#5a6ff0' : '#ccc'};
            background: ${isUnlocked ? '#fff' : '#f5f5f5'};
            border-radius: 12px;
            cursor: ${isUnlocked ? 'pointer' : 'not-allowed'};
            transition: all 0.2s;
            opacity: ${isUnlocked ? '1' : '0.5'};
        `;

        if (isUnlocked) {
            levelBtn.addEventListener("click", () => {
                currentLevel = index;

                // Highlight level được chọn
                document.querySelectorAll("#levelGrid button").forEach(btn => {
                    btn.style.background = '#fff';
                    btn.style.transform = 'scale(1)';
                });
                levelBtn.style.background = '#e3f2fd';
                levelBtn.style.transform = 'scale(1.05)';
            });

            levelBtn.addEventListener("mouseenter", () => {
                if (levelBtn.style.background !== 'rgb(227, 242, 253)') {
                    levelBtn.style.background = '#f0f0f0';
                }
            });

            levelBtn.addEventListener("mouseleave", () => {
                if (levelBtn.style.background !== 'rgb(227, 242, 253)') {
                    levelBtn.style.background = '#fff';
                }
            });
        }

        levelGrid.appendChild(levelBtn);
    });

    // Nút bắt đầu game
    const startBtn = document.getElementById("startGameBtn");
    if (startBtn) {
        startBtn.onclick = () => {
            levelSelection.remove();
            canvas.style.display = "block";
            resetGameState(true);
            setTimeout(autoResizeCanvas, 30);
        };
    }
}
// ===============================
// 🎉 CONFETTI MINI GAME
// ===============================
function triggerConfetti() {
    const popupContent = document.querySelector("#miniGamePopup .mini-game-content");
    if (!popupContent) return;

    // Nếu đã có container cũ thì xóa để tránh chồng nhiều lớp
    const old = popupContent.querySelector(".confetti-container");
    if (old) old.remove();

    const container = document.createElement("div");
    container.className = "confetti-container";
    popupContent.appendChild(container);

    const colors = ["#ff8a65", "#ffd54f", "#4db6ac", "#9575cd", "#ff4081"];
    const pieceCount = 80;

    for (let i = 0; i < pieceCount; i++) {
        const piece = document.createElement("div");
        piece.className = "confetti-piece";

        piece.style.left = Math.random() * 100 + "%";
        piece.style.backgroundColor = colors[i % colors.length];
        piece.style.animationDelay = (Math.random() * 0.4) + "s";
        piece.style.opacity = (0.7 + Math.random() * 0.3).toFixed(2);
        piece.style.transform = `rotate(${Math.random() * 360}deg)`;

        container.appendChild(piece);
    }

    // Xóa container sau khi animation kết thúc
    setTimeout(() => {
        container.remove();
    }, 1800);
}


// ===============================
// 🎮 WIN SCREEN
// ===============================
function showFoodReward() {
    const miniGameInner = document.getElementById("miniGameInner");
    const canvas = document.getElementById("gameCanvas");
    if (!miniGameInner || !canvas) return;

    canvas.style.display = "none";
    
    // 🆕 LƯU TIẾN ĐỘ VÀ NHẬN SỐ SAO
    saveGameProgress(currentLevel).then(stars => {
       // 🔄 Cập nhật album sau khi hoàn thành (nếu bạn đã có hàm này)
        if (typeof loadAlbumCards === "function") {
            loadAlbumCards();
        }

        // 🎉 BẮN CONFETTI
        triggerConfetti();
       // 🔄 Sau khi lưu tiến độ, cập nhật lại Album
        loadAlbumCards();
        // ⏱️ TÍNH THỜI GIAN HIỂN THỊ
        const timeTaken = (Date.now() - levelStartTime) / 1000;
        const timeDisplay = timeTaken.toFixed(1) + "s";
        
        // ⭐ TẠO CHUỖI SAO
        const starDisplay = '⭐'.repeat(stars || 1);

        const overlay = document.createElement("div");
        overlay.id = "winOverlay";

        overlay.style.cssText = `
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            gap: 20px;
            text-align: center;
            min-height: 400px;
        `;

        overlay.innerHTML = `
            <h2 style="font-size: 28px; margin: 0;">🎉 Chúc mừng bạn!</h2>
            
            <!-- 🆕 HIỂN THỊ SAO -->
            <div style="font-size: 48px; margin: 10px 0;">
                ${starDisplay}
            </div>
            
            <!-- 🆕 HIỂN THỊ THỜI GIAN VÀ SỐ LẦN CHẾT -->
            <div style="font-size: 16px; color: #666; background: #f5f5f5; padding: 12px 24px; border-radius: 12px;">
                ⏱️ Thời gian: <strong style="color: #5a6ff0;">${timeDisplay}</strong> 
                &nbsp;&nbsp;|&nbsp;&nbsp; 
                💀 Chết: <strong style="color: #e53935;">${levelDeaths} lần</strong>
            </div>
            
            <p style="font-size: 18px; margin: 10px 0;">
                Đây là món ăn dành cho bạn hôm nay:
            </p>

            <img 
                src="${foodReward}" 
                alt="Món ăn gợi ý" 
                style="
                    width: 260px;
                    max-width: 80%;
                    border-radius: 16px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                "
            />

            <div style="display: flex; gap: 16px; margin-top: 10px; flex-wrap: wrap; justify-content: center;">
                <button 
                    id="nextLevelBtn"
                    type="button"
                    style="
                        padding: 10px 20px;
                        border-radius: 999px;
                        border: none;
                        background: #5a6ff0;
                        color: #fff;
                        font-size: 16px;
                        cursor: pointer;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                    "
                >
                    ${currentLevel + 1 < levels.length ? '➡ Level tiếp theo' : '🏆 Hoàn thành!'}
                </button>

                <button 
                    id="selectLevelBtn"
                    type="button"
                    style="
                        padding: 10px 20px;
                        border-radius: 999px;
                        border: none;
                        background: #4CAF50;
                        color: #fff;
                        font-size: 16px;
                        cursor: pointer;
                    "
                >
                    🎮 Chọn màn khác
                </button>

                <button 
                    id="closeGameBtn"
                    type="button"
                    style="
                        padding: 10px 20px;
                        border-radius: 999px;
                        border: none;
                        background: #ccc;
                        color: #333;
                        font-size: 16px;
                        cursor: pointer;
                    "
                >
                    ✖ Đóng
                </button>
            </div>
        `;

        miniGameInner.appendChild(overlay);

        // 👉 NEXT LEVEL BUTTON
        const nextLevelBtn = overlay.querySelector("#nextLevelBtn");
        if (nextLevelBtn) {
            nextLevelBtn.addEventListener("click", () => {
                currentLevel++;

                if (currentLevel >= levels.length) {
                    alert("🎉 Bạn đã hoàn thành tất cả các level!");
                    overlay.remove();
                    showLevelSelection();
                    return;
                }

                overlay.remove();
                resetGameState(true);
            });
        }

        // 👉 NÚT CHỌN MÀN KHÁC
        const selectLevelBtn = overlay.querySelector("#selectLevelBtn");
        if (selectLevelBtn) {
            selectLevelBtn.addEventListener("click", () => {
                overlay.remove();
                showLevelSelection();
            });
        }

        // 👉 CLOSE BUTTON
        const closeGameBtn = overlay.querySelector("#closeGameBtn");
        if (closeGameBtn) {
            closeGameBtn.addEventListener("click", () => {
                document.getElementById("miniGamePopup").classList.add("hidden");
                overlay.remove();
            });
        }
    });
}

// ===============================
// 🔥 AUTO RESIZE GAME
// ===============================
function autoResizeCanvas() {
    const container = document.getElementById("miniGameInner");
    if (!container) return;

    const tilesX = map[0].length;
    const tilesY = map.length;

    const availableWidth  = container.clientWidth;
    const availableHeight = container.clientHeight;

    const tileW = Math.floor(availableWidth  / tilesX);
    const tileH = Math.floor(availableHeight / tilesY);

    tileSize = Math.min(tileW, tileH);

    canvas.width  = tilesX * tileSize;
    canvas.height = tilesY * tileSize;

    // player
    playerPixelX = player.x * tileSize;
    playerPixelY = player.y * tileSize;

   // ⭐⭐ TẤT CẢ BOT CŨNG PHẢI SCALE THEO TILESIZE MỚI ⭐⭐
    bots.forEach(bot => {
        bot.pixelX = bot.x * tileSize;
        bot.pixelY = bot.y * tileSize;
    });

       // 🧱 MOVING WALLS CŨNG SCALE THEO TILESIZE MỚI
    movingWalls.forEach(w => {
        w.pixelX = w.x * tileSize;
        w.pixelY = w.y * tileSize;
    });

    drawMap();
}



miniGameBtn.addEventListener("click", () => {
    setTimeout(autoResizeCanvas, 30);
});

window.addEventListener("resize", () => {
    if (!miniGamePopup.classList.contains("hidden")) {
        autoResizeCanvas();
    }
});

    wallImg.onload = () => {
        floorImg.onload = () => {
            drawMap();
        };
    };

// 🎮 SMOOTH MOVEMENT CONTROLS
// ----------------------------
const keys = {
    w: false,
    a: false,
    s: false,
    d: false
};

document.addEventListener("keydown", e => {
    const k = e.key.toLowerCase();
    if (keys[k] !== undefined) keys[k] = true;
});

document.addEventListener("keyup", e => {
    const k = e.key.toLowerCase();
    if (keys[k] !== undefined) keys[k] = false;
});

// ----------------------------
// 🎮 GAME LOOP (mượt)
// ----------------------------
function gameLoop() {

   // 🛡️ Hết thời gian shield thì tắt
    if (shield.active && Date.now() > shield.endTime) {
        shield.active = false;
    }


    const speed = tileSize * 0.02;

    let moveX = 0;
    let moveY = 0;

    if (keys.w) { playerDir = "up"; moveY = -speed; }
    if (keys.s) { playerDir = "down"; moveY = speed; }
    if (keys.a) { playerDir = "left"; moveX = -speed; }
    if (keys.d) { playerDir = "right"; moveX = speed; }

    const nextTileX = Math.floor((playerPixelX + moveX + tileSize/2) / tileSize);
    const nextTileY = Math.floor((playerPixelY + moveY + tileSize/2) / tileSize);

     if (map[nextTileY] && map[nextTileY][nextTileX] === 0 &&!isMovingWallAt(nextTileX, nextTileY)) 
    {
        playerPixelX += moveX;
        playerPixelY += moveY;

        player.x = Math.floor((playerPixelX + tileSize/2) / tileSize);
        player.y = Math.floor((playerPixelY + tileSize/2) / tileSize);
    }

    // ⭐⭐⭐ CHECK MỞ RƯƠNG ⭐⭐⭐
    if (!chest.opened && player.x === chest.x && player.y === chest.y) {
        chest.opened = true;
        playChestSound();
        setTimeout(showFoodReward, 350);
    }
     // 🛡️ CHECK NHẶT SHIELD
    if (
        shield.visible &&
        !shield.active &&
        shield.x === player.x &&
        shield.y === player.y
    ) {
        shield.visible = false;          // ẩn icon trên map
        shield.active = true;            // bắt đầu miễn nhiễm
        shield.endTime = Date.now() + 5000; // 5 giây
    }


// ------------------------------------------------------
// ⭐⭐⭐ BOT RANDOM WALK CHO TẤT CẢ CÁC BOT ⭐⭐⭐
// ------------------------------------------------------
const botSpeed = tileSize * 0.02;

bots.forEach(bot => {
    // 1. Kiểm tra các hướng có thể đi (dựa trên tile)
    const dirs = [];
    if (map[bot.y - 1] && map[bot.y - 1][bot.x] === 0) dirs.push("up");
    if (map[bot.y + 1] && map[bot.y + 1][bot.x] === 0) dirs.push("down");
    if (map[bot.y] && map[bot.y][bot.x - 1] === 0) dirs.push("left");
    if (map[bot.y] && map[bot.y][bot.x + 1] === 0) dirs.push("right");

    // Nếu lỡ spawn vào chỗ kín hoàn toàn thì bỏ qua để khỏi crash
    if (dirs.length === 0) return;

    // 2. Thỉnh thoảng random đổi hướng (tăng lên 5% cho bot lanh hơn)
    if (Math.random() < 0.05) {
        bot.dir = dirs[Math.floor(Math.random() * dirs.length)];
    }

    // 3. Nếu hướng hiện tại không còn hợp lệ → chọn hướng khác ngay
    if (!dirs.includes(bot.dir)) {
        bot.dir = dirs[Math.floor(Math.random() * dirs.length)];
    }

    // 4. Di chuyển theo hướng hiện tại
    let moveBX = 0, moveBY = 0;
    if (bot.dir === "up") moveBY = -botSpeed;
    if (bot.dir === "down") moveBY = botSpeed;
    if (bot.dir === "left") moveBX = -botSpeed;
    if (bot.dir === "right") moveBX = botSpeed;

    const nextBX = Math.floor((bot.pixelX + moveBX + tileSize / 2) / tileSize);
    const nextBY = Math.floor((bot.pixelY + moveBY + tileSize / 2) / tileSize);

    // 5. Nếu đi được thì cập nhật vị trí
      if ( map[nextBY] && map[nextBY][nextBX] === 0 && !isMovingWallAt(nextBX, nextBY)) 
    {
        bot.pixelX += moveBX;
        bot.pixelY += moveBY;

        bot.x = Math.floor((bot.pixelX + tileSize/2) / tileSize);
        bot.y = Math.floor((bot.pixelY + tileSize/2) / tileSize);
    } else {
        // 6. Bị tường chặn → đổi sang 1 hướng hợp lệ khác để khỏi đứng im
        bot.dir = dirs[Math.floor(Math.random() * dirs.length)];
    }
});
// ------------------------------------------------------

    // ------------------------------------------------------
    // 🧱 CẬP NHẬT VỊ TRÍ MOVING WALLS (LƯỚT MƯỢT)
    // ------------------------------------------------------
    const wallSpeed = tileSize * 0.02; // giống speed bot / player

    movingWalls.forEach(w => {
        let moveWX = 0;
        let moveWY = 0;

        if (w.axis === "horizontal") {
            moveWX = w.dir * wallSpeed;
        } else if (w.axis === "vertical") {
            moveWY = w.dir * wallSpeed;
        }

        let nextPixelX = w.pixelX + moveWX;
        let nextPixelY = w.pixelY + moveWY;

        // Tính tile nếu di chuyển
        let nextTileX = Math.floor((nextPixelX + tileSize / 2) / tileSize);
        let nextTileY = Math.floor((nextPixelY + tileSize / 2) / tileSize);

        // Kiểm tra vượt range hoặc đụng tường tĩnh -> đổi hướng
        if (w.axis === "horizontal") {
            if (
                nextTileX < w.min ||
                nextTileX > w.max ||
                map[w.y] && map[w.y][nextTileX] === 1
            ) {
                w.dir *= -1; // quay đầu
                moveWX = w.dir * wallSpeed;
                nextPixelX = w.pixelX + moveWX;
                nextTileX = Math.floor((nextPixelX + tileSize / 2) / tileSize);
            }
        } else if (w.axis === "vertical") {
            if (
                nextTileY < w.min ||
                nextTileY > w.max ||
                !map[nextTileY] ||
                map[nextTileY][w.x] === 1
            ) {
                w.dir *= -1;
                moveWY = w.dir * wallSpeed;
                nextPixelY = w.pixelY + moveWY;
                nextTileY = Math.floor((nextPixelY + tileSize / 2) / tileSize);
            }
        }

        // Chỉ di chuyển nếu ô tiếp theo là đường (0)
        if (map[nextTileY] && map[nextTileY][nextTileX] === 0) {
            w.pixelX = nextPixelX;
            w.pixelY = nextPixelY;

            // Cập nhật tile logic (để va chạm với player/bot dùng được)
            w.x = nextTileX;
            w.y = nextTileY;
        }
    });


// ⭐⭐⭐ BẤT KỲ BOT NÀO CHẠM NGƯỜI → DIE (trừ khi đang có shield) ⭐⭐⭐
const hitBot = !shield.active && bots.some(bot => bot.x === player.x && bot.y === player.y);
// 🧱 MOVING WALL ĐÈ LÊN NGƯỜI → CŨNG CHẾT (trừ khi có shield)
const hitMovingWall = !shield.active && isMovingWallAt(player.x, player.y);

if (hitBot || hitMovingWall) {
    // ⭐ RESET PHÍM TRƯỚC KHI ALERT
    keys.w = false;
    keys.a = false;
    keys.s = false;
    keys.d = false;
    
    levelDeaths++;

    alert("💀 Bạn bị bắt / bị tường đè! Hãy thử lại level này.");
    resetGameState(false);  // không reset deaths

    drawMap();
    requestAnimationFrame(gameLoop);
    return;
}

    // ⭐ Cuối cùng mới vẽ map
    drawMap();
    requestAnimationFrame(gameLoop);
}


// ⭐⭐⭐ BẮT ĐẦU VÒNG LẶP GAME (CHỈ 1 LẦN DUY NHẤT!)
if (!gameLoopStarted) {
    gameLoopStarted = true;
    requestAnimationFrame(gameLoop);
}

// 🆕 THÊM EVENT LISTENER ĐỂ GỌI showLevelSelection TỪ NGOÀI
document.addEventListener('showLevelSelection', () => {
    showLevelSelection();
});

}); // <-- Chỉ đóng DOMContentLoaded 1 lần duy nhất