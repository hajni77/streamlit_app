from visualization_file import draw_2d_floorplan    
import streamlit as st
import matplotlib.pyplot as plt
import io
import base64
from PIL import Image
import json

# Load object types from JSON file
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)

# Function to render 2D floorplan for saved reviews
def render_saved_floorplan(review):
        """
        Generate a 2D floorplan visualization for a saved review.
        
        Args:
            review (dict): The review data from the database
            
        Returns:
            tuple: (image, bytes_data) where image is a PIL Image and bytes_data is the raw image data
                  or None if an error occurs
        """

        try:
            # Extract room dimensions
            room_width = review.get('room_width', 200)
            room_depth = review.get('room_depth', 200)
            room_height = review.get('room_height', 280)
            
            # Extract objects and their positions
            objects = review.get('objects', [])
            objects_positions = review.get('objects_positions', [])
            # Combine objects with their positions
            placed_objects = []
            for i, obj in enumerate(objects):
                if i < len(objects_positions):
                    pos = objects_positions[i]
                    # Get object name and find corresponding object type for shadow values
                    obj_name = obj.get('name', 'Unknown')
                    # Convert object name to lowercase and replace spaces with underscores for dictionary lookup
                    obj_type_key = obj_name.lower().replace(' ', '_')
                    
                    # Get shadow value from object_types.json, default to [20,20,20,0] if not found
                    shadow_value = [60, 0, 0, 0]  # Fallback default value as a list with 4 values
                    
                    # Try to find the object type in OBJECT_TYPES
                    if obj_type_key in OBJECT_TYPES:
                        # Use the shadow_space from the object type
                        shadow_space = OBJECT_TYPES[obj_type_key].get('shadow_space', [60,0,0,0])
                        # Make sure shadow_space is a list with 4 values
                        if isinstance(shadow_space, (list, tuple)) and len(shadow_space) == 4:
                            shadow_value = shadow_space
                        elif isinstance(shadow_space, (list, tuple)) and len(shadow_space) > 0:
                            # If it's a list but not with 4 values, use the first value and pad
                            first_val = shadow_space[0]
                            shadow_value = [first_val, first_val, first_val, 0]
                        elif isinstance(shadow_space, (int, float)):
                            # If it's a single number, use it for the first three values
                            shadow_value = [shadow_space, shadow_space, shadow_space, 0]
                        # else use the default shadow_value already set
                    
                    # Ensure all values are properly formatted
                    placed_objects.append([
                        pos.get('x', 0),
                        pos.get('y', 0),
                        obj.get('width', 50),
                        obj.get('depth', 50),
                        obj.get('height', 100),
                        obj_name,
                        pos.get('must_be_corner', False),
                        pos.get('against_wall', False),
                        shadow_value  # Real shadow value from object_types.json
                    ])
            
            # Extract doors and windows
            doors_windows = review.get('doors_windows', [])
            formatted_doors = []
            for item in doors_windows:
                door_type = item.get('type', 'top')
                position = item.get('position', {})
                dimensions = item.get('dimensions', {})
                # Format: [id, wall, x, y, width, height, parapet, way, hinge]
                formatted_doors.append([
                    'door',
                    door_type,
                    position.get('x', 0),
                    position.get('y', 0),
                    dimensions.get('width', 75),
                    dimensions.get('height', 200),
                    0,  # parapet
                    'Inward',  # way
                    'Left'  # hinge
                ])
            
            # Close any existing figures to prevent memory leaks
            plt.close('all')
            
            # Validate objects before passing to draw_2d_floorplan
            # Filter out any invalid objects (non-list/tuple or wrong length)
            valid_placed_objects = []
            for obj in placed_objects:
                if isinstance(obj, (list, tuple)) and len(obj) == 9:
                    valid_placed_objects.append(obj)
                else:
                    st.warning(f"Skipping invalid object format: {obj}")
            # Generate 2D floorplan with validated objects
            fig = draw_2d_floorplan((room_width, room_depth), valid_placed_objects, formatted_doors, 'Inward')
            
            # Convert matplotlib figure to image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            
            # Convert to PIL Image
            img = Image.open(buf)
            
            # Convert to bytes for display
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Close the figure to free memory
            plt.close(fig)
            
            return img, img_bytes.getvalue()
        except Exception as e:
            st.error(f"Error rendering floorplan: {str(e)}")
            plt.close('all')  # Make sure to close figures even on error
            return None, None


# Function to Save Data to Supabase-not used
def save_data(supabase, room_sizes, positions, doors, review, is_enough_path, space, overall, is_everything, room_name=None, calculated_reward=None, reward=None):
    if not st.session_state.auth.get('user'):
        st.error("Please sign in to submit reviews")
        return False
    
    with st.spinner("Saving your review to the database..."):
        try:
            objects = []
            objects_positions = []
            for position in positions:
                if isinstance(position, (list, tuple)) and len(position) >= 8:
                    objects.append({
                        "name": position[5],
                        "width": position[2],
                        "depth": position[3],
                        "height": position[4]
                    })
                    objects_positions.append({
                        "x": position[0],
                        "y": position[1],
                        "must_be_corner": position[6],
                        "against_wall": position[7]
                    })

            # Convert input data to match table schema
            review_data = {
                "room_name": room_name or "My Bathroom Design",
                "room_width": int(room_sizes[0]),
                "room_depth": int(room_sizes[1]),
                "room_height": int(room_sizes[2]),
                "objects": objects,
                "objects_positions": objects_positions,
                "review": {
                    "text": review,
                },
                "doors_windows": [{
                    "type": door[1],
                    "position": {"x": door[2], "y": door[3]},
                    "dimensions": {"width": door[4], "height": door[5]}
                } for door in doors],
                "user_id": st.session_state.user.id,
                "room_name": room_name,
                "calculated_reward": calculated_reward,
                "real_reward": reward
            }

            # Add optional fields if available
            if is_enough_path is not None and space is not None and overall is not None:
                review_data.update({
                    "is_enough_path": is_enough_path,
                    "space": space,
                    "overall": overall,
                    "is_everything": is_everything,
                })
                
            # Insert into Supabase
            response = supabase.table('reviews').insert(review_data).execute()
            if response.data:
                return True
            else:
                st.error("Failed to save review")
                return False
        except Exception as e:
            st.error(f"Error saving review: {str(e)}")
            return False