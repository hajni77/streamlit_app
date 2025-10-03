"""
Test script for authentication integration with the bathroom layout API.

This script tests the authentication endpoints and protected routes.
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_user_registration():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    user_data = {
        "email": f"test_user_{datetime.now().timestamp()}@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = requests.post(
        f"{BASE_URL}/users/",
        json=user_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return user_data["email"], user_data["password"]
    else:
        print(f"Error: {response.text}")
        return None, None

def test_user_login(email, password):
    """Test user login"""
    print("\n=== Testing User Login ===")
    login_data = {
        "username": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        print(f"Access Token: {token_data['access_token'][:50]}...")
        print(f"Token Type: {token_data['token_type']}")
        print(f"Provider: {token_data['provider']}")
        return token_data["access_token"]
    else:
        print(f"Error: {response.text}")
        return None

def test_get_current_user(token):
    """Test getting current user info"""
    print("\n=== Testing Get Current User ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/users/me/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_public_layout_generation():
    """Test public layout generation (no authentication required)"""
    print("\n=== Testing Public Layout Generation ===")
    layout_request = {
        "id": f"test_layout_{datetime.now().timestamp()}",
        "room_width": 300,
        "room_depth": 240,
        "room_height": 280,
        "objects_to_place": ["toilet", "sink", "shower"],
        "windows_doors": [
            {
                "name": "door",
                "wall": "left",
                "position": [0, 120],
                "width": 80,
                "depth": 5,
                "height": 210,
                "hinge": "left",
                "way": "inward"
            }
        ],
        "beam_width": 10
    }
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=layout_request
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Layout ID: {result['layout_id']}")
        print(f"Score: {result['score']}")
        print(f"Objects placed: {len(result['objects'])}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        return result["layout_id"]
    else:
        print(f"Error: {response.text}")
        return None

def test_protected_layout_generation(token):
    """Test protected layout generation (authentication required)"""
    print("\n=== Testing Protected Layout Generation ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    layout_request = {
        "id": f"protected_layout_{datetime.now().timestamp()}",
        "room_width": 350,
        "room_depth": 280,
        "room_height": 280,
        "objects_to_place": ["toilet", "sink", "bathtub"],
        "windows_doors": [],
        "beam_width": 10
    }
    
    response = requests.post(
        f"{BASE_URL}/api/protected/generate",
        json=layout_request,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Layout ID: {result['layout_id']}")
        print(f"Score: {result['score']}")
        print(f"Objects placed: {len(result['objects'])}")
        return result["layout_id"]
    else:
        print(f"Error: {response.text}")
        return None

def test_get_user_layouts(token):
    """Test getting all user layouts"""
    print("\n=== Testing Get User Layouts ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/protected/layouts/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        layouts = response.json()
        print(f"Number of layouts: {len(layouts)}")
        for layout in layouts:
            print(f"  - Layout ID: {layout['layout_id']}, Score: {layout['score']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_get_user_layout_by_id(token, layout_id):
    """Test getting a specific user layout"""
    print("\n=== Testing Get User Layout by ID ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/protected/layout/{layout_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Layout ID: {result['layout_id']}")
        print(f"Score: {result['score']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_delete_user_layout(token, layout_id):
    """Test deleting a user layout"""
    print("\n=== Testing Delete User Layout ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(
        f"{BASE_URL}/api/protected/layout/{layout_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_unauthorized_access():
    """Test that protected endpoints reject unauthorized requests"""
    print("\n=== Testing Unauthorized Access ===")
    
    # Try to access protected endpoint without token
    response = requests.get(f"{BASE_URL}/api/protected/layouts/")
    print(f"Status (no token): {response.status_code}")
    
    # Try with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(
        f"{BASE_URL}/api/protected/layouts/",
        headers=headers
    )
    print(f"Status (invalid token): {response.status_code}")
    
    return response.status_code == 401

def run_all_tests():
    """Run all authentication tests"""
    print("=" * 60)
    print("BATHROOM LAYOUT API - AUTHENTICATION INTEGRATION TESTS")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health check
    results["health_check"] = test_health_check()
    
    # Test 2: User registration (skip if using existing auth providers)
    # email, password = test_user_registration()
    
    # For testing with existing Supabase/Firebase users, use credentials
    # Comment out the registration test and use these instead:
    email = "test@example.com"  # Replace with actual test user
    password = "testpassword"    # Replace with actual password
    
    # Test 3: User login
    token = test_user_login(email, password)
    results["login"] = token is not None
    
    if token:
        # Test 4: Get current user
        results["get_current_user"] = test_get_current_user(token)
        
        # Test 5: Public layout generation
        public_layout_id = test_public_layout_generation()
        results["public_generation"] = public_layout_id is not None
        
        # Test 6: Protected layout generation
        protected_layout_id = test_protected_layout_generation(token)
        results["protected_generation"] = protected_layout_id is not None
        
        # Test 7: Get user layouts
        results["get_user_layouts"] = test_get_user_layouts(token)
        
        # Test 8: Get specific user layout
        if protected_layout_id:
            results["get_layout_by_id"] = test_get_user_layout_by_id(token, protected_layout_id)
            
            # Test 9: Delete user layout
            results["delete_layout"] = test_delete_user_layout(token, protected_layout_id)
    
    # Test 10: Unauthorized access
    results["unauthorized_access"] = test_unauthorized_access()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()
