"""
Simple script to register a user with the Bathroom Layout API.

Usage:
    python register_user_example.py
"""

import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"

def register_user(email, password, full_name):
    """
    Register a new user with the API.
    
    Args:
        email (str): User's email address
        password (str): User's password
        full_name (str): User's full name
        
    Returns:
        dict: User data if successful, None otherwise
    """
    print(f"\n🔐 Registering user: {email}")
    
    user_data = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ User registered successfully!")
            print(f"   User ID: {user_info.get('id')}")
            print(f"   Email: {user_info.get('email')}")
            print(f"   Name: {user_info.get('full_name')}")
            return user_info
        else:
            print(f"❌ Registration failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server.")
        print("   Make sure the API is running at http://localhost:8000")
        print("   Start it with: python api.py")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def login_user(email, password):
    """
    Login with registered credentials.
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        str: Access token if successful, None otherwise
    """
    print(f"\n🔑 Logging in as: {email}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/token",
            data={
                "username": email,
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful!")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Provider: {token_data.get('provider')}")
            print(f"   Access Token: {token_data.get('access_token')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"❌ Login failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def get_user_info(token):
    """
    Get current user information.
    
    Args:
        token (str): Access token
        
    Returns:
        dict: User information if successful
    """
    print(f"\n👤 Getting user information...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/users/me/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ User info retrieved!")
            print(f"   ID: {user_info.get('id')}")
            print(f"   Email: {user_info.get('email')}")
            return user_info
        else:
            print(f"❌ Failed to get user info!")
            print(f"   Status Code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Main function to demonstrate user registration and login."""
    print("=" * 60)
    print("BATHROOM LAYOUT API - USER REGISTRATION")
    print("=" * 60)
    
    # Get user input
    print("\nEnter your registration details:")
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    full_name = input("Full Name: ").strip()
    
    # Validate input
    if not email or not password or not full_name:
        print("❌ All fields are required!")
        return
    
    # Register the user
    user = register_user(email, password, full_name)
    
    if user:
        print("\n" + "=" * 60)
        print("Registration successful! Now testing login...")
        print("=" * 60)
        
        # Try to login
        token = login_user(email, password)
        
        if token:
            # Get user info to verify
            get_user_info(token)
            
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\nYou can now use this account to:")
            print("  • Generate bathroom layouts")
            print("  • Save and retrieve your layouts")
            print("  • Manage your layout history")
            print("\nYour access token has been generated.")
            print("Use it in the Authorization header for protected endpoints.")
        else:
            print("\n❌ Login failed after registration.")
    else:
        print("\n❌ Registration failed.")
        print("\nPossible reasons:")
        print("  • Email already exists")
        print("  • API server is not running")
        print("  • Supabase/Firebase not configured")
        print("\nTo start the API server, run: python api.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Registration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
