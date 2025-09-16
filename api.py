from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple, Literal
import json
import os
import uuid
import pickle
import enum
from datetime import datetime
from pathlib import Path

# Define enums for wall types and door ways
class WallType(str, enum.Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"

class DoorWay(str, enum.Enum):
    INWARD = "inward"
    OUTWARD = "outward"

# Import the bathroom layout generator functions
from models.bathroom import Bathroom
from models.object import BaseObject, BathroomObject
from models.layout import Layout

from algorithms.beam_search import BeamSearch

from optimization.scoring import BathroomScoringFunction
from utils.helpers import sort_objects_by_size
generated_layouts = {}

# Create a directory for saving layout states if it doesn't exist
LAYOUT_STATES_DIR = Path("data/layout_states")
LAYOUT_STATES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Bathroom Layout Generator API",
    description="API for generating optimized bathroom layouts for Flutter applications",
    version="1.0.0"
)

# Add CORS middleware to allow requests from Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Load object types data
try:
    with open("object_types.json", "r") as f:
        OBJECT_TYPES = json.load(f)
except FileNotFoundError:
    # Fallback to load from the app if not found directly
    import utils.helpers
    OBJECT_TYPES = utils.helpers.OBJECT_TYPES

class WindowsDoors(BaseModel):
    name: str # name of the object
    wall: str # type of the object, top, left, right, bottom
    position: Tuple[float, float] # position of the object, x, y(on the wall floor)
    width: float # width of the object
    depth: float # depth of the object
    height: float # height of the object
    hinge: str # hinge of the object, left or right
    way: str # way of the object, inwards or outwards

class GenerateLayoutRequest(BaseModel):
    id: str = Field(description="Unique ID for the layout")
    room_width: float = Field(description="Width of the bathroom in cm")
    room_depth: float = Field(description="Depth of the bathroom in cm")
    room_height: float = Field(description="Height of the bathroom in cm")
    objects_to_place: List[str] = Field(description="List of object types to place in the bathroom")
    windows_doors: List[WindowsDoors] = Field(description="List of windows and doors in the bathroom")
    beam_width: int = Field(description="Beam width for the search algorithm (higher = more thorough but slower)")

class ObjectPosition(BaseModel):
    object_type: str
    position: Tuple[float, float]
    width: float
    depth: float
    height: float
    wall: str

    shadow: List[float] = [0, 0, 0, 0]


class GenerateLayoutResponse(BaseModel):
    layout_id: str  # Adding this field for Flutter compatibility
    score: float
    room_width: float
    room_depth: float
    room_height: float
    objects: List[ObjectPosition]
    score_breakdown: Dict[str, float] = {}
    processing_time: float
    windows_doors: List[WindowsDoors]

# Store generated layouts in memory (in production, consider using a database)
generated_layouts = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Bathroom Layout Generator API is running"}

def save_layout_state(layout_id: str, state_type: str, data: dict):
    """
    Save layout state to disk. If a file for this layout_id and state_type already exists,
    it will update that file instead of creating a new one.
    
    Args:
        layout_id: Unique identifier for the layout
        state_type: Type of state ("before" or "after")
        data: Layout data to save
    """
    try:
        # Check if we already have a file for this layout_id and state_type
        existing_files = list(LAYOUT_STATES_DIR.glob(f"{layout_id}_{state_type}_*.json"))
        
        if existing_files:
            # Use the existing filename without timestamp (rewrite the file)
            base_filename = existing_files[0].stem
            # If multiple files exist, use the most recent one
            if len(existing_files) > 1:
                existing_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                base_filename = existing_files[0].stem
        else:
            # Create a new filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{layout_id}_{state_type}_{timestamp}"
        
        # Save as JSON (human-readable)
        json_path = LAYOUT_STATES_DIR / f"{base_filename}.json"
        with open(json_path, "w") as f:
            # Convert non-serializable objects to their string representation
            serializable_data = {}
            for key, value in data.items():
                try:
                    # Test if the value is JSON serializable
                    json.dumps({key: value})
                    serializable_data[key] = value
                except (TypeError, OverflowError):
                    # If not serializable, convert to string representation
                    serializable_data[key] = str(value)
            
            json.dump(serializable_data, f, indent=2)
        
        # Save as pickle (preserves Python objects)
        pickle_path = LAYOUT_STATES_DIR / f"{base_filename}.pkl"
        with open(pickle_path, "wb") as f:
            pickle.dump(data, f)
        
        # Add timestamp to the data for reference
        data["last_updated"] = datetime.now().isoformat()
            
        return {"json_path": str(json_path), "pickle_path": str(pickle_path), "updated": bool(existing_files)}
    
    except Exception as e:
        print(f"Error saving layout state: {str(e)}")
        return {"error": str(e)}

