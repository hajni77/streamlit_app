from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client
import streamlit as st
# Add to your app.py
def auth_section(supabase: Client):
    """Handles user authentication flows"""
    if 'auth' not in st.session_state:
        st.session_state.auth = {
            'user': None,
            'session': None
        }

    with st.sidebar:
        st.header("Authentication")
        
        # Login/Signup Tabs
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("Sign In"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.form_submit_button("Sign In"):
                    try:
                        session = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        st.session_state.auth.update({
                            'user': session.user,
                            'session': session,
                            'access_token': session.session.access_token if hasattr(session, 'session') and hasattr(session.session, 'access_token') else None
                        })
                        supabase.auth.session = session.session
                        # Store access_token in session_state for RLS
                        user = session.user
                        st.session_state['user'] = user
                        st.session_state['access_token'] = session.session.access_token if hasattr(session, 'session') and hasattr(session.session, 'access_token') else None
                        st.rerun()
                        # Insert row — make sure to include user_id

                        return session.session.access_token if hasattr(session, 'session') and hasattr(session.session, 'access_token') else None
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
        with tab2:
            with st.form("Sign Up"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                if st.form_submit_button("Create Account"):
                    try:
                        session = supabase.auth.sign_up({
                            "email": email,
                            "password": password,
                            "options": {
                                "email_confirm": True  # Enable email confirmation
                            }
                        })
                        st.success("Account created! Check your email for confirmation.")
                    except Exception as e:
                        st.error(f"Signup failed: {str(e)}")

        # Social Auth Providers
        st.write("Or continue with:")
        cols = st.columns(3)
        with cols[0]:
            if st.button("Google"):
                st.write("Redirecting to Google...")
                st.session_state.auth_url = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"redirect_to": "http://localhost:8501"}
                })
        with cols[1]:
            if st.button("GitHub"):
                st.write("Redirecting to GitHub...")
                st.session_state.auth_url = supabase.auth.sign_in_with_oauth({
                    "provider": "github",
                    "options": {"redirect_to": "http://localhost:8501"}
                })
        
        # Logout
        if st.session_state.auth['user']:
            if st.button("Sign Out"):
                supabase.auth.sign_out()
                st.session_state.auth = {'user': None, 'session': None}
                st.rerun()

# Add protected route example
def protected_route():
    if not st.session_state.auth.get('user'):
        st.warning("Please sign in to access this page")
        return
    
    st.write(f"Welcome {st.session_state.auth['user'].email}!")
    # Your protected content here

# Call auth_section() in your main app flow
