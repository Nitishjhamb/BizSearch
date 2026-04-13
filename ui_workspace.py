from fasthtml.common import * # type: ignore

# ==========================================
# THE POPUP COMPONENT
# ==========================================
def LimitModal():
    return Div(
        Div(
            Div("Daily limit reached", cls="modal-title"),
            P("Standard accounts are limited to 5 high-compute RAG queries per day to maintain server integrity. Request a limit increase from the administrator below.", cls="modal-body"),
            Div(
                Form(
                    Input(name="message", placeholder="Reason for increase…", cls="modal-input", required=True),
                    Button("Request override", cls="btn-danger", hx_post="/request-access", hx_target="#modal-body"),
                ),
                id="modal-body"
            ),
            Button("Dismiss", onclick="document.getElementById('modal-container').innerHTML=''", cls="btn-dismiss"),
            cls="modal-box"
        ),
        cls="modal-backdrop"
    )

# ==========================================
# MAIN WORKSPACE
# ==========================================
def WorkspaceLayout(user_id, co2_saved):
    
    sidebar = Aside(
        Div("Bizsearch.", cls="logo"),

        # 1. SYNC DOCUMENT SECTION
        Div(
            Div("Sync Document", cls="sb-label"),
            Form(
                # Hidden file input and visible dropzone
                Script("function triggerFile() { document.getElementById('file-in').click(); } function onFile(el) { if(el.files[0]) { document.getElementById('fz-label').innerHTML = el.files[0].name + ' &middot; <span>change</span>'; } }"),
                Div(
                    NotStr('<svg class="fz-icon" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'),
                    Div(NotStr("Drop PDF or TXT &middot; <span>browse</span>"), cls="fz-label", id="fz-label"),
                    cls="file-zone", id="dropzone", onclick="triggerFile()"
                ),
                Input(type="file", name="file_upload", id="file-in", accept=".pdf,.txt", style="display:none", onchange="onFile(this)"),
                
                # Buttons
                Div(
                    Button("Sync", cls="btn btn-lime", hx_post="/upload-sync", hx_target="#sync-status", hx_indicator="#sync-spinner", hx_encoding="multipart/form-data"),
                    Button("Clear", cls="btn btn-ghost", hx_post="/clear-index", hx_target="#sync-status", type="button"), 
                    cls="btn-row"
                ),
            ),
            # Targets for HTMX Responses
            Div(id="sync-status"),
            Span("PROCESSING...", id="sync-spinner", cls="htmx-indicator status-pill show", style="display:none;"),
            cls="sb-section"
        ),

        # 2. OPERATOR SECTION
        Div(
            Div("Operator", cls="sb-label"),
            Div(
                Div("Session ID", cls="ic-label"),
                Div(user_id, cls="ic-val"),
                cls="info-card"
            ),
            cls="sb-section"
        ),

        # 3. CO2 SECTION
        Div(
            Div("CO₂ Offset", cls="sb-label"),
            Div(
                Div(f"{co2_saved:.2f}", id="carbon-amount", cls="co2-num"),
                Div("g CO₂ · local embedding nodes", cls="co2-sub"),
                cls="info-card"
            ),
            cls="sb-section"
        ),

        # 4. LOGOUT FOOTER
        Div(
            Form(Button("Log out", cls="btn-logout"), action="/logout", method="post"),
            cls="sb-footer"
        ),
        cls="sidebar"
    )

    # CHANGED FROM Main() to Div() to bypass FastHTML's automatic Pico.css constraints!
    main_content = Div(
     
        # CHAT HISTORY (Starts completely empty!)
        Div(id="chat-history", cls="messages"),

        # TYPING INDICATOR (HTMX Target)
        Div(
            Div(NotStr('<svg viewBox="0 0 24 24" fill="#c8ff00"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg>'), cls="ai-avatar"),
            Div(Div(cls="td"), Div(cls="td"), Div(cls="td"), cls="typing-bubble"),
            id="chat-indicator", cls="htmx-indicator typing-wrap", style="display:none;"
        ),

        # INPUT AREA
        Div(
            Div(
                Input(name="search_query", placeholder="Ask anything about the report…", id="query-input",
                      hx_post="/search", hx_trigger="keyup[key=='Enter']", hx_target="#chat-history",
                      hx_swap="beforeend", hx_indicator="#chat-indicator", maxlength="500", autocomplete="off",
                      onkeyup="if(event.key=='Enter') appendUserMsg(); document.getElementById('char-count').innerText = this.value.length + ' / 500';",
                      oninput="document.getElementById('char-count').innerText = this.value.length + ' / 500';",
                      cls="chat-input"),
                Button(
                    NotStr('<svg class="send-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14.5 8L2 2.5L4.5 8L2 13.5L14.5 8Z" fill="#000" stroke="#000" stroke-width="0.5" stroke-linejoin="round"/></svg>'),
                    hx_post="/search", hx_target="#chat-history", hx_swap="beforeend", hx_indicator="#chat-indicator",
                    hx_include="#query-input", onclick="appendUserMsg();", cls="send-btn", aria_label="Send message"
                ),
                cls="input-shell"
            ),
            Div(
                Span("Enter to send", cls="meta-hint"),
                Span("0 / 500", id="char-count", cls="meta-count"),
                cls="input-meta"
            ),
            cls="input-area"
        ),
        
        # JAVASCRIPT LOGIC
        Script("""
            function appendUserMsg() {
                const input = document.getElementById('query-input');
                const text = input.value.trim();
                if(text) {
                    const chat = document.getElementById('chat-history');
                    const w = document.createElement('div'); w.className = 'msg-user';
                    const b = document.createElement('div'); b.className = 'bubble-user'; b.textContent = text;
                    w.appendChild(b); chat.appendChild(w);
                    chat.scrollTop = chat.scrollHeight;
                    setTimeout(() => { input.value = ''; document.getElementById('char-count').innerText = '0 / 500'; }, 20);
                }
            }

            document.body.addEventListener('htmx:afterSettle', function(evt) {
                const newMsgs = evt.detail.target.querySelectorAll('.ai-msg:not(.typed)');
                newMsgs.forEach(msg => {
                    msg.classList.add('typed');
                    msg.className = 'msg-ai typed'; 
                    const text = msg.innerHTML; 
                    
                    msg.innerHTML = `
                        <div class="ai-avatar"><svg viewBox="0 0 24 24" fill="#c8ff00"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg></div>
                        <div class="bubble-ai"></div>
                    `;
                    const bubble = msg.querySelector('.bubble-ai');
                    
                    let i = 0; let isTag = false; let currentHtml = "";
                    function typeWriter() {
                        if (i < text.length) {
                            if(text.charAt(i) === '<') isTag = true;
                            currentHtml += text.charAt(i);
                            if(text.charAt(i) === '>') isTag = false;
                            
                            bubble.innerHTML = currentHtml;
                            i++;
                            
                            if(isTag) { typeWriter(); } else {
                                const chat = document.getElementById('chat-history');
                                chat.scrollTop = chat.scrollHeight;
                                setTimeout(typeWriter, 12);
                            }
                        }
                    }
                    typeWriter();
                });
            });
        """),
        cls="main"
    )

    # ==========================================
    # CSS STYLES (Enforcing 100vw to break out of Pico.css)
    # ==========================================
    ws_style = Style("""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root { --lime: #c8ff00; --lime-hover: #d4ff33; --lime-active: #b5ef00; --bg-root: #080808; --bg-sidebar: #0d0d0d; --bg-card: #0a0a0a; --bg-input: #0d0d0d; --bg-msg-ai: #0f0f0f; --bg-msg-user: #141414; --border-subtle: #1a1a1a; --border-mid: #1e1e1e; --border-active: #2e2e2e; --text-primary: #e8e8e8; --text-secondary: #ccc; --text-muted: #666; --text-faint: #333; --text-placeholder: #2e2e2e; --radius-sm: 8px; --radius-md: 10px; --radius-lg: 12px; --radius-xl: 16px; }
        
        /* Forces the body to ignore all padding and take up the whole screen */
        html, body { height: 100vh; width: 100vw; margin: 0 !important; padding: 0 !important; overflow: hidden; background: #050505; font-family: 'Inter', sans-serif; color: var(--text-primary); -webkit-font-smoothing: antialiased; }
        
        /* The workspace now forcefully stretches across the full viewport */
        .workspace { display: flex; width: 100vw !important; max-width: none !important; height: 100vh; background: var(--bg-root); overflow: hidden; margin: 0; }
        .ws-wrapper { display: flex; width: 100%; height: 100%; flex: 1; }
        
        .sidebar { width: 260px; min-width: 260px; background: var(--bg-sidebar); border-right: 1px solid var(--border-subtle); display: flex; flex-direction: column; padding: 28px 20px; overflow-y: auto; flex-shrink: 0; }
        .sidebar::-webkit-scrollbar { width: 3px; } .sidebar::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 2px; }
        .logo { font-size: 1.4rem; font-weight: 600; color: var(--lime); letter-spacing: -0.5px; margin-bottom: 30px; flex-shrink: 0; }
        .sb-section { margin-bottom: 26px; }
        .sb-label { font-size: 10px; font-weight: 600; letter-spacing: 2.5px; color: #333; text-transform: uppercase; margin-bottom: 12px; }
        
        .file-zone { border: 1px dashed #242424; border-radius: var(--radius-md); padding: 16px 12px; text-align: center; cursor: pointer; transition: border-color 0.2s, background 0.2s; margin-bottom: 10px; }
        .file-zone:hover { border-color: var(--lime); background: #0e0e0e; }
        .file-zone:hover .fz-label span { opacity: 1; }
        .fz-icon { display: block; margin: 0 auto 8px; width: 22px; height: 22px; opacity: 0.3; }
        .fz-label { font-size: 11px; color: #444; font-weight: 500; }
        .fz-label span { color: var(--lime); opacity: 0.7; transition: opacity 0.2s; }
        
        .btn-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .btn { height: 38px; border: none; border-radius: var(--radius-sm); font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; cursor: pointer; transition: background 0.18s, transform 0.15s, border-color 0.18s, color 0.18s; display: flex; align-items: center; justify-content: center; gap: 6px; outline: none; }
        .btn:focus-visible { box-shadow: 0 0 0 2px rgba(200,255,0,0.3); }
        .btn-lime { background: var(--lime); color: #000; }
        .btn-lime:hover { background: var(--lime-hover); transform: translateY(-1px); }
        .btn-lime:active { background: var(--lime-active); transform: translateY(0); }
        .btn-ghost { background: #111; color: #777; border: 1px solid var(--border-mid); }
        .btn-ghost:hover { background: #161616; color: #bbb; border-color: #2a2a2a; }
        
        #sync-status { margin-top: 10px; min-height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--lime); background: #0d1a00; border: 1px solid #1c2e00; text-align: center; }
        #sync-status:empty { display: none; }
        .status-pill { margin-top: 10px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--lime); background: #0d1a00; border: 1px solid #1c2e00; opacity: 0; transform: translateY(4px); transition: opacity 0.25s, transform 0.25s; }
        .status-pill.show { opacity: 1; transform: translateY(0); }
        
        .info-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 8px; }
        .ic-label { font-size: 10px; color: #2e2e2e; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 6px; }
        .ic-val { font-size: 13px; font-weight: 500; color: #ccc; word-break: break-all; line-height: 1.4; }
        .co2-num { font-size: 1.6rem; font-weight: 600; color: var(--lime); line-height: 1; letter-spacing: -1px; }
        .co2-sub { font-size: 10px; color: #333; margin-top: 5px; font-weight: 500; letter-spacing: 0.3px; }
        
        .sb-footer { margin-top: auto; padding-top: 16px; }
        .btn-logout { width: 100%; height: 38px; background: transparent; border: 1px solid #1c1c1c; border-radius: var(--radius-sm); font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: #333; cursor: pointer; transition: border-color 0.18s, color 0.18s; outline: none; }
        .btn-logout:hover { border-color: #3a3a3a; color: #777; }
        
        /* The main section now forcefully takes up all remaining width */
        .main { flex: 1; display: flex; flex-direction: column; min-width: 0; width: 100%; background: var(--bg-root); max-width: none !important; padding: 0 !important; margin: 0 !important; }
        
        .topbar { height: 54px; min-height: 54px; display: flex; align-items: center; justify-content: space-between; padding: 0 28px; border-bottom: 1px solid #111; flex-shrink: 0; }
        .topbar-title { font-size: 12px; font-weight: 500; color: #2e2e2e; letter-spacing: 0.3px; }
        .topbar-status { display: flex; align-items: center; gap: 7px; font-size: 11px; color: #2e2e2e; font-weight: 500; }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--lime); box-shadow: 0 0 0 0 rgba(200,255,0,0.4); animation: pulse-dot 2.5s infinite; }
        @keyframes pulse-dot { 0% { box-shadow: 0 0 0 0 rgba(200,255,0,0.35); } 60% { box-shadow: 0 0 0 5px rgba(200,255,0,0); } 100% { box-shadow: 0 0 0 0 rgba(200,255,0,0); } }
        
        .messages { flex: 1; overflow-y: auto; padding: 28px 32px 20px; display: flex; flex-direction: column; gap: 20px; scroll-behavior: smooth; }
        .messages::-webkit-scrollbar { width: 3px; } .messages::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 2px; }
        .msg-ai { display: flex; align-items: flex-start; gap: 12px; animation: msgIn 0.22s ease both; }
        .msg-user { display: flex; justify-content: flex-end; animation: msgIn 0.22s ease both; }
        @keyframes msgIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        
        .ai-avatar { width: 30px; height: 30px; min-width: 30px; border-radius: 9px; background: #0f0f0f; border: 1px solid var(--border-mid); display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
        .ai-avatar svg { width: 14px; height: 14px; fill: var(--lime); }
        .bubble-ai { background: var(--bg-msg-ai); border: 1px solid var(--border-subtle); border-radius: 2px var(--radius-lg) var(--radius-lg) var(--radius-lg); padding: 14px 18px; max-width: 78%; font-size: 13.5px; line-height: 1.75; color: var(--text-secondary); }
        .bubble-user { background: var(--bg-msg-user); border: 1px solid #202020; border-radius: var(--radius-lg) 2px var(--radius-lg) var(--radius-lg); padding: 14px 18px; max-width: 70%; font-size: 13.5px; line-height: 1.75; color: var(--text-primary); font-weight: 500; }
        
        .typing-wrap { display: flex; align-items: flex-start; gap: 12px; animation: msgIn 0.22s ease both; }
        .typing-bubble { background: var(--bg-msg-ai); border: 1px solid var(--border-subtle); border-radius: 2px var(--radius-lg) var(--radius-lg) var(--radius-lg); padding: 14px 18px; display: flex; align-items: center; gap: 5px; height: 49px; }
        .td { width: 6px; height: 6px; border-radius: 50%; background: var(--lime); animation: tdpulse 1.2s infinite ease-in-out both; }
        .td:nth-child(2) { animation-delay: 0.2s; } .td:nth-child(3) { animation-delay: 0.4s; }
        @keyframes tdpulse { 0%, 80%, 100% { opacity: 0.15; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1); } }
        
        .input-area { padding: 14px 24px 20px; border-top: 1px solid #111; flex-shrink: 0; }
        
        /* ====== APPLIED FIXES HERE ====== */
        .input-shell { display: flex; align-items: center; background: var(--bg-input); border: 1px solid var(--border-mid); border-radius: var(--radius-lg); padding: 7px 7px 7px 18px; gap: 10px; transition: border-color 0.2s; }
        .input-shell:focus-within { border-color: var(--lime) !important; }
        
        .chat-input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 13.5px; font-weight: 400; line-height: 1.5; resize: none; min-height: 22px; max-height: 120px; overflow-y: auto; margin: 0 !important; padding: 0 !important; }
        .chat-input:focus, .chat-input:active { outline: none !important; box-shadow: none !important; border: none !important; background: transparent !important; }
        .chat-input::placeholder { color: var(--text-placeholder); }
        
        .send-btn { width: 36px; height: 36px; min-width: 36px; border-radius: 9px; background: var(--lime); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.18s, transform 0.15s; flex-shrink: 0; outline: none; margin: 0 !important; padding: 0 !important; }
        .send-btn:hover { background: var(--lime-hover); transform: scale(1.06); }
        .send-btn:active { background: var(--lime-active); transform: scale(0.97); }
        .send-icon { width: 15px; height: 15px; display: block; flex-shrink: 0; margin: 0 !important; }
        /* ================================ */
        
        .input-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding: 0 2px; }
        .meta-hint, .meta-count { font-size: 10px; color: #222; font-weight: 500; letter-spacing: 0.3px; }
        
        .modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.82); display: flex; align-items: center; justify-content: center; border-radius: 0; z-index: 100; animation: fadeIn 0.2s ease; }
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        .modal-box { background: #070707; border: 1px solid #ff4444; border-radius: var(--radius-xl); padding: 40px; width: 90%; max-width: 480px; }
        .modal-title { font-size: 1.3rem; font-weight: 600; color: #ff4444; margin-bottom: 12px; letter-spacing: -0.5px; }
        .modal-body { font-size: 13px; color: #666; line-height: 1.7; margin-bottom: 24px; }
        .modal-input { width: 100%; height: 42px; background: #0f0f0f; border: 1px solid #1e1e1e; border-radius: var(--radius-sm); padding: 0 14px; font-family: 'Inter', sans-serif; font-size: 13px; color: #ddd; outline: none; margin-bottom: 10px; transition: border-color 0.2s; }
        .modal-input:focus { border-color: #333; }
        .btn-danger { width: 100%; height: 42px; background: #ff4444; color: #000; border: none; border-radius: var(--radius-sm); font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; cursor: pointer; margin-bottom: 8px; transition: background 0.18s; }
        .btn-danger:hover { background: #ff6060; }
        .btn-dismiss { width: 100%; height: 38px; background: transparent; border: 1px solid #1e1e1e; border-radius: var(--radius-sm); font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: #444; cursor: pointer; transition: border-color 0.18s, color 0.18s; }
        .btn-dismiss:hover { border-color: #333; color: #777; }
        
        .htmx-indicator { display: none; }
        .htmx-request.typing-wrap { display: flex !important; }
        .htmx-request.status-pill { display: flex !important; opacity: 1 !important; transform: translateY(0) !important; }
    """)

    return Div(ws_style, Div(Div(sidebar, main_content, cls="ws-wrapper"), cls="workspace"), Div(id="modal-container"))