from fasthtml.common import * # type: ignore
import os

# Your Dark Mode CSS
custom_style = Style("""
    body { background-color: #09090b; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .auth-card { background-color: #121212; border: 1px solid #27272a; border-radius: 16px; padding: 50px 40px 30px 40px; width: 380px; max-width: 90%; position: relative; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
    .window-dots { position: absolute; top: 16px; left: 16px; display: flex; gap: 6px; }
    .dot { width: 10px; height: 10px; border-radius: 50%; background-color: #ffffff; opacity: 0.8;}
    .logo-box { width: 50px; height: 50px; background-color: #ffffff; border-radius: 12px; margin: 0 auto 15px; display: flex; justify-content: center; align-items: center; color: black; font-weight: 900; font-size: 24px; }
    h1 { text-align: center; margin: 0 0 5px 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;}
    h2 { text-align: center; margin: 0 0 10px 0; font-size: 22px; font-weight: 500;}
    .subtitle { text-align: center; color: #a1a1aa; font-size: 14px; margin-bottom: 30px; line-height: 1.4;}
    input { width: 100%; padding: 14px 16px; background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; color: white; box-sizing: border-box; font-size: 14px; transition: border-color 0.2s; margin-bottom: 12px; }
    input:focus { outline: none; border-color: #3b82f6; }
    button { width: 100%; padding: 14px; background-color: #2563eb; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 10px; }
    button:hover { background-color: #1d4ed8; }
    .switch-mode { text-align: center; display: block; margin-top: 20px; color: #a1a1aa; text-decoration: none; font-size: 13px; }
    .footer { text-align: center; color: #52525b; font-size: 11px; margin-top: 40px; line-height: 1.6; }
""")

def WindowDots(): return Div(Div(cls="dot"), Div(cls="dot"), Div(cls="dot"), cls="window-dots")

def AuthHeader():
    return Div(WindowDots(), Div("BZ", cls="logo-box"), H1("BizSearch", Span("™", style="font-size: 12px; vertical-align: top;")))

def AuthFooter():
    return Div(A("Privacy Policy", href="#"), " • ", A("Cookie Policy", href="#"), Br(), "© — All Right Reserved 2026", cls="footer")

def FirebaseJS():
    script_content = f"""
    import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
    import {{ getAuth, GoogleAuthProvider, GithubAuthProvider, signInWithPopup, sendSignInLinkToEmail, isSignInWithEmailLink, signInWithEmailLink }} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";

    const firebaseConfig = {{
        apiKey: "{os.getenv('FIREBASE_API_KEY')}",
        authDomain: "{os.getenv('FIREBASE_AUTH_DOMAIN')}",
        projectId: "{os.getenv('FIREBASE_PROJECT_ID')}",
        storageBucket: "{os.getenv('FIREBASE_STORAGE_BUCKET')}",
        messagingSenderId: "{os.getenv('FIREBASE_MESSAGING_SENDER_ID')}",
        appId: "{os.getenv('FIREBASE_APP_ID')}"
    }};

    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    // --- MAGIC LINK HANDLER ---
    if (isSignInWithEmailLink(auth, window.location.href)) {{
        let email = window.localStorage.getItem('emailForSignIn');
        if (!email) email = window.prompt('Please provide your email for confirmation');
        signInWithEmailLink(auth, email, window.location.href)
            .then((result) => {{
                window.localStorage.removeItem('emailForSignIn');
                sendToPython(result.user.uid);
            }}).catch((error) => alert(error.message));
    }}

    window.sendMagicLink = async function() {{
        const email = document.getElementsByName('email')[0].value;
        const actionCodeSettings = {{ url: window.location.origin + '/login', handleCodeInApp: true }};
        try {{
            await sendSignInLinkToEmail(auth, email, actionCodeSettings);
            window.localStorage.setItem('emailForSignIn', email);
            alert("Check your email!");
        }} catch (error) {{ alert(error.message); }}
    }};

    // --- SOCIAL LOGINS ---
    window.loginWithGoogle = async function() {{
        const provider = new GoogleAuthProvider();
        try {{
            const result = await signInWithPopup(auth, provider);
            sendToPython(result.user.uid);
        }} catch (error) {{ alert("Google Error: " + error.message); }}
    }};

    window.loginWithGithub = async function() {{
        const provider = new GithubAuthProvider();
        try {{
            const result = await signInWithPopup(auth, provider);
            sendToPython(result.user.uid);
        }} catch (error) {{ alert("GitHub Error: " + error.message); }}
    }};
    
    function sendToPython(uid) {{
        // 1. Create an invisible HTML form
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/auth/callback';
        
        // 2. Add an invisible text box containing the user's UID
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'uid';
        input.value = uid;
        
        // 3. Attach it to the page and hit submit!
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit(); // The browser takes over completely from here!
    }}
    """
    return Script(script_content, type="module")