@app.post("/api/generate", response_model=GenerateLayoutResponse)
async def generate_layout(request: GenerateLayoutRequest, background_tasks: BackgroundTasks):
    """Generate a bathroom layout based on user input."""
    try:
        import time
        start_time = time.time()
        # Convert object names to lowercase
        print("objects_to_place type", type(request.objects_to_place))
        objects_to_place = [obj.lower() for obj in request.objects_to_place]
        # Create a bathroom instance
        bathroom = Bathroom(
            width=request.room_width,
            depth=request.room_depth,
            height=request.room_height,
            object_types=OBJECT_TYPES
        )
        print("ok")
        # Add windows and doors
        windows_doors_objects = []
        for wd in request.windows_doors:
            # Create a WindowsDoors instance
            print(wd)  # Debug print statement
            wd_obj = WindowsDoors(
                name=wd.name,
                wall=wd.wall,
                position=tuple(map(float, wd.position)),  # Ensure position is a tuple of floats
                width=float(wd.width),
                depth=float(wd.depth),
                height=float(wd.height),
                hinge=wd.hinge or WallType.LEFT,  # Default to left if not specified
                way=wd.way or DoorWay.INWARD  # Use provided way or default to Inward
            )
            windows_doors_objects.append(wd_obj)
            bathroom.add_window_door(wd_obj)
        
        # Save the initial state (before generation)
        initial_state = {
            "timestamp": datetime.now().isoformat(),
            "request": request.dict(),
            "bathroom": bathroom,
            "windows_doors": windows_doors_objects
        }
        save_layout_state(request.id, "before", initial_state)
        
        # Set up beam search
        beam_search = BeamSearch(bathroom, objects_to_place, beam_width=request.beam_width)
        # Run beam search to generate layouts
        layouts = beam_search.generate(objects_to_place, windows_doors_objects)
        print("ok")
        # If no layouts were generated, raise an error
        if not layouts or len(layouts) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Could not generate any valid layouts with the given constraints"
            )
        # Select the best layout (highest score)
        best_layout = layouts[0]  # Layouts are already sorted by score
        
        # Format the response
        objects_name = []
        for obj in best_layout.bathroom.objects:
            name = obj['object'].name
            objects_name.append(name)
        objects = []
        i=0
        for obj in best_layout.bathroom.objects:
            object_position = obj['position']
            wall = obj['object'].wall

            objects.append(ObjectPosition(
                object_type=objects_name[i],
                position=(float(object_position[0]), float(object_position[1])),
                width=float(object_position[2]),
                depth=float(object_position[3]),
                height=float(object_position[4]),
                shadow=(object_position[5] if object_position[5] else [0, 0, 0, 0]),
                wall=wall
            ))
            i+=1
        # Use the request ID if provided, otherwise generate a unique ID
        layout_id = request.id 
        print("ok")
        # Calculate processing time
        processing_time = time.time() - start_time
        # print out types
        print("type of layout_id", type(layout_id))
        print("type of score", type(best_layout.score))
        print("type of room_width", type(request.room_width))
        print("type of room_depth", type(request.room_depth))
        print("type of room_height", type(request.room_height))
        print("type of objects", type(objects))
        print("type of score_breakdown", type(best_layout.score_breakdown))
        print("score ", best_layout.score_breakdown)
        print("type of processing_time", type(processing_time))
        # Create response object
        response = GenerateLayoutResponse(
            layout_id=layout_id,  # Add layout_id for Flutter compatibility
            score=best_layout.score if best_layout.score else 0,
            room_width=request.room_width,
            room_depth=request.room_depth,
            room_height=request.room_height,
            objects=objects,
            score_breakdown=best_layout.score_breakdown if hasattr(best_layout, 'score_breakdown') else {},
            processing_time=processing_time,
            windows_doors = request.windows_doors
        )
        
        # Store the layout in memory using the same ID
        generated_layouts[layout_id] = {
            "layout": best_layout,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        # Clean up old layouts in the background
        #background_tasks.add_task(cleanup_old_layouts)
        
        # Save the final state (after generation)
        final_state = {
            "timestamp": datetime.now().isoformat(),
            "request": request.dict(),
            "bathroom": best_layout.bathroom,
            "layout": best_layout,
            "response": response.dict(),
            "score": best_layout.score,
            "score_breakdown": best_layout.score_breakdown
        }
        save_layout_state(layout_id, "after", final_state)
        
        return response
    
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error generating layout: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating layout: {str(e)}"
        )

