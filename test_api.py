"""
Test script for the bathroom layout generator API endpoints
"""
import json
import requests
import time
from pprint import pprint

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print("\n=== Health Check Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generate_layout():
    """Test the layout generation endpoint"""
    # Sample request data
    request_data = {
        "room_width": 300,
        "room_depth": 240,
        "room_height": 280,
        "objects_to_place": [
            "toilet",
            "sink",
            "shower"
        ],
        "windows_doors": [
            {
                "name": "door",
                "position": [0, 120],
                "width": 80,
                "depth": 5,
                "height": 210,
                "wall": "left",
                "hinge": "bottom"
            },
            {
                "name": "window",
                "position": [100, 0],
                "width": 100,
                "depth": 5,
                "height": 120,
                "wall": "top"
            }
        ],
        "beam_width": 5  # Use smaller beam width for faster testing
    }
    
    print("\n=== Generate Layout Test ===")
    print("Sending request...")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=request_data
    )
    
    end_time = time.time()
    print(f"Request completed in {end_time - start_time:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        layout_id = result["layout_id"]
        
        print("\nGenerated Layout Summary:")
        print(f"Layout ID: {layout_id}")
        print(f"Score: {result['score']}")
        print(f"Processing Time: {result['processing_time']:.2f}s")
        print(f"Number of objects: {len(result['objects'])}")
        
        print("\nPlaced Objects:")
        for obj in result['objects']:
            print(f"- {obj['object_type']}: position={obj['position']}, size={obj['width']}x{obj['depth']}cm")
        
        if "score_breakdown" in result and result["score_breakdown"]:
            print("\nScore Breakdown:")
            for criterion, score in result["score_breakdown"].items():
                print(f"- {criterion}: {score}")
        
        # Now test retrieving the layout by ID
        print("\nTesting layout retrieval...")
        return layout_id
    else:
        print(f"Error: {response.text}")
        return None

def test_get_layout(layout_id):
    """Test the get layout endpoint"""
    if not layout_id:
        print("Skipping layout retrieval test (no layout ID)")
        return
    
    print("\n=== Get Layout Test ===")
    response = requests.get(f"{BASE_URL}/api/layout/{layout_id}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Successfully retrieved layout with ID: {layout_id}")
        print(f"Score: {result['score']}")
    else:
        print(f"Error: {response.text}")

def test_invalid_layout_id():
    """Test retrieving a non-existent layout ID"""
    print("\n=== Invalid Layout ID Test ===")
    response = requests.get(f"{BASE_URL}/api/layout/non-existent-id")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 404

def test_invalid_generation_request():
    """Test generating a layout with invalid data"""
    print("\n=== Invalid Generation Request Test ===")
    # Missing required fields
    invalid_data = {
        "room_width": 300,
        # Missing room_depth
        "objects_to_place": []  # Empty object list
    }
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=invalid_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code in [400, 422]  # 422 is FastAPI's validation error code

if __name__ == "__main__":
    print("Starting API Tests...")
    print("Make sure the API server is running at", BASE_URL)
    
    try:
        # Run tests
        test_health_check()
        layout_id = test_generate_layout()
        test_get_layout(layout_id)
        test_invalid_layout_id()
        test_invalid_generation_request()
        
        print("\n=== All tests completed ===")
    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to the API server at {BASE_URL}")
        print("Please make sure the server is running with:")
        print("    uvicorn api:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
