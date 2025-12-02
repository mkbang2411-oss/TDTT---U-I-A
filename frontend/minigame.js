// ========================================
// 🧩 JIGSAW PUZZLE MINI GAME WITH PROGRESS SAVE
// ========================================

class JigsawPuzzle {
  constructor() {
    this.svg = document.getElementById("puzzle");
    
    if (!this.svg) {
      console.error("Không tìm thấy SVG #puzzle");
      return;
    }

    this.svg.style.display = 'block';
    
    this.defs = this.svg.querySelector("defs");
    this.layer = document.getElementById("pieces");
    this.piecePaths = [...this.defs.querySelectorAll("path")];
    
    this.pieces = [];
    this.draggedPiece = null;
    this.dragOffset = { x: 0, y: 0 };
    this.snapThreshold = 30;
    
    this.moves = 0;
    this.startTime = null;
    this.timerInterval = null;
    this.completedPieces = 0;
    
    this.svgNS = "http://www.w3.org/2000/svg";
    this.xlinkNS = "http://www.w3.org/1999/xlink";
    
    this.currentMap = "banh_mi";
    this.userProgress = {}; // 🆕 Lưu tiến độ user
    
    this.init();
  }
  
  async init() {
    // Load progress async - không block
    this.loadUserProgress().then(() => {
        this.updateMapButtons();
    }).catch(() => {
        console.log('Chưa có progress');
    });

    this.createPieces();
    this.setupEventListeners();
    this.setupMapSelector();
    
    // 🆕 Kiểm tra xem map hiện tại đã hoàn thành chưa
    // ✅ CHỜ 200MS ĐỂ ĐẢM BẢO DOM ĐÃ SẴN SÀNG
    setTimeout(() => {
      if (this.isMapCompleted(this.currentMap)) {
        this.showCompletedState();
      } else {
        this.shuffle();
        this.startTimer();
      }
    }, 50);
  }
  
  // 🆕 LOAD TIẾN ĐỘ USER
  async loadUserProgress() {
    try {
      const response = await fetch('/api/puzzle/progress/', {
        credentials: 'include'
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        this.userProgress = data.progress;
        console.log('✅ Đã load tiến độ:', this.userProgress);
        // ✅ CHỈ CẬP NHẬT SAU KHI DOM SẴN SÀNG
        setTimeout(() => {
          this.updateMapButtons();
        }, 100);
      }
    } catch (error) {
      console.log('ℹ️ Chưa đăng nhập hoặc chưa có tiến độ');
      this.userProgress = {};
    }
  }
  
  // 🆕 KIỂM TRA MAP ĐÃ HOÀN THÀNH CHƯA
  isMapCompleted(mapName) {
    return this.userProgress[mapName]?.completed === true;
  }
  
  // 🆕 CẬP NHẬT GIAO DIỆN NÚT MAP (thêm dấu ✅)
  updateMapButtons() {
    const mapButtons = document.querySelectorAll('.map-option');
    mapButtons.forEach(btn => {
      const mapName = btn.dataset.map;
      const span = btn.querySelector('span');
      
      if (this.isMapCompleted(mapName)) {
        // Thêm dấu tích vào map đã hoàn thành
        if (!span.textContent.includes('✅')) {
          span.textContent = '✅ ' + span.textContent;
        }
        btn.style.background = 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)';
      } else {
        // Xóa dấu tích nếu có
        span.textContent = span.textContent.replace('✅ ', '');
        btn.style.background = '';
      }
    });
  }
  
