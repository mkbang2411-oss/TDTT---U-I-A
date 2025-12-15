def get_language_toggle_html():
    """
    Component toggle ngôn ngữ VI/EN với CSS đẹp
    ✨ V3: FIX LƯU TRỮ - Không tự chuyển về English
    - Lưu vào CẢLOCALstorage + COOKIE (double backup)
    - Mặc định: Tiếng Việt nếu chưa có lựa chọn
    - Không bao giờ tự reset về English
    """
    return """
<!-- ==================== LANGUAGE TOGGLE COMPONENT V3 (FIXED) ==================== -->
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
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 9px;
    color: white;
    z-index: 2;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

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

input:not(:checked) + .lang-slider .lang-text-left {
    color: rgba(0, 0, 0, 0.6);
}

input:not(:checked) + .lang-slider .lang-text-right {
    color: rgba(0, 0, 0, 0.2);
}

.lang-slider:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

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

@keyframes sync-pulse {
    0%, 100% { 
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2),
                    inset 0 1px 2px rgba(255, 255, 255, 0.8);
    }
    50% { 
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.8),
                    inset 0 1px 2px rgba(255, 255, 255, 0.8);
    }
}

.lang-slider.syncing {
    animation: sync-pulse 0.6s ease-in-out;
}
</style>

<script>
// ==================== LANGUAGE TOGGLE LOGIC V3 (FIXED) ====================
(function() {
    const STORAGE_KEY = 'user_language';
    const COOKIE_NAME = 'user_lang';
    const CHANNEL_NAME = 'language-sync-channel';
    const DEFAULT_LANGUAGE = 'vi'; // ✅ MẶC ĐỊNH LÀ TIẾNG VIỆT
    
    const checkbox = document.getElementById('lang-toggle-checkbox');
    const langThumb = document.getElementById('lang-thumb');
    const langSlider = document.querySelector('.lang-slider');
    
    let translations = {};
    let broadcastChannel = null;
    
    // ==================== COOKIE HELPERS ====================
    function setCookie(name, value, days = 365) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Lax";
        console.log(`🍪 Cookie set: ${name}=${value}`);
    }
    
    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) {
                const value = c.substring(nameEQ.length, c.length);
                console.log(`🍪 Cookie read: ${name}=${value}`);
                return value;
            }
        }
        console.log(`🍪 Cookie not found: ${name}`);
        return null;
    }
    
    // ==================== BROADCAST CHANNEL ====================
    if ('BroadcastChannel' in window) {
        try {
            broadcastChannel = new BroadcastChannel(CHANNEL_NAME);
            console.log('✅ BroadcastChannel initialized');
        } catch (e) {
            console.warn('⚠️ BroadcastChannel failed:', e);
        }
    }
    
    // ==================== LOAD TRANSLATIONS ====================
    async function loadTranslations() {
        try {
            const response = await fetch('/languages.json');
            if (response.ok) {
                translations = await response.json();
                console.log('✅ Loaded translations');
            } else {
                // Fallback
                translations = {
                    vi: { title: "Trang chủ", greeting: "Xin chào!" },
                    en: { title: "Home", greeting: "Hello!" }
                };
            }
        } catch (error) {
            console.error('❌ Translation load error:', error);
            translations = {
                vi: { title: "Trang chủ", greeting: "Xin chào!" },
                en: { title: "Home", greeting: "Hello!" }
            };
        }
    }
    
    // ==================== GET CURRENT LANGUAGE (FIXED V3 - IGNORE BROWSER) ====================
    function getCurrentLanguage() {
        // ⚠️ CRITICAL: NEVER use navigator.language - it causes auto-switching!
        // Priority: localStorage > Cookie > Default (NEVER browser language)
        
        let lang = null;
        
        // 1. Check localStorage FIRST
        try {
            lang = localStorage.getItem(STORAGE_KEY);
            if (lang && (lang === 'vi' || lang === 'en')) {
                console.log(`📦 Language from localStorage: ${lang}`);
                return lang;
            }
            
            // ⚠️ Clear invalid values
            if (lang) {
                console.warn(`⚠️ Invalid language in localStorage: "${lang}", clearing...`);
                localStorage.removeItem(STORAGE_KEY);
            }
        } catch (e) {
            console.warn('⚠️ localStorage read failed:', e);
        }
        
        // 2. Check Cookie
        lang = getCookie(COOKIE_NAME);
        if (lang && (lang === 'vi' || lang === 'en')) {
            console.log(`🍪 Language from cookie: ${lang}`);
            // Sync back to localStorage
            try {
                localStorage.setItem(STORAGE_KEY, lang);
            } catch (e) {}
            return lang;
        }
        
        // ⚠️ Clear invalid cookie
        if (lang) {
            console.warn(`⚠️ Invalid language in cookie: "${lang}", clearing...`);
            document.cookie = `${COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        }
        
        // 3. Default - ALWAYS Vietnamese, NEVER use browser language
        console.log(`🌍 First visit - Setting default: ${DEFAULT_LANGUAGE} (ignoring browser: ${navigator.language})`);
        try {
            localStorage.setItem(STORAGE_KEY, DEFAULT_LANGUAGE);
            setCookie(COOKIE_NAME, DEFAULT_LANGUAGE, 365);
        } catch (e) {
            console.warn('⚠️ Cannot save default language:', e);
        }
        return DEFAULT_LANGUAGE;
    }
    
    // ==================== SET LANGUAGE (FIXED) ====================
    function setLanguage(lang, isFromBroadcast = false) {
        const oldLang = getCurrentLanguage();
        
        if (oldLang === lang) {
            console.log(`✅ Language already set to: ${lang}`);
            return;
        }
        
        console.log(`🔄 Changing language: ${oldLang} → ${lang}`);
        
        // ✅ LƯU VÀO CẢ 2 NƠI (localStorage + Cookie)
        try {
            localStorage.setItem(STORAGE_KEY, lang);
            console.log(`✅ Saved to localStorage: ${lang}`);
        } catch (e) {
            console.error('❌ localStorage save failed:', e);
        }
        
        setCookie(COOKIE_NAME, lang, 365); // Lưu 1 năm
        
        updateUI(lang, isFromBroadcast);
        applyTranslations(lang);
        
        // Broadcast to other tabs
        if (!isFromBroadcast && broadcastChannel) {
            try {
                broadcastChannel.postMessage({
                    type: 'LANGUAGE_CHANGED',
                    language: lang,
                    timestamp: Date.now()
                });
                console.log(`📡 Broadcast sent: ${lang}`);
            } catch (e) {
                console.error('❌ Broadcast failed:', e);
            }
        }
        
        // Dispatch event
        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { language: lang, isFromBroadcast } 
        }));
        
        console.log(`✅ Language set to: ${lang}`);
    }
    
    // ==================== UPDATE UI ====================
    function updateUI(lang, isFromBroadcast = false) {
        const isEnglish = lang === 'en';
        
        // ✅ CRITICAL FIX: Đảm bảo checkbox luôn sync với language
        if (checkbox) {
            checkbox.checked = isEnglish;
            console.log(`🎚️ Checkbox updated: ${isEnglish ? 'EN' : 'VI'}`);
        }
        
        if (langThumb) {
            langThumb.textContent = isEnglish ? 'EN' : 'VN';
        }
        
        if (isFromBroadcast && langSlider) {
            langSlider.classList.add('syncing');
            setTimeout(() => langSlider.classList.remove('syncing'), 600);
        }
    }
    
    // ==================== APPLY TRANSLATIONS ====================
    function applyTranslations(lang) {
        if (!translations[lang]) return;
        
        const langData = translations[lang];
        
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
        
        document.querySelectorAll('[data-translate-placeholder]').forEach(el => {
            const key = el.getAttribute('data-translate-placeholder');
            if (langData[key]) el.placeholder = langData[key];
        });
        
        document.querySelectorAll('[data-translate-title]').forEach(el => {
            const key = el.getAttribute('data-translate-title');
            if (langData[key]) el.title = langData[key];
        });
    }
    
    // ==================== BROADCAST LISTENER ====================
    if (broadcastChannel) {
        broadcastChannel.onmessage = (event) => {
            const { type, language } = event.data;
            if (type === 'LANGUAGE_CHANGED') {
                console.log(`📩 Received from other tab: ${language}`);
                setLanguage(language, true);
            }
        };
        
        window.addEventListener('beforeunload', () => {
            if (broadcastChannel) broadcastChannel.close();
        });
    }
    
    // ==================== STORAGE EVENT (FALLBACK) ====================
    window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_KEY && e.newValue !== null) {
            console.log(`📦 Storage event: ${e.newValue}`);
            setLanguage(e.newValue, true);
        }
    });
    
    // ==================== CHECKBOX EVENT ====================
    if (checkbox) {
        checkbox.addEventListener('change', function() {
            const newLang = this.checked ? 'en' : 'vi';
            console.log(`👆 User clicked: ${newLang}`);
            setLanguage(newLang, false);
        });
    }
    
    // ==================== INITIALIZE ====================
    async function init() {
        console.log('🚀 Language Toggle V3 initializing...');
        
        await loadTranslations();
        
        // ✅ CRITICAL: Đọc language TRƯỚC
        const currentLang = getCurrentLanguage();
        console.log(`🌍 Initial language: ${currentLang}`);
        
        // ✅ CRITICAL: Update UI NGAY (đảm bảo checkbox đúng)
        updateUI(currentLang, false);
        
        // ✅ SAU ĐÓ mới apply translations
        applyTranslations(currentLang);
        
        console.log('✅ Language Toggle V3 ready');
        console.log(`   📍 Checkbox state: ${checkbox ? checkbox.checked : 'N/A'}`);
        console.log(`   📍 Language: ${currentLang}`);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ==================== GLOBAL API ====================
    window.LanguageToggle = {
        getCurrentLanguage,
        setLanguage: (lang) => setLanguage(lang, false),
        applyTranslations: () => applyTranslations(getCurrentLanguage()),
        getTranslation: (key) => {
            const lang = getCurrentLanguage();
            return translations[lang]?.[key] || key;
        },
        broadcastCurrentLanguage: () => {
            if (broadcastChannel) {
                const lang = getCurrentLanguage();
                broadcastChannel.postMessage({
                    type: 'LANGUAGE_CHANGED',
                    language: lang,
                    timestamp: Date.now()
                });
            }
        }
    };
})();
</script>
<!-- ==================== END LANGUAGE TOGGLE V3 ==================== -->
"""


