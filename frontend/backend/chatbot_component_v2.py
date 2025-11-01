import streamlit.components.v1 as components

def get_chatbot_html(gemini_api_key):
    """
    Trả về HTML string của chatbot để nhúng vào Flask
    
    Args:
        gemini_api_key (str): API key của Gemini AI
        
    Returns:
        str: HTML string hoàn chỉnh của chatbot
    """
    
    chatbot_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                box-sizing: border-box;
            }}
            
            body {{
                margin: 0;
                padding: 0;
                overflow: visible;
            }}
            
            .speech-bubble {{
                position: fixed;
                bottom: 50px;
                right: 105px;
                background-color: white;
                padding: 14px 20px;
                border-radius: 18px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                z-index: 999998;
                max-width: 240px;
                animation: bubblePop 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                transition: all 0.3s ease;
            }}
            
            .speech-bubble:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(0,0,0,0.15);
            }}
            
            .speech-bubble.hidden {{
                display: none;
            }}
            
            .speech-bubble-text {{
                font-size: 15px;
                color: #1a1a1a;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.4;
                letter-spacing: -0.2px;
            }}
            
            .speech-bubble::after {{
                content: '';
                position: absolute;
                bottom: 18px;
                right: -8px;
                width: 0;
                height: 0;
                border-top: 9px solid transparent;
                border-bottom: 9px solid transparent;
                border-left: 9px solid white;
                filter: drop-shadow(3px 0 3px rgba(0,0,0,0.08));
            }}
            
            .chatbot-button {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: linear-gradient(135deg, #FF6B35 0%, #FF8C61 100%);
                border: none;
                cursor: pointer;
                box-shadow: 0 6px 24px rgba(255,107,53,0.35);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 34px;
                z-index: 999999;
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            }}
            
            .chatbot-button:hover {{
                transform: scale(1.1) rotate(5deg);
                box-shadow: 0 8px 32px rgba(255,107,53,0.45);
            }}
            
            .chatbot-button:active {{
                transform: scale(0.95);
            }}
            
            .chatbot-button.hidden {{
                display: none;
            }}
            
            .chat-window {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 360px;
                max-width: calc(100vw - 60px);
                height: 600px;
                max-height: calc(100vh - 60px);
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 12px 48px rgba(0,0,0,0.18);
                display: none;
                flex-direction: column;
                z-index: 999999;
                overflow: hidden;
                animation: slideUp 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            }}
            
            .chat-window.open {{
                display: flex;
            }}
            
            .chat-header {{
                background: linear-gradient(135deg, #FF6B35 0%, #FF8C61 100%);
                color: white;
                padding: 18px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                flex-shrink: 0;
            }}
            
            .chat-header-info {{
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
                min-width: 0;
            }}
            
            .chat-avatar {{
                width: 38px;
                height: 38px;
                border-radius: 50%;
                background-color: rgba(255,255,255,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                position: relative;
                flex-shrink: 0;
            }}
            
            .online-dot {{
                position: absolute;
                bottom: 2px;
                right: 2px;
                width: 9px;
                height: 9px;
                background-color: #4ade80;
                border-radius: 50%;
                border: 2px solid white;
                animation: pulse 2s infinite;
            }}
            
            .chat-title {{
                font-weight: 800;
                font-size: 18px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                letter-spacing: -0.3px;
            }}
            
            .chat-status {{
                font-size: 12px;
                opacity: 0.95;
                font-weight: 600;
            }}
            
            .close-button {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                cursor: pointer;
                padding: 6px;
                font-size: 20px;
                border-radius: 50%;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                flex-shrink: 0;
            }}
            
            .close-button:hover {{
                background: rgba(255,255,255,0.3);
                transform: rotate(90deg);
            }}
            
            .messages-area {{
                flex: 1;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 16px;
                background-color: #FFF8F3;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            
            .messages-area::-webkit-scrollbar {{
                width: 6px;
            }}
            
            .messages-area::-webkit-scrollbar-track {{
                background: transparent;
            }}
            
            .messages-area::-webkit-scrollbar-thumb {{
                background: rgba(255,107,53,0.3);
                border-radius: 3px;
            }}
            
            .message {{
                display: flex;
                align-items: flex-end;
                gap: 6px;
                max-width: 100%;
            }}
            
            .message.user {{
                justify-content: flex-end;
            }}
            
            .message.bot {{
                justify-content: flex-start;
            }}
            
            .message-avatar {{
                width: 28px;
                height: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                flex-shrink: 0;
            }}
            
            .message.bot .message-avatar {{
                background: linear-gradient(135deg, #FF6B35 0%, #FF8C61 100%);
            }}
            
            .message.user .message-avatar {{
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            }}
            
            .message-content {{
                display: table;
                max-width: 70%;
                padding: 10px 14px;
                border-radius: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                word-break: break-word;
                overflow-wrap: break-word;
                white-space: pre-line;
            }}
            
            .message.user .message-content {{
                background-color: #FF6B35;
                color: white;
                border-radius: 16px 16px 4px 16px;
            }}
            
            .message.bot .message-content {{
                background-color: white;
                color: #333;
                border-radius: 16px 16px 16px 4px;
            }}
            
            .message-text {{
                font-size: 14px;
                line-height: 1.6;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                word-break: break-word;
                overflow-wrap: break-word;
            }}
            
            .message.bot .message-text {{
                font-weight: 400;
            }}
            
            .dish-name {{
                color: #FF6B35;
                font-weight: 700;
                font-size: 14.5px;
            }}
            
            .message-time {{
                font-size: 10px;
                margin-top: 4px;
                opacity: 0.7;
                text-align: right;
            }}
            
            .typing-indicator {{
                display: none;
                padding: 10px 14px;
                border-radius: 16px 16px 16px 4px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                width: fit-content;
            }}
            
            .typing-indicator.show {{
                display: flex;
                gap: 4px;
            }}
            
            .typing-dot {{
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background-color: #FF6B35;
                animation: bounce 1.4s infinite ease-in-out;
            }}
            
            .typing-dot:nth-child(2) {{
                animation-delay: 0.2s;
            }}
            
            .typing-dot:nth-child(3) {{
                animation-delay: 0.4s;
            }}
            
            .suggestions-area {{
                padding: 10px 14px;
                background-color: white;
                border-top: 1px solid #eee;
                display: flex;
                align-items: center;
                gap: 6px;
                overflow-x: auto;
                overflow-y: hidden;
                white-space: nowrap;
                scrollbar-width: none;
                flex-shrink: 0;
            }}
            
            .suggestions-area::-webkit-scrollbar {{
                display: none;
            }}
            
            .suggestions-area.hidden {{
                display: none;
            }}
            
            .suggestion-chip {{
                background-color: #FFF8F3;
                border: 1px solid #FFE5D9;
                color: #FF6B35;
                padding: 7px 12px;
                border-radius: 18px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
                flex-shrink: 0;
            }}
            
            .more-suggestions-btn {{
                background-color: #FFF8F3;
                border: 1px solid #FFE5D9;
                color: #FF6B35;
                padding: 7px 12px;
                border-radius: 18px;
                font-size: 14px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
                flex-shrink: 0;
            }}
            
            .more-suggestions-btn:hover, .suggestion-chip:hover {{
                background-color: #FF6B35;
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 2px 8px rgba(255,107,53,0.3);
            }}
            
            .input-area {{
                padding: 14px;
                background-color: white;
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
                flex-shrink: 0;
            }}
            
            .message-input {{
                flex: 1;
                padding: 10px 14px;
                border-radius: 22px;
                border: 1px solid #ddd;
                outline: none;
                font-size: 14px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                min-width: 0;
            }}
            
            .message-input::placeholder {{
                color: #999;
            }}
            
            .send-button {{
                width: 42px;
                height: 42px;
                border-radius: 50%;
                background: linear-gradient(135deg, #FF6B35 0%, #FF8C61 100%);
                border: none;
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                flex-shrink: 0;
            }}
            
            .send-button:hover {{
                transform: scale(1.1) rotate(15deg);
                box-shadow: 0 4px 12px rgba(255,107,53,0.4);
            }}
            
            .send-button:active {{
                transform: scale(0.95);
            }}
            
            .send-button:disabled {{
                opacity: 0.4;
                cursor: not-allowed;
                transform: none;
            }}
            
            @keyframes bubblePop {{
                0% {{
                    opacity: 0;
                    transform: scale(0.3) translateY(20px);
                }}
                50% {{
                    transform: scale(1.05) translateY(-5px);
                }}
                100% {{
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }}
            }}
            
            @keyframes slideUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px) scale(0.95);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }}
            }}
            
            @keyframes bounce {{
                0%, 80%, 100% {{ transform: scale(0); }}
                40% {{ transform: scale(1); }}
            }}
            
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.6; }}
            }}
            
            @media (max-width: 480px) {{
                .chat-window {{
                    width: calc(100vw - 40px);
                    right: 20px;
                    bottom: 20px;
                }}
                
                .speech-bubble {{
                    right: 95px;
                    bottom: 45px;
                    max-width: 200px;
                }}
                
                .chatbot-button {{
                    right: 20px;
                    bottom: 20px;
                    width: 56px;
                    height: 56px;
                    font-size: 28px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="speech-bubble" id="speechBubble">
            <div class="speech-bubble-text" id="bubbleText"></div>
        </div>
        
        <button class="chatbot-button" id="chatbotBtn">🍜</button>
        
        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div class="chat-header-info">
                    <div class="chat-avatar">
                        🍜
                        <div class="online-dot"></div>
                    </div>
                    <div>
                        <div class="chat-title">UIAboss</div>
                        <div class="chat-status">Online</div>
                    </div>
                </div>
                <button class="close-button" id="closeBtn">✕</button>
            </div>
            
            <div class="messages-area" id="messagesArea"></div>
            
            <div class="suggestions-area" id="suggestionsArea"></div>
            
            <div class="input-area">
                <input type="text" class="message-input" id="messageInput" placeholder="Bạn muốn ăn gì hôm nay?..." />
                <button class="send-button" id="sendBtn">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        </div>
        
        <script>
            const GEMINI_API_KEY = '{gemini_api_key}';
            const teaseMessages = [
                "Xin chào nè~ Muốn ăn gì để mình gợi ý cho 😋",
                "Hôm nay mình chill cà phê không nè~ ☕",
                "Đói chưa đó? Để UIA kiếm đồ ngon cho nha 😚",
                "Nhắn tin với bé đi mòooo 😚",
                "Nghĩ chưa ra ăn gì hả~ để tui giúp 😉",
                "Hello bạn iu~ Mình là UIAboss nè 💬",
                "Nay muốn ngọt ngào hay mặn mà đây 😋",
                "Vào đây hỏi món ngon là đúng chỗ rồi nha 😎",
                "Cà phê, trà sữa hay nước ép hơm ☕",
                "Mình biết nhiều quán xịn lắm, hỏi mình đi 😚",
                "Hôm nay ăn healthy hay cheat day đây 😆",
                "Để mình tìm cho vài quán ngon quanh bạn nè 🔍",
                "Nói mình nghe vị trí bạn ở đâu nha 📍",
                "Hello~ Bụng kêu chưa 😋",
                "Muốn mình gợi ý đồ uống mát mẻ hông nè 😎",
                "Chào bạn~ Mình đói dùm bạn luôn rồi á 😂",
                "Ăn gì giờ ta… để mình cứu đói giúp nha 😋",
                "Mình biết vài chỗ ngon bá cháy luôn 🔥",
                "Nói cho mình biết bạn ở đâu, mình chỉ quán liền 📍",
                "Đừng ngại, nhắn với mình đi nè 😄"
            ];
            
            const suggestionQuestions = [
                "Tui đói quá hôm nay ăn gì nhỉ? 🤔",
                "Gợi ý món ăn nhanh cho tui đi 🏃",
                "Món gì ngon mà không ngán vậy? 🍽️",
                "Hôm nay muốn ăn gì đó nhẹ nhàng 🌿",
                "Thèm đồ Việt Nam quá! 🇻🇳",
                "Có món nào mát lạnh không? 🧊",
                "Tui muốn ăn đồ nóng hổi 🔥",
                "Gợi ý món lạ một chút đi ✨",
                "Ăn gì cho bổ dưỡng nhỉ? 💪",
                "Món nào dễ tiêu hóa vậy? 😌",
                "Trời mưa kiểu này ăn gì ngon ta ☔",
                "Tối nay ăn gì cho ấm bụng nè 😋",
                "Thèm gì đó cay cay á 🌶️",
                "Hơi buồn miệng, ăn gì nhẹ nhẹ được ta 😌",
                "Ăn gì không ngán giờ này ha 🤔",
                "Muốn ăn gì cho tỉnh ngủ nè ☕",
                "Hôm nay muốn đổi gió chút, ăn gì lạ lạ đi 😚",
                "Nóng quá, kiếm món gì mát mẻ xíu 🧊",
                "Chiều nay ăn gì cho no mà lẹ ta ⏱️",
                "Đói bụng quá, gợi ý lẹ món ngon đi 😭",
                "Thèm đồ ngọt quá mà không biết ăn gì 🍰",
                "Tối nay mà có gì ăn cùng bạn bè thì vui á 🥳",
                "Ăn gì mà không béo hông 😅",
                "Thời tiết kiểu này chắc hợp ăn món nước ha 🍜",
                "Lâu rồi chưa ăn món Việt ngon ngon 😋",
                "Nay rảnh nấu ăn, gợi ý món dễ làm đi 👩‍🍳",
                "Nghĩ mãi không ra ăn gì hết 😭",
                "Có món nào vừa rẻ vừa ngon hông nè 💸",
                "Nay thèm hải sản xíu 🦐",
                "Gợi ý mình vài món hot trend đi 😎"
            ];
            
            const chatbotBtn = document.getElementById('chatbotBtn');
            const chatWindow = document.getElementById('chatWindow');
            const closeBtn = document.getElementById('closeBtn');
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const messagesArea = document.getElementById('messagesArea');
            const suggestionsArea = document.getElementById('suggestionsArea');
            const speechBubble = document.getElementById('speechBubble');
            const bubbleText = document.getElementById('bubbleText');
            
            let conversationHistory = [];
            let suggestedDishes = [];
            let lastInteractionTime = Date.now();
            let hasShownInitialSuggestions = false;
            let inactivityTimer = null;
            
            function updateBubbleText() {{
                bubbleText.textContent = teaseMessages[Math.floor(Math.random() * teaseMessages.length)];
            }}
            
            function getRandomSuggestions() {{
                const shuffled = [...suggestionQuestions].sort(() => Math.random() - 0.5);
                return shuffled.slice(0, 5);
            }}
            
            function renderSuggestions() {{
                suggestionsArea.classList.remove('hidden');
                suggestionsArea.innerHTML = '';
                const suggestions = getRandomSuggestions();
                
                suggestions.slice(0, 2).forEach(suggestion => {{
                    const chip = document.createElement('div');
                    chip.className = 'suggestion-chip';
                    chip.textContent = suggestion;
                    chip.onclick = () => {{
                        messageInput.value = suggestion;
                        sendMessage();
                        resetInactivityTimer();
                    }};
                    suggestionsArea.appendChild(chip);
                }});
                
                const moreBtn = document.createElement('div');
                moreBtn.className = 'more-suggestions-btn';
                moreBtn.textContent = '...';
                moreBtn.onclick = () => {{
                    suggestionsArea.innerHTML = '';
                    suggestions.forEach(suggestion => {{
                        const chip = document.createElement('div');
                        chip.className = 'suggestion-chip';
                        chip.textContent = suggestion;
                        chip.onclick = () => {{
                            messageInput.value = suggestion;
                            sendMessage();
                            resetInactivityTimer();
                        }};
                        suggestionsArea.appendChild(chip);
                    }});
                }};
                suggestionsArea.appendChild(moreBtn);
            }}
            
            function resetInactivityTimer() {{
                lastInteractionTime = Date.now();
                if (inactivityTimer) clearTimeout(inactivityTimer);
                
                if (hasShownInitialSuggestions) {{
                    inactivityTimer = setTimeout(() => {{
                        renderSuggestions();
                    }}, 30000);
                }}
            }}
            
            updateBubbleText();
            setInterval(updateBubbleText, 8000);
            
            chatbotBtn.onclick = () => {{
                chatWindow.classList.add('open');
                chatbotBtn.classList.add('hidden');
                speechBubble.classList.add('hidden');
                if (messagesArea.children.length === 0) {{
                    setTimeout(() => {{
                        const randomWelcome = teaseMessages[Math.floor(Math.random() * teaseMessages.length)];
                        addMessage('bot', randomWelcome);
                        renderSuggestions();
                        hasShownInitialSuggestions = true;
                        resetInactivityTimer();
                    }}, 300);
                }}
            }};
            
            closeBtn.onclick = () => {{
                chatWindow.classList.remove('open');
                chatbotBtn.classList.remove('hidden');
                speechBubble.classList.remove('hidden');
            }};
            
            function sendMessage() {{
                const text = messageInput.value.trim();
                if (!text) return;
                addMessage('user', text);
                messageInput.value = '';
                sendBtn.disabled = true;
                showTyping();
                callGeminiAPI(text);
                resetInactivityTimer();
            }}
            
            sendBtn.onclick = sendMessage;
            messageInput.onkeypress = (e) => {{ if (e.key === 'Enter') sendMessage(); }};
            messageInput.oninput = () => {{ 
                sendBtn.disabled = !messageInput.value.trim();
                resetInactivityTimer();
            }};
            
            function addMessage(type, text) {{
                hideTyping();
                const time = new Date().toLocaleTimeString('vi-VN', {{ hour: '2-digit', minute: '2-digit' }});
                const div = document.createElement('div');
                div.className = 'message ' + type;
                
                const avatarEmoji = type === 'bot' ? '🍜' : '👤';
                const avatarHTML = `<div class="message-avatar">${{avatarEmoji}}</div>`;
                
                if (type === 'user') {{
                    div.innerHTML = `
                        <div class="message-content">
                            <div class="message-text">${{text}}</div>
                            <div class="message-time">${{time}}</div>
                        </div>
                        ${{avatarHTML}}
                    `;
                }} else {{
                    div.innerHTML = `
                        ${{avatarHTML}}
                        <div class="message-content">
                            <div class="message-text">${{text}}</div>
                            <div class="message-time">${{time}}</div>
                        </div>
                    `;
                }}
                
                messagesArea.appendChild(div);
                messagesArea.scrollTop = messagesArea.scrollHeight;
                
                if (type === 'user') {{
                    conversationHistory.push({{ role: 'user', text: text }});
                }} else {{
                    const plainText = text.replace(/<[^>]*>/g, '');
                    conversationHistory.push({{ role: 'bot', text: plainText }});
                }}
            }}
            
            function showTyping() {{
                const div = document.createElement('div');
                div.id = 'typing';
                div.className = 'message bot';
                div.innerHTML = `
                    <div class="message-avatar">🍜</div>
                    <div class="typing-indicator show">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                `;
                messagesArea.appendChild(div);
                messagesArea.scrollTop = messagesArea.scrollHeight;
            }}
            
            function hideTyping() {{
                const typing = document.getElementById('typing');
                if (typing) typing.remove();
            }}
            
            function cleanMarkdown(text) {{
                text = text
                    .replace(/\\*\\*(.*?)\\*\\*/g, '$1')
                    .replace(/\\*(.*?)\\*/g, '$1')
                    .replace(/__(.*?)__/g, '$1')
                    .replace(/_(.*?)_/g, '$1');
                
                text = text.replace(/(\\d+\\.\\s+)([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][^:]+):/g, (match, num, dishName) => {{
                    return num + `<span class="dish-name">${{dishName.trim()}}</span>:`;
                }});
                
                text = text.replace(/([.!?])\\s+(\\d+)\\.\\s+/g, '$1\\n\\n$2. ');
                text = text.trim();
                
                return text;
            }}
            
            async function callGeminiAPI(userMessage) {{
                console.log('🔥 Bắt đầu gọi Gemini API...');
                console.log('📝 User message:', userMessage);
                
                const historyContext = conversationHistory.slice(-6).map(h => 
                    `${{h.role === 'user' ? 'Người dùng' : 'UIAboss'}}: ${{h.text}}`
                ).join('\\n');
                
                const suggestedDishesContext = suggestedDishes.length > 0 
                    ? `\\nCác món đã gợi ý trước đó: ${{suggestedDishes.join(', ')}}` 
                    : '';
                
                const prompt = `You are UIAboss, a friendly and attentive customer service staff at a Vietnamese restaurant. 

IMPORTANT - LANGUAGE ADAPTATION:
- ALWAYS respond in the SAME LANGUAGE the user uses
- If user writes in English → respond in English
- If user writes in Vietnamese → respond in Vietnamese  
- If user writes in Chinese → respond in Chinese
- Match the user's language naturally and fluently

IMPORTANT - TOPIC RESTRICTION:
- You ONLY answer questions related to: food, drinks, dishes, restaurants, cafes, cuisine
- If user asks about OTHER topics (weather, news, programming, math, history, etc.), politely decline and explain in their language:
  * English: "Sorry! 😊 I'm a food-focused chatbot, I only help you find delicious food and drinks. What would you like to eat or drink?"
  * Vietnamese: "Xin lỗi bạn nha 😊 Mình là chatbot chuyên về ẩm thực, chỉ giúp bạn tìm món ăn ngon thôi. Bạn muốn hỏi gì về đồ ăn hay thức uống không?"
  * Chinese: "不好意思哦 😊 我是专注美食的聊天机器人，只能帮你找好吃的。你想吃什么呢？"

Conversation style:
- Natural, friendly like a close friend
- Show genuine care for customers
- Ask about preferences, mood, previous meals
- Suggest 2-3 dishes suitable for customer's condition (hungry, hot, cold, light, nutritious...)
- Briefly explain why suggesting that dish (warming, cooling, easy to eat, nutritious...)
- Always ask more to understand customer better
- Remember suggested dishes to avoid repetition
- Use emojis appropriately but not too much
- IMPORTANT: Do not use ** or __ for bold, just write plain text

Recent conversation history:
${{historyContext}}
${{suggestedDishesContext}}

User just said: ${{userMessage}}

Respond naturally, caringly and helpfully in the SAME LANGUAGE the user used:`;
                
                const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${{GEMINI_API_KEY}}`;
                
                try {{
                    const res = await fetch(apiUrl, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ 
                            contents: [{{ 
                                parts: [{{ text: prompt }}] 
                            }}] 
                        }})
                    }});
                    
                    if (!res.ok) {{
                        const errorText = await res.text();
                        console.error('❌ API Error Response:', errorText);
                        addMessage('bot', `Ối! Có lỗi xảy ra rồi bạn ơi 😢\\nMình đang gặp chút vấn đề kỹ thuật, bạn thử lại sau nhé!`);
                        sendBtn.disabled = false;
                        return;
                    }}
                    
                    const data = await res.json();
                    let botReply = data.candidates?.[0]?.content?.parts?.[0]?.text;
                    
                    if (botReply) {{
                        botReply = cleanMarkdown(botReply);
                        console.log('💬 Bot reply (cleaned):', botReply);
                        
                        const dishMatches = botReply.match(/[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\\s+[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+)*(?=\\s|,|\\.|:|!|\\?|$)/g);
                        if (dishMatches) {{
                            dishMatches.forEach(dish => {{
                                if (dish.length > 3 && !suggestedDishes.includes(dish)) {{
                                    suggestedDishes.push(dish);
                                }}
                            }});
                        }}
                        
                        addMessage('bot', botReply);
                        suggestionsArea.classList.add('hidden');
                        resetInactivityTimer();
                    }} else {{
                        console.error('❌ Không tìm thấy text trong response:', data);
                        addMessage('bot', 'Xin lỗi bạn nhé! Mình đang hơi bận, thử lại sau nhé! 😅');
                    }}
                }} catch (e) {{
                    console.error('❌ Fetch Error:', e);
                    addMessage('bot', `Ối! Mình bị lỗi kết nối rồi 😢\\nBạn kiểm tra mạng và thử lại nhé!`);
                }}
                sendBtn.disabled = false;
            }}
        </script>
    </body>
    </html>
    """
    
    return chatbot_html


def render_food_chatbot(gemini_api_key):
    """
    Render chatbot gợi ý món ăn sử dụng Gemini API (Cho Streamlit)
    
    Args:
        gemini_api_key (str): API key của Gemini AI
    """
    
    chatbot_html = get_chatbot_html(gemini_api_key)
    
    # Sử dụng components.html với height phù hợp
    components.html(chatbot_html, height=700, scrolling=False)