  // 🆕 HIỂN THỊ TRẠNG THÁI ĐÃ HOÀN THÀNH
  showCompletedState() {
    // ✅ KIỂM TRA PIECES ĐÃ TẠO CHƯA
    if (this.pieces.length === 0) {
      console.warn('⚠️ Pieces chưa được tạo, bỏ qua showCompletedState');
      return;
    }
    
    // Đặt tất cả mảnh về đúng vị trí
    this.pieces.forEach(piece => {
      piece.currentX = piece.correctX;
      piece.currentY = piece.correctY;
      piece.isCorrect = true;
      piece.element.classList.add('correct');
      this.updatePiecePosition(piece);
    });
    
    this.completedPieces = this.pieces.length;
    
    // Hiển thị thông tin
    const progress = this.userProgress[this.currentMap];
    if (progress) {
      const minutes = Math.floor(progress.completion_time / 60);
      const seconds = progress.completion_time % 60;
      
      const timerEl = document.querySelector('.mini-game-overlay .timer span');
      const movesEl = document.querySelector('.mini-game-overlay .moves span');
      
      if (timerEl) timerEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      if (movesEl) movesEl.textContent = progress.moves_count;
    }
    
    // 🆕 ẨN NÚT XÁO LẠI
    this.hideShuffleButton();
    
    // Thêm nút Reset
    this.addResetButton();
  }
  
  // 🆕 ẨN NÚT XÁO LẠI
  hideShuffleButton() {
    const shuffleBtn = document.querySelector('.mini-game-overlay .btn-shuffle');
    if (shuffleBtn) {
      shuffleBtn.style.display = 'none';
    }
  }
  
  // 🆕 HIỆN NÚT XÁO LẠI
  showShuffleButton() {
    const shuffleBtn = document.querySelector('.mini-game-overlay .btn-shuffle');
    if (shuffleBtn) {
      shuffleBtn.style.display = 'block';
    }
  }
  
  // 🆕 THÊM NÚT RESET
  addResetButton() {
    const header = document.querySelector('.mini-game-overlay .game-header');
    
    // ✅ KIỂM TRA HEADER TỒN TẠI
    if (!header) {
      console.warn('⚠️ Không tìm thấy game-header, bỏ qua thêm nút reset');
      return;
    }
    
    // Xóa nút cũ nếu có
    const oldResetBtn = document.getElementById('btnResetProgress');
    if (oldResetBtn) oldResetBtn.remove();
    
    const resetBtn = document.createElement('button');
    resetBtn.id = 'btnResetProgress';
    resetBtn.className = 'btn-shuffle';
    resetBtn.innerHTML = '🔄 Chơi lại';
    resetBtn.style.background = '#ef4444';
    
    resetBtn.addEventListener('click', () => this.resetProgress());
    
    header.appendChild(resetBtn);
  }
  
