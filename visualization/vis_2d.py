import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from utils.helpers import check_which_wall, convert_values
from models.layout import Layout
from models.bathroom import Bathroom
import streamlit as st
class Visualizer2D:
    def __init__(self, bathroom:Bathroom):
        self.room_width = bathroom.width
        self.room_depth = bathroom.depth
        self.room_height = bathroom.height
        self.objects = bathroom.objects
        self.windows_doors = bathroom.windows_doors
        
    # Function to render 2D floorplan for saved reviews
    def render_saved_floorplan(self,review):
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
                        shadow_value = 75  # Fallback default value
                        
                        # Try to find the object type in OBJECT_TYPES
                        if obj_type_key in OBJECT_TYPES:
                            # Use the shadow_space from the object type
                            shadow_space = OBJECT_TYPES[obj_type_key].get('shadow_space', [20,20,20,0])
                            # For compatibility with the existing code, we'll use the first value
                            # or sum them if needed for a single shadow value
                            shadow_value = shadow_space
                        
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
        
    def draw_2d_floorplan(self):
        """
        Draw a 2D floorplan of the bathroom layout.
        
        Returns:
            matplotlib.figure.Figure: A 2D figure that can be displayed and saved
        """
        # Ensure room dimensions are scalar values, not lists or tuples
        room_depth = self.room_depth[0] if isinstance(self.room_depth, (list, tuple)) else self.room_depth
        room_width = self.room_width[0] if isinstance(self.room_width, (list, tuple)) else self.room_width
        
        # Convert to integers if they're not already
        try:
            room_depth = int(room_depth)
            room_width = int(room_width)
        except (TypeError, ValueError):
            # Default values if conversion fails
            room_depth = 300
            room_width = 300

        # figsize based on room size but smaller
        fig, ax = plt.subplots(figsize=((room_depth/100)*6, (room_width/100)*6))
        
        # Draw the room boundary
        ax.set_ylim(0, room_width)
        ax.set_xlim(0, room_depth)
        ax.set_xticks(range(0, room_depth + 1, 10))
        ax.set_yticks(range(0, room_width + 1, 10))
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_title("Floor Plan")
        ax.invert_yaxis()
        # Draw walls
        ax.plot([0, self.room_depth], [0, 0], "k-", linewidth=3)  # Bottom wall
        ax.plot([0, self.room_depth], [self.room_width, self.room_width], "k-", linewidth=3)  # Top wall
        ax.plot([0, 0], [0, self.room_width], "k-", linewidth=3)  # Left wall
        ax.plot([self.room_depth, self.room_depth], [0, self.room_width], "k-", linewidth=3)  # Right wall
        
        selected_door_type = ""

        name = self.windows_doors.name
        x = self.windows_doors.position[0]
        y = self.windows_doors.position[1]
        door_width = self.windows_doors.width
        door_height = self.windows_doors.height

        shadow = self.windows_doors.width
        selected_door_type = self.windows_doors.wall
        way = self.windows_doors.way
        hinge = self.windows_doors.hinge
        alpha = 0.5
        #fig = draw_door_only(selected_door_type, way, hinge, x, door_width, door_height, room_width, room_depth, fig,ax)
        # draw line in place of door
        if selected_door_type == "top":
            obj_shadow = patches.Rectangle((y, x), door_width, shadow, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(y + door_width / 2, x + shadow / 2, name + " " + hinge, ha="center", va="center", fontsize=10, fontweight="bold")
            
        elif selected_door_type == "bottom":
            obj_shadow = patches.Rectangle((y, self.room_width-shadow), door_width, shadow, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(y + door_width / 2, self.room_width - shadow + door_width / 2, name + " " + hinge, ha="center", va="center", fontsize=10, fontweight="bold")

        elif selected_door_type == "left":
            obj_shadow = patches.Rectangle((0, x), shadow, door_width, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(0 + shadow / 2, x + door_width / 2, name + " " + hinge, ha="center", va="center", fontsize=10, fontweight="bold")

        elif selected_door_type == "right":
            obj_shadow = patches.Rectangle((self.room_depth-shadow, x), shadow, door_width, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(self.room_depth - shadow + door_width / 2, x + door_width / 2, name + " " + hinge, ha="center", va="center", fontsize=10, fontweight="bold")

        
        # Draw objects
        for obj in self.objects:

            x = obj["object"].position[0]
            y = obj["object"].position[1]
            width = obj["object"].width
            depth = obj["object"].depth
            height = obj["object"].height
            shadow = obj["object"].shadow
            name = obj["object"].name
            wall = obj["object"].wall
            if shadow is not None:
                shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
                shadow_x = x - shadow_top
                shadow_y = y - shadow_left
                shadow_w = width + shadow_left + shadow_right
                shadow_d = depth + shadow_top + shadow_bottom
                obj_rect = patches.Rectangle((y, x), width, depth, edgecolor="blue", facecolor="lightblue", alpha=0.7)
                obj_shadow = patches.Rectangle((shadow_y, shadow_x), shadow_w, shadow_d, edgecolor="gray", facecolor="lightgray", alpha=0.5)
                ax.add_patch(obj_rect)
                ax.add_patch(obj_shadow)
                ax.text(y + width / 2, x + depth / 2, name, ha="center", va="center", fontsize=10, fontweight="bold")

        return fig
        
    def visualize_available_spaces(self, placed_objects, available_spaces_dict, shadow=True):
        """
        Visualizes the room with placed objects and available spaces.
        
        Args:
            placed_objects (list): List of placed objects.
            available_spaces_dict (dict): Dictionary of available spaces
            shadow (bool): Whether to show shadow spaces
            
        Returns:
            matplotlib.figure.Figure: The visualization figure
        """
        fig, ax = plt.subplots(figsize=((self.room_depth/100)*6, (self.room_width/100)*6))
        # Draw room boundaries
        ax.add_patch(patches.Rectangle((0, 0), self.room_depth, self.room_width, fill=False, edgecolor='black', linewidth=2))
        # Draw placed objects
        for obj in placed_objects:
            x, y, width, depth, height, *_ = obj
            ax.add_patch(patches.Rectangle((y, x), width, depth, fill=True, color='blue', alpha=0.7))
        # Draw available spaces WITHOUT shadow (green)
        if not shadow:
            for space in available_spaces_dict:
                x, y, width, depth = space
                ax.add_patch(patches.Rectangle((y, x), width, depth, fill=True, color='green', alpha=0.3, label='Available (no shadow)'))
        # Draw available spaces WITH shadow (orange, with some transparency)
        else:
            for space in available_spaces_dict:
                x, y, width, depth = space
                ax.add_patch(patches.Rectangle((y, x), width, depth, fill=True, color='orange', alpha=0.3, label='Available (with shadow)'))
        # Set limits and labels
        ax.set_xlim(0, self.room_depth)
        ax.set_ylim(0, self.room_width)
        ax.set_xlabel('Width (cm)')
        ax.set_ylabel('Depth (cm)')
        ax.set_title('Room Layout with Available Spaces')
        # Add legend (avoid duplicate labels)
        handles = [
            patches.Patch(color='blue', alpha=0.7, label='Placed Objects'),
            patches.Patch(color='green', alpha=0.3, label='Available (no shadow)'),
            patches.Patch(color='orange', alpha=0.3, label='Available (with shadow)')
        ]
        ax.legend(handles=handles)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        return fig
        
    def visualize_pathway_accessibility(self, placed_objects, windows_doors):
        """
        Visualize pathway accessibility between doors and objects.
        
        Args:
            placed_objects: List of objects with their positions and dimensions
            windows_doors: List of windows and doors
            
        Returns:
            matplotlib figure showing the room layout with pathway accessibility
        """
        
        fig, ax = plt.subplots(figsize=((self.room_depth/100)*6, (self.room_width/100)*6))
        
        # Draw room boundaries
        ax.add_patch(patches.Rectangle((0, 0), self.room_depth, self.room_width, fill=False, edgecolor='black', linewidth=2))
        
        # Create a grid for the room to check pathways
        grid_resolution = 5  # cm per grid cell
        grid_width = int(self.room_width / grid_resolution) + 1
        grid_depth = int(self.room_depth / grid_resolution) + 1
        
        # Create a grid where 1 = occupied, 0 = free space
        grid = np.zeros((grid_width, grid_depth), dtype=bool)
        
        # Mark all objects on the grid
        for obj in placed_objects:
            x, y, width, depth, height, name, _, _, _ = obj
            # Convert to grid coordinates
            grid_x_start = max(0, int(x / grid_resolution))
            grid_y_start = max(0, int(y / grid_resolution))
            grid_x_end = min(grid_width, int((x + depth) / grid_resolution) + 1)
            grid_y_end = min(grid_depth, int((y + width) / grid_resolution) + 1)
            
            # Mark object cells as occupied
            grid[grid_x_start:grid_x_end, grid_y_start:grid_y_end] = 1
            
            # Draw the object
            ax.add_patch(patches.Rectangle((y, x), width, depth, fill=True, color='blue', alpha=0.7))
            ax.text(y + width/2, x + depth/2, name, ha="center", va="center", fontsize=10, fontweight="bold", color='white')
        
        # Function to check if there's a clear path of at least 60cm width
        def has_clear_path(start_x, start_y, target_x, target_y):
            """
            Find a clear path from start to target that is at least 60cm wide using BFS.
            The path can go in any direction (not just straight lines).
            
            Args:
            start_x, start_y: Starting position in grid coordinates
            target_x, target_y: Target position in grid coordinates
        
            Returns:
            bool: True if there's a clear path, False otherwise
            list: List of coordinates along the path if found, empty list otherwise
            """
            # 60cm path width in grid units
            path_width = int(60 / grid_resolution)
            path_radius = path_width // 2
            
            # Create a visited grid to track which cells have been visited
            visited = np.zeros_like(grid, dtype=bool)
        
            # Create a queue for BFS
            queue = [(start_x, start_y, [(start_x, start_y)])]
            visited[start_x, start_y] = True
        
            # Define possible movement directions (including diagonals)
            directions = [
                (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal directions
                (-1, -1), (-1, 1), (1, -1), (1, 1)    # Diagonal directions
            ]
        
            while queue:
                current_x, current_y, path = queue.pop(0)
            
                # Check if we've reached the target
                if current_x == target_x and current_y == target_y:
                    return True, path
            
                # Try all possible directions
                for dx, dy in directions:
                    new_x, new_y = current_x + dx, current_y + dy
                    
                    # Check if the new position is within grid bounds
                    if (0 <= new_x < grid_width and 
                        0 <= new_y < grid_depth and 
                        not visited[new_x, new_y]):
                        
                        # Check if there's enough clearance for a 60cm wide path
                        # We need to check a square area of path_width×path_width centered at the new position
                        x_min = max(0, new_x - path_radius)
                        x_max = min(grid_width, new_x + path_radius + 1)
                        y_min = max(0, new_y - path_radius)
                        y_max = min(grid_depth, new_y + path_radius + 1)
                        
                        # If there are no obstacles in this area, we can move here
                        if not np.any(grid[x_min:x_max, y_min:y_max]):
                            visited[new_x, new_y] = True
                            new_path = path + [(new_x, new_y)]
                            queue.append((new_x, new_y, new_path))
        
            # If we've explored all possible paths and haven't found the target, return False
            return False, []
        
        # Draw doors
        door_positions = []
        for door in self.windows_doors:
            if 'door' in door[0].lower():  # Only check actual doors, not windows
                door_type = door[1]  # wall type (top, bottom, left, right)
                door_x, door_y = door[2], door[3]  # position
                door_width = door[4]  # width
                
                # Draw the door
                if door_type == "top":
                    ax.add_patch(patches.Rectangle((door_y, 0), door_width, 10, fill=True, color='green', alpha=0.7))
                    door_grid_x = 0
                    door_grid_y = int((door_y + door_width/2) / grid_resolution)
                elif door_type == "bottom":
                    ax.add_patch(patches.Rectangle((door_y, self.room_width-10), door_width, 10, fill=True, color='green', alpha=0.7))
                    door_grid_x = grid_width-1
                    door_grid_y = int((door_y + door_width/2) / grid_resolution)
                elif door_type == "left":
                    ax.add_patch(patches.Rectangle((0, door_x), 10, door_width, fill=True, color='green', alpha=0.7))
                    door_grid_x = int((door_x + door_width/2) / grid_resolution)
                    door_grid_y = 0
                elif door_type == "right":
                    ax.add_patch(patches.Rectangle((self.room_depth-10, door_x), 10, door_width, fill=True, color='green', alpha=0.7))
                    door_grid_x = int((door_x + door_width/2) / grid_resolution)
                    door_grid_y = grid_depth-1
                
                door_positions.append((door_grid_x, door_grid_y))
                ax.text(door_y + door_width/2, door_x + 5, "Door", ha="center", va="center", fontsize=8, color='black')
        
        # Check pathway from each door to each object
        accessible_objects = set()
        accessible_paths = []
        
        for door_grid_x, door_grid_y in door_positions:
            for i, obj in enumerate(self.objects):
                x, y, width, depth, height, name, _, _, _ = obj
                
                # Get multiple points around the object's perimeter for more realistic accessibility
                perimeter_points = []
                
                # Left side - multiple points along the left edge
                for j in range(1, int(width / grid_resolution), 10):  # Check every 10cm
                    perimeter_points.append((int(x / grid_resolution), int((y + j) / grid_resolution)))
                
                # Right side - multiple points along the right edge
                for j in range(1, int(width / grid_resolution), 10):
                    perimeter_points.append((int((x + depth) / grid_resolution), int((y + j) / grid_resolution)))
                
                # Top side - multiple points along the top edge
                for j in range(1, int(depth / grid_resolution), 10):
                    perimeter_points.append((int((x + j) / grid_resolution), int(y / grid_resolution)))
                
                # Bottom side - multiple points along the bottom edge
                for j in range(1, int(depth / grid_resolution), 10):
                    perimeter_points.append((int((x + j) / grid_resolution), int((y + width) / grid_resolution)))
                
                # Add the corners and midpoints of sides for good measure
                perimeter_points.extend([
                    (int(x / grid_resolution), int(y / grid_resolution)),  # top-left corner
                    (int((x + depth) / grid_resolution), int(y / grid_resolution)),  # top-right corner
                    (int(x / grid_resolution), int((y + width) / grid_resolution)),  # bottom-left corner
                    (int((x + depth) / grid_resolution), int((y + width) / grid_resolution)),  # bottom-right corner
                    (int(x / grid_resolution), int((y + width/2) / grid_resolution)),  # middle of left side
                    (int((x + depth) / grid_resolution), int((y + width/2) / grid_resolution)),  # middle of right side
                    (int((x + depth/2) / grid_resolution), int(y / grid_resolution)),  # middle of top side
                    (int((x + depth/2) / grid_resolution), int((y + width) / grid_resolution))   # middle of bottom side
                ])
                
                # Check if any perimeter point has a clear path to the door
                has_access = False
                for point_x, point_y in perimeter_points:
                    path_exists, path_coords = has_clear_path(door_grid_x, door_grid_y, point_x, point_y)
                    if path_exists:
                        # Store the actual path found by BFS for visualization
                        accessible_paths.append(path_coords)
                        
                        has_access = True
                        accessible_objects.add(i)
                        break
        
        # Draw all accessible paths with 60cm width circles at each point
        path_radius = 30  # 60cm diameter / 2 = 30cm radius
        for path in accessible_paths:
            # Draw path segments connecting points
            for i in range(len(path)-1):
                # Get current and next point in the path
                x1, y1 = path[i]
                x2, y2 = path[i+1]
                
                # Convert from grid to room coordinates
                room_x1 = y1 * grid_resolution
                room_y1 = x1 * grid_resolution
                room_x2 = y2 * grid_resolution
                room_y2 = x2 * grid_resolution
                
                # Draw circles with 30cm radius at each path position to represent 60cm clearance
                ax.add_patch(patches.Circle(
                    (room_x1, room_y1), 
                    path_radius,
                    fill=True, color='lightgreen', alpha=0.2, zorder=0
                ))
                
                # Draw line connecting the centers of adjacent circles
                ax.plot(
                    [room_x1, room_x2], 
                    [room_y1, room_y2], 
                    color='lightgreen', linewidth=3, alpha=0.6, zorder=1
                )
            
            # Draw circle at the last point too
            if path:
                last_x, last_y = path[-1]
                room_x = last_y * grid_resolution
                room_y = last_x * grid_resolution
                ax.add_patch(patches.Circle(
                    (room_x, room_y), 
                    path_radius,
                    fill=True, color='lightgreen', alpha=0.2, zorder=0
                ))
        
        # Highlight accessible vs inaccessible objects
        for i, obj in enumerate(self.objects):
            x, y, width, depth, height, name, _, _, _ = obj
            if i in accessible_objects:
                # Draw a green border around accessible objects
                ax.add_patch(patches.Rectangle((y, x), width, depth, fill=False, edgecolor='green', linewidth=2))
            else:
                # Draw a red border around inaccessible objects
                ax.add_patch(patches.Rectangle((y, x), width, depth, fill=False, edgecolor='red', linewidth=2))
        
        # Set limits and labels
        ax.set_xlim(0, room_depth)
        ax.set_ylim(0, room_width)
        ax.set_xlabel('Width (cm)')
        ax.set_ylabel('Depth (cm)')
        ax.set_title(f'Bathroom Layout with Pathway Accessibility')
        
        # Add legend
        handles = [
            patches.Patch(color='blue', alpha=0.7, label='Objects'),
            patches.Patch(color='green', alpha=0.7, label='Doors'),
            patches.Patch(color='lightgreen', alpha=0.3, label='Accessible Pathways'),
            patches.Patch(color='green', fill=False, linewidth=2, label='Accessible Objects'),
            patches.Patch(color='red', fill=False, linewidth=2, label='Inaccessible Objects')
        ]
        ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)
        
        ax.set_aspect('equal')
        ax.invert_yaxis()
        return fig
        
    def visualize_opposite_walls_distance(self, placed_objects, violations=None, min_distance=60):
        """
        Visualize the distance between objects on opposite walls, highlighting violations.
        
        Args:
            placed_objects: List of objects with their positions and dimensions
            violations: List of violations as returned by check_opposite_walls_distance
                       Each violation is (idx1, idx2, name1, name2, distance)
            min_distance: Minimum required distance (default 60cm)
            
        Returns:
            matplotlib figure showing the room layout with distance annotations
        """
        room_width, room_depth = self.room_width, self.room_depth
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw room boundaries
        ax.add_patch(patches.Rectangle((0, 0), room_width, room_depth, fill=False, edgecolor='black', linewidth=2))
        
        # Draw all objects
        for i, obj in enumerate(self.objects):
            x, y, width, depth, _, name, wall_pos, corner_pos, _ = obj
            label = f"{name} (#{i})"
            
            # Draw object
            ax.add_patch(patches.Rectangle(
                (y, x), width, depth,
                fill=True, facecolor='lightgray', edgecolor='black',
                linewidth=1, alpha=0.7
            ))
            
            # Add label
            ax.text(y + width/2, x + depth/2, label, ha='center', va='center', fontsize=8)
        
        # If no violations provided, calculate them
        if violations is None:
            from optimization import check_opposite_walls_distance
            _, violations = check_opposite_walls_distance(placed_objects, (room_width, room_depth), min_distance)
        
        # Draw distance lines and annotations for violations
        for left_idx, right_idx, left_name, right_name, distance in violations:
            # Get the objects
            left_obj = placed_objects[left_idx]
            right_obj = placed_objects[right_idx]
            
            # Unpack coordinates
            left_x, left_y, left_width, left_depth = left_obj[0], left_obj[1], left_obj[2], left_obj[3]
            right_x, right_y, right_width, right_depth = right_obj[0], right_obj[1], right_obj[2], right_obj[3]
            
            # Determine if this is a left-right or top-bottom pair
            is_horizontal = abs(left_x + left_depth - right_x) < abs(left_y + left_width - right_y)
            
            if is_horizontal:  # Left-right pair (horizontal violation)
                # Find middle y-coordinate where both objects overlap
                mid_y = max(left_y, right_y) + (min(left_y + left_width, right_y + right_width) - max(left_y, right_y)) / 2
                
                # Draw distance line
                ax.plot(
                    [left_y + left_width, right_y],
                    [left_x + left_depth/2, right_x + right_depth/2],
                    'r--', linewidth=1.5
                )
                
                # Add distance annotation
                ax.text(
                    (left_y + left_width + right_y) / 2,
                    (left_x + left_depth/2 + right_x + right_depth/2) / 2,
                    f"{distance:.1f}cm",
                    color='red', fontweight='bold', ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.3')
                )
            else:  # Top-bottom pair (vertical violation)
                # Find middle x-coordinate where both objects overlap
                mid_x = max(left_x, right_x) + (min(left_x + left_depth, right_x + right_depth) - max(left_x, right_x)) / 2
                
                # Draw distance line
                ax.plot(
                    [left_y + left_width/2, right_y + right_width/2],
                    [left_x + left_depth, right_x],
                    'r--', linewidth=1.5
                )
                
                # Add distance annotation
                ax.text(
                    (left_y + left_width/2 + right_y + right_width/2) / 2,
                    (left_x + left_depth + right_x) / 2,
                    f"{distance:.1f}cm",
                    color='red', fontweight='bold', ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.3')
                )
        
        # Add legend for minimum distance requirement
        legend_patch = patches.Patch(color='red', fill=False, hatch='///', label=f'Min Distance: {min_distance}cm')
        ax.legend(handles=[legend_patch], loc='upper right')
        
        # Add title
        if violations:
            ax.set_title(f"Opposite Walls Distance Check: {len(violations)} violation(s)")
        else:
            ax.set_title("Opposite Walls Distance Check: No violations")
        
        # Set equal aspect ratio and invert y-axis to match room layout
        ax.set_aspect('equal')
        ax.set_xlabel('Width (cm)')
        ax.set_ylabel('Depth (cm)')
        
        # Set limits
        ax.set_xlim(0, room_width)
        ax.set_ylim(room_depth, 0)  # Inverted y-axis
        
        return fig
def draw_door(selected_door_type, selected_door_way, selected_door_hinge, x, door_width, door_height, room_width, room_depth):
        # Create and display room dimension visualization
        fig, ax = plt.subplots(figsize=(5, 5))
        # Draw rectangle with room dimensions
        room_rect = plt.Rectangle((0, 0), room_depth, room_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
        ax.add_patch(room_rect)
                
        # Set plot limits with some padding
        padding = max(room_depth, room_width) * 0.1
        ax.set_xlim(-padding, room_depth + padding)
        ax.set_ylim(-padding, room_width + padding)
                
        # Add dimension labels
        ax.text(room_depth/2, -padding/2, f'{room_depth:.1f}cm', ha='center', va='top')
        ax.text(-padding/2, room_width/2, f'{room_width:.1f}cm', ha='right', va='center', rotation=90)
                
        # Add center point
        ax.plot(room_depth/2, room_width/2, 'ro')


            # add door based on selected door type, way, and hinge side
        if selected_door_type == "top":
            if selected_door_way == "Inward":
                #door_rect = plt.Rectangle((x, self.room_width - door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if selected_door_hinge == "Right":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [room_width, room_width - door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x, room_width ), door_width*2, door_width*2, 
                                    angle=-90, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge (from outside perspective)
                    ax.plot([x + door_width, x + door_width], [room_width, room_width - door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x + door_width, room_width ), door_width*2, door_width*2, 
                                    angle=90, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
            elif selected_door_way == "Outward":
                #door_rect = plt.Rectangle((x, self.room_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [room_width, room_width + door_width], 'k-', linewidth=3)
                else: # Right hinge
                    ax.plot([x + door_width, x + door_width], [room_width, room_width + door_width], 'k-', linewidth=3)
                ax.text(x+door_width/2, room_width, f'{door_width:.1f}cm', ha='center', va='bottom')
                # distance from corner
                ax.text(x/2,room_width, f'{x:.1f}cm', ha='center', va='bottom')
                ax.text(x+door_width + x/2, room_width, f'{room_depth-door_width-x:.1f}cm', ha='center', va='bottom')
        elif selected_door_type == "bottom":
            if selected_door_way == "Inward":
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [0, door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x, 0), door_width*2, door_width*2, 
                                    angle=0, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge (from outside perspective)
                    ax.plot([x + door_width, x + door_width], [0, door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x + door_width, 0), door_width*2, door_width*2, 
                                    angle=0, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
            elif selected_door_way == "Outward":
                #door_rect = plt.Rectangle((x, -door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [0, -door_width], 'k-', linewidth=3)
                else: # Right hinge
                    # Right hinge (from outside perspective)
                    ax.plot([x + door_width, x + door_width], [0, -door_width], 'k-', linewidth=3)

                # distance from corner
                ax.text(x/2, 0, f'{x:.1f}cm', ha='center', va='bottom')
                ax.text(x+door_width/2,0, f'{door_width:.1f}cm', ha='center', va='bottom')
                ax.text(x+door_width + x/2, 0, f'{room_depth-door_width-x:.1f}cm', ha='center', va='bottom')
        elif selected_door_type == "right":
            if selected_door_way == "Inward":
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge from outside perspective (top of the door in this orientation)
                    ax.plot([room_depth - door_width, room_depth], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((room_depth, room_width-x-door_width), door_width*2, door_width*2, 
                                    angle=270, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge from outside perspective (bottom of the door in this orientation)
                        ax.plot([room_depth - door_width, room_depth], [room_width-x, room_width-x], 'k-', linewidth=3)
                        # Door swing arc
                        arc = patches.Arc((room_depth , room_width-x), door_width*2, door_width*2, 
                                        angle=270, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                        ax.add_patch(arc)
            elif selected_door_way == "Outward":
                #door_rect = plt.Rectangle((self.room_depth, self.room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge from outside perspective (top of the door in this orientation)
                    ax.plot([room_depth, room_depth + door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                else: # Right hinge
                    # Right hinge from outside perspective (bottom of the door in this orientation)
                    ax.plot([room_depth, room_depth + door_width], [room_width-x, room_width-x], 'k-', linewidth=3)

                ax.text(room_depth + padding/2, room_width-x-door_width/2, f'{door_width:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(room_depth + padding/2, padding, f'{room_width-door_width-x:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(room_depth + padding/2, room_width-x/2, f'{x:.1f}cm', ha='right', va='center', rotation=90)
        elif selected_door_type == "left":
            if selected_door_way == "Inward":
                #door_rect = plt.Rectangle((0, room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge from outside perspective (bottom of the door in this orientation)
                    ax.plot([0, door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((0, room_width-x), door_width*2, door_width*2, 
                                    angle=90, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge from outside perspective (top of the door in this orientation)
                    ax.plot([0, door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((0, room_width-x-door_width), door_width*2, door_width*2, 
                                    angle=90, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
            elif selected_door_way == "Outward":
                #door_rect = plt.Rectangle((-door_width, self.room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if selected_door_hinge == "Left":
                    # Left hinge from outside perspective (bottom of the door in this orientation)
                    ax.plot([0, -door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                else: # Right hinge
                    # Right hinge from outside perspective (top of the door in this orientation)
                    ax.plot([0, -door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                ax.text(0+ padding/2, room_width-x-door_width/2, f'{door_width:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(0+padding/2, padding, f'{room_width-door_width-x:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(0+padding/2, room_width-x/2, f'{x:.1f}cm', ha='right', va='center', rotation=90)
                # Remove axis ticks and labels for cleaner look
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect('equal')
        return fig
def draw_door_only(selected_door_type, way, hinge, x, door_width, door_height, room_width, room_depth, fig,ax):
    #padding = max(room_depth, room_width) * 0.1
    print(hinge,way,selected_door_type)
    if selected_door_type == "top":
        if way == "Inward":
                #door_rect = plt.Rectangle((x, self.room_width - door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if hinge == "Right":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [room_width, room_width - door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x, room_width ), door_width*2, door_width*2, 
                                    angle=-90, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge (from outside perspective)
                    ax.plot([x + door_width, x + door_width], [room_width, room_width - door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x + door_width, room_width ), door_width*2, door_width*2, 
                                    angle=90, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
        elif way == "Outward":
                #door_rect = plt.Rectangle((x, self.room_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [room_width, room_width + door_width], 'k-', linewidth=3)
                else: # Right hinge
                    ax.plot([x + door_width, x + door_width], [room_width, room_width + door_width], 'k-', linewidth=3)
                ax.text(x+door_width/2, room_width, f'{door_width:.1f}cm', ha='center', va='bottom')
                # distance from corner
                ax.text(x/2,room_width, f'{x:.1f}cm', ha='center', va='bottom')
                ax.text(x+door_width + x/2, room_width, f'{room_depth-door_width-x:.1f}cm', ha='center', va='bottom')
    elif selected_door_type == "bottom":
        if way == "Inward":
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [0, door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x, 0), door_width*2, door_width*2, 
                                    angle=0, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge (from outside perspective)
                    ax.plot([x + door_width, x + door_width], [0, door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((x + door_width, 0), door_width*2, door_width*2, 
                                    angle=0, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
        elif way == "Outward":
                #door_rect = plt.Rectangle((x, -door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge (from outside perspective)
                    ax.plot([x, x], [0, -door_width], 'k-', linewidth=3)
                else: # Right hinge
                    # Right hinge (from outside perspective)
                    ax.plot([x + door_width, x + door_width], [0, -door_width], 'k-', linewidth=3)

                # distance from corner
                ax.text(x/2, 0, f'{x:.1f}cm', ha='center', va='bottom')
                ax.text(x+door_width/2,0, f'{door_width:.1f}cm', ha='center', va='bottom')
                ax.text(x+door_width + x/2, 0, f'{room_depth-door_width-x:.1f}cm', ha='center', va='bottom')
    elif selected_door_type == "right":
        if way == "Inward":
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge from outside perspective (top of the door in this orientation)
                    ax.plot([room_depth - door_width, room_depth], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((room_depth, room_width-x-door_width), door_width*2, door_width*2, 
                                    angle=270, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge from outside perspective (bottom of the door in this orientation)
                        ax.plot([room_depth - door_width, room_depth], [room_width-x, room_width-x], 'k-', linewidth=3)
                        # Door swing arc
                        arc = patches.Arc((room_depth , room_width-x), door_width*2, door_width*2, 
                                        angle=270, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                        ax.add_patch(arc)
        elif way == "Outward":
                #door_rect = plt.Rectangle((self.room_depth, self.room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge from outside perspective (top of the door in this orientation)
                    ax.plot([room_depth, room_depth + door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                else: # Right hinge
                    # Right hinge from outside perspective (bottom of the door in this orientation)
                    ax.plot([room_depth, room_depth + door_width], [room_width-x, room_width-x], 'k-', linewidth=3)

                ax.text(room_depth + padding/2, room_width-x-door_width/2, f'{door_width:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(room_depth + padding/2, padding, f'{room_width-door_width-x:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(room_depth + padding/2, room_width-x/2, f'{x:.1f}cm', ha='right', va='center', rotation=90)
    elif selected_door_type == "left":
        if way == "Inward":
                #door_rect = plt.Rectangle((0, room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge from outside perspective (bottom of the door in this orientation)
                    ax.plot([0, door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((0, room_width-x), door_width*2, door_width*2, 
                                    angle=90, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
                else: # Right hinge
                    # Right hinge from outside perspective (top of the door in this orientation)
                    ax.plot([0, door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                    # Door swing arc
                    arc = patches.Arc((0, room_width-x-door_width), door_width*2, door_width*2, 
                                    angle=90, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                    ax.add_patch(arc)
        elif way == "Outward":
                #door_rect = plt.Rectangle((-door_width, self.room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                # Add hinge indicator
                if hinge == "Left":
                    # Left hinge from outside perspective (bottom of the door in this orientation)
                    ax.plot([0, -door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                else: # Right hinge
                    # Right hinge from outside perspective (top of the door in this orientation)
                    ax.plot([0, -door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                ax.text(0+ padding/2, room_width-x-door_width/2, f'{door_width:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(0+padding/2, padding, f'{room_width-door_width-x:.1f}cm', ha='right', va='center', rotation=90)
                ax.text(0+padding/2, room_width-x/2, f'{x:.1f}cm', ha='right', va='center', rotation=90)

    return fig