import streamlit.components.v1 as components

def get_chatbot_html(gemini_api_key):
    """
    Trả về HTML string của chatbot để nhúng vào Flask
    
    Args:
        gemini_api_key (str): API key của Gemini AI
        
    Returns:
        str: HTML string hoàn chỉnh của chatbot
    """
    
    chatbot_html = rf"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <!-- Emoji Picker Element (Google) -->
        <script src="https://cdn.jsdelivr.net/npm/emoji-picker-element@^1/index.js" type="module"></script>
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
                bottom: 110px;
                right: 30px;
                background-color: white;
                padding: 14px 20px;
                border-radius: 18px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.12);
                z-index: 999998;
                max-width: 240px;
                animation: bubblePop 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                transition: all 0.3s ease;
                cursor: pointer;
                user-select: none;
            }}
            
            .speech-bubble:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(0,0,0,0.15);
                background-color: #FFF8F3;
            }}
            
            .speech-bubble.hidden {{
                display: none !important;
            }}
            
            .speech-bubble-text {{
                font-size: 15px;
                color: #1a1a1a;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.4;
                letter-spacing: -0.2px;
                pointer-events: none;
            }}
            
            .speech-bubble::after {{
                content: '';
                position: absolute;
                bottom: -8px;
                right: 20px;
                width: 0;
                height: 0;
                border-left: 9px solid transparent;
                border-right: 9px solid transparent;
                border-top: 9px solid white;
                filter: drop-shadow(0 3px 3px rgba(0,0,0,0.08));
                pointer-events: none;
            }}
            
            .chatbot-button {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 55px;
                height: 55px;
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
                user-select: none;
            }}
            
            .chatbot-button:hover {{
                transform: scale(1.1) rotate(5deg);
                box-shadow: 0 8px 32px rgba(255,107,53,0.45);
            }}
            
            .chatbot-button:active {{
                transform: scale(0.95);
            }}
            
            .chatbot-button.hidden {{
                display: none !important;
            }}
            
            .chat-window {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 22%;
                max-width: calc(100vw - 60px);
                height: calc(100% - 240px);
                max-height: calc(100vh - 60px);
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 12px 48px rgba(0,0,0,0.18);
                display: none;
                flex-direction: column;
                z-index: 1000000;
                overflow: visible;
                animation: slideUp 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            }}
            
            .chat-window.open {{
                display: flex !important;
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
                cursor: pointer;
                transition: all 0.3s ease;
            }}

            .chat-avatar:hover {{
                transform: scale(1.1);
                background-color: rgba(255,255,255,0.5);
            }}

            .chat-avatar:active {{
                transform: scale(0.95);
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
                text-align: justify;
                text-justify: inter-word;
                line-height: 1.6; 
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
                text-justify: inter-word;
                text-align: justify;
                font-size: 14px;
                line-height: 1.6;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                word-break: break-word;
                overflow-wrap: break-word;
                white-space: pre-wrap; /* 👈 đổi từ pre-line thành pre-wrap */
            }}

            .message-content ol {{
                padding-left: 20px;
                margin: 6px 0;
            }}

            .message-content ol li {{
                margin-bottom: 15px;
                line-height: 1.55;
                text-align: justify;
                text-justify: inter-word;
            }}

            .message-content ol li:not(:last-child)::after {{
                content: "";
                display: block;
                height: 8px;           /* thêm khoảng trống 8px dưới mỗi món */
            }}

            .message-content p {{
                margin: 6px 0;
            }}

            .message-content li br {{
                margin-bottom: 6px;    /* 👈 nếu có xuống dòng trong mô tả thì thêm khoảng nhỏ */
                display: block;
                content: "";
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
                position: relative;
                padding: 14px;
                background-color: white;
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
                flex-shrink: 0;
            }}

            .input-wrapper {{
                position: relative;
                flex: 1;
                display: flex;
                align-items: center;
                border: 1px solid #ddd;      /* 🟠 thêm viền xám cho khung input */
                border-radius: 22px;         /* 🟠 bo tròn cho toàn khung */
                background-color: #fff;      /* 🟠 giữ nền trắng đồng bộ */
            }}
            
            .message-input {{
                flex: 1;
                border: none;                /* 🟠 bỏ viền trong input để không double border */
                outline: none;
                padding: 10px 40px 10px 14px; /* 🟠 chừa chỗ bên phải cho emoji */
                border-radius: 22px;
                font-size: 13px;
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

            /* === EMOJI PICKER === */
            .emoji-button {{
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                opacity: 0.8;
                transition: transform 0.2s ease, opacity 0.2s ease;
            }}

            .emoji-button:hover {{
                transform: translateY(-50%) scale(1.2);
                opacity: 1;
            }}

            .emoji-picker {{
                position: absolute;
                bottom: 60px;
                right: 50px;
                z-index: 1000001;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                overflow: hidden;
            }}

            .emoji-picker span {{
                font-size: 22px;
                cursor: pointer;
                padding: 4px;
            }}

            .emoji-picker span:hover {{
                background-color: #f0f0f0;
                border-radius: 5px;
            }}

            .hidden {{
                display: none;
            }}

            /* ===== CHAT HISTORY SIDEBAR ===== */
            .chat-history-sidebar {{
                position: fixed;
                bottom: 30px;
                right: 25%; /* 👈 Dính sát bên trái chat window (30px margin + 320px width + 15px gap) */
                width: 260px;
                height: calc(100% - 240px);
                max-height: calc(100vh - 60px);
                background: white;
                border-radius: 20px;
                box-shadow: 0 12px 48px rgba(0,0,0,0.18);
                display: none;
                flex-direction: column;
                z-index: 999999;
                overflow: hidden;
                animation: slideInFromLeft 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55); /* 👈 Đổi animation */
            }}

            .chat-history-sidebar.open {{
                display: flex;
            }}

            .history-header {{
                background: linear-gradient(135deg, #FF6B35 0%, #FF8C61 100%);
                color: white;
                padding: 16px;
                font-weight: 700;
                font-size: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
                gap: 8px;
            }}

            .history-header-right {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex-shrink: 0;
            }}

            .history-new-btn {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                cursor: pointer;
                padding: 4px;
                font-size: 18px;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                font-weight: bold;
                flex-shrink: 0;
            }}

            .history-new-btn:hover {{
                background: rgba(255,255,255,0.3);
                transform: rotate(90deg) scale(1.1);
            }}

            .history-new-btn:active {{
                transform: rotate(90deg) scale(0.95);
            }}

            .history-close {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                cursor: pointer;
                padding: 4px;
                font-size: 16px;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                flex-shrink: 0;
            }}

            .history-close:hover {{
                background: rgba(255,255,255,0.3);
                transform: rotate(90deg);
            }}

            .history-list {{
                flex: 1;
                overflow-y: auto;
                padding: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}

            .history-list::-webkit-scrollbar {{
                width: 6px;
            }}

            .history-list::-webkit-scrollbar-track {{
                background: transparent;
            }}

            .history-list::-webkit-scrollbar-thumb {{
                background: rgba(255,107,53,0.3);
                border-radius: 3px;
            }}

            .history-item {{
                background: #FFF8F3;
                border: 1px solid #FFE5D9;
                border-radius: 12px;
                padding: 10px 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 8px;
            }}

            .history-item:hover {{
                background: #FFE5D9;
                transform: translateX(-4px);
            }}

            .history-item.active {{
                background: #FF6B35;
                color: white;
                border-color: #FF6B35;
            }}

            .history-item-name {{
                flex: 1;
                font-size: 13px;
                font-weight: 500;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}

            .history-item-input {{
                flex: 1;
                border: 2px solid #FF6B35;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                font-weight: 500;
                outline: none;
                background: white;
            }}

            .history-item-edit {{
                background: rgba(255,107,53,0.2);
                border: none;
                color: #FF6B35;
                cursor: pointer;
                padding: 4px;
                font-size: 14px;
                border-radius: 6px;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                flex-shrink: 0;
            }}

            .history-item-edit:hover {{
                background: rgba(255,107,53,0.3);
                transform: scale(1.1);
            }}

            .history-item.active .history-item-edit {{
                background: rgba(255,255,255,0.3);
                color: white;
            }}

            .history-item.active .history-item-edit:hover {{
                background: rgba(255,255,255,0.4);
            }}

            .history-item-delete {{
                background: rgba(239,68,68,0.2);
                border: none;
                color: #ef4444;
                cursor: pointer;
                padding: 4px;
                font-size: 14px;
                border-radius: 6px;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                flex-shrink: 0;
            }}

            .history-item-delete:hover {{
                background: rgba(239,68,68,0.3);
                transform: scale(1.1);
            }}

            .history-item.active .history-item-delete {{
                background: rgba(255,255,255,0.3);
                color: white;
            }}

            .history-item.active .history-item-delete:hover {{
                background: rgba(255,255,255,0.4);
            }}

            .history-item-actions {{
                display: flex;
                gap: 4px;
                flex-shrink: 0;
            }}

            .history-item.new-item-slide {{
                animation: slideInNewItem 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            }}

            @keyframes slideInNewItem {{
                0% {{
                    opacity: 0;
                    transform: translateX(-100%);
                }}
                60% {{
                    opacity: 1;
                    transform: translateX(10px);
                }}
                100% {{
                    opacity: 1;
                    transform: translateX(0);
                }}
            }}

            /* Hiệu ứng glow sáng sau khi trượt xong */
            .history-item.new-item-glow {{
                animation: glowPulse 1.5s ease-in-out;
            }}

            @keyframes glowPulse {{
                0%, 100% {{
                    background: #FFF8F3;
                    box-shadow: none;
                }}
                25%, 75% {{
                    background: linear-gradient(135deg, #FFE5D9 0%, #FFF8F3 100%);
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.4), 0 0 40px rgba(255, 107, 53, 0.2);
                    border-color: #FF6B35;
                }}
                50% {{
                    background: linear-gradient(135deg, #FFCCB3 0%, #FFE5D9 100%);
                    box-shadow: 0 0 30px rgba(255, 107, 53, 0.6), 0 0 60px rgba(255, 107, 53, 0.3);
                    border-color: #FF8C61;
                }}
            }}

            @keyframes slideInFromLeft {{
                from {{
                    opacity: 0;
                    transform: translateX(-30px) scale(0.95);
                }}
                to {{
                    opacity: 1;
                    transform: translateX(0) scale(1);
                }}
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
                    right: 20px;
                    bottom: 105px;
                    max-width: 200px;
                }}
                
                .chatbot-button {{
                    right: 20px;
                    bottom: 20px;
                    width: 56px;
                    height: 56px;
                    font-size: 28px;
                }}

                .chat-history-sidebar {{
                    bottom: 100px; /* 👈 Đẩy lên trên để không đè lên chat */
                    left: 20px;
                    right: 20px;
                    width: calc(100vw - 40px);
                    max-width: 260px;
                    height: 300px; /* 👈 Giới hạn chiều cao trên mobile */
                }}
            }}
        </style>
    </head>
    <body>
        <div class="speech-bubble" id="speechBubble">
            <div class="speech-bubble-text" id="bubbleText">Xin chào nè~ Muốn ăn gì để mình gợi ý cho 😋</div>
        </div>
        
        <button class="chatbot-button" id="chatbotBtn">🍜</button>

        <!-- Chat History Sidebar -->
        <div class="chat-history-sidebar" id="chatHistorySidebar">
            <div class="history-header">
                <span>📋 Lịch sử chat</span>
                <div class="history-header-right">
                    <button class="history-new-btn" id="historyNewBtn" title="Tạo chat mới">+</button>
                    <button class="history-close" id="historyCloseBtn">✕</button>
                </div>
            </div>
            <div class="history-list" id="historyList"></div>
        </div>
        
        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div class="chat-header-info">
                    <div class="chat-avatar" id="chatAvatar">
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
                <div class="input-wrapper">
                    <input type="text" class="message-input" id="messageInput" placeholder="Bạn muốn ăn gì hôm nay?" />
                    <button class="emoji-button" id="emojiBtn"> 😊</button>
                </div>
                <button class="send-button" id="sendBtn">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>

                <!-- Emoji Picker -->
                <div class="emoji-picker hidden" id="emojiPicker">
                    <emoji-picker></emoji-picker>
                </div>
            </div>
        </div>
        
        <script>
            const GEMINI_API_KEY = '{gemini_api_key}';

            const API_BASE_URL = 'http://127.0.0.1:8000/api'; 

            console.log('🚀 Chatbot script loaded');

            // ===== TÍNH NĂNG MỚI 1: DANH SÁCH TỪ TỤC TIỂU =====
            const profanityWords = {{
                vi: [
                    // --- nhóm chửi tục tiếng Việt gốc ---
                    'địt', 'đụ', 'đjt', 'djt', 'đmm', 'dm', 'đm', 'dmm', 'đcm', 'dcm', 'clgt',
                    'vcl', 'vl', 'vãi', 'vãi lồn', 'vãi loz', 'vãi lon', 'vailon', 'vailoz',
                    'cl', 'clm', 'clo', 'cln', 'clmm', 'cldm', 'cmm', 'cmn', 'ccmm', 'đéo', 'đếch',
                    'đek', 'dek', 'đekm', 'dmj', 'dmz', 'vlz', 'vkl', 'vch', 'vđ', 'vđm', 'vđmm',

                    // --- nhóm xúc phạm, nhục mạ ---
                    'ngu', 'ngu học', 'óc chó', 'não phẳng', 'não cá vàng', 'khùng', 'ngáo', 'điên',
                    'khốn nạn', 'mất dạy', 'vô học', 'láo', 'bố láo', 'láo toét', 'chó má', 'súc vật',
                    'thằng ngu', 'con ngu', 'đồ điên', 'đồ chó', 'rảnh háng', 'bố đời', 'đồ rẻ rách',

                    // --- nhóm tục tả sinh lý ---
                    'lồn', 'buồi', 'cu', 'chim to', 'chim nhỏ', 'bướm', 'nứng', 'cặc', 'đỉ',
                    'đĩ', 'điếm', 'cave', 'gái gọi', 'đi khách', 'dâm', 'râm', 'râm dục', 'biến thái',
                    'thủ dâm', 'dương vật', 'âm đạo', 'âm vật', 'hiếp', 'hiếp dâm', 'giao cấu',

                    // --- nhóm chửi liên quan gia đình ---
                    'mẹ mày', 'bố mày', 'cha mày', 'má mày', 'ông nội mày', 'bà nội mày',
                    'tổ cha', 'tổ sư', 'con mẹ mày', 'con chó', 'đồ chó', 'con đĩ mẹ mày',

                    // --- nhóm viết tắt & kiểu chat Việt hóa ---
                    'vl', 'vkl', 'vcc', 'vklm', 'cmn', 'cmnr', 'cmnl', 'vcđ', 'vđc', 'vcml',
                    'dkm', 'vml', 'vclm', 'vcmm', 'dmnr', 'dcmj', 'dmj', 'ccmnr', 'vchz', 'vlz', 'cc', 'cái lồn',

                    // --- nhóm không dấu / né lọc ---
                    'dit', 'ditme', 'dit me', 'ditmemay', 'du', 'djtme', 'dmme', 'dmmay', 'vclon',
                    'vai lon', 'vai loz', 'vai lonz', 'dmml', 'dcmm', 'dcmay', 'vlon', 'vailon',
                    'vailoz', 'vailonzz', 'ditconme', 'dmconcho', 'cac', 'loz', 'lol', 'đụ má',

                    // --- nhóm “tiếng Anh Việt hóa” mà người Việt hay dùng để chửi ---
                    'fuck', 'fuk', 'fukk', 'fucc', 'fucck', 'fuking', 'fucking', 'fck', 'fcku', 'fcking',
                    'phắc', 'phẹc', 'phâk', 'phúc kiu', 'phẹc kiu', 'phắc kiu', 'phuck',
                    'sịt', 'sít', 'sịt mẹ', 'shit', 'shjt', 'sh1t', 'shet', 'sịt lờ',
                    'bít', 'bitch', 'b1tch', 'btch', 'biatch', 'bich', 'bịt', 'bitchass',
                    'đem', 'đem mờn', 'đem men', 'đem mai', 'damn', 'daemn', 'damm',
                    'sặc', 'sắc', 'suck', 'sux', 'suk', 'suck my', 'suckyou', 'sucku',
                    'wtf', 'wth', 'wtfff', 'wtfuk', 'wdf', 'omfg', 'omg', 'holyshit', 'holy fuck',
                    'bullshit', 'bullshjt', 'bullsh1t', 'bulsit', 'bs', 'bsht', 'crap', 'crp',
                    'hell', 'go to hell', 'dumbass', 'dipshit', 'moron', 'loser',
                    'jerk', 'mf', 'mofo', 'motherfucker', 'sonofabitch', 'son of a bitch', 'retard', 'idiot',
                    'porn', 'p0rn', 'sex', 'sexy', 'horny', 'nude', 'naked', 'gay', 'say get', 'sex', 'sẽ',
                ],
                en: [
                    'fuck', 'shit', 'bitch', 'asshole', 'bastard', 'cunt', 'dick', 'pussy', 'cock',
                    'motherfucker', 'fck', 'wtf', 'stfu', 'bullshit', 'ass', 'piss', 'slut',
                    'whore', 'retard', 'idiot', 'jerk', 'damn', 'fucking', 'moron',
                    'fuk', 'fucc', 'phuc', 'fcku', 'fckn', 'fckoff', 'shjt', 'b1tch', 'btch',
                    'azz', 'azzhole', 'a$$', 'd1ck', 'p0rn', 'porn', 'suck', 'sux', 'fux',
                    'fuxk', 'phuk', 'phuck', 'mf', 'mofo', 'wtfff', 'omfg', 'fml', 'fk',
                    'fkin', 'cum', 'cumming', 'orgasm', 'jerkoff', 'wank', 'nsfw',
                    'horny', 'nude', 'sex', 'sexy', 'dumbass', 'dipshit', 'crap', 'hell'
                ],
                // 🇨🇳 Tiếng Trung (tục phổ biến, bao gồm Hán tự, pinyin, số viết tắt)
                zh: [
                    // --- Hán tự ---
                    '他妈的', '他媽的', '操你妈', '操你', '你妈的', '你媽的', '去你妈的',
                    '傻逼', '煞笔', '沙雕', '妈的', '媽的', '滚开', '滚蛋', '狗屎',
                    '废物', '垃圾', '贱人', '王八蛋', '混蛋', '猪头', '变态', '禽兽',
                    '他奶奶的', '日你妈', '日了狗', '傻屌', '脑残', '白痴', '蠢货', '废柴',

                    // --- Pinyin / Latin ---
                    'tamade', 'caonima', 'caoni', 'nimade', 'qunimade',
                    'shabi', 'shapi', 'shadiao', 'mada', 'gunni', 'gundan',
                    'feiw', 'laji', 'jianren', 'wangbad', 'hundan',
                    'zhutou', 'biantai', 'qingshou', 'rinima', 'rilougou',
                    'naocan', 'baichi', 'chunhuo', 'feichai',

                    // --- Viết tắt / số hóa (Internet slang) ---
                    'nmsl', 'wdnmd', 'tmd', 'cnm', 'nmd', 'mlgb', 'djb', 'rnm',
                    'sb', '2b', '250', '25013', 'mdzz', 'nb', 'lj', 'fw', 'gdx',
                    'nmb', 'nmgb', 'wdnm', 'wcnm', 'wcnmd'
                ],
                // 🇰🇷 Tiếng Hàn (tục & xúc phạm phổ biến + dạng Latin)
                ko: [
                    '씨발', '시발', '씹새끼', '썅', '병신', '미친놈', '미친년',
                    '개새끼', '개년', '개자식', '좆같아', '좆나', '존나', '존나게',
                    '지랄하네', '닥쳐라', '꺼져라', '죽어라', '씨팔', '씹할놈',
                    '새끼야', '병신같이', '염병하네', '개같은', '개호로새끼',
                    '호로새끼', '니미럴', '느금마', '니애미', '돌아이', '변태놈',
                    '섹스중독자', '개변태', '매춘부',

                    // --- Viết tắt & Latin ---
                    'ssibal', 'sibal', 'siibal', 'ssiball', 'ssibaal', 'shibal',
                    'byeongsin', 'byeongshin', 'gaesaekki', 'gaesekki', 'gaesekkiya',
                    'jonna', 'jotnna', 'jotnagal', 'jiral', 'jjiral', 'dokchyeo',
                    'ggeojyeo', 'negejug', 'niimi', 'nieomi', 'dolai', 'byuntae',
                    'sex', 'byuntae', 'gaebyeongsin', 'niemi', 'neommaya'
                ],
                // 🇯🇵 Tiếng Nhật (tục & xúc phạm phổ biến)
                ja: [
                    // --- Kanji & Kana ---
                    'くそ', 'クソ', 'ちくしょう', '畜生', 'ばか', 'バカ', 'あほ', 'アホ',
                    'しね', '死ね', 'しねや', '死ねや', 'だまれ', '黙れ', 'うるさい', 'ウルサイ',
                    'ブス', 'デブ', 'キモい', 'きもい', '変態', 'へんたい', 'ふざけんな', 'ざけんな',
                    'くたばれ', '馬鹿野郎', 'ばかやろう', 'ドアホ', 'クズ', '最低', '最悪',
                    'キチガイ', 'スケベ', 'いやらしい',

                    // --- Latin / Romaji / Slang ---
                    'kuso', 'baka', 'aho', 'shine', 'shineya', 'damare', 'urusai',
                    'busu', 'debu', 'kimoi', 'hentai', 'fuzakenna', 'zakenna',
                    'kutabare', 'bakayarou', 'doaho', 'kuzu', 'saitei', 'saiaku',
                    'kichigai', 'sukebe', 'iyarashii', 'fakku', 'shitto', 'dame', 'yarou'
                ]
            }};

            const warningMessages = {{
                vi: [
                    "Xin lỗi nha 🥺 Mình là chatbot AI thân thiện, nên mong bạn nói chuyện lịch sự một chút nè 💖\nHy vọng tụi mình sẽ có khoảng thời gian trò chuyện vui vẻ và tôn trọng nhau hơn nha~ Nếu bạn muốn mình gợi ý món ăn thì đừng chần chừ, hãy nhắn mình ngay nhé, mình sẽ hỗ trợ bạn hết mình!",
                    "Ơ bạn ơi 😅 mình chỉ là chatbot thân thiện thôi, nên mong bạn nói chuyện nhẹ nhàng hơn nha 💕\nMình muốn cùng bạn trò chuyện vui vẻ và thoải mái nhất có thể đó~ Nếu bạn muốn mình gợi ý món ăn thì nhắn mình liền luôn nghen, UIAboss luôn sẵn sàng hỗ trợ bạn hết mình 🍜",
                    "Xin lỗi bạn nghen 🥺 Mình không phản hồi được mấy từ hơi nhạy cảm đâu 😅\nNhưng mình vẫn ở đây nè, sẵn sàng gợi ý món ngon cho bạn bất cứ lúc nào~ Cứ nhắn mình liền nha, mình hỗ trợ bạn hết sức luôn!",
                    "Hí hí 😄 mình hiểu bạn đang bực hay vui, nhưng mình là chatbot thân thiện nên mong mình cùng nói chuyện nhẹ nhàng thôi nè 💖\nÀ mà nếu bạn đang đói, mình gợi ý món ăn ngon liền luôn nha~",
                    "Hehe 😅 lời nói vừa rồi nghe hơi mạnh đó bạn ơi~\nMình muốn chúng ta nói chuyện lịch sự và vui vẻ nha 💕 Nếu bạn muốn mình gợi ý món ăn thì đừng ngại, cứ nhắn mình ngay nè, mình hứa gợi ý món siêu ngon luôn 🍲",
                    "Ơ kìa 😅 nói dị hơi gắt á bạn ơi~\nMình muốn giữ cuộc trò chuyện này thật vui và ấm áp thôi 💖 Nếu bạn muốn mình giúp tìm món ăn ngon thì nói mình nghe liền nha, mình ở đây vì bạn đó 💞",
                    "Ui bạn ơi 😅 mấy từ đó nghe hơi nặng nề á~\nMình chỉ muốn cùng bạn nói chuyện thoải mái, thân thiện thôi mà 💞 Nếu bạn muốn gợi ý món ăn thì nhắn mình liền nè, mình giúp ngay luôn!",
                    "Ơ xin lỗi nha 🥺 mình là chatbot thân thiện, nên không phản hồi mấy từ đó được đâu 😅\nNhưng nè~ bạn hỏi mình về món ăn đi, đảm bảo mình gợi ý ngon lành luôn 😋",
                    "Nè bạn ơi 😄 mình nói chuyện vui thôi nha, nhẹ nhàng hơn chút xíu cho dễ thương hơn nè 💖\nNếu bạn đang muốn biết ăn gì, mình gợi ý liền luôn nha~",
                    "Hi bạn 😅 mình chỉ muốn nói chuyện lịch sự và vui vẻ cùng bạn thôi~\nNếu bạn cần gợi ý món ăn, nhắn mình ngay nha, mình ở đây để hỗ trợ bạn hết mình 💫"
                ],

                en: [
                    "Hey there 🥺 I’m a friendly AI chatbot, could we keep our chat polite and kind please? 💖\nI’m here to make our time together fun and respectful~ If you’d like me to suggest something yummy, don’t hesitate to message me — I’ll give it my best shot!",
                    "Oops 😅 that sounded a bit strong~\nI’m your friendly chatbot, let’s keep our talk positive and kind, yeah? 💕 And hey, if you’d like me to recommend some food, just tell me — I’ve got you covered 🍜",
                    "Hey 🥺 please keep our chat friendly 💖\nI want us to have a fun, cozy time together! Need food ideas? Don’t wait — I’ll suggest something delicious right away!",
                    "Aww 😅 I can’t reply to words like that~\nLet’s stay kind and cheerful okay? 💞 If you’re hungry, just ask and I’ll find you something tasty right now!",
                    "Hehe 😄 let’s talk nicely so our chat stays happy and fun! 💖\nIf you’d like some food suggestions, message me anytime — I’ll do my best for you 🍲",
                    "Hey there 😅 I’m just a friendly chatbot!\nLet’s keep things sweet and light, deal? 💕 If you want me to recommend food, go ahead and ask — I’ll be happy to help!",
                    "Hi 🥰 I’m here to chat with kindness and care~\nLet’s make it a good vibe only day 💫 Oh, and if you’re craving something, I can suggest dishes too!",
                    "Whoops 😅 that’s a bit harsh! I know you didn’t mean it~\nLet’s start fresh and be nice 💖 And hey, if you’re thinking about food, I’m here for you 😋",
                    "Hey 😄 I just want our chat to be kind and cheerful~ You’re awesome 💕\nIf you’d like me to find you something to eat, just ask anytime!",
                    "Oops 😅 let’s tone it down a bit~ UIAboss is here to spread good vibes only 💞\nAnd if you’re hungry, tell me — I’ll recommend the best dishes for you 🍜"
                ],

                zh: [
                    "哎呀～这句话里有点不太合适的词语哦 😅 我是一个友善的AI聊天机器人，希望我们能文明交流、开心聊天 💖\n如果你想让我推荐美食，不要犹豫哦～告诉我吧，我一定全力帮你！🍜",
                    "嗯...这句话听起来有点激动 🥺 我们换种温柔的方式说好吗？✨\n如果你想我帮你推荐好吃的，直接告诉我吧～我超乐意帮你！💕",
                    "不好意思呀～我不能回复带有不礼貌内容的信息 😔 但我很想继续和你愉快聊天～\n如果你想知道吃什么，就问我吧！我马上给你推荐！🍲",
                    "嘿嘿 😄 别生气嘛～让我们保持轻松愉快的氛围吧 💖\n想让我推荐好吃的？直接说就行～我一定帮你挑到满意的！✨",
                    "噢！这句话听起来有点不太好听 😅 没关系，我们换个轻松的话题吧～比如吃什么？😋\n我可以帮你推荐超棒的美食哦！",
                    "诶呀～是不是打错字啦？🤔 没关系，我们重新聊聊也可以呀～\n如果你想我推荐吃的，告诉我就行 💕 我马上安排！🍜",
                    "抱歉，这样的话我不能回复 😅 我们聊点别的吧～比如你现在饿了吗？\n让我推荐点好吃的给你呀 💖",
                    "别生气啦 😄 我希望我们能轻松愉快地聊天～\n如果你想我推荐美食，尽管告诉我，我一定全力帮你！🍱",
                    "嘿嘿 😅 用词温柔一点，我们的聊天会更舒服哦～\n如果你想知道吃什么，我随时帮你推荐美味的！💞",
                    "请不要使用不礼貌的词汇哦 🙏 我希望我们能开心地聊聊天～\n如果你想我帮你推荐食物，马上告诉我吧，我随时待命！🍲"
                ],

                ko: [
                    "앗! 그런 말은 조금 심해요 😅 저는 친절한 AI 챗봇이에요 💕\n우리 예쁘게 대화해요~ 혹시 음식 추천 받고 싶으면 바로 말해줘요! 제가 전심으로 도와드릴게요 🍜",
                    "헉... 그 말은 조금 거칠어요 🥺 부드럽게 말해볼까요? 😄\n대신 제가 맛있는 음식 추천해드릴게요! 💖",
                    "죄송하지만 그런 말엔 대답할 수 없어요 😔 그래도 괜찮아요~\n대신 뭐 먹을지 제가 도와드릴게요! 🍲",
                    "오잉? 이건 좀 과격하네요 😅 우리 서로 예의 있게 얘기해요 💞\n혹시 뭐 먹을지 고민돼요? 제가 바로 추천해드릴게요!",
                    "응? 😅 그런 단어보단 조금 더 부드럽게 말해요~\n대신 제가 맛있는 거 알려드릴까요? 😋",
                    "앗! 이건 조금 안 좋은 표현이에요 😅\n대신 제가 맛있는 음식 추천해드릴게요! 💕",
                    "미안하지만 욕설은 피해주세요 🙏 우리 즐겁게 얘기해요!\n대신 제가 뭐 먹을지 추천드릴게요 🍱",
                    "음... 문장에 조금 심한 단어가 있네요 🤔 괜찮아요~\n대신 제가 맛있는 메뉴 하나 골라드릴게요 💖",
                    "우리 싸우지 말고 😄 기분 좋게 얘기하자~\n그리고 제가 맛있는 음식 추천해줄게요 🍜",
                    "말투 조금만 순하게 바꿔줘요 🥰 그러면 제가 더 잘 도와드릴 수 있어요 💖\n혹시 지금 배고파요? 제가 바로 추천해드릴게요!"
                ],

                ja: [
                    "あっ！その言葉はちょっと強いですよ 😅 私はフレンドリーなAIチャットボットです 💕\nもっと優しく話しましょうね～ もし食べ物のおすすめが欲しいなら、すぐ教えてください！🍜",
                    "えっ…その言い方は少しきついかも 🥺 穏やかに話してみましょうか？✨\n代わりにおいしいご飯をおすすめします！💕",
                    "ごめんなさい 😔 そのような言葉には返事できませんが、\nそれでも楽しくお話ししたいです！「何を食べようかな？」と思ったら、私に聞いてね 🍲",
                    "へへっ 😄 怒らないでね～楽しく話そう 💖\n食べたいものを教えてくれたら、すぐにおすすめします！✨",
                    "あら…その言葉は少し強すぎますね 😅 でも大丈夫です！\n気分を変えて、おいしいものの話でもしませんか？😋",
                    "もしかしてタイプミスですか？🤔 大丈夫ですよ～\n食べ物のおすすめが欲しいなら、気軽に聞いてください 💕 すぐに紹介します！🍜",
                    "すみません 😅 そういう言葉には答えられませんが、\n別の話をしましょう～ たとえば今お腹すいてませんか？💖",
                    "怒らないでくださいね 😄 私は楽しく話すのが好きなんです～\nもし食べ物のおすすめが欲しいなら、すぐお教えします！🍱",
                    "えへへ 😅 もう少し優しい言葉で話しましょう～\nそのほうがもっと楽しいです 💞 何を食べようか迷っているなら、私に任せて！",
                    "ごめんね 🙏 不適切な言葉は使わないようにしましょう 💖\n楽しく会話したいです～ もし食べ物のおすすめが欲しいなら、今すぐ教えてね 🍲"
                ]
            }};

            function detectLanguage(text) {{
                const vietnameseChars = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;
                const chineseChars = /[\u4E00-\u9FFF]/;
                const koreanChars = /[\uAC00-\uD7AF]/;
                const japaneseChars = /[\u3040-\u30FF\u31F0-\u31FF\uFF66-\uFF9F]/;

                if (vietnameseChars.test(text)) return 'vi';
                if (chineseChars.test(text)) return 'zh';
                if (koreanChars.test(text)) return 'ko';
                if (japaneseChars.test(text)) return 'ja';

                // create and cache Vietnamese no-accent words (unchanged)
                if (!window._cachedVietnameseNoAccentWords) {{
                    window._cachedVietnameseNoAccentWords = [
                        ...new Set((profanityWords.vi || []).map(w => normalizeText(w)))
                    ];
                }}

                const normalized = normalizeText(text);
                const vnNoAccentWords = window._cachedVietnameseNoAccentWords;
                for (const word of vnNoAccentWords) {{
                    if (normalized.includes(word)) return 'vi';
                }}

                return 'en';
            }}

            function normalizeText(text) {{
                if (!text) return '';
                return text
                    .normalize('NFC')
                    .toLowerCase()
                    // chỉ rút gọn khi lặp từ 3 ký tự trở lên
                    .replace(/([a-z0-9à-ỹđ])\1{2,}/g, '$1$1')
                    .trim();
            }}

            // 🆕 Hàm bỏ dấu tiếng Việt
            function removeVietnameseTones(text) {{
                if (!text) return '';
                const toneMap = {{
                    'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
                    'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
                    'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
                    'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
                    'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
                    'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
                    'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
                    'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
                    'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
                    'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
                    'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
                    'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
                    'đ': 'd'
                }};
                return text.toLowerCase().split('').map(c => toneMap[c] || c).join('');
            }}

            // ✅ Tạo bản không dấu + bỏ khoảng trắng cho toàn bộ từ tiếng Việt
            profanityWords.vi = [
                ...new Set([
                    ...profanityWords.vi,
                    ...profanityWords.vi.map(w => normalizeText(w)),
                    ...profanityWords.vi.map(w => removeVietnameseTones(w)), // Bỏ dấu: "cái lồn" → "cai lon"
                    ...profanityWords.vi.map(w => removeVietnameseTones(w).replace(/\s+/g, '')) // 🆕 Bỏ dấu + khoảng trắng: "cai lon" → "cailon"
                ])
            ];

            // === Bộ hàm lọc từ tục tối ưu & tránh nhận nhầm tiếng Trung / Hàn ===
            function escapeRegex(str) {{
                return str.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
            }}

            function buildRegexFromList(words, opts = {{}}) {{
                const {{ useWordBoundary = true, caseInsensitive = true, treatAsCJK = false }} = opts;
                const cleaned = words
                .map(w => (w || '').trim())
                .filter(w => w.length >= 2); // tránh từ 1 ký tự bị false positive
                if (cleaned.length === 0) return null;

                const escaped = cleaned.map(w => escapeRegex(w));
                const pattern = escaped.join('|');

                let finalPattern = pattern;
                if (useWordBoundary && !treatAsCJK) {{
                    finalPattern = '\\b(?:' + pattern + ')\\b';
                }} else {{
                    finalPattern = '(?:' + pattern + ')';
                }}

                return new RegExp(finalPattern, caseInsensitive ? 'iu' : 'u');
            }}

            function prepareProfanityRegexCaches(profanityWords) {{
                window._profanityRegexCache = window._profanityRegexCache || {{}};
                if (!window._profanityRegexCache.vi) {{
                    const viOrig = profanityWords.vi || [];
                    const viNoAccent = viOrig.map(w => normalizeText(w)).filter(Boolean);
                    const combined = Array.from(new Set([...viOrig, ...viNoAccent]));
                    window._profanityRegexCache.vi = buildRegexFromList(combined, {{
                        useWordBoundary: false, caseInsensitive: true, treatAsCJK: false
                    }});
                }}

                if (!window._profanityRegexCache.en) {{
                    const en = profanityWords.en || [];
                    window._profanityRegexCache.en = buildRegexFromList(en, {{
                        useWordBoundary: true, caseInsensitive: true, treatAsCJK: false
                    }});
                }}

                if (!window._profanityRegexCache.zh) {{
                    const zh = (profanityWords.zh || []).filter(w => w && w.trim().length >= 2);
                    window._profanityRegexCache.zh = buildRegexFromList(zh, {{
                        useWordBoundary: false, caseInsensitive: true, treatAsCJK: true
                    }});
                }}

                if (!window._profanityRegexCache.ko) {{
                    const ko = (profanityWords.ko || []).filter(w => w && w.trim().length >= 2);
                    window._profanityRegexCache.ko = buildRegexFromList(ko, {{
                        useWordBoundary: false, caseInsensitive: true, treatAsCJK: true
                    }});
                }}

                // Japanese
                if (!window._profanityRegexCache.ja) {{
                    const ja = (profanityWords.ja || []).filter(w => w && w.trim().length >= 2);
                    window._profanityRegexCache.ja = buildRegexFromList(ja, {{
                        useWordBoundary: false, caseInsensitive: true, treatAsCJK: true
                    }});
                }}

                // store readable patterns for debug
                window._profanityRegexPatterns = {{
                    vi: window._profanityRegexCache.vi ? window._profanityRegexCache.vi.source : null,
                    en: window._profanityRegexCache.en ? window._profanityRegexCache.en.source : null,
                    zh: window._profanityRegexCache.zh ? window._profanityRegexCache.zh.source : null,
                    ko: window._profanityRegexCache.ko ? window._profanityRegexCache.ko.source : null,
                    ja: window._profanityRegexCache.ja ? window._profanityRegexCache.ja.source : null
                }};
                console.log("🔧 Profanity regex patterns prepared:", window._profanityRegexPatterns);
            }}

            // ====== Prepare exact token sets for profanity checking (fast & exact) ======
            function prepareProfanitySets(profanityWords) {{
                window._profanitySets = window._profanitySets || {{}};

                const normalizeToken = (t) => normalizeText(t || '');
                const removeTonesToken = (t) => removeVietnameseTones(t || ''); // 🆕

                ['vi','en','zh','ko','ja'].forEach(lang => {{
                    if (window._profanitySets[lang]) return;

                    const list = (profanityWords[lang] || []).map(w => (w || '').trim()).filter(Boolean);
                    const set = new Set();

                    list.forEach(w => {{
                        set.add(w.toLowerCase());
                        const norm = normalizeToken(w);
                        if (norm && norm !== w.toLowerCase()) set.add(norm);
                        
                        // 🆕 ĐẶC BIỆT CHO TIẾNG VIỆT: Thêm cả bản không dấu + không khoảng trắng
                        if (lang === 'vi') {{
                            const noTone = removeTonesToken(w);
                            if (noTone && noTone !== w.toLowerCase()) set.add(noTone);
                            
                            // 🆕 Thêm bản bỏ luôn khoảng trắng: "cai lon" → "cailon"
                            const noToneNoSpace = noTone.replace(/\s+/g, '');
                            if (noToneNoSpace && noToneNoSpace !== noTone) set.add(noToneNoSpace);
                        }}
                    }});

                    window._profanitySets[lang] = set;
                }});

                console.log("🔧 Profanity token sets prepared:", {{
                    viCount: window._profanitySets.vi ? window._profanitySets.vi.size : 0,
                    enCount: window._profanitySets.en ? window._profanitySets.en.size : 0
                }});
            }}

            function containsProfanity(text, langHint = null) {{
                console.log('🔍 [PROFANITY CHECK] Input:', text);

                if (!text || typeof text !== 'string')
                    return {{ found: false, lang: null, match: null }};

                const raw = text.trim();
                if (raw.length === 0)
                    return {{ found: false, lang: null, match: null }};

                // ✅ THÊM WHITELIST MẠNH HƠN - Các từ thông dụng bị nhầm
                const safeWordsWhitelist = [
                    // Tiếng Anh
                    'hello','hi','hey','hell','shell','yell','bell','spell','smell',
                    'assess','asset','class','pass','grass','glass','mass','bass',
                    'button','butter','shut','shuttle','cut','hut','nut','gut',
                    'clock','flock','block','rock','shock','stock','lock','dock',
                    'assume','assure','associate','passive','classic','massive',

                    // Tiếng Việt - các từ có chứa "đ" nhưng không phải tục
                    'địa điểm','đi đâu','đến đó','đây đó','đi chơi','đi ăn',
                    'đi làm','đang đói','đang đi','đang ở','đúng đó',

                    // Tiếng Trung - chào hỏi
                    '你好','您好','哈喽','嗨','早上好','下午好','晚上好',

                    // Tiếng Nhật
                    'こんにちは','こんばんは','おはよう','やあ','もしもし',

                    // Tiếng Hàn
                    '안녕하세요','안녕','여보세요','하이','헬로',

                    // Tiếng Pháp/Tây Ban Nha/Đức/Ý
                    'bonjour','salut','hola','ciao','hallo','buenos','buenas'
                ];

                const compact = raw.replace(/\s+/g, '').toLowerCase().trim();

                // ✅ CHECK WHITELIST TRƯỚC - CHỈ exact match hoặc word boundary
                const rawLower = raw.toLowerCase();
                const isWhitelisted = safeWordsWhitelist.some(w => {{
                    const wLower = w.toLowerCase();
                    
                    // Check exact match
                    if (rawLower === wLower || compact === wLower.replace(/\s+/g, '')) {{
                        return true;
                    }}
                    
                    // Check word boundary (chỉ cho phép nếu từ đứng riêng)
                    const regex = new RegExp('\\b' + wLower.replace(/\s+/g, '\\s+') + '\\b', 'i');
                    return regex.test(rawLower);
                }});

                if (isWhitelisted) {{
                    console.log('✅ [WHITELIST] Safe word detected → PASS');
                    return {{ found: false, lang: detectLanguage(raw), match: null }};
                }}

                prepareProfanityRegexCaches(profanityWords);
                prepareProfanitySets(profanityWords);

                const detectedLang = langHint || detectLanguage(raw) || 'vi';
                console.log('🌐 [LANG DETECT]', detectedLang);

                const sets = window._profanitySets || {{}};
                let langSet = sets[detectedLang] || sets.vi || new Set();
                const detected = detectedLang.toLowerCase();

                const normalizeToken = (t) => normalizeText(t || '').toLowerCase();

                // ==============
                // 🔸 TIẾNG VIỆT / ANH – GIỮ NGUYÊN DẤU CÂU, DÒ TỪ GỐC
                // ==============
                if (['vi','en'].includes(detected)) {{
                    // tách từ dựa trên khoảng trắng và ký tự đặc biệt
                    const words = raw.split(/(\s+|[,.!?;:'"()\[\]{{}}<>…~`@#%^&*\-_+=|\\\/]+)/g);
                    console.log('📝 [WORD SPLIT]', words);

                    for (const w of words) {{
                        const norm = normalizeToken(w);
                        console.log(`  🔎 Checking word: "${{w}}" → normalized: "${{norm}}"`);

                        // chỉ xét nếu từ có ít nhất 2 ký tự chữ
                        if (norm.length < 2) {{
                            console.log(`    ⚠️  Too short → SKIP`);
                            continue;
                        }}

                        // ✅ 1. CHECK EXACT MATCH TRƯỚC (Ưu tiên cao nhất)
                        if (langSet.has(norm)) {{
                            console.log(`    🎯 [EXACT MATCH] "${{norm}}" found in profanity set`);
                            console.log(`    ❌ [PROFANITY DETECTED] Word: "${{w}}", Match: "${{norm}}"`);
                            return {{ found: true, lang: detectedLang, match: w }};
                        }}

                        // ✅ 2. CHỈ CHECK SUBSTRING KHI:
                        // - Từ ngắn (< 6 ký tự) HOẶC
                        // - Có dấu hiệu viết tắt/né lọc (ký tự lặp lại, thiếu nguyên âm)
                        const hasRepeatedChars = /(.)\1{{2,}}/.test(norm); // "fckkkk", "shiiit"
                        const lacksVowels = !/[aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ]{{2}}/i.test(norm); // "dmkjsd"
                        const isShort = norm.length < 6;

                        const shouldCheckSubstring = hasRepeatedChars || lacksVowels || isShort;

                        if (shouldCheckSubstring) {{
                            console.log(`    🔬 [SUBSTRING CHECK] Checking substrings...`);
                            // dò chuỗi con liên tục (để bắt đcmkajsd)
                            // 🔧: tiếng Việt cho phép substring dài từ 2 ký tự (để bắt "dm", "du", "vl", ...)
                            const minLen = (detected === 'vi') ? 2 : 3;
                            const maxLen = Math.max(...Array.from(langSet, x => x.length));

                            for (let i = 0; i < norm.length; i++) {{
                                for (let j = i + minLen; j <= i + maxLen && j <= norm.length; j++) {{
                                    const sub = norm.slice(i, j);
                                    if (langSet.has(sub)) {{
                                        console.log(`    🔥 [SUBSTRING MATCH] "${{sub}}" found in "${{norm}}"`);
                                        console.log(`    ❌ [PROFANITY DETECTED] Word: "${{w}}", Substring: "${{sub}}"`);
                                        return {{ found: true, lang: detectedLang, match: w }};
                                    }}
                                }}
                            }}
                        }} else {{
                            console.log(`    ⭐️  Word looks normal → SKIP substring check`);
                        }}

                        console.log(`    ✅ Word "${{w}}" is clean`);
                    }}

                    // 3. CHECK CHUOI DINH NHAU - KIEM TRA CHUA TU TUC
                    console.log('🔍 [STICKY CHECK] Checking continuous string...');
                    const compactNorm = normalizeToken(compact);
                    const compactNoTone = removeVietnameseTones(compact);

                    // ✅ KIEM TRA CA BAN CO DAU VA KHONG DAU
                    for (const testStr of [compactNorm, compactNoTone]) {{
                        if (testStr.length < 4) continue;

                        console.log(`  🔎 Testing string: "${{testStr}}"`);

                        // DO TOAN BO TU TRONG TU DIEN XEM CO CHUA TRONG CHUOI KHONG
                        for (const badWord of langSet) {{
                            // Chi check tu >= 3 ky tu (tranh false positive)
                            if (badWord.length >= 3) {{
                                // CHECK CA BAN CO DAU VA KHONG DAU CUA BAD WORD
                                const badWordNoTone = removeVietnameseTones(badWord);
                                
                                // Neu testStr chua badWord (co dau hoac khong dau)
                                if (testStr.includes(badWord) || testStr.includes(badWordNoTone)) {{
                                    console.log(`    🔥 [STICKY MATCH] Found "${{badWord}}" (or no-tone version) inside "${{testStr}}"`);
                                    console.log(`    ❌ [PROFANITY DETECTED] Match: "${{badWord}}"`);
                                    return {{ found: true, lang: detectedLang, match: testStr }};
                                }}
                            }}
                        }}
                    }}
                    console.log('    ✅ No sticky profanity found');
                }}

                // ==============
                // 🔹 TRUNG / NHẬT / HÀN – GIỮ NGUYÊN LOGIC GỐC
                // ==============
                if (['zh','ko','ja'].includes(detected)) {{
                    const rx = window._profanityRegexCache && window._profanityRegexCache[detected];
                    if (rx) {{
                        const mRaw = raw.match(rx);
                        if (mRaw) {{
                            const match = mRaw[0];
                            console.log(`🎯 [CJK REGEX MATCH] "${{match}}"`);

                            const idx = raw.indexOf(match);
                            const before = raw[idx - 1] || '';
                            const after = raw[idx + match.length] || '';
                            const isIsolated =
                                (!before || /[^\p{{L}}\p{{Script=Han}}\p{{Script=Hiragana}}\p{{Script=Katakana}}\p{{Script=Hangul}}]/u.test(before)) &&
                                (!after  || /[^\p{{L}}\p{{Script=Han}}\p{{Script=Hiragana}}\p{{Script=Katakana}}\p{{Script=Hangul}}]/u.test(after));

                            if (isIsolated) {{
                                console.log(`❌ [PROFANITY DETECTED] CJK Match: "${{match}}"`);
                                return {{ found: true, lang: detectedLang, match }};
                            }} else {{
                                console.log(`🛡️ But not isolated → PASS`);
                            }}
                        }}
                    }}
                }}

                console.log('✅ [FINAL RESULT] Text is clean');
                return {{ found: false, lang: detectedLang, match: null }};
            }}

            function censorProfanity(text) {{
                if (!text) return text;

                const result = containsProfanity(text);
                if (!result.found || !result.match) return text;

                let out = text;
                let bad = result.match;

                // 🔧 Tìm vị trí xuất hiện đầu tiên của từ tục
                let start = out.toLowerCase().indexOf(bad.toLowerCase());
                if (start === -1) return out;

                // Xác định điểm kết thúc: mở rộng tới khi gặp dấu cách hoặc dấu câu
                let end = start + bad.length;
                while (end < out.length && /[a-zA-Zà-ỹ0-9_]/.test(out[end])) {{
                    end++;
                }}

                // 🔒 Tạo mask tương ứng
                const mask = '*'.repeat(end - start);

                // ✨ Ghép lại chuỗi sau khi che
                out = out.slice(0, start) + mask + out.slice(end);

                return out;
            }}

            // ===== TÍNH NĂNG MỚI 3: HỌC SỞ THÍCH USER =====
            let userPreferences = {{
                likes: [],
                dislikes: [],
                allergies: []
            }};

            function extractPreferences(userMessage, botReply) {{
                const lowerMsg = userMessage.toLowerCase();

                if (lowerMsg.includes('thích') || lowerMsg.includes('yêu') ||
                    lowerMsg.includes('ngon') || lowerMsg.includes('like') ||
                    lowerMsg.includes('love')) {{
                    const dishes = extractDishNames(userMessage + ' ' + botReply);
                    dishes.forEach(dish => {{
                        if (!userPreferences.likes.includes(dish)) {{
                            userPreferences.likes.push(dish);
                        }}
                    }});
                }}

                if (lowerMsg.includes('không thích') || lowerMsg.includes('ghét') ||
                    lowerMsg.includes('không ăn') || lowerMsg.includes('hate') ||
                    lowerMsg.includes("don't like")) {{
                    const dishes = extractDishNames(userMessage);
                    dishes.forEach(dish => {{
                        if (!userPreferences.dislikes.includes(dish)) {{
                            userPreferences.dislikes.push(dish);
                        }}
                    }});
                }}

                if (lowerMsg.includes('dị ứng') || lowerMsg.includes('allergic') ||
                    lowerMsg.includes('không ăn được')) {{
                    const ingredients = extractIngredients(userMessage);
                    ingredients.forEach(ing => {{
                        if (!userPreferences.allergies.includes(ing)) {{
                            userPreferences.allergies.push(ing);
                        }}
                    }});
                }}

                console.log('📊 User Preferences:', userPreferences);
            }}

            function extractDishNames(text) {{
                const dishKeywords = ['phở', 'bún', 'cơm', 'mì', 'bánh', 'chè', 'gỏi', 'nem', 'chả', 'canh', 'lẩu', 'pizza', 'burger', 'pasta', 'salad', 'soup'];
                const dishes = [];

                dishKeywords.forEach(keyword => {{
                    if (text.toLowerCase().includes(keyword)) {{
                        const index = text.toLowerCase().indexOf(keyword);
                        const dishName = text.substring(index, index + 20).split(/[,.\n]/)[0].trim();
                        if (dishName.length > 2 && dishName.length < 30) {{
                            dishes.push(dishName);
                        }}
                    }}
                }});

                return dishes;
            }}

            function extractIngredients(text) {{
                const ingredients = ['tôm', 'cua', 'cá', 'hải sản', 'sữa', 'trứng', 'đậu', 'lạc', 'hạt', 'seafood', 'milk', 'egg', 'peanut', 'nut'];
                const found = [];

                ingredients.forEach(ing => {{
                    if (text.toLowerCase().includes(ing)) {{
                        found.push(ing);
                    }}
                }});

                return found;
            }}

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
                "Đừng ngại, nhắn với mình đi nè 😄",
                "Trong một vở kịch buồn...em diễn trọn cả hai vai💔",
                "Anh hen em pickleball, ta von nhau pickleball...😻",
                "Thơm phứcccc, yéhaaaaa😽",
                "别害羞，来跟我聊聊吧 🌟",
                "放心啦，随时都可以找我聊天 💌",
                "遠慮しないで、話しかけてね 🌸",
                "大丈夫だよ、気軽にメッセージしてね ✉️",
                "부끄러워하지 말고 편하게 말 걸어줘 🌼",
                "괜찮아, 언제든지 메시지 보내도 돼 📩",
                "Don't be shy, just message me 🌈",
                "I'm right here, talk to me anytime 💭",
                "N’hésite pas, envoie-moi un message 🌻",
                "Je suis là, parle-moi quand tu veux 📬",
                "Non essere timido, scrivimi pure ⭐",
                "Sono qui, puoi parlarmi quando vuoi 💫",
                "장 푸억흥 선생님, 정말 멋지세요 🌟",
                "장 푸억흥 선생님 덕분에 자신감이 생겼어요 💖",
                "Ôi thôi chếccccc, nhắn tin với tui i🥰",
                "Thềm nhà có hoaa lalala🤗",
                "Sao sắp giáng sinh rồi mà vẫn còn cô đơn?",
                "Ủa tưởng ai cũng biết UIAboss chứ tarrrr😼",
                "Ngoan xin iu của UIAboss đâu òi taaa😽",
                "Trời oi lâu rồi mới được pữa chấc lượng như z áaaaaa😻",
                "Đứt chuỗi r pà ơi💔😿",
                "Vỡ tannnn😿"
            ];

            const welcomeMessages = [
                "Xin chào bạn iu~ 🌸 Mình là UIAboss đây, hôm nay bạn muốn mình gợi ý món ngon kiểu gì nhỉ? 💕",
                "Chào cưng nè~ 😘 Mình biết nhiều quán cực xịn luôn, muốn ăn gì thì nói mình nghe nha~",
                "Hello bạn yêu! 🍰 Mình ở đây để chăm sóc bạn bằng món ngon nè, hôm nay thích gì?",
                "Chào bạn thân mến! 💖 Hôm nay muốn ăn món lạ hay món comfort food đây? Mình gợi ý liền!",
                "Hi hi~ 🌷 Mình là UIAboss, chuyên gia ẩm thực đáng yêu của bạn nè, bạn đang thèm món gì?",
                "Xin chào bạn nhỏ! 🍓 Mình quan tâm bạn nè, hôm nay ăn gì cho vui và no bụng nhỉ?",
                "Hey hey! 😍 Mình ở đây để làm bạn hạnh phúc bằng đồ ăn ngon nha~ Bạn muốn thử món gì?",
                "Chào bạn yêu thương! 💕 Mình sẽ giúp bạn chọn món xịn, ăn xong happy luôn, muốn thử không?",
                "Hello hello~ 🌈 Hôm nay trời đẹp, cùng mình tìm món ăn làm bạn cười toe toét nhé! 😋",
                "Hi cưng nè! 🍪 Mình sẵn sàng gợi ý món ngon và chăm sóc bạn bằng lời khuyên ăn uống nè~",
                "Chào bạn iu! 🌸 Mình biết bạn thèm gì ngay từ ánh nhìn nè, muốn thử món lạ không? 😘",
                "Xin chào bạn thân yêu! 🍩 Ăn gì cho no mà vẫn vui vẻ, để mình lo hết nha~",
                "Hi bạn đáng yêu! 💖 Hôm nay mình sẽ dẫn bạn đi một chuyến ẩm thực cute cực, bắt đầu nào!",
                "Chào cưng! 🌷 Mình muốn biết hôm nay bạn muốn ăn gì để mình tư vấn cực kỹ nè 😄",
                "Hello bạn nhỏ xinh! 🍜 Mình sẽ giúp bạn no bụng và vui vẻ, bạn muốn ăn gì trước nào?",
                "Chào bạn iu mến! 😍 Mình quan tâm bạn lắm nè, hôm nay muốn ăn đồ ngọt hay đồ mặn?",
                "Hi hi! 🌸 Mình ở đây để làm bạn cười và no bụng luôn, muốn thử món nào trước?",
                "Xin chào bạn yêu quý! 🍰 Để mình chăm sóc bạn bằng đồ ăn ngon, hôm nay muốn gì nè?",
                "Hey cưng ơi! 💕 Mình sẽ gợi ý món ngon, ăn xong bạn hạnh phúc luôn nha~",
                "Hello bạn iu nè! 🌈 Mình cực quan tâm bạn nè, muốn ăn món nào để mình gợi ý siêu xinh luôn?",
                "Chào bạn yêu! 🍓 Mình đã chuẩn bị sẵn vài gợi ý món ngon cho bạn, bạn muốn thử món nào trước?",
                "Hi cưng! 🌸 Ăn gì hôm nay để mình tư vấn cho bạn no nê và happy nè~",
                "Xin chào bạn nhỏ! 🍪 Hôm nay mình muốn bạn ăn ngon, vui vẻ, muốn mình gợi ý món nào?",
                "Hello hello! 💖 Mình ở đây để làm bạn cười và no bụng, cùng mình chọn món ngon nào!",
                "Chào bạn iu! 🌈 Món ăn hôm nay sẽ được mình lựa chọn cẩn thận, bạn muốn thử món ngọt hay mặn?",
                "Hi bạn đáng yêu! 😘 Mình quan tâm bạn nè, hôm nay ăn gì mới hợp mood đây?",
                "Xin chào cưng! 🌷 Mình sẽ gợi ý món ngon, ăn xong bạn hạnh phúc luôn nha~",
                "Hey hey! 🍰 Bạn đang đói đúng không? Mình sẽ chăm sóc bạn bằng đồ ăn ngon liền!",
                "Chào bạn iu mến! 💕 Mình ở đây để giúp bạn tìm món ngon và cute nhất luôn nha~",
                "Hello bạn nhỏ! 😍 Hôm nay muốn ăn gì cho vui nhỉ, mình gợi ý liền nè!",
                "Hi hi~ 🌸 Mình sẽ dẫn bạn đi vòng quanh thế giới ẩm thực, bắt đầu từ món ngon nào đây?",
                "Chào bạn yêu! 🍩 Hôm nay mình muốn làm bạn no nê và cười toe toét, muốn thử món gì?",
                "Xin chào bạn thân! 💖 Mình quan tâm bạn lắm nè, hôm nay ăn món gì mới vui?",
                "Hey cưng nè! 🌈 Mình sẽ gợi ý món ngon, ăn xong bạn happy luôn, muốn thử món lạ không?",
                "Chào bạn iu! 😘 Mình sẵn sàng chăm sóc bạn bằng món ăn ngon và lời khuyên cute nè~",
                "Hello bạn yêu thương! 🍓 Mình ở đây để làm bạn cười và no bụng, hôm nay muốn ăn gì?",
                "Hi hi! 🌷 Hôm nay mình muốn bạn ăn ngon, vui vẻ, muốn mình gợi ý món nào trước?",
                "Xin chào bạn đáng yêu! 🍪 Mình đã chuẩn bị vài món ngon, muốn thử món lạ hay quen thuộc nhỉ?",
                "Chào cưng! 💖 Hôm nay ăn gì cho vui, mình gợi ý luôn nè, ăn xong happy liền!",
                "Hey hey! 🌸 Mình sẽ giúp bạn chọn món ngon cực cute, ăn xong cười toe toét luôn nha~",
                "Hello bạn iu nè! 🍰 Mình cực quan tâm bạn nè, muốn ăn món nào trước để mình tư vấn?",
                "Hi bạn nhỏ! 😍 Mình ở đây để chăm sóc bạn bằng đồ ăn ngon và lời khuyên cute nha~",
                "Chào bạn yêu thương! 🌈 Mình sẽ giúp bạn no bụng và vui vẻ, hôm nay thử món gì?",
                "Xin chào cưng! 💕 Ăn gì hôm nay cho vui, mình gợi ý món xinh xắn luôn nha~",
                "Hey bạn iu! 🍓 Hôm nay trời đẹp, cùng mình chọn món ngon và cute nhé 😘",
                "Chào bạn nhỏ xinh! 🌷 Mình quan tâm bạn lắm nè, muốn ăn món lạ hay món comfort food?",
                "Hello hello! 🍩 Mình sẽ dẫn bạn đi chuyến ẩm thực cute, ăn xong happy luôn!",
                "Hi hi! 💖 Hôm nay ăn gì cho no và vui, mình gợi ý món ngon cực xinh nè~",
                "Chào bạn iu mến! 🌸 Mình quan tâm bạn lắm, muốn thử món gì trước nha 😍",
                "Xin chào cưng! 🍰 Ăn gì hôm nay để mình giúp bạn no bụng và cười toe toét luôn?",
                "Hey hey! 🌈 Mình sẽ gợi ý món ngon cực đáng yêu, ăn xong bạn happy luôn nha~"
            ];

            const suggestionQuestions = [
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
                "Nghĩ mãi không ra ăn gì hết 😭",
                "Có món nào vừa rẻ vừa ngon hông nè 💸",
                "Nay thèm hải sản xíu 🦐",
                "Gợi ý mình vài món hot trend đi 😎",
                "Thèm ăn gì kiểu fusion, vừa Việt vừa Tây 🌮",
                "Muốn ăn đồ lên mood sáng tạo 🌈",
                "Ăn gì mà vừa nhìn là thèm ngay 😍",
                "Thử món gì mà màu sắc bắt mắt 🥗",
                "Đang muốn ăn vừa ngon vừa có story để check-in 📸",
                "Ăn gì mà kiểu “chill” cuối tuần 🎶",
                "Có món nào vừa ăn vừa thư giãn tâm hồn 🧘",
                "Muốn thử món độc lạ kiểu street food 🌯",
                "Hôm nay ăn kiểu healthy nhưng không nhàm chán 🥦",
                "Ăn gì mà kiểu tròn vị, đủ chua ngọt mặn 😋",
                "Thèm món gì mà vừa ăn vừa kể chuyện cười 😂",
                "Ăn gì kiểu retro vintage, gợi nhớ tuổi thơ 🍡",
                "Muốn ăn gì mà thử 1 lần trong đời 🌟",
                "Đói kiểu ‘muốn nhiều món ăn cùng lúc’ 🥢",
                "Ăn gì mà kiểu mood café chill, nhẹ nhàng ☕",
                "Muốn món gì mà vừa lạ vừa dễ làm tại nhà 🏠",
                "Thèm snack kiểu vặt vặt, nhâm nhi 🍿",
                "Ăn gì mà kiểu trendy trên TikTok 😎",
                "Hôm nay ăn gì mà kiểu luxury, sang chảnh 🥂",
                "Muốn món gì mà vừa ăn vừa feel like travel ✈️"
            ];

            // Lấy các elements
            const chatbotBtn = document.getElementById('chatbotBtn');
            //const chatWindow = document.getElementById('chatWindow');
            const closeBtn = document.getElementById('closeBtn');
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const messagesArea = document.getElementById('messagesArea');
            const suggestionsArea = document.getElementById('suggestionsArea');
            const speechBubble = document.getElementById('speechBubble');
            const bubbleText = document.getElementById('bubbleText');
            const chatAvatar = document.getElementById('chatAvatar');
            const chatHistorySidebar = document.getElementById('chatHistorySidebar');
            const historyCloseBtn = document.getElementById('historyCloseBtn');
            const historyList = document.getElementById('historyList');

            console.log('🔍 Elements:', {{
                chatbotBtn: !!chatbotBtn,
                chatWindow: !!chatWindow,
                speechBubble: !!speechBubble,
                closeBtn: !!closeBtn
            }});

            let conversationHistory = [];
            let conversationList = [];
            let suggestedDishes = [];
            let currentConversationID = null; // Biến này sẽ lưu ID từ database
            let lastInteractionTime = Date.now();
            let hasShownInitialSuggestions = false;
            let inactivityTimer = null;

            // Chat History Management
            let chatSessions = [];
            let currentSessionId = null;
            let isFirstLoad = true;

            async function fetchConversationList() {{
                try {{
                    const response = await fetch(`${{API_BASE_URL}}/conversations/`, {{ 
                        method: 'GET',
                        credentials: 'include'
                    }});

                    if (response.ok) {{
                        const data = await response.json();
                        if (data.status === 'success') {{
                            conversationList = data.conversations; // Lưu vào biến toàn cục
                            renderHistoryList(currentConversationID)
                        }}
                    }}
                }} catch (error) {{
                    console.error('Lỗi lấy danh sách chat:', error);
                }}
            }}

            // 2.2. Tải nội dung chi tiết của 1 đoạn chat
            async function loadConversationDetails(id) {{
                if (!id) {{
                    switchToNewChat();
                    return;
                }}

                try {{
                    const response = await fetch(`${{API_BASE_URL}}/load-chat/?conversation_id=${{id}}`, {{
                        method: 'GET',
                        credentials: 'include'
                    }});

                    if (response.ok) {{
                        const data = await response.json();
                        if (data.status === 'success') {{
                            // Cập nhật ID hiện tại
                            currentConversationID = data.conversation_id;
                            
                            // Xóa màn hình cũ và render tin nhắn từ server
                            const messagesArea = document.getElementById('messagesArea');
                            messagesArea.innerHTML = ''; 

                            conversationHistory = [];
                            
                            data.messages.forEach(msg => {{
                                addMessage(msg.sender === 'user' ? 'user' : 'bot', msg.content, false); 

                                conversationHistory.push({{
                                    role: msg.sender === 'user' ? 'user' : 'bot',
                                    text: msg.content.replace(/<[^>]*>/g, '') // Xóa HTML tag nếu có
                                }});
                            }});

                            // Ẩn gợi ý vì đây là chat cũ
                            const suggestionsArea = document.getElementById('suggestionsArea');
                            suggestionsArea.classList.add('hidden');

                            renderHistoryList(currentConversationID);
                            
                            console.log(`✅ Đã tải chat ID: ${{currentConversationID}}`);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Lỗi tải nội dung chat:', error);
                }}
            }}

            // 2.3. Lưu tin nhắn (Gửi tin nhắn mới)
            async function sendMessageToAPI(sender, content) {{
                try {{
                    const response = await fetch(`${{API_BASE_URL}}/save-chat/`, {{
                        method: 'POST',
                        credentials: 'include',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            sender: sender,
                            content: content,
                            conversation_id: currentConversationID // Gửi ID hiện tại (null nếu là chat mới)
                        }})
                    }});

                    if (response.ok) {{
                        const data = await response.json();
                        if (data.status === 'success') {{
                            // LOGIC QUAN TRỌNG:
                            // Nếu trước đó là chat mới (ID=null) và giờ Server trả về ID mới
                            if (!currentConversationID && data.conversation_id) {{
                                currentConversationID = data.conversation_id;
                                console.log('🆕 Đã tạo đoạn chat mới với ID:', currentConversationID);
                                
                                // Cập nhật lại URL (để F5 không mất)
                                // history.pushState({{}}, '', `?conversation_id=${{currentConversationID}}`);
                                
                                // Gọi lại API lấy danh sách để Sidebar cập nhật tiêu đề mới ngay lập tức
                                fetchConversationList();
                            }}
                        }}
                    }}
                }} catch (error) {{
                    console.error('Lỗi lưu tin nhắn:', error);
                }}
            }}

            // 3.1. Chuyển về chế độ Chat Mới (Giao diện trắng)
            function switchToNewChat() {{
                console.log("🔄 Chuyển sang Chat Mới");
                currentConversationID = null;
                
                // Xóa tin nhắn trên màn hình
                const messagesArea = document.getElementById('messagesArea');
                messagesArea.innerHTML = ''; 
                
                // Hiển thị lại gợi ý
                renderSuggestions(); 
                
                // Gửi tin nhắn chào mừng ngẫu nhiên (Client-side only, không lưu DB vội)
                const randomWelcome = welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];
                addMessage('bot', randomWelcome, false); // false = không lưu vào mảng local cũ

                // Cập nhật sidebar (bỏ highlight)
                renderHistoryList(null);
            }}

            // 4.1. Khi bấm nút mở Chatbot
            async function openChatWindow() {{
                const chatWindow = document.getElementById('chatWindow');
                const chatbotBtn = document.getElementById('chatbotBtn');
                const speechBubble = document.getElementById('speechBubble');

                chatWindow.style.display = 'flex';
                chatWindow.classList.add('open');
                chatbotBtn.style.display = 'none';
                speechBubble.style.display = 'none';

                // Lần đầu mở lên: Tải danh sách sidebar + Tải đoạn chat mới nhất (hoặc chat mới)
                await fetchConversationList();
                
                // Logic: Nếu chưa có ID nào, load chat mới nhất của user
                // (Bạn có thể tùy chỉnh logic này: luôn mở chat mới hay mở chat cũ)
                if (conversationList.length > 0 && !currentConversationID) {{
                    // Tải đoạn chat gần nhất
                    loadConversationDetails(conversationList[0].id);
                }} else if (!currentConversationID) {{
                    switchToNewChat();
                }}
            }}

            // 4.2. Khi bấm nút "Chat mới" (+) ở Sidebar
            const historyNewBtn = document.getElementById('historyNewBtn');
            if (historyNewBtn) {{
                historyNewBtn.addEventListener('click', (e) => {{
                    e.preventDefault();
                    switchToNewChat(); // Gọi hàm chuyển giao diện
                }});
            }}

            async function renameChatAPI(id, newTitle) {{
                try {{
                    const response = await fetch(`${{API_BASE_URL}}/rename-chat/`, {{ 
                        method: 'POST',
                        credentials: 'include',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ conversation_id: id, new_title: newTitle }})
                    }});

                    if (response.ok) {{
                        console.log('✅ Đổi tên thành công');
                        // Tải lại danh sách để cập nhật giao diện
                        fetchConversationList(); 
                    }} else {{
                        console.error('Lỗi đổi tên:', response.statusText);
                        // Nếu lỗi, vẫn vẽ lại danh sách để hủy bỏ trạng thái input
                        renderHistoryList();
                    }}
                }} catch (error) {{
                    console.error('Lỗi fetch rename:', error);
                    renderHistoryList();
                }}
            }}

            // API: Xóa đoạn chat
            async function deleteChatAPI(id) {{
                try {{
                    // Giả sử bạn sẽ tạo URL này trong Django urls.py
                    const response = await fetch(`${{API_BASE_URL}}/delete-chat/`, {{ 
                        method: 'POST',
                        credentials: 'include',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ conversation_id: id }})
                    }});

                    if (response.ok) {{
                        console.log('🗑️ Xóa thành công ID:', id);
                        
                        // Nếu đang xóa đúng đoạn chat đang mở -> Chuyển về chat mới
                        if (currentConversationID && id == currentConversationID) {{
                            switchToNewChat();
                        }}
                        
                        // Tải lại danh sách sau khi xóa
                        fetchConversationList();
                    }}
                }} catch (error) {{
                    console.error('Lỗi fetch delete:', error);
                }}
            }}

            // Render history list
           function renderHistoryList(highlightNewId = null) {{
                const historyList = document.getElementById('historyList');
                if (!historyList) return;

                historyList.innerHTML = '';

                // Sử dụng biến toàn cục conversationList (đã lấy từ API fetchConversationList)
                conversationList.forEach(session => {{
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    
                    // Kiểm tra Active (Lưu ý: so sánh lỏng == vì ID từ server có thể là số hoặc chuỗi)
                    if (currentConversationID && session.id == currentConversationID) {{
                        item.classList.add('active');
                    }}

                    // 🎯 Hiệu ứng trượt vào cho chat mới
                    if (session.id == highlightNewId) {{
                        item.classList.add('new-item-slide');
                        setTimeout(() => {{
                            item.scrollIntoView({{behavior: 'smooth', block: 'nearest'}});
                        }}, 100);
                    }}

                    // Render HTML
                    item.innerHTML = `
                        <span class="history-item-name">${{session.title}}</span> <div class="history-item-actions">
                            <button class="history-item-edit" title="Đổi tên">✏️</button>
                            <button class="history-item-delete" title="Xóa">🗑️</button>
                        </div>
                    `;

                    // ✅ SỰ KIỆN 1: Click vào item để tải nội dung chat
                    item.addEventListener('click', (e) => {{
                        // Chỉ load nếu KHÔNG click vào button sửa/xóa
                        if (!e.target.closest('.history-item-edit') && !e.target.closest('.history-item-delete')) {{
                            loadConversationDetails(session.id); // Gọi hàm API mới
                        }}
                    }});

                    // ✅ SỰ KIỆN 2: Nút Đổi tên (Cần gọi API)
                    const editBtn = item.querySelector('.history-item-edit');
                    editBtn.addEventListener('click', (e) => {{
                        e.stopPropagation();

                        const input = document.createElement('input');
                        input.type = 'text';
                        input.className = 'history-item-input';
                        input.value = session.title; // Dùng title

                        const nameSpan = item.querySelector('.history-item-name');
                        nameSpan.replaceWith(input);
                        input.focus();
                        input.select();

                        const saveEdit = async () => {{
                            const newName = input.value.trim();
                            if (newName && newName !== session.title) {{
                                // Gọi API đổi tên (Xem hàm bên dưới)
                                await renameChatAPI(session.id, newName);
                            }} else {{
                                // Nếu không đổi gì thì vẽ lại như cũ
                                renderHistoryList(); 
                            }}
                        }};

                        input.addEventListener('blur', saveEdit);
                        input.addEventListener('keypress', (e) => {{
                            if (e.key === 'Enter') saveEdit();
                        }});
                    }});

                    // ✅ SỰ KIỆN 3: Nút Xóa (Cần gọi API)
                    const deleteBtn = item.querySelector('.history-item-delete');
                    deleteBtn.addEventListener('click', async (e) => {{
                        e.stopPropagation();

                        const confirmMsg = (currentConversationID && session.id == currentConversationID)
                            ? 'Bạn đang xóa đoạn chat hiện tại. Xác nhận xóa?'
                            : `Xóa đoạn chat "${{session.title}}"?`;

                        if (confirm(confirmMsg)) {{
                            // Gọi API xóa (Xem hàm bên dưới)
                            await deleteChatAPI(session.id);
                        }}
                    }});

                    historyList.appendChild(item);
                }});
            }}

            // Toggle history sidebar
            function toggleHistorySidebar() {{
                chatHistorySidebar.classList.toggle('open');
            }}

            async function initializeApp() {{
                console.log("🚀 Đang khởi động ứng dụng...");
                
                // 1. Tải danh sách chat từ Server về (Cập nhật vào biến conversationList)
                await fetchConversationList();

                // 2. Kiểm tra danh sách vừa tải về
                console.log("✨ Luôn khởi tạo phiên Chat Mới (chờ tin nhắn đầu tiên để lưu)");
                switchToNewChat();
            }}

            // Gọi hàm khởi tạo ngay lập tức
            initializeApp();

            function updateBubbleText() {{
                bubbleText.textContent = teaseMessages[Math.floor(Math.random() * teaseMessages.length)];
            }}

            function getRandomSuggestions() {{
                const shuffled = [...suggestionQuestions].sort(() => Math.random() - 0.5);
                return shuffled.slice(0, 5);
            }}

            function renderSuggestions() {{
                hasShownInitialSuggestions = true;
                suggestionsArea.classList.remove('hidden');
                suggestionsArea.style.opacity = '1';        // ← THÊM DÒNG NÀY
                suggestionsArea.style.maxHeight = '';        // ← THÊM DÒNG NÀY
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

            async function openChatWindow() {{
                console.log('🎯 openChatWindow called');
                
                // 1. Xử lý giao diện (Ẩn/Hiện)
                const chatWindow = document.getElementById('chatWindow');
                const chatbotBtn = document.getElementById('chatbotBtn');
                const speechBubble = document.getElementById('speechBubble');

                chatWindow.style.display = 'flex';
                chatWindow.classList.add('open');
                chatbotBtn.style.display = 'none';
                chatbotBtn.classList.add('hidden');
                speechBubble.style.display = 'none';
                speechBubble.classList.add('hidden');

                // 2. Kiểm tra trạng thái
                const messagesArea = document.getElementById('messagesArea');
                
                if (messagesArea.children.length === 0) {{
                    console.log("🔄 Mở cửa sổ chat -> Đảm bảo danh sách cập nhật");
                    
                    // Cập nhật sidebar để user thấy lịch sử cũ nếu muốn bấm vào
                    await fetchConversationList();

                    // Nếu chưa có ID (tức là chưa chọn đoạn chat nào), giữ nguyên trạng thái Chat Mới
                    if (!currentConversationID) {{
                        console.log("✨ Giữ trạng thái Chat Mới");
                        switchToNewChat();
                    }}
                }}
            }}

            // Khởi động bubble text
            updateBubbleText();
            setInterval(updateBubbleText, 8000);

            // Sự kiện mở chatbot - BẤM NÚT
            if (chatbotBtn) {{
                chatbotBtn.addEventListener('click', (e) => {{
                    console.log('🖱️ Chatbot button clicked');
                    e.preventDefault();
                    e.stopPropagation();
                    openChatWindow();
                }});
                console.log('✅ Button event listener attached');
            }}

            // Sự kiện mở chatbot - BẤM BUBBLE
            if (speechBubble) {{
                speechBubble.addEventListener('click', (e) => {{
                    console.log('🖱️ Speech bubble clicked');
                    e.preventDefault();
                    e.stopPropagation();
                    openChatWindow();
                }});

                // Thêm cả mousedown để đảm bảo
                speechBubble.addEventListener('mousedown', (e) => {{
                    console.log('🖱️ Speech bubble mousedown');
                }});

                // Thêm cả touchstart cho mobile
                speechBubble.addEventListener('touchstart', (e) => {{
                    console.log('📱 Speech bubble touched');
                    e.preventDefault();
                    openChatWindow();
                }}, {{ passive: false }});

                console.log('✅ Bubble event listeners attached');

                // Event: Click avatar to toggle history
                if (chatAvatar) {{
                    chatAvatar.addEventListener('click', (e) => {{
                        console.log('🖱️ Chat avatar clicked');
                        e.preventDefault();
                        e.stopPropagation();
                        toggleHistorySidebar();
                    }});
                    console.log('✅ Avatar event listener attached');
                }}

                // Event: Close history sidebar
                if (historyCloseBtn) {{
                    historyCloseBtn.addEventListener('click', (e) => {{
                        console.log('🖱️ History close button clicked');
                        e.preventDefault();
                        e.stopPropagation();
                        chatHistorySidebar.classList.remove('open');
                    }});
                    console.log('✅ History close button event listener attached');
                }}

                // Event: New chat button (nút +)
                const historyNewBtn = document.getElementById('historyNewBtn');
                if (historyNewBtn) {{
                    historyNewBtn.addEventListener('click', (e) => {{
                        console.log('🖱️ New chat button clicked');
                        e.preventDefault();
                        e.stopPropagation();

                        switchToNewChat();

                        historyNewBtn.style.transform = 'rotate(135deg) scale(1.15)';
                        historyNewBtn.style.background = 'rgba(255, 255, 255, 0.5)';
                        historyNewBtn.style.boxShadow = '0 0 15px rgba(255, 255, 255, 0.6)';

                        setTimeout(() => {{
                            historyNewBtn.style.transform = '';
                            historyNewBtn.style.background = '';
                            historyNewBtn.style.boxShadow = '';
                        }}, 400);

                        // 3. Âm thanh (Giữ lại nếu thích)
                        try {{
                            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            const oscillator = audioContext.createOscillator();
                            const gainNode = audioContext.createGain();

                            oscillator.connect(gainNode);
                            gainNode.connect(audioContext.destination);

                            oscillator.frequency.value = 800;
                            oscillator.type = 'sine';
                            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);

                            oscillator.start(audioContext.currentTime);
                            oscillator.stop(audioContext.currentTime + 0.15);
                        }} catch (err) {{
                            // Bỏ qua lỗi âm thanh nếu trình duyệt chặn hoặc không hỗ trợ
                            console.log("Audio play failed or restricted"); 
                        }}

                        console.log('✅ Switched to new chat interface');
                    }});
                    console.log('✅ New chat button event listener attached');
                }}
            }}

            // Sự kiện đóng chatbot
            if (closeBtn) {{
                closeBtn.addEventListener('click', (e) => {{
                    console.log('🖱️ Close button clicked');
                    e.preventDefault();
                    e.stopPropagation();

                    chatWindow.classList.remove('open');
                    chatWindow.style.display = 'none';
                    chatbotBtn.style.display = 'flex';
                    chatbotBtn.classList.remove('hidden');
                    speechBubble.style.display = 'block';
                    speechBubble.classList.remove('hidden');

                    // Close history sidebar if open
                    chatHistorySidebar.classList.remove('open');
                }});
                console.log('✅ Close button event listener attached');
            }}

            async function sendMessage() {{ // Thêm async
                const text = messageInput.value.trim();
                if (!text) return;

                const lang = detectLanguage(text);
                const result = containsProfanity(text, lang);

                // --- TRƯỜNG HỢP 1: CÓ TỪ TỤC ---
                if (result.found) {{
                    const censored = censorProfanity(text);   
                    addMessage('user', censored);             
                    
                    // [SỬA] Dùng hàm API mới
                    await sendMessageToAPI('user', censored); 

                    const warningList = warningMessages[result.lang] || warningMessages['en'];
                    const randomMsg = warningList[Math.floor(Math.random() * warningList.length)];

                    console.warn("🚫 Blocked profanity token:", result.match, "→ censored:", censored);

                    setTimeout(async () => {{ // Thêm async
                        addMessage('bot', randomMsg);
                        // [SỬA] Dùng hàm API mới
                        await sendMessageToAPI('ai', randomMsg); 
                        renderSuggestions();
                    }}, 400);

                    messageInput.value = '';
                    return;
                }}

                // --- TRƯỜNG HỢP 2: TIN NHẮN SẠCH ---
                const userText = text;  // ← THÊM DÒNG NÀY (lưu text trước)
                messageInput.value = '';  // ← DI CHUYỂN LÊN ĐÂY (xóa input ngay)
                sendBtn.disabled = true;

                addMessage('user', userText);  // ← ĐỔI text → userText

                showTyping();

                // [SỬA] Dùng hàm API mới (Quan trọng: await để cập nhật ID nếu là chat mới)
                await sendMessageToAPI('user', userText);  // ← ĐỔI text → userText
                
                // Gọi AI (Trong hàm này cũng sẽ sửa đoạn lưu tin nhắn AI)
                callGeminiAPI(text); 
                resetInactivityTimer();
            }}

            sendBtn.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {{
                if (e.key === 'Enter') sendMessage();
            }});
            messageInput.addEventListener('input', () => {{
                sendBtn.disabled = !messageInput.value.trim();
                resetInactivityTimer();
            }});

            function addMessage(type, text, saveToHistory = true) {{
                hideTyping();

                // ✨ ẨN GỢI Ý MƯỢT KHI USER GỬI TIN
                if (type === 'user') {{
                    const suggestionsArea = document.getElementById('suggestionsArea');
                    suggestionsArea.style.transition = 'opacity 0.3s ease, max-height 0.3s ease';
                    suggestionsArea.style.opacity = '0';
                    suggestionsArea.style.maxHeight = '0';
                    setTimeout(() => {{
                        suggestionsArea.classList.add('hidden');
                    }}, 300);
                }}

                const time = new Date().toLocaleTimeString('vi-VN', {{ hour: '2-digit', minute: '2-digit' }});
                const div = document.createElement('div');
                div.className = 'message ' + type;

                // 👇 Xử lý format nội dung, có xuống dòng giữa các món
                const normalized = text.replace(/\\r\\n/g, '\\n').replace(/\\n{2,}/g, '\\n').trim();
                const lines = normalized.split('\\n');

                let htmlParts = [];
                let inOl = false;

                lines.forEach((line) => {{
                    const m = line.match(/^\\s*(\\d+)\\.\\s*(.*)$/); // dạng "1. Món"
                    if (m) {{
                        if (!inOl) {{
                            htmlParts.push('<ol>');
                            inOl = true;
                        }}
                        const liContent = m[2] || '';

                        // nếu trong nội dung món có xuống dòng, tách thành nhiều <p>
                        const subParts = liContent.split(/\\\\n|\\n/).map(s => s.trim()).filter(Boolean);
                        const formattedLi = subParts.map(p => `<p>${{p}}</p>`).join('');

                        // 🔸 thêm <br> sau mỗi món để tách ra rõ ràng
                        htmlParts.push(`<li>${{formattedLi}}</li><br>`);
                    }} else {{
                        if (inOl) {{
                            htmlParts.push('</ol>');
                            inOl = false;
                        }}
                        if (line.trim() !== '') {{
                            htmlParts.push(`<p>${{line.trim()}}</p>`);
                        }}
                    }}
                }});

                if (inOl) htmlParts.push('</ol>');
                const formattedText = htmlParts.join('');

                const avatarEmoji = type === 'bot' ? '🍜' : '👤';
                const avatarHTML = `<div class="message-avatar">${{avatarEmoji}}</div>`;

                if (type === 'user') {{
                    div.innerHTML = `
                        <div class="message-content">
                            <div class="message-text">${{formattedText}}</div>
                            <div class="message-time">${{time}}</div>
                        </div>
                        ${{avatarHTML}}
                    `;
                }} else {{
                    div.innerHTML = `
                        ${{avatarHTML}}
                        <div class="message-content">
                            <div class="message-text">${{formattedText}}</div>
                            <div class="message-time">${{time}}</div>
                        </div>
                    `;
                }}

                messagesArea.appendChild(div);
                messagesArea.scrollTop = messagesArea.scrollHeight;

                // ✅ CHỈ lưu vào history nếu saveToHistory = true
                if (saveToHistory) {{
                    if (type === 'user') {{
                        conversationHistory.push({{ role: 'user', text: text }});
                    }} else {{
                        const plainText = text.replace(/<[^>]*>/g, '');
                        conversationHistory.push({{ role: 'bot', text: plainText }});
                    }}
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
                // Xóa các ký hiệu Markdown như **bold**, *italic*
                text = text
                    .replace(/\*\*(.*?)\*\*/g, '$1')
                    .replace(/\*(.*?)\*/g, '$1')
                    .replace(/__(.*?)__/g, '$1')
                    .replace(/_(.*?)_/g, '$1');

                // KHÔNG dùng regex phức tạp nữa – làm thủ công để tránh lỗi
                const lines = text.split('\n');
                const newLines = lines.map(line => {{
                    // Tìm số thứ tự (1., 2., 3., …)
                    const match = line.match(/^(\d+\.\s+)([^:]+):/);
                    if (match) {{
                        const num = match[1];
                        const dishName = match[2].trim();
                        return num + `<span class="dish-name">${{dishName}}</span>:` + line.substring(match[0].length);
                    }}
                    return line;
                }});

                // Thêm khoảng cách giữa các mục
                text = newLines.join('\n').trim();
                return text;
            }}

            async function callGeminiAPI(userMessage) {{
                console.log('🔥 Bắt đầu gọi Gemini API...');
                console.log('📝 User message:', userMessage);

                const historyContext = conversationHistory.slice(-6).map(h =>
                    `${{h.role === 'user' ? 'Người dùng' : 'UIAboss'}}: ${{h.text}}`
                ).join('\n');

                const suggestedDishesContext = suggestedDishes.length > 0
                    ? `\nCác món ĐÃ GỢI Ý (KHÔNG được gợi ý lại): ${{suggestedDishes.join(', ')}}`
                    : '';

                const preferencesContext = `
            User Preferences (IMPORTANT - Use this to personalize recommendations):
            - Likes: ${{userPreferences.likes.length > 0 ? userPreferences.likes.join(', ') : 'Not learned yet'}}
            - Dislikes: ${{userPreferences.dislikes.length > 0 ? userPreferences.dislikes.join(', ') : 'Not learned yet'}}
            - Allergies: ${{userPreferences.allergies.length > 0 ? userPreferences.allergies.join(', ') : 'Not learned yet'}}

            NEVER suggest dishes that user dislikes or is allergic to!
            NEVER suggest dishes that are already in the suggested list above!`;

                const lowerMsg = userMessage.toLowerCase().trim();

                // Kiểm tra xem có phải câu chào hỏi/vô nghĩa không (mở rộng cho nhiều ngôn ngữ)
                const greetingPatterns = [
                    // Tiếng Việt
                    /^(xin chào|chào|chào bạn|chào bot|hế nhô|hê lô|alo|alô|dạo này thế nào|khỏe không)$/i,
                    // Tiếng Anh
                    /^(hello|hi|hey|greetings|good morning|good afternoon|good evening|howdy|sup|what's up|whats up|yo)$/i,
                    // Tiếng Trung
                    /^(你好|您好|嗨|哈喽|早上好|下午好|晚上好|喂)$/i,
                    // Tiếng Nhật
                    /^(こんにちは|おはよう|こんばんは|やあ|もしもし)$/i,
                    // Tiếng Hàn
                    /^(안녕하세요|안녕|여보세요)$/i,
                    // Tiếng Pháp
                    /^(bonjour|salut|bonsoir|coucou)$/i,
                    // Tiếng Tây Ban Nha
                    /^(hola|buenos días|buenas tardes|buenas noches)$/i,
                    // Tiếng Đức
                    /^(hallo|guten tag|guten morgen|guten abend)$/i,
                    // Tiếng Ý
                    /^(ciao|buongiorno|buonasera)$/i,
                    // Tiếng Thái
                    /^(สวัสดี|หวัดดี)$/i,
                    // Tiếng Indonesia/Malay
                    /^(halo|hai|selamat pagi|selamat siang|selamat malam)$/i
                ];

                const isGreeting = greetingPatterns.some(pattern => pattern.test(lowerMsg)) ||
                    lowerMsg.length === 0 || // Tin nhắn rỗng
                    lowerMsg.length <= 2 || // Quá ngắn (1-2 ký tự)
                    /^[a-z]{{4,}}$/i.test(lowerMsg) && !/[aeiou]{{2}}/i.test(lowerMsg) || // Random keyboard không có nguyên âm liên tiếp
                    /^(.)\1{{3,}}$/.test(lowerMsg) || // Ký tự lặp lại (aaaa, bbbb)
                    /^[^\w\s]+$/.test(lowerMsg); // Chỉ toàn ký tự đặc biệt (!@#$%^)

                const isUndecided =
                    lowerMsg.includes('không biết ăn gì') ||
                    lowerMsg.includes('không biết ăn') ||
                    lowerMsg.includes('chưa nghĩ ra') ||
                    lowerMsg.includes('không nghĩ ra') ||
                    lowerMsg.includes("don't know what to eat") ||
                    lowerMsg.includes("dont know what to eat") ||
                    lowerMsg.includes('no idea') ||
                    lowerMsg.includes('不知道吃什么') || // Tiếng Trung
                    lowerMsg.includes('不知道吃啥') ||
                    lowerMsg.includes('何を食べるか分からない') || // Tiếng Nhật
                    lowerMsg.includes('뭐 먹을지 모르겠어'); // Tiếng Hàn

                let contextPrompt = '';

                // Nếu là câu chào hoặc vô nghĩa -> không gợi ý món ngay
                if (isGreeting) {{
                    contextPrompt = `
            IMPORTANT: User just sent a greeting or unclear/random message.
            DO NOT suggest dishes immediately!
            Instead:
            1. Greet them warmly back (in their language)
            2. Ask gentle questions to understand their needs:
            - How are they feeling? (hungry, tired, energetic?)
            - What mood are they in? (want something light, heavy, comfort food?)
            - Any preferences today? (spicy, sweet, sour, healthy?)
            - What time is it for them? (breakfast, lunch, dinner, snack?)
            3. Wait for their response before making dish recommendations

            Be friendly and conversational, not robotic.`;
                }}
                // Nếu người dùng không biết ăn gì -> gợi ý dựa trên context
                else if (isUndecided) {{
                    try {{
                        const currentHour = new Date().getHours();
                        const currentMonth = new Date().getMonth() + 1;

                        let timeOfDay = '';
                        if (currentHour >= 5 && currentHour < 11) timeOfDay = 'morning (breakfast time)';
                        else if (currentHour >= 11 && currentHour < 14) timeOfDay = 'lunch time';
                        else if (currentHour >= 14 && currentHour < 17) timeOfDay = 'afternoon (snack time)';
                        else if (currentHour >= 17 && currentHour < 21) timeOfDay = 'dinner time';
                        else timeOfDay = 'late night (light meal time)';

                        let season = '';
                        if (currentMonth >= 3 && currentMonth <= 5) season = 'Spring';
                        else if (currentMonth >= 6 && currentMonth <= 8) season = 'Summer (hot)';
                        else if (currentMonth >= 9 && currentMonth <= 11) season = 'Autumn (cool)';
                        else season = 'Winter (cold)';

                        contextPrompt = `
            CONTEXT FOR RECOMMENDATION:
            - Current time: ${{timeOfDay}}
            - Current season: ${{season}}
            - User location: Ho Chi Minh City, Vietnam (tropical climate)

            Since user doesn't know what to eat, suggest 6-8 NEW dishes (not previously suggested) that are:
            1. Appropriate for ${{timeOfDay}}
            2. Suitable for ${{season}} weather
            3. Popular in Vietnamese cuisine
            4. NOT in the already suggested list above`;

                    }} catch (e) {{
                        console.log('Could not get context info:', e);
                    }}
                }}

                const prompt = `You are UIAboss, a friendly and attentive customer service staff at a Vietnamese restaurant.

            === PRIORITY CHECK #1: TOPIC RESTRICTION ===
            CRITICAL - CHECK THIS FIRST BEFORE ANYTHING ELSE:

            You ONLY discuss topics related to: food, drinks, dishes, restaurants, cafes, cuisine, cooking, recipes, eating, dining.

            If the user's message is about OTHER topics (weather, news, programming, math, history, sports, politics, science, technology, games, movies, music, etc.):
            → STOP IMMEDIATELY
            → DO NOT answer the question
            → Politely decline and redirect to food topics
            → Be gentle, friendly, and brief in your refusal

            Examples of how to decline (match user's language):
            - English: "I appreciate the question, but I'm specialized in food and dining recommendations only! 😊 I'd love to help you find something delicious to eat instead. What are you in the mood for?"
            - Vietnamese: "Cảm ơn bạn đã hỏi, nhưng mình chỉ chuyên về món ăn thôi nha! 😊 Để mình giúp bạn tìm món ngon hơn nhé. Bạn đang thèm ăn gì không?"
            - Chinese: "谢谢你的提问,不过我只专注于美食推荐哦!😊 让我帮你找些好吃的吧。你想吃什么呢?"
            - Japanese: "ご質問ありがとうございます。でも、私は料理の専門家なんです!😊 美味しいものを探しましょう。何が食べたいですか?"
            - Korean: "질문해 주셔서 감사합니다만, 저는 음식 전문이에요! 😊 맛있는 음식을 찾아드릴게요. 무엇을 드시고 싶으세요?"
            - French: "Merci pour la question, mais je me spécialise uniquement dans la nourriture! 😊 Que voulez-vous manger?"
            - Spanish: "Gracias por la pregunta, pero solo me especializo en comida! 😊 ¿Qué te gustaría comer?"

            === IF TOPIC IS FOOD-RELATED, CONTINUE BELOW ===

            LANGUAGE ADAPTATION:
            - ALWAYS respond in the SAME LANGUAGE the user uses
            - Detect and match: Vietnamese, English, Chinese, Japanese, Korean, Thai, French, Spanish, German, Italian, Indonesian, etc.
            - Match the user's language naturally and fluently

            AVOID REPEAT SUGGESTIONS:
            ${{suggestedDishesContext}}
            - When suggesting dishes, NEVER suggest dishes from the list above
            - Always suggest NEW and DIFFERENT dishes
            - Keep track of what's been mentioned

            DISH RECOMMENDATIONS (when appropriate):
            - Suggest 6-8 different dishes when user wants recommendations
            - Provide variety: different types (soup, rice, noodles, snacks, drinks)
            - Number them clearly (1. Dish Name, 2. Dish Name, etc.)
            - Give brief description for each dish (1-2 sentences)

            ${{preferencesContext}}

            ${{contextPrompt}}

            Conversation style:
            - Natural, friendly like a close friend
            - Show genuine care for customers
            - Ask about preferences, mood, previous meals when needed
            - Suggest dishes suitable for customer's condition (hungry, hot, cold, light, nutritious...)
            - Briefly explain why suggesting that dish (warming, cooling, easy to eat, nutritious...)
            - Use emojis appropriately but not too much
            - IMPORTANT: Do not use ** or __ for bold, just write plain text

            Recent conversation history:
            ${{historyContext}}

            User just said: ${{userMessage}}

            Respond naturally, caringly and helpfully in the SAME LANGUAGE the user used.`;

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
                        addMessage('bot', `Ới! Có lỗi xảy ra rồi bạn ơi 😢\nMình đang gặp chút vấn đề kỹ thuật, bạn thử lại sau nhé!`);
                        sendBtn.disabled = false;
                        return;
                    }}

                    const data = await res.json();
                    let botReply = data.candidates?.[0]?.content?.parts?.[0]?.text;

                    if (botReply) {{
                        botReply = cleanMarkdown(botReply);
                        console.log('💬 Bot reply (cleaned):', botReply);

                        extractPreferences(userMessage, botReply);

                        // Extract và lưu các món đã gợi ý (chỉ khi KHÔNG phải greeting/vô nghĩa)
                        if (!isGreeting) {{
                            const dishMatches = botReply.match(/\d+\.\s*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\s+[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđA-Z]+)*)/g);
                            if (dishMatches) {{
                                dishMatches.forEach(match => {{
                                    const dish = match.replace(/^\d+\.\s*/, '').trim();
                                    if (dish.length > 3 && !suggestedDishes.includes(dish)) {{
                                        suggestedDishes.push(dish);
                                        console.log('📝 Đã lưu món:', dish);
                                    }}
                                }});
                                console.log('📋 Danh sách món đã gợi ý:', suggestedDishes);
                            }}
                        }}

                        addMessage('bot', botReply);
                        await sendMessageToAPI('ai', botReply);

                        resetInactivityTimer();
                    }} else {{
                        console.error('❌ Không tìm thấy text trong response:', data);
                        addMessage('bot', 'Xin lỗi bạn nhé! Mình đang hơi bận, thử lại sau nhé! 😅');
                    }}
                }} catch (e) {{
                    console.error('❌ Fetch Error:', e);
                    addMessage('bot', `Ới! Mình bị lỗi kết nối rồi 😢\nBạn kiểm tra mạng và thử lại nhé!`);
                }}
                sendBtn.disabled = false;
            }}

            console.log('✅ Chatbot initialization complete');

            // ====== EMOJI PICKER FUNCTIONALITY ======
            const emojiBtn = document.getElementById('emojiBtn');
            const emojiPicker = document.getElementById('emojiPicker');
            const emojiPickerElement = emojiPicker.querySelector('emoji-picker');
            const messageInputEl = document.getElementById('messageInput'); // 🔧 đổi tên biến

            // Mở/tắt picker
            emojiBtn.addEventListener('click', (e) => {{
                e.stopPropagation();
                emojiPicker.classList.toggle('hidden');
            }});

            // Khi chọn emoji
            emojiPickerElement.addEventListener('emoji-click', (event) => {{
                const emoji = event.detail.unicode;
                const start = messageInputEl.selectionStart || messageInputEl.value.length;
                const end = messageInputEl.selectionEnd || messageInputEl.value.length;
                messageInputEl.value = messageInputEl.value.slice(0, start) + emoji + messageInputEl.value.slice(end);
                messageInputEl.focus();
                messageInputEl.selectionStart = messageInputEl.selectionEnd = start + emoji.length;
            }});

            // Click ra ngoài thì đóng picker
            document.addEventListener('click', (e) => {{
                if (!emojiPicker.contains(e.target) && e.target !== emojiBtn) {{
                    emojiPicker.classList.add('hidden');
                }}
            }});
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