  // 🆕 RESET TIẾN ĐỘ
  async resetProgress() {
    if (!confirm('Bạn có chắc muốn reset tiến độ map này?')) return;
    
    try {
      const response = await fetch(`/api/puzzle/reset/${this.currentMap}/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Xóa tiến độ khỏi local
        delete this.userProgress[this.currentMap];
        
        // Xóa nút reset
        const resetBtn = document.getElementById('btnResetProgress');
        if (resetBtn) resetBtn.remove();
        
        // 🆕 HIỆN LẠI NÚT XÁO
        this.showShuffleButton();
        
        // Update lại giao diện map buttons
        this.updateMapButtons();
        
        // Reset game
        this.reset();
        
        console.log('✅ Đã reset tiến độ');
      }
    } catch (error) {
      console.error('❌ Lỗi reset:', error);
      alert('Lỗi khi reset tiến độ. Vui lòng thử lại!');
    }
  }
  
 setupMapSelector() {
  // 🆕 1. XỬ LÝ TAB SWITCHING
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      
      // Remove active từ tất cả
      tabButtons.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      // Add active cho tab được chọn
      btn.classList.add('active');
      document.getElementById(`tab-${targetTab}`).classList.add('active');
      
      // 🆕 Nếu click vào tab Achievements → Load achievements
      if (targetTab === 'achievements') {
        this.loadAchievements();
      }
    });
  });
  
  // 🆕 2. XỬ LÝ CLICK MAP OPTIONS (giữ nguyên logic cũ)
  const mapButtons = document.querySelectorAll('.map-option');
  
  mapButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const newMap = btn.dataset.map;
      
      mapButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      this.changeMap(newMap);
    });
  });
}
  // 🆕 Helper function để preload ảnh
  preloadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        console.log('✅ Ảnh đã load xong:', src);
        resolve(img);
      };
      img.onerror = () => {
        console.error('❌ Lỗi load ảnh:', src);
        reject();
      };
      img.src = src;
    });
  }

  // 🆕 Hiển thị loading spinner
  showLoadingState() {
    const overlay = document.querySelector('.mini-game-overlay');
    let loader = overlay.querySelector('.map-loading');
    
    if (!loader) {
      loader = document.createElement('div');
      loader.className = 'map-loading';
      loader.innerHTML = `
        <div class="spinner"></div>
        <p>Đang tải ảnh...</p>
      `;
      overlay.appendChild(loader);
    }
    
    loader.classList.add('show');
  }

  // 🆕 Ẩn loading spinner
  hideLoadingState() {
    const loader = document.querySelector('.map-loading');
    if (loader) {
      loader.classList.remove('show');
    }
  }
  
  async changeMap(mapName) {
  // 🆕 1. Hiển thị loading NGAY LẬP TỨC
  this.showLoadingState();
  
  this.currentMap = mapName;
  
  // ❌ BỎ CACHE-BUSTING ?t=
  const imagePath = `Picture/${mapName}.png`;
  
  console.log('🗺️ Đổi map sang:', imagePath);
  
  try {
    // 🆕 2. Chờ ảnh load xong TRƯỚC KHI update DOM
    await this.preloadImage(imagePath);
    
    // 3. Đổi ảnh trong defs
    const fullImg = this.defs.querySelector('#full-img');
    if (fullImg) {
      fullImg.setAttributeNS(this.xlinkNS, 'href', imagePath);
    }
    
    // 4. Đổi tất cả ảnh trong các mảnh ghép
    this.pieces.forEach(piece => {
      const img = piece.element.querySelector('image');
      if (img) {
        img.setAttributeNS(this.xlinkNS, 'href', imagePath);
      }
    });
    
    // 5. Đổi ảnh nền mờ
    const oldBgImg = this.svg.querySelector('#bg-hint-img');
    if (oldBgImg) {
      oldBgImg.remove();
      console.log('🗑️ Đã xóa background cũ');
    }

    const newBgImg = document.createElementNS(this.svgNS, 'image');
    newBgImg.id = 'bg-hint-img';
    newBgImg.setAttributeNS(this.xlinkNS, 'href', imagePath);
    newBgImg.setAttribute('x', '0');
    newBgImg.setAttribute('y', '0');
    newBgImg.setAttribute('width', '1071');
    newBgImg.setAttribute('height', '750');
    newBgImg.setAttribute('preserveAspectRatio', 'none');
    newBgImg.setAttribute('opacity', '0.18');
    newBgImg.style.pointerEvents = 'none';

    this.svg.insertBefore(newBgImg, this.layer);
    console.log('✅ Đã thêm background mới:', imagePath);
    
  } catch (error) {
    console.error('❌ Lỗi khi đổi map:', error);
    alert('Không thể tải ảnh. Vui lòng thử lại!');
  } finally {
    // 🆕 6. ẨN LOADING SAU KHI XONG
    this.hideLoadingState();
  }
  
  // 7. Kiểm tra map mới đã hoàn thành chưa
  if (this.isMapCompleted(mapName)) {
    this.showCompletedState();
  } else {
    const resetBtn = document.getElementById('btnResetProgress');
    if (resetBtn) resetBtn.remove();
    
    this.showShuffleButton();
    this.reset();
  }
}
  
  createPieces() {
    const viewBox = this.svg.viewBox.baseVal;
    const imgWidth = viewBox.width;
    const imgHeight = viewBox.height;
    
    this.piecePaths.forEach((path, index) => {
      const bbox = path.getBBox();
      
      const cp = document.createElementNS(this.svgNS, "clipPath");
      cp.id = `clip-${index}`;
      const useClip = document.createElementNS(this.svgNS, "use");
      useClip.setAttributeNS(this.xlinkNS, "xlink:href", `#${path.id}`);
      cp.appendChild(useClip);
      this.defs.appendChild(cp);
      
      const g = document.createElementNS(this.svgNS, "g");
      g.classList.add("piece");
      g.dataset.id = index;
      
      const img = document.createElementNS(this.svgNS, "image");
      img.setAttributeNS(this.xlinkNS, "xlink:href", `Picture/${this.currentMap}.png`);
      img.setAttribute("x", "0");
      img.setAttribute("y", "0");
      img.setAttribute("width", imgWidth);
      img.setAttribute("height", imgHeight);
      img.setAttribute("clip-path", `url(#clip-${index})`);
      img.setAttribute("preserveAspectRatio", "none");
      
      const outline = document.createElementNS(this.svgNS, "use");
      outline.setAttributeNS(this.xlinkNS, "xlink:href", `#${path.id}`);
      outline.setAttribute("style", "fill:none;stroke:#333;stroke-width:2");
      
      g.appendChild(img);
      g.appendChild(outline);
      this.layer.appendChild(g);
      
      this.pieces.push({
        element: g,
        index: index,
        correctX: 0,
        correctY: 0,
        currentX: 0,
        currentY: 0,
        isCorrect: false,
        bbox: bbox
      });
    });
  }
  