def get_language_script_only():
    """
    Script DỊCH trang - KHÔNG CÓ NÚT (cho Account, Login, etc.)
    ✨ V3: FIX - Không tự chuyển về English
    """
    return """
<script>
// ==================== LANGUAGE LOGIC V3 (NO UI - FIXED) ====================
(function() {
    const STORAGE_KEY = 'user_language';
    const COOKIE_NAME = 'user_lang';
    const CHANNEL_NAME = 'language-sync-channel';
    const DEFAULT_LANGUAGE = 'vi'; // ✅ MẶC ĐỊNH TIẾNG VIỆT
    
    let translations = {};
    let broadcastChannel = null;
    
    // ==================== COOKIE HELPERS ====================
    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1);
            if (c.indexOf(nameEQ) === 0) {
                return c.substring(nameEQ.length);
            }
        }
        return null;
    }
    
    // ==================== BROADCAST CHANNEL ====================
    if ('BroadcastChannel' in window) {
        try {
            broadcastChannel = new BroadcastChannel(CHANNEL_NAME);
            console.log('✅ BroadcastChannel ready (no UI)');
        } catch (e) {
            console.warn('⚠️ BroadcastChannel failed:', e);
        }
    }
    
    // ==================== LOAD TRANSLATIONS ====================
    async function loadTranslations() {
        try {
            const response = await fetch('/languages.json');
            if (response.ok) {
                translations = await response.json();
                console.log('✅ Translations loaded (no UI)');
            } else {
                translations = {
                    vi: { title: "Tài khoản", greeting: "Xin chào!" },
                    en: { title: "Account", greeting: "Hello!" }
                };
            }
        } catch (error) {
            console.error('❌ Translation error:', error);
            translations = {
                vi: { title: "Tài khoản", greeting: "Xin chào!" },
                en: { title: "Account", greeting: "Hello!" }
            };
        }
    }
    
    // ==================== GET LANGUAGE (FIXED) ====================
    function getCurrentLanguage() {
        // Priority: localStorage > Cookie > Default
        let lang = null;
        
        try {
            lang = localStorage.getItem(STORAGE_KEY);
            if (lang && (lang === 'vi' || lang === 'en')) {
                return lang;
            }
        } catch (e) {}
        
        lang = getCookie(COOKIE_NAME);
        if (lang && (lang === 'vi' || lang === 'en')) {
            try {
                localStorage.setItem(STORAGE_KEY, lang);
            } catch (e) {}
            return lang;
        }
        
        // ✅ LƯU DEFAULT NGAY
        try {
            localStorage.setItem(STORAGE_KEY, DEFAULT_LANGUAGE);
        } catch (e) {}
        
        return DEFAULT_LANGUAGE;
    }
    
    // ==================== APPLY TRANSLATIONS ====================
    function applyTranslations(lang) {
        if (!lang) lang = getCurrentLanguage();
        if (!translations[lang]) return;
        
        const langData = translations[lang];
        
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
        
        document.querySelectorAll('[data-translate-placeholder]').forEach(el => {
            const key = el.getAttribute('data-translate-placeholder');
            if (langData[key]) el.placeholder = langData[key];
        });
        
        document.querySelectorAll('[data-translate-title]').forEach(el => {
            const key = el.getAttribute('data-translate-title');
            if (langData[key]) el.title = langData[key];
        });
        
        console.log(`🌍 Applied: ${lang} (no UI)`);
    }
    
    // ==================== BROADCAST LISTENER ====================
    if (broadcastChannel) {
        broadcastChannel.onmessage = (event) => {
            const { type, language } = event.data;
            if (type === 'LANGUAGE_CHANGED') {
                console.log(`📩 Sync from main: ${language}`);
                localStorage.setItem(STORAGE_KEY, language);
                applyTranslations(language);
                
                window.dispatchEvent(new CustomEvent('languageChanged', { 
                    detail: { language, isFromBroadcast: true } 
                }));
            }
        };
        
        window.addEventListener('beforeunload', () => {
            if (broadcastChannel) broadcastChannel.close();
        });
    }
    
    // ==================== STORAGE EVENT ====================
    window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_KEY && e.newValue !== null) {
            console.log(`📦 Storage sync: ${e.newValue}`);
            applyTranslations(e.newValue);
        }
    });
    
    // ==================== INITIALIZE ====================
    async function init() {
        console.log('🚀 Language Script V3 (no UI) init...');
        
        await loadTranslations();
        
        const currentLang = getCurrentLanguage();
        console.log(`🌍 Language: ${currentLang}`);
        
        applyTranslations(currentLang);
        
        console.log('✅ Ready');
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ==================== GLOBAL API ====================
    window.LanguageToggle = {
        getCurrentLanguage,
        applyTranslations: () => applyTranslations(getCurrentLanguage()),
        getTranslation: (key) => {
            const lang = getCurrentLanguage();
            return translations[lang]?.[key] || key;
        }
    };
})();
</script>
"""