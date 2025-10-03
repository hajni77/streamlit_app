"""
OAuth Authentication Example for Bathroom Layout API

This demonstrates how to use OAuth providers (Google, GitHub) with the API.
"""

import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

BASE_URL = "http://127.0.0.1:8000"

# Global variable to store the OAuth callback data
oauth_callback_data = {}

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from the provider"""
    
    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        global oauth_callback_data
        
        # Parse the callback URL
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Extract the code or token
        if 'code' in params:
            oauth_callback_data['code'] = params['code'][0]
        if 'access_token' in params:
            oauth_callback_data['access_token'] = params['access_token'][0]
        if 'error' in params:
            oauth_callback_data['error'] = params['error'][0]
        
        # Send response to browser
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if 'error' in oauth_callback_data:
            html = f"""
            <html>
            <body>
                <h1>❌ Authentication Failed</h1>
                <p>Error: {oauth_callback_data['error']}</p>
                <p>You can close this window.</p>
            </body>
            </html>
            """
        else:
            html = """
            <html>
            <body>
                <h1>✅ Authentication Successful!</h1>
                <p>You can close this window and return to the application.</p>
                <script>window.close();</script>
            </body>
            </html>
            """
        
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

def start_callback_server(port=8080):
    """Start a local server to handle OAuth callback"""
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server

def oauth_login_google():
    """
    Login using Google OAuth.
    
    Note: This requires Supabase to be configured with Google OAuth provider.
    """
    print("\n🔐 Starting Google OAuth login...")
    print("⚠️  Note: Supabase must be configured with Google OAuth provider")
    
    # Start local callback server
    callback_port = 8080
    callback_url = f"http://localhost:{callback_port}/callback"
    
    print(f"Starting callback server on port {callback_port}...")
    server = start_callback_server(callback_port)
    
    # In a real implementation, you would:
    # 1. Get the OAuth URL from your Supabase project
    # 2. Open it in the browser
    # 3. Wait for the callback
    
    print("\n⚠️  Manual OAuth Setup Required:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to Authentication > Providers")
    print("3. Enable Google provider")
    print("4. Configure redirect URL:", callback_url)
    print("5. Get your OAuth URL from Supabase")
    
    # For demonstration, show how it would work
    print("\nOnce configured, the OAuth URL would look like:")
    print(f"https://your-project.supabase.co/auth/v1/authorize?provider=google&redirect_to={callback_url}")
    
    server.shutdown()
    return None

def verify_firebase_token(id_token):
    """
    Verify a Firebase ID token and get API access token.
    
    This is used when you authenticate with Firebase on the client side
    and need to exchange the Firebase token for an API token.
    
    Args:
        id_token (str): Firebase ID token from client authentication
        
    Returns:
        str: API access token if successful
    """
    print(f"\n🔑 Verifying Firebase token...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/firebase/verify-token",
            json={"idToken": id_token},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Token verified successfully!")
            print(f"   User ID: {token_data.get('user_id')}")
            print(f"   Email: {token_data.get('email')}")
            print(f"   Access Token: {token_data.get('access_token')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"❌ Token verification failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def supabase_oauth_flow():
    """
    Demonstrate Supabase OAuth flow.
    
    This shows the complete OAuth flow with Supabase.
    """
    print("\n" + "=" * 60)
    print("SUPABASE OAUTH AUTHENTICATION FLOW")
    print("=" * 60)
    
    print("\n📋 Setup Steps:")
    print("\n1. Configure Supabase OAuth Provider:")
    print("   - Go to: https://app.supabase.com/project/YOUR_PROJECT/auth/providers")
    print("   - Enable Google/GitHub/etc.")
    print("   - Add redirect URL: http://localhost:8080/callback")
    
    print("\n2. Update your .env file:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_KEY=your_anon_key")
    
    print("\n3. OAuth Flow:")
    print("   a) User clicks 'Login with Google'")
    print("   b) Redirected to Google login")
    print("   c) Google redirects back with code/token")
    print("   d) Exchange code for Supabase session")
    print("   e) Use Supabase token with API")
    
    print("\n4. In your Flutter/Web app:")
    print("   - Use Supabase client library")
    print("   - Call: supabase.auth.signInWithOAuth({provider: 'google'})")
    print("   - Get session token")
    print("   - Use token with API protected endpoints")

def firebase_oauth_flow():
    """
    Demonstrate Firebase OAuth flow.
    """
    print("\n" + "=" * 60)
    print("FIREBASE OAUTH AUTHENTICATION FLOW")
    print("=" * 60)
    
    print("\n📋 Setup Steps:")
    print("\n1. Configure Firebase Authentication:")
    print("   - Go to: https://console.firebase.google.com")
    print("   - Select your project")
    print("   - Go to Authentication > Sign-in method")
    print("   - Enable Google/GitHub/etc.")
    
    print("\n2. In your Flutter/Web app:")
    print("   - Use firebase_auth package")
    print("   - Example for Google:")
    print("     ```dart")
    print("     final GoogleSignIn googleSignIn = GoogleSignIn();")
    print("     final GoogleSignInAccount? googleUser = await googleSignIn.signIn();")
    print("     final GoogleSignInAuthentication googleAuth = await googleUser!.authentication;")
    print("     final credential = GoogleAuthProvider.credential(")
    print("       accessToken: googleAuth.accessToken,")
    print("       idToken: googleAuth.idToken,")
    print("     );")
    print("     final userCredential = await FirebaseAuth.instance.signInWithCredential(credential);")
    print("     final idToken = await userCredential.user!.getIdToken();")
    print("     ```")
    
    print("\n3. Exchange Firebase token for API token:")
    print("   - Call: POST /auth/firebase/verify-token")
    print("   - Body: {\"idToken\": \"firebase_id_token\"}")
    print("   - Get API access token in response")
    
    print("\n4. Use API token for protected endpoints")

def workaround_email_confirmation():
    """
    Workaround for Supabase email confirmation issue.
    """
    print("\n" + "=" * 60)
    print("WORKAROUND: EMAIL CONFIRMATION ISSUE")
    print("=" * 60)
    
    print("\n⚠️  Current Issue:")
    print("   - User registered successfully")
    print("   - But login fails with 'Invalid login credentials'")
    print("   - This is because Supabase requires email confirmation")
    
    print("\n✅ Solutions:")
    
    print("\n1. Disable Email Confirmation (Development Only):")
    print("   - Go to Supabase Dashboard")
    print("   - Authentication > Settings")
    print("   - Disable 'Enable email confirmations'")
    print("   - ⚠️  NOT recommended for production!")
    
    print("\n2. Confirm Email Manually:")
    print("   - Check your email inbox")
    print("   - Click the confirmation link")
    print("   - Then try logging in again")
    
    print("\n3. Use OAuth Instead (Recommended):")
    print("   - OAuth providers (Google, GitHub) don't need email confirmation")
    print("   - Better user experience")
    print("   - More secure")
    
    print("\n4. Use Supabase Dashboard:")
    print("   - Go to Authentication > Users")
    print("   - Find your user")
    print("   - Click 'Confirm email' manually")

def main():
    """Main function to demonstrate OAuth options"""
    print("=" * 60)
    print("OAUTH AUTHENTICATION OPTIONS")
    print("=" * 60)
    
    print("\nChoose an option:")
    print("1. View Supabase OAuth setup guide")
    print("2. View Firebase OAuth setup guide")
    print("3. View email confirmation workaround")
    print("4. Test Firebase token verification (requires token)")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        supabase_oauth_flow()
    elif choice == "2":
        firebase_oauth_flow()
    elif choice == "3":
        workaround_email_confirmation()
    elif choice == "4":
        token = input("Enter Firebase ID token: ").strip()
        if token:
            verify_firebase_token(token)
        else:
            print("❌ No token provided")
    elif choice == "5":
        print("\n👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
    
    print("\n" + "=" * 60)
    print("For more information, see the documentation:")
    print("- HOW_TO_REGISTER.md")
    print("- REGISTRATION_SUMMARY.md")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