  shuffle() {
    const boardWidth = 1071;
    const boardHeight = 750;
    
    this.pieces.forEach(piece => {
      const randomX = (Math.random() - 0.5) * 300;
      const randomY = (Math.random() - 0.5) * 300;
      
      piece.currentX = Math.max(-100, Math.min(boardWidth - 100, randomX));
      piece.currentY = Math.max(-100, Math.min(boardHeight - 100, randomY));
      
      this.updatePiecePosition(piece);
    });
    
    this.completedPieces = 0;
    this.updateStats();
  }
  
  updatePiecePosition(piece) {
    piece.element.setAttribute("transform", 
      `translate(${piece.currentX}, ${piece.currentY})`);
  }
  
  setupEventListeners() {
    const btnShuffle = document.querySelector('.mini-game-overlay .btn-shuffle');
    if (btnShuffle) {
      btnShuffle.addEventListener('click', () => this.reset());
    }
    
    this.svg.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.svg.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.svg.addEventListener('mouseup', (e) => this.onMouseUp(e));
    
    this.svg.addEventListener('touchstart', (e) => this.onTouchStart(e), { passive: false });
    this.svg.addEventListener('touchmove', (e) => this.onTouchMove(e), { passive: false });
    this.svg.addEventListener('touchend', (e) => this.onTouchEnd(e));
  }
  
  getPointerPosition(e) {
    const pt = this.svg.createSVGPoint();
    pt.x = e.clientX || (e.touches && e.touches[0].clientX);
    pt.y = e.clientY || (e.touches && e.touches[0].clientY);
    
    const svgP = pt.matrixTransform(this.svg.getScreenCTM().inverse());
    return { x: svgP.x, y: svgP.y };
  }
  
  onMouseDown(e) {
    const target = e.target.closest('.piece');
    if (!target || target.classList.contains('correct')) return;
    
    const piece = this.pieces.find(p => p.element === target);
    if (!piece) return;
    
    this.draggedPiece = piece;
    const pos = this.getPointerPosition(e);
    
    this.dragOffset.x = pos.x - piece.currentX;
    this.dragOffset.y = pos.y - piece.currentY;
    
    piece.element.classList.add('dragging');
    this.layer.appendChild(piece.element);
  }
  
  onMouseMove(e) {
    if (!this.draggedPiece) return;
    e.preventDefault();
    
    const pos = this.getPointerPosition(e);
    this.draggedPiece.currentX = pos.x - this.dragOffset.x;
    this.draggedPiece.currentY = pos.y - this.dragOffset.y;
    
    this.updatePiecePosition(this.draggedPiece);
  }
  
  onMouseUp(e) {
    if (!this.draggedPiece) return;
    
    this.draggedPiece.element.classList.remove('dragging');
    this.checkPiecePosition(this.draggedPiece);
    this.draggedPiece = null;
    
    this.moves++;
    this.updateStats();
  }
  
