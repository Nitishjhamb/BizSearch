import os
import datetime
import markdown
import time
from fasthtml.common import * # type: ignore
from dotenv import load_dotenv


# Firebase SDK imports
import firebase_admin
from firebase_admin import credentials, db

from biz_logic import BizSearchEngine
search_engine = BizSearchEngine()

from login import LoginScreen
from ui_workspace import WorkspaceLayout, LimitModal 

load_dotenv()

# ==========================================
# FIREBASE CLOUD SETUP
# ==========================================
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_DB_URL", 'https://bizsearch-45e0c-default-rtdb.asia-southeast1.firebasedatabase.app/') 
    })

app, rt = fast_app(secret_key=os.getenv("SESSION_SECRET_KEY", "fallback_dev_key_123"))

# ==========================================
# USAGE TRACKING & RATE LIMITS
# ==========================================
MASTER_USER_ID = os.getenv("MASTER_USER_ID")
DAILY_LIMIT = 5

def get_safe_user_id(user_id: str) -> str:
    return str(user_id).replace('.', '_').replace('#', '_').replace('$', '_').replace('[', '_').replace(']', '_')

def can_make_request(user_id: str) -> bool:
    today = datetime.date.today().isoformat()
    safe_user_id = get_safe_user_id(user_id)
    
    user_ref = db.reference(f'users/{safe_user_id}')
    user_stats = user_ref.get() # type: ignore
    
    if not user_stats:
        user_stats = {"date": today, "count": 0, "lifetime": 0}
        
    if user_stats.get("date") != today: # type: ignore
        user_stats["date"] = today # type: ignore
        user_stats["count"] = 0 # type: ignore
        
    if user_id != MASTER_USER_ID and user_stats.get("count", 0) >= DAILY_LIMIT: # type: ignore
        return False
        
    user_stats["count"] = user_stats.get("count", 0) + 1 # type: ignore
    user_stats["lifetime"] = user_stats.get("lifetime", 0) + 1 # type: ignore
    
    user_ref.set(user_stats)
    return True

# ==========================================
# ROUTES
# ==========================================
@rt("/")
@rt("/login")
def login_get():
    return LoginScreen()

@rt("/login", methods=["POST"])
def login_post(email: str): 
    print(f"\n✨ REQUESTED MAGIC LINK FOR: {email}\n")
    success_message = f"✨ Magic link sent to {email}! Check your inbox to log in."
    return LoginScreen(error_msg=success_message)

@rt("/workspace")
def workspace(session):
    # Added ignores to silence VS Code
    if 'user_id' not in session: # type: ignore
        return RedirectResponse("/login", status_code=303)
    user_id = session.get('user_id') # type: ignore
    
    safe_user_id = get_safe_user_id(str(user_id))
    user_stats = db.reference(f'users/{safe_user_id}').get() or {"lifetime": 0} # type: ignore
    
    co2_saved = user_stats.get("lifetime", 0) * 0.42 # type: ignore
    
    return Title("BizSearch | Dashboard"), WorkspaceLayout(user_id, co2_saved)

@rt("/clear-index")
def post_clear():
    search_engine.clear_data() 
    return (
        P("🗑️ All data cleared.", style="color: #f87171;", id="sync-status"),
        Div(id="chat-history", cls="messages", hx_swap_oob="true")
    )

@rt("/upload-sync")
async def post_upload(file_upload: UploadFile, session): 
    # 1. Start the stopwatch
    start_time = time.time()
    
    os.makedirs("uploads", exist_ok=True)
    local_path = f"uploads/{file_upload.filename}"
    
    with open(local_path, "wb") as f:
        f.write(await file_upload.read())
    
    try:
        result_msg = search_engine.ingest_and_sync(local_path)
        os.remove(local_path)
        
        # 2. Stop the stopwatch and calculate the difference
        elapsed_time = time.time() - start_time
        
        # 3. Format the final success message
        final_msg = f"{result_msg} ⏱️ (Took {elapsed_time:.1f}s)"
        
        return (
            P(final_msg, style="color: #CCFF00; font-weight: bold;", id="sync-status"),
            Div(id="chat-history", cls="messages", hx_swap_oob="true")
        )
    except Exception as e:
        if os.path.exists(local_path):
            os.remove(local_path)
        return P(f"Sync Error: {str(e)}", style="color: #ff4444;", id="sync-status")

@rt("/search")
def post_search(search_query: str, session):
    if not search_query.strip(): return ""
    
    # Silence VS Code
    user_id = session.get('user_id', 'anonymous') # type: ignore
    
    if not can_make_request(str(user_id)):
        return Div(LimitModal(), id="modal-container", hx_swap_oob="true")
        
    # 1. Get the raw markdown answer from the AI
    raw_answer = search_engine.ask(search_query)
    
    # 2. Translate the Markdown into beautiful HTML
    html_answer = markdown.markdown(raw_answer)
    
    safe_user_id = get_safe_user_id(str(user_id))
    user_stats = db.reference(f'users/{safe_user_id}').get() or {"lifetime": 0} # type: ignore
    new_co2 = user_stats.get("lifetime", 0) * 0.42 # type: ignore
    
    return (
        # 3. Wrap it in NotStr() so FastHTML knows it's safe to render as actual HTML
        Div(NotStr(html_answer), cls="ai-msg"),
        Script("document.getElementById('chat-history').scrollTop = document.getElementById('chat-history').scrollHeight;"),
        Span(f"{new_co2:.2f}", id="carbon-amount", hx_swap_oob="true")
    )

@rt("/request-access")
def request_access(message: str, session):
    user_id = session.get('user_id', 'anonymous') # type: ignore
    print(f"\n🚨 ACCESS REQUEST FROM {user_id}: {message}\n")
    return Div(
        H3("REQUEST SENT.", style="color: #CCFF00; margin-bottom: 10px;"),
        P("The system administrator has been notified. We will review your request shortly.", style="color: #888888; line-height: 1.6;"),
        Button("CLOSE", onclick="document.getElementById('modal-container').innerHTML=''", cls="c40-btn c40-btn-outline", style="margin-top: 30px; width: 100%;")
    )

@rt("/logout", methods=["POST"])
def logout_post(session):
    session.clear() # type: ignore
    return RedirectResponse("/login", status_code=303)

@rt("/auth/callback", methods=["POST"])
def auth_callback(uid: str, session):
    print(f"\n🔐 NATIVE FORM SUCCESS! Received UID: {uid}\n")
    session['user_id'] = uid # type: ignore
    return RedirectResponse("/workspace", status_code=303)

if __name__ == "__main__":
    serve()