@app.get("/api/layout/{layout_id}", response_model=GenerateLayoutResponse)
async def get_layout(layout_id: str):
    """Retrieve a previously generated layout by ID"""
    if layout_id not in generated_layouts:
        raise HTTPException(
            status_code=404,
            detail=f"Layout with ID {layout_id} not found"
        )
    
    return generated_layouts[layout_id]["response"]

@app.get("/layouts/{layout_id}")
async def get_layout_for_frontend(layout_id: str):
    """Retrieve a previously generated layout by ID for Flutter frontend
    
    This endpoint matches the expected URL pattern in the Flutter application.
    """
    if layout_id not in generated_layouts:
        raise HTTPException(
            status_code=404,
            detail=f"Layout with ID {layout_id} not found"
        )
    layout_entry = generated_layouts[layout_id]
    print("layout_entry", layout_entry)
    # Return the response as is (will be automatically converted to JSON)
    return {
        "layout": layout_entry["layout"],       # may need .to_dict() if it's not JSON serializable
        "response": layout_entry["response"],
        "timestamp": layout_entry["timestamp"],
    }
    

def cleanup_old_layouts():
    """Remove layouts older than 24 hours to prevent memory leaks"""
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(hours=24)
    
    # Convert to list to avoid "dictionary changed size during iteration" error
    for layout_id in list(generated_layouts.keys()):
        timestamp = datetime.fromisoformat(generated_layouts[layout_id]["timestamp"])
        if timestamp < cutoff:
            del generated_layouts[layout_id]

@app.get("/api/layout/{layout_id}/states")
async def get_layout_states(layout_id: str):
    """Retrieve saved states (before/after) for a specific layout"""
    # Check if layout exists
    if layout_id not in generated_layouts:
        raise HTTPException(
            status_code=404,
            detail=f"Layout with ID {layout_id} not found"
        )
    
    # Find all saved states for this layout ID
    before_files = list(LAYOUT_STATES_DIR.glob(f"{layout_id}_before_*.json"))
    after_files = list(LAYOUT_STATES_DIR.glob(f"{layout_id}_after_*.json"))
    
    # Get the most recent files if multiple exist
    before_file = max(before_files, key=lambda x: x.stat().st_mtime) if before_files else None
    after_file = max(after_files, key=lambda x: x.stat().st_mtime) if after_files else None
    
    result = {
        "layout_id": layout_id,
        "states": {}
    }
    
    # Load the content of the before state if it exists
    if before_file:
        try:
            with open(before_file, "r") as f:
                result["states"]["before"] = {
                    "file_path": str(before_file),
                    "timestamp": datetime.fromtimestamp(before_file.stat().st_mtime).isoformat(),
                    "metadata": json.load(f)  # Only include metadata, not full content
                }
        except Exception as e:
            result["states"]["before"] = {"error": str(e)}
    
    # Load the content of the after state if it exists
    if after_file:
        try:
            with open(after_file, "r") as f:
                result["states"]["after"] = {
                    "file_path": str(after_file),
                    "timestamp": datetime.fromtimestamp(after_file.stat().st_mtime).isoformat(),
                    "metadata": json.load(f)  # Only include metadata, not full content
                }
        except Exception as e:
            result["states"]["after"] = {"error": str(e)}
    
    return result

@app.get("/api/layout/{layout_id}/state/{state_type}")
async def get_layout_state_detail(layout_id: str, state_type: str):
    """Retrieve detailed content of a specific layout state (before or after)"""
    if state_type not in ["before", "after"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state type: {state_type}. Must be 'before' or 'after'."
        )
    
    # Find the file for this layout ID and state type
    state_files = list(LAYOUT_STATES_DIR.glob(f"{layout_id}_{state_type}_*.json"))
    if not state_files:
        raise HTTPException(
            status_code=404,
            detail=f"No {state_type} state found for layout ID {layout_id}"
        )
    
    # Get the most recent file if multiple exist
    state_file = max(state_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(state_file, "r") as f:
            state_data = json.load(f)
            return {
                "layout_id": layout_id,
                "state_type": state_type,
                "file_path": str(state_file),
                "timestamp": datetime.fromtimestamp(state_file.stat().st_mtime).isoformat(),
                "data": state_data
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading {state_type} state data: {str(e)}"
        )

# If running this file directly, start the API server
if __name__ == "__main__":
    import uvicorn
    #uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