  onTouchStart(e) {
    if (e.touches.length === 1) {
      this.onMouseDown(e.touches[0]);
    }
  }
  
  onTouchMove(e) {
    if (this.draggedPiece && e.touches.length === 1) {
      e.preventDefault();
      this.onMouseMove(e.touches[0]);
    }
  }
  
  onTouchEnd(e) {
    this.onMouseUp(e);
  }
  
  checkPiecePosition(piece) {
    const dx = Math.abs(piece.currentX - piece.correctX);
    const dy = Math.abs(piece.currentY - piece.correctY);
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance < this.snapThreshold) {
      piece.currentX = piece.correctX;
      piece.currentY = piece.correctY;
      piece.isCorrect = true;
      piece.element.classList.add('correct');
      
      this.updatePiecePosition(piece);
      this.completedPieces++;
      
      if (this.completedPieces === this.pieces.length) {
        this.onComplete();
      }
    }
  }
  
  startTimer() {
    this.startTime = Date.now();
    this.timerInterval = setInterval(() => {
      this.updateTimer();
    }, 1000);
  }
  
  updateTimer() {
    const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    const timerEl = document.querySelector('.mini-game-overlay .timer span');
    if (timerEl) {
      timerEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
  }
  
  updateStats() {
    const movesEl = document.querySelector('.mini-game-overlay .moves span');
    if (movesEl) {
      movesEl.textContent = this.moves;
    }
  }
  
  onComplete() {
    clearInterval(this.timerInterval);
    this.svg.classList.add('completed');
    
    // 🆕 Lưu tiến độ vào database
    const completionTime = Math.floor((Date.now() - this.startTime) / 1000);
    this.saveCompletion(completionTime, this.moves);
    
    setTimeout(() => {
      this.showCompletionModal();
    }, 600);
  }
  
  // 🆕 LƯU TIẾN ĐỘ HOÀN THÀNH
  // 🆕 LƯU TIẾN ĐỘ HOÀN THÀNH
async saveCompletion(completionTime, moves) {
  try {
    // 1️⃣ Lưu tiến độ puzzle
    const response = await fetch('/api/puzzle/complete/', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        map_name: this.currentMap,
        completion_time: completionTime,
        moves_count: moves
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('✅ Đã lưu tiến độ hoàn thành');
      
      // Cập nhật local progress
      this.userProgress[this.currentMap] = {
        completed: true,
        completion_time: completionTime,
        moves_count: moves
      };
      
      // Cập nhật giao diện map buttons
      this.updateMapButtons();
      
      // 2️⃣ 🆕 TỰ ĐỘNG UNLOCK FOOD STORY
      await this.unlockFoodStory();
    }
  } catch (error) {
    console.log('ℹ️ Chưa đăng nhập, không lưu tiến độ');
  }
}

// 🆕 UNLOCK FOOD STORY
async unlockFoodStory() {
  try {
    const response = await fetch(`/api/food-story/unlock/${this.currentMap}/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (data.status === 'success' && data.is_new) {
      console.log('🎉 Đã unlock food story:', data.story_preview.title);
      // Sẽ hiển thị trong completion modal
    }
  } catch (error) {
    console.log('ℹ️ Không thể unlock food story');
  }
}
  
  async showCompletionModal() {
  const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  
  const overlay = document.getElementById('miniGameOverlay');
  const modal = document.createElement('div');
  modal.className = 'completion-modal show';
  
  // 🆕 LẤY THÔNG TIN FOOD STORY
  let storyUnlockHTML = '';
  try {
    const response = await fetch(`/api/food-story/${this.currentMap}/`, {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.status === 'unlocked') {
      const story = data.story;
      storyUnlockHTML = `
        <div class="story-unlock-section">
          <div class="unlock-badge">🎉 ĐÃ MỞ KHÓA 🎉</div>
          <h3>📖 ${story.title}</h3>
          <p class="story-desc">${story.description}</p>
          <div class="story-stats">
            <span>💡 ${story.fun_facts.length} Fun Facts</span>
            <span>🍽️ ${story.variants.length} Biến thể</span>
            ${story.unesco_recognized ? '<span>🏆 UNESCO nhận nhận</span>' : ''}
          </div>
          <button class="btn-view-story" data-map="${this.currentMap}">
            Xem câu chuyện đầy đủ →
          </button>
        </div>
      `;
    }
  } catch (error) {
    console.log('Không thể load food story');
  }
  
  modal.innerHTML = `
    <div class="modal-content">
      <h2>🎉 Chúc mừng! 🎉</h2>
      <p>Bạn đã hoàn thành puzzle!</p>
      <div class="stats">
        <div>⏱️ Thời gian: ${minutes}:${seconds.toString().padStart(2, '0')}</div>
        <div>🔄 Số bước: ${this.moves}</div>
      </div>
      
      ${storyUnlockHTML}
      
      <button class="btn-play-again">Đóng</button>
    </div>
  `;
  
  overlay.appendChild(modal);
  
  // Event: Đóng modal
  modal.querySelector('.btn-play-again').addEventListener('click', () => {
    modal.remove();
    this.showCompletedState();
  });
  
  // 🆕 Event: Xem Food Story
  const btnViewStory = modal.querySelector('.btn-view-story');
  if (btnViewStory) {
    btnViewStory.addEventListener('click', () => {
      modal.remove();
      this.showFoodStoryModal(btnViewStory.dataset.map);
    });
  }
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
      this.showCompletedState();
    }
  });
}
// 🆕 HIỂN THỊ FOOD STORY ĐẦY ĐỦ
async showFoodStoryModal(mapName) {
  try {
    const response = await fetch(`/api/food-story/${mapName}/`, {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.status !== 'unlocked') {
      alert('Bạn cần hoàn thành puzzle để xem câu chuyện!');
      return;
    }
    
    const story = data.story;
    const overlay = document.getElementById('miniGameOverlay');
    const modal = document.createElement('div');
    modal.className = 'food-story-modal show';
    
    // Tạo HTML Fun Facts
    const funFactsHTML = story.fun_facts.map(fact => 
      `<li>${fact}</li>`
    ).join('');
    
    // Tạo HTML Variants
    const variantsHTML = story.variants.map(variant => 
      `<span class="variant-tag">${variant}</span>`
    ).join('');
    
    modal.innerHTML = `
      <div class="story-modal-content">
        <button class="story-close-btn">×</button>
        
        <div class="story-header">
          <img src="${story.image_url}" alt="${story.title}" />
          <div class="story-title-section">
            <h2>${story.title}</h2>
            <p class="story-origin">📍 ${story.origin_region}</p>
            ${story.unesco_recognized ? `
              <div class="unesco-badge">
                🏆 ${story.recognition_text}
              </div>
            ` : ''}
          </div>
        </div>
        
        <div class="story-body">
          <section class="story-section">
            <h3>📜 Lịch Sử Hình Thành</h3>
            <p class="story-text">${story.history.trim()}</p>
          </section>
          
          <section class="story-section">
            <h3>💡 Fun Facts</h3>
            <ul class="fun-facts-list">
              ${funFactsHTML}
            </ul>
          </section>
          
          <section class="story-section">
            <h3>🍽️ Các Biến Thể Phổ Biến</h3>
            <div class="variants-container">
              ${variantsHTML}
            </div>
          </section>
          
          ${story.video_url ? `
            <section class="story-section">
              <h3>🎥 Video Giới Thiệu</h3>
              <a href="${story.video_url}" target="_blank" class="btn-watch-video">
                Xem video →
              </a>
            </section>
          ` : ''}
        </div>
      </div>
    `;
    
    overlay.appendChild(modal);
    
    // Event đóng modal
    const closeBtn = modal.querySelector('.story-close-btn');
    closeBtn.addEventListener('click', () => modal.remove());
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });
    
  } catch (error) {
    console.error('Lỗi load food story:', error);
    alert('Không thể tải thông tin món ăn!');
  }
}
// 🆕 LOAD VÀ HIỂN THỊ DANH SÁCH THÀNH TỰU
async loadAchievements() {
  const container = document.querySelector('.achievements-container');
  
  // Hiển thị loading
  container.innerHTML = '<p class="loading-achievements">Đang tải thành tựu...</p>';
  
  try {
    const response = await fetch('/api/food-stories/unlocked/', {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.status === 'success') {
      if (data.count === 0) {
        // Chưa có thành tựu nào
        container.innerHTML = `
          <div class="empty-achievements">
            <div class="empty-achievements-icon">🏆</div>
            <p class="empty-achievements-text">
              Bạn chưa có thành tựu nào!<br>
              Hoàn thành puzzle để mở khóa.
            </p>
          </div>
        `;
        return;
      }
      
      // Có thành tựu → Hiển thị danh sách
      this.renderAchievements(data.stories);
    }
  } catch (error) {
    console.error('Lỗi load achievements:', error);
    container.innerHTML = `
      <div class="empty-achievements">
        <div class="empty-achievements-icon">⚠️</div>
        <p class="empty-achievements-text">
          Không thể tải thành tựu.<br>
          Vui lòng đăng nhập để xem!
        </p>
      </div>
    `;
  }
}

// 🆕 RENDER DANH SÁCH THÀNH TỰU
// 🆕 RENDER DANH SÁCH THÀNH TỰU - GỌNG HƠN
async renderAchievements(unlockedStories) {
  const container = document.querySelector('.achievements-container');
  
  // Danh sách TẤT CẢ các món (bao gồm locked và unlocked)
  const allMaps = [
    { map_name: 'banh_mi', title: 'Bánh Mì', image: 'https://res.cloudinary.com/dbmq2hme4/image/upload/Picture/banh_mi.png' },
    { map_name: 'com_tam', title: 'Cơm Tấm', image: 'https://res.cloudinary.com/dbmq2hme4/image/upload/Picture/com_tam.png' },
    { map_name: 'bun_bo_hue', title: 'Bún Bò Huế', image: 'https://res.cloudinary.com/dbmq2hme4/image/upload/Picture/bun_bo_hue.png' }
  ];
  
  // Tạo Set các map đã unlock để check nhanh
  const unlockedMapNames = new Set(unlockedStories.map(s => s.map_name));
  
  let html = '';
  
  for (const mapInfo of allMaps) {
    const isUnlocked = unlockedMapNames.has(mapInfo.map_name);
    
    if (isUnlocked) {
      // ✅ ĐÃ MỞ KHÓA - Card xanh lá
      html += `
        <div class="achievement-card unlocked" data-map="${mapInfo.map_name}">
          <span class="achievement-badge">✅</span>
          <img src="${mapInfo.image}" alt="${mapInfo.title}" class="achievement-icon">
          <h4 class="achievement-title">${mapInfo.title}</h4>
        </div>
      `;
    } else {
      // 🔒 CHƯA MỞ KHÓA - Card xám
      html += `
        <div class="achievement-card locked">
          <span class="achievement-badge">🔒</span>
          <img src="${mapInfo.image}" alt="${mapInfo.title}" class="achievement-icon">
          <h4 class="achievement-title">${mapInfo.title}</h4>
        </div>
      `;
    }
  }
  
  container.innerHTML = html;
  
  // 🆕 THÊM EVENT CLICK VÀO CÁC CARD ĐÃ MỞ KHÓA
  const unlockedCards = container.querySelectorAll('.achievement-card.unlocked');
  unlockedCards.forEach(card => {
    card.addEventListener('click', () => {
      const mapName = card.dataset.map;
      this.showFoodStoryModal(mapName);
    });
  });
}
  
  reset() {
    this.moves = 0;
    this.completedPieces = 0;
    this.updateStats();
    
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    
    this.pieces.forEach(piece => {
      piece.isCorrect = false;
      piece.element.classList.remove('correct');
    });
    
    this.svg.classList.remove('completed');
    
    // 🆕 ĐẢM BẢO NÚT XÁO ĐƯỢC HIỆN
    this.showShuffleButton();
    
    this.shuffle();
    this.startTimer();
  }
  // ✅ CLEANUP KHI ĐÓNG MINI GAME
    cleanup() {
      // Xóa ảnh background hint
      if (this.svg) {
        const bgHint = this.svg.querySelector('#bg-hint-img');
        if (bgHint) {
          bgHint.remove();
          console.log('🗑️ Đã xóa background hint image');
        }
      }
      
      // Dừng timer
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
    }
}



    

// ========================================
// 🎮 MỞ/ĐÓNG MINI GAME
// ========================================

let puzzleGame = null;

function ensurePuzzleReady() {
  if (!puzzleGame) {
    puzzleGame = new JigsawPuzzle();
  }
}

function initMiniGame() {
  const openBtn = document.getElementById('miniGameBtn');
  const closeBtn = document.getElementById('miniGameCloseBtn');
  const overlay = document.getElementById('miniGameOverlay');
  
  if (!openBtn || !closeBtn || !overlay) {
    console.error('Không tìm thấy các element mini game');
    return;
  }
    
  openBtn.addEventListener('click', () => {
    // 🚀 MỞ OVERLAY TRƯỚC TIÊN
    overlay.classList.remove('hidden');

    // ⚡ ĐÓNG CHATBOT ĐỒNG BỘ (nhanh)
    const chatWindow = document.getElementById('chatWindow');
    const chatbotBtn = document.getElementById('chatbotBtn');
    const speechBubble = document.getElementById('speechBubble');
    const chatHistorySidebar = document.getElementById('chatHistorySidebar');

    if (chatWindow) {
      chatWindow.classList.remove('open');
      chatWindow.style.display = 'none';
    }
    if (chatbotBtn) {
      chatbotBtn.style.display = 'flex';
      chatbotBtn.classList.remove('hidden');
    }
    if (speechBubble) {
      speechBubble.style.display = 'block';
      speechBubble.classList.remove('hidden');
    }
    if (chatHistorySidebar) {
      chatHistorySidebar.classList.remove('open');
    }

    // ✅ ĐẢM BẢO PUZZLE ĐÃ ĐƯỢC TẠO SẴN (nhẹ hơn rất nhiều)
    ensurePuzzleReady();

    // Khi user mở game thì reset lại timer + shuffle
    if (puzzleGame.isMapCompleted(puzzleGame.currentMap)) {
      puzzleGame.showCompletedState();
    } else {
      puzzleGame.reset();
    }
  });

  closeBtn.addEventListener('click', () => {
    overlay.classList.add('hidden');
    
    if (puzzleGame && puzzleGame.timerInterval) {
      clearInterval(puzzleGame.timerInterval);
    }
  });
  
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.add('hidden');
      if (puzzleGame && puzzleGame.timerInterval) {
        clearInterval(puzzleGame.timerInterval);
      }
    }
  });
}

// ========================================
// 🚀 PRELOAD TẤT CẢ ẢNH MAP
// ========================================
function preloadMapImages() {
  const maps = ['banh_mi', 'com_tam', 'bun_bo_hue'];
  
  console.log('🖼️ Bắt đầu preload ảnh...');
  
  maps.forEach(mapName => {
    const img = new Image();
    img.src = `Picture/${mapName}.png`;
    img.onload = () => console.log(`✅ Đã load: ${mapName}.png`);
    img.onerror = () => console.error(`❌ Lỗi load: ${mapName}.png`);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('🎮 Mini Game script loaded');
  initMiniGame();
  
  // 🔥 PRELOAD ẢNH NGAY KHI PAGE LOAD
  preloadMapImages();

  // 🔥 Preload puzzle ở background
  if ('requestIdleCallback' in window) {
    requestIdleCallback(ensurePuzzleReady);
  } else {
    setTimeout(ensurePuzzleReady, 500);
  }
});

