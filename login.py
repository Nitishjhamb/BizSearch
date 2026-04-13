# login.py
from fasthtml.common import * # type: ignore
from ui_auth import custom_style, AuthHeader, AuthFooter, FirebaseJS

def LoginScreen(error_msg=None):
    # Magic Link Section
    form_content = [
        H2("Welcome back"),
        P("Enter your email for a secure magic link.", cls="subtitle"),
        Input(type="email", name="email", placeholder="Your Email*", required=True),
        Button("Send Link", type="button", onclick="sendMagicLink()", style="margin-bottom: 20px;")
    ]
    
    if error_msg:
        form_content.insert(2, P(error_msg, style="color: #ef4444; font-size: 13px; text-align: center; margin-bottom: 10px;"))

    # Social Logins Section
    alternative_logins = Div(
        Div(
            Span("OR CONTINUE WITH", style="background: #09090b; padding: 0 10px; color: #71717a; font-size: 12px; font-weight: bold; letter-spacing: 1px;"),
            style="text-align: center; border-top: 1px solid #27272a; margin: 20px 0; line-height: 0.1em;"
        ),
        Div(
            Button("Google", type="button", onclick="loginWithGoogle()", style="background: #ffffff; color: #000; border: none; padding: 10px; border-radius: 6px; width: 48%; cursor: pointer; font-weight: bold; font-size: 14px;"),
            Button("GitHub", type="button", onclick="loginWithGithub()", style="background: #24292e; color: #fff; border: 1px solid #3f3f46; padding: 10px; border-radius: 6px; width: 48%; cursor: pointer; font-weight: bold; font-size: 14px;"),
            style="display: flex; justify-content: space-between; margin-bottom: 10px;"
        )
    )

    return Title("BizSearch | Login"), custom_style, Div(
        FirebaseJS(),
        AuthHeader(),
        Form(*form_content, hx_target="body"), 
        alternative_logins,
        P("New to BizSearch? Just use a social provider or email to get started.", 
          style="color: #71717a; font-size: 12px; margin-top: 25px; text-align: center;"),
        AuthFooter(),
        cls="auth-card",
        style="width: 400px;"
    )
   
