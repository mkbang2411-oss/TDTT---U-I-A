def get_language_toggle_html():
    """
    Component toggle ngôn ngữ VI/EN với CSS đẹp
    Cục tròn trắng có text VN/EN bên trong và trượt qua trượt lại
    Lưu trạng thái vào localStorage để giữ khi chuyển trang
    """
    return """
<!-- ==================== LANGUAGE TOGGLE COMPONENT ==================== -->
<div id="language-toggle-container">
    <div class="lang-toggle-wrapper">
        <label class="lang-switch">
            <input type="checkbox" id="lang-toggle-checkbox">
            <span class="lang-slider">
                <span class="lang-text-left">VN</span>
                <span class="lang-text-right">EN</span>
                <span class="lang-thumb" id="lang-thumb">VN</span>
            </span>
        </label>
    </div>
</div>

<style>
/* ==================== LANGUAGE TOGGLE STYLES ==================== */
#language-toggle-container {
    position: fixed;
    top: 20px;
    left: 33px;
    z-index: 9999;
    transition: all 0.3s ease;
}

#language-toggle-container:hover {
    transform: translateY(-2px);
}

.lang-toggle-wrapper {
    display: flex;
    align-items: center;
    
}

/* Toggle Switch - SMALLER SIZE */
.lang-switch {
    position: relative;
    display: inline-block;
    width: 70px;
    height: 30px;
}

.lang-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.lang-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: #FFF5E6;
    transition: 0.4s;
    border-radius: 40px;
    box-shadow: 
        0 2px 8px rgba(0, 0, 0, 0.2),
        inset 0 1px 2px rgba(255, 255, 255, 0.8);
}

/* Text VN bên trái */
.lang-text-left {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(0, 0, 0, 0.3);
    font-weight: 700;
    font-size: 10px;
    transition: all 0.3s ease;
    pointer-events: none;
    z-index: 1;
}

/* Text EN bên phải */
.lang-text-right {
    position: absolute;
    right: 5px;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(0, 0, 0, 0.3);
    font-weight: 700;
    font-size: 10px;
    transition: all 0.3s ease;
    pointer-events: none;
    z-index: 1;
}

/* Cục tròn trắng với text bên trong */
.lang-thumb {
    position: absolute;
    height: 24px;
    width: 32px;
    left: 3px;
    bottom: 3px;
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    transition: 0.4s;
    border-radius: 24px;
    box-shadow: 
        0 2px 8px rgba(0, 0, 0, 0.3),
        0 0 15px rgba(255, 215, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    
    /* Text styling */
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 9px;
    color: white;
    z-index: 2;
    backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(32px);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Khi checked (EN) */
input:checked + .lang-slider {
    background: #FFF5E6;
}

input:checked + .lang-slider .lang-thumb {
    transform: translateX(35px);
    background: linear-gradient(135deg, #FF8C00 0%, #FF4500 100%);
    color: white;
    box-shadow: 
        0 2px 8px rgba(0, 0, 0, 0.3),
        0 0 15px rgba(255, 140, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

input:checked + .lang-slider .lang-text-left {
    color: rgba(0, 0, 0, 0.2);
}

input:checked + .lang-slider .lang-text-right {
    color: rgba(0, 0, 0, 0.6);
}

/* Khi không checked (VN) */
input:not(:checked) + .lang-slider .lang-text-left {
    color: rgba(0, 0, 0, 0.6);
}

input:not(:checked) + .lang-slider .lang-text-right {
    color: rgba(0, 0, 0, 0.2);
}

.lang-slider:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
    #language-toggle-container {
        top: 10px;
        left: 10px;
    }
    
    .lang-switch {
        width: 60px;
        height: 26px;
    }
    
    .lang-thumb {
        height: 20px;
        width: 28px;
        font-size: 8px;
    }
    
    .lang-text-left,
    .lang-text-right {
        font-size: 9px;
    }
    
    input:checked + .lang-slider .lang-thumb {
        transform: translateX(30px);
    }
}
</style>

<script>
// ==================== LANGUAGE TOGGLE LOGIC ====================
(function() {
    const STORAGE_KEY = 'user_language';
    const checkbox = document.getElementById('lang-toggle-checkbox');
    const langThumb = document.getElementById('lang-thumb');
    
    // Load translations (sẽ fetch từ file JSON)
    let translations = {};
    
    // Load file ngôn ngữ
    async function loadTranslations() {
        try {
            const response = await fetch('/languages.json');
            if (response.ok) {
                translations = await response.json();
                console.log('✅ Đã load translations:', translations);
            } else {
                console.warn('⚠️ Không tìm thấy languages.json, sử dụng bản dịch mặc định');
                // Fallback translations
                translations = {
                    vi: {
                        title: "Trang chủ",
                        greeting: "Xin chào!",
                        instruction: "Chọn ngôn ngữ ở góc trên bên phải"
                    },
                    en: {
                        title: "Home",
                        greeting: "Hello!",
                        instruction: "Select language at top right corner"
                    }
                };
            }
        } catch (error) {
            console.error('❌ Error loading translations:', error);
        }
    }
    
    // Lấy ngôn ngữ hiện tại
    function getCurrentLanguage() {
        return localStorage.getItem(STORAGE_KEY) || 'vi';
    }
    
    // Lưu ngôn ngữ
    function setLanguage(lang) {
        localStorage.setItem(STORAGE_KEY, lang);
        updateUI(lang);
        applyTranslations(lang);
        
        // Dispatch event để các component khác biết
        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { language: lang } 
        }));
        
        console.log(`🌐 Language changed to: ${lang}`);
    }
    
    // Update UI
    function updateUI(lang) {
        const isEnglish = lang === 'en';
        checkbox.checked = isEnglish;
        
        // Update text trong cục tròn
        if (langThumb) {
            langThumb.textContent = isEnglish ? 'EN' : 'VN';
        }
    }
    
    // Áp dụng bản dịch cho trang
    function applyTranslations(lang) {
        if (!translations[lang]) return;
        
        const langData = translations[lang];
        
        // Tìm và thay thế các element có data-translate
        document.querySelectorAll('[data-translate]').forEach(el => {
            const key = el.getAttribute('data-translate');
            if (langData[key]) {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    el.placeholder = langData[key];
                } else {
                    el.textContent = langData[key];
                }
            }
        });
        
        // Xử lý placeholder riêng
        document.querySelectorAll('[data-translate-placeholder]').forEach(el => {
            const key = el.getAttribute('data-translate-placeholder');
            if (langData[key]) {
                el.placeholder = langData[key];
            }
        });
        
        // Xử lý title/tooltip
        document.querySelectorAll('[data-translate-title]').forEach(el => {
            const key = el.getAttribute('data-translate-title');
            if (langData[key]) {
                el.title = langData[key];
            }
        });
    }
    
    // Event listeners
    if (checkbox) {
        checkbox.addEventListener('change', function() {
            const newLang = this.checked ? 'en' : 'vi';
            setLanguage(newLang);
        });
    }
    
    // Initialize
    async function init() {
        await loadTranslations();
        const currentLang = getCurrentLanguage();
        updateUI(currentLang);
        applyTranslations(currentLang);
    }
    
    // Chạy khi trang load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
// Export functions cho global scope
    window.LanguageToggle = {
        getCurrentLanguage,
        setLanguage,
        applyTranslations: () => {
            const currentLang = getCurrentLanguage();
            applyTranslations(currentLang);
        },
        getTranslation: (key) => {
            const lang = getCurrentLanguage();
            return translations[lang]?.[key] || key;
        }
    };
})();
</script>
<!-- ==================== END LANGUAGE TOGGLE COMPONENT ==================== -->
"""