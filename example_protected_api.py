from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

# Import user authentication utilities
from user_api import setup_user_api_routes, User, get_current_active_user

# Initialize FastAPI app
app = FastAPI(
    title="Protected Bathroom Layout API",
    description="Secure API for generating bathroom layouts with user authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup user authentication routes
setup_user_api_routes(app)

# Example of a protected endpoint
@app.get("/protected/layouts/", response_model=Dict[str, Any])
async def get_user_layouts(current_user: User = Depends(get_current_active_user)):
    """
    Get layouts associated with the authenticated user
    This is a protected endpoint that requires authentication
    """
    # Here you would typically query a database for layouts owned by current_user.id
    # For this example, we'll return a mock response
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "layouts": [
            {"id": "layout1", "name": "Master Bathroom", "created_at": "2025-09-30T10:00:00Z"},
            {"id": "layout2", "name": "Guest Bathroom", "created_at": "2025-09-29T15:30:00Z"}
        ]
    }

# Example of how to protect a route with optional authentication
@app.get("/layouts/public/")
async def get_public_layouts(current_user: User = Depends(get_current_active_user)):
    """
    Get public layouts accessible to all authenticated users
    """
    return {
        "public_layouts": [
            {"id": "pub1", "name": "Modern Bathroom Template", "created_by": "admin"},
            {"id": "pub2", "name": "Minimalist Bathroom", "created_by": "admin"}
        ],
        "user_info": {
            "id": current_user.id,
            "email": current_user.email
        } if current_user else None
    }

# Example of integrating with the main api.py functionality
@app.post("/protected/generate_layout/")
async def generate_user_layout(
    room_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a bathroom layout and associate it with the current user
    """
    # Here you would call your layout generation function
    # from api.py and then associate the result with the user
    
    # Example:
    # layout = generate_layout(**room_data)
    # store_user_layout(user_id=current_user.id, layout=layout)
    
    layout_id = f"layout_{current_user.id}_{hash(str(room_data))}"
    
    return {
        "layout_id": layout_id,
        "user_id": current_user.id,
        "message": "Layout generated and saved successfully",
        "preview_url": f"/layouts/{layout_id}/preview"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
