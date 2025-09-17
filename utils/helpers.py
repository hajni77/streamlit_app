
import numpy as np
import streamlit as st
import math
import json
from algorithms.available_space import check_enclosed_spaces, identify_available_space
OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)

def save_data(supabase, room_sizes, positions, doors, review, is_enough_path, space, overall, is_everything, room_name=None, calculated_reward=None, reward=None):
    if not st.session_state.auth.get('user'):
        st.error("Please sign in to submit reviews")
        return False
    
    with st.spinner("Saving your review to the database..."):
        try:
            print(type(positions))
            print(positions.bathroom.objects)
            placed_objects = positions.bathroom.objects
            objects = []
            objects_positions = []
            for position in placed_objects:
                object = position['object']
                objects.append({
                        "name": object.name,
                        "width": object.width,
                        "depth": object.depth,
                        "height": object.height
                    })
                objects_positions.append({
                        "x": object.position[0],
                        "y": object.position[1],
                        "wall": object.wall,
                        "must_be_corner": OBJECT_TYPES[object.name]["must_be_corner"],
                        "against_wall": OBJECT_TYPES[object.name]["must_be_against_wall"]
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
                    "type": door.wall,
                    "position": {"x": door.position[0], "y": door.position[1]},
                    "dimensions": {"width": door.width, "depth": door.depth, "height": door.height,"wall": door.wall, "hinge": door.hinge, "way": door.way}
                } for door in doors ],
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
def check_which_wall(new_rect, room_width, room_depth):
    x,y,width,depth, height = new_rect
    
    """Check which wall the object is closest to."""
    if x == 0 and y==0:
        return "top-left"
    elif y == room_depth-width and x == 0:
        return "top-right"
    elif x == room_width-depth and y == 0:
        return "bottom-left"
    elif x == room_width-depth and y == room_depth-width:
        return "bottom-right"
    elif x == 0 and y!= 0:
        return "top"
    elif y == 0 and x!=0:
        return "left"
    elif x == room_width-depth and y != 0:
        return "bottom"
    elif y == room_depth-width and x != 0:
        return "right"
    else:
        return "middle"


def check_distance_from_wall(rect, room_width, room_depth, wall, shadow):
    """Check the distance of the object from the wall."""
    x, y, width, depth = rect
    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
    
    if wall == "top":
        return x
    elif wall == "left":
        return y
    elif wall == "bottom":
        return room_width - (x + depth)
    elif wall == "right":
        return room_depth - (y + width)
    else:
        return min(x, y, room_width - (x + depth), room_depth - (y + width))

# only modify shadow values
def convert_values(rect, shadow, wall):
    """Converts the values of the object and shadow based on the wall it is closest to."""
    x, y, width, depth, height = rect



    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
    new_shadow_top = 0
    new_shadow_right = 0
    new_shadow_left = 0
    new_shadow_bottom = 0
    if wall == "top":
        new_shadow_left = shadow_right
        new_shadow_right = shadow_left
        new_shadow_bottom = shadow_top
        new_shadow_top = shadow_bottom
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "right":
        new_shadow_right = shadow_bottom
        new_shadow_top = shadow_right
        new_shadow_bottom = shadow_left
        new_shadow_left = shadow_top
        return x, y, width, depth,  new_shadow_top, new_shadow_left,new_shadow_right, new_shadow_bottom
    elif wall == "left":
        new_shadow_left = shadow_bottom
        new_shadow_top = shadow_left
        new_shadow_bottom = shadow_right
        new_shadow_right = shadow_top
        return x, y, width, depth,  new_shadow_top, new_shadow_left,new_shadow_right, new_shadow_bottom 
    elif wall == "bottom":
        return x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom
    elif wall == "top-left":
        if width > depth :
            new_shadow_right = shadow_left
            new_shadow_bottom = shadow_top
        if width < depth :
            new_shadow_right = shadow_top
            new_shadow_bottom = shadow_right
        if width == depth:
            new_shadow_right = shadow_top
            new_shadow_bottom = shadow_right

        
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
   #TODO javítani az árnyékkiosztást     
    elif wall == "top-right":
    
        if width > depth :   
            new_shadow_left = shadow_right
            new_shadow_bottom = shadow_top
        if width < depth:
            new_shadow_left = shadow_top
            new_shadow_bottom = shadow_left
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "bottom-left":
        if width > depth:
            new_shadow_right = shadow_right
            new_shadow_top = shadow_top
        if width < depth:
            new_shadow_right = shadow_top
            new_shadow_top = shadow_left
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "bottom-right":
        if width > depth:
            new_shadow_left = shadow_left
            new_shadow_top = shadow_top
        if width < depth:
            new_shadow_left = shadow_top
            new_shadow_top = shadow_right
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    else:
        return x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom
def get_required_area(selected_object, room_width, room_depth, OBJECT_TYPES):
    object_areas = []
    room_area = room_width * room_depth
    required_area = 0
    # Calculate area needed for each object
    for obj_type in selected_object:
        if obj_type in OBJECT_TYPES:
            obj_def = OBJECT_TYPES[obj_type]
            optimal_size = obj_def["optimal_size"]
                
            # Calculate the base area (width * depth)
            obj_width, obj_depth, _ = optimal_size
                
            obj_area = obj_width * obj_depth
            # Get priority index (higher = more important)
            # If not in priority list, assign lowest priority
            priority = priority_list.index(obj_type) if obj_type in priority_list else -1
                
            object_areas.append((obj_type, obj_area, priority))
            required_area += obj_area
        
        # Add 20% for pathways and space between objects
        required_area *= 1.2
        
        print(f"Room area: {room_area} cm², Required area: {required_area:.2f} cm²")
    return required_area




def mark_inaccessible_spaces(available_spaces, placed_objects, room_sizes, windows_doors, grid_size=1, min_path_width=30):
    """
    Check available spaces (without shadow) and mark those that aren't accessible 
    from doors with at least a minimum width path as closed spaces.
    
    Args:
        available_spaces (list): List of available spaces as (x, y, width, depth) tuples
        placed_objects (list): List of placed objects [(x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)]
        room_sizes (tuple): Room dimensions (width, depth)
        windows_doors (list): List of windows and doors in the room [(id, wall, x, y, width, height, parapet)]
        grid_size (int): Size of grid cells in cm
        min_path_width (int): Minimum required path width in cm (default: 30cm)
        
    Returns:
        tuple: (accessible_spaces, inaccessible_spaces) - Lists of spaces that are accessible and inaccessible
    """
    room_width, room_depth = room_sizes
    grid_width = room_width // grid_size
    grid_depth = room_depth // grid_size
    
    # Create a grid representation of the room (0 = occupied, 1 = free)
    grid = [[1 for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Mark placed objects on the grid
    for obj in placed_objects:

            i = 0
            while i < len(obj):

                name = obj[i]['object'].name
                width = obj[i]['object'].width
                depth = obj[i]['object'].depth
                height = obj[i]['object'].height
                shadow = obj[i]['object'].shadow
                position = obj[i]['object'].position
                wall = obj[i]['object'].wall
                x,y = position
        
                start_x = max(0, int(x) // grid_size)
                start_y = max(0, int(y) // grid_size)
                end_x = min(grid_width, int(x + width) // grid_size)
                end_y = min(grid_depth, int(y + depth) // grid_size)
                
                for i in range(start_x, end_x):
                    for j in range(start_y, end_y):
                        if 0 <= i < grid_width and 0 <= j < grid_depth:
                            grid[i][j] = 0
            
    # Find door positions
    door_positions = []
    if windows_doors:
        
        if windows_doors.name.startswith("door"):
            # Mark the door area and add entry points
            start_x = max(0, int(windows_doors.position[0]) // grid_size)
            start_y = max(0, int(windows_doors.position[1]) // grid_size)
            end_x = min(grid_width, int(windows_doors.position[0] + windows_doors.width) // grid_size)
            end_y = min(grid_depth, int(windows_doors.position[1] + windows_doors.width) // grid_size)
            # Determine door entry points based on which wall it's on
            if windows_doors.wall == "left" or windows_doors.wall == "right":
                # Door on top or bottom wall, entry points along x-axis
                for i in range(start_x, end_x):
                    entry_y = start_y if windows_doors.wall == "left" else end_y - 1
                    door_positions.append((i, entry_y))
            else:
                # Door on left or right wall, entry points along y-axis
                for j in range(start_y, end_y):
                    entry_x = start_x if windows_doors.wall == "top" else end_x - 1
                    door_positions.append((entry_x, j))
    
    # If no doors found, use the center of each wall as potential entry points
    if not door_positions:
        door_positions = [
            (grid_width // 2, 0),  # Top wall
            (grid_width // 2, grid_depth - 1),  # Bottom wall
            (0, grid_depth // 2),  # Left wall
            (grid_width - 1, grid_depth // 2)  # Right wall
        ]
    
    # Create a copy of the grid to mark visited cells
    visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Define minimum path width in grid cells
    min_path_cells = min_path_width // grid_size
    
    def is_accessible(x, y):
        """Check if a cell is accessible and within bounds."""
        return (0 <= x < grid_width and 0 <= y < grid_depth and 
                grid[x][y] == 1 and not visited[x][y])
    
    def check_path_width(x, y):
        """Check if there's enough width for the path."""
        # Check horizontal width
        horizontal_clear = True
        for dx in range(-min_path_cells//2, min_path_cells//2 + 1):
            nx = x + dx
            if not (0 <= nx < grid_width) or grid[nx][y] == 0:
                horizontal_clear = False
                break
        
        # Check vertical width
        vertical_clear = True
        for dy in range(-min_path_cells//2, min_path_cells//2 + 1):
            ny = y + dy
            if not (0 <= ny < grid_depth) or grid[x][ny] == 0:
                vertical_clear = False
                break
        
        # Need at least one direction to be clear
        return horizontal_clear and vertical_clear
    
    def bfs_from_doors():
        """Breadth-first search from door positions to mark accessible areas."""
        queue = []
        for door_x, door_y in door_positions:
            if is_accessible(door_x, door_y):
                queue.append((door_x, door_y))
                visited[door_x][door_y] = True
        
        while queue:
            x, y = queue.pop(0)
            
            # Add neighbors to queue if they're accessible and have enough path width
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if is_accessible(nx, ny):
                    # Only mark as accessible if there's enough width for the path
                    if check_path_width(nx, ny):
                        visited[nx][ny] = True
                        queue.append((nx, ny))
    
    # Run BFS from door positions
    bfs_from_doors()
    
    # Check which available spaces are accessible and which are not
    accessible_spaces = []
    inaccessible_spaces = []
    
    for space in available_spaces:
        x, y, width, depth = space
        # Convert to grid coordinates
        grid_x = int(x) // grid_size
        grid_y = int(y) // grid_size
        grid_end_x = min(grid_width, int(x + width) // grid_size)
        grid_end_y = min(grid_depth, int(y + depth) // grid_size)
        
        # Check if any part of the space is accessible
        space_accessible = False
        for i in range(grid_x, grid_end_x):
            for j in range(grid_y, grid_end_y):
                if 0 <= i < grid_width and 0 <= j < grid_depth and visited[i][j]:
                    space_accessible = True
                    break
            if space_accessible:
                break
        
        if space_accessible:
            accessible_spaces.append(space)
        else:
            inaccessible_spaces.append(space)
    
    return accessible_spaces, inaccessible_spaces


def sort_objects_by_priority(objects, room_type):
    """Sort objects by priority."""
    if room_type == "bathroom":
        return sorted(objects, key=lambda obj: obj.priority)

def find_contiguous_space(grid, visited, start_x, start_y, grid_width, grid_depth):
    """
    Helper function to find a contiguous available space starting from a given cell.
    Uses a flood-fill approach to find the rectangular bounds of the space.
    
    Args:
        grid (list): 2D grid representation of the room.
        visited (list): 2D grid tracking visited cells.
        start_x (int): Starting x coordinate.
        start_y (int): Starting y coordinate.
        grid_width (int): Width of the grid.
        grid_depth (int): Depth of the grid.
    
    Returns:
        dict: Dictionary with the bounds of the contiguous space.
    """
    # Mark the starting cell as visited
    visited[start_x][start_y] = True
    
    # Find the maximum width (right expansion)
    end_y = start_y
    while end_y + 1 < grid_depth and grid[start_x][end_y + 1] == 1:
        end_y += 1
        visited[start_x][end_y] = True
    
    # Find the maximum depth (downward expansion)
    end_x = start_x
    is_rectangle = True
    
    while is_rectangle and end_x + 1 < grid_width:
        # Check if the next row is all available
        for j in range(start_y, end_y + 1):
            if grid[end_x + 1][j] == 0:
                is_rectangle = False
                break
        
        if is_rectangle:
            end_x += 1
            # Mark the row as visited
            for j in range(start_y, end_y + 1):
                visited[end_x][j] = True
    
    return {
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x + 1,  # Add 1 to get the exclusive end
        "end_y": end_y + 1   # Add 1 to get the exclusive end
    }

def sort_objects_by_size(object_list, room_width, room_depth):
    """Sort objects by their maximum possible area (largest first)."""
    # Check if both "Sink" and "Double Sink" are in the object list
    object_list = [item.lower() for item in object_list]

            
    has_sink = "Sink" in object_list or "sink" in object_list
    has_double_sink = "Double Sink" in object_list or "double sink" in object_list
    
    # If both types of sinks are present, choose which one to keep
    filtered_object_list = object_list.copy()
    if has_sink and has_double_sink:
    # For small bathrooms (< 300x300 cm), always keep the regular sink
        if room_width < 300 or room_depth < 300:
            sink_to_keep = "sink"
            filtered_object_list.remove("double sink")
            print(f"Small bathroom detected ({room_width}x{room_depth}). Keeping only regular Sink.")
        else:
            # For larger bathrooms, randomly choose which sink type to keep
            sink_to_keep = random.choice(["sink", "double sink"])
            if sink_to_keep == "sink":
                filtered_object_list.remove("double sink")
            else:
                filtered_object_list.remove("sink")
            print(f"Larger bathroom detected. Keeping only: {sink_to_keep}")
            object_list = filtered_object_list.copy()
    elif not has_sink and not has_double_sink:
        # add sink to the list
        object_list.append("sink")
    if len(object_list) <= 2:
        if "sink" in object_list[1] or "Sink" in object_list[1]:
            object_list = object_list[::-1]
    
    objects_list_priority = ["bathtub", "shower", "asymmetrical bathtub", "toilet bidet","double sink", "sink","toilet", "washing machine", "washing dryer",  "cabinet", "washing machine dryer"]
    # sort object_list by priority
    object_list.sort(key=lambda obj: objects_list_priority.index(obj) if obj in objects_list_priority else len(objects_list_priority), reverse=False)
    return object_list
# Check if two rectangles overlap
def check_overlap(rect1, rect2):
    # Extract coordinates (x, y, width, depth, height)
    x1, y1, width1, depth1 = rect1[0], rect1[1], rect1[2], rect1[3]
    x2, y2, width2, depth2 = rect2[0], rect2[1], rect2[2], rect2[3]
    
    # Calculate rectangle boundaries
    rect1_left = y1
    rect1_right = y1 + width1
    rect1_top = x1
    rect1_bottom = x1 + depth1

    rect2_left = y2
    rect2_right = y2 + width2
    rect2_top = x2
    rect2_bottom = x2 + depth2
    
    # Check height overlap if height is provided
    height_overlap = True
    if len(rect1) > 4 and len(rect2) > 4:
        height1 = rect1[4]
        height2 = rect2[4]
        # No overlap if one object is above the other
        if height1 <= 0 or height2 <= 0:
            height_overlap = False
    # check if the rectangles are inside each other (1 in 2)
    if rect1_left >= rect2_left and rect1_right <= rect2_right and rect1_top >= rect2_top and rect1_bottom <= rect2_bottom:
        return True

    # check if the rectangles are inside each other (2 in 1)
    if rect2_left >= rect1_left and rect2_right <= rect1_right and rect2_top >= rect1_top and rect2_bottom <= rect1_bottom:
        return True
    
    
    # Check if the rectangles overlap
    if (rect1_right <= rect2_left or rect2_right <= rect1_left) or (rect1_bottom <= rect2_top or rect2_bottom <= rect1_top): 
        return False  # No overlap 

    # If none of the above conditions are met, there is an overlap
    return True


def check_euclidean_distance(rect1, rect2):
    x1, y1, width1, depth1 = rect1
    x2, y2, width2, depth2 = rect2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def is_corner_placement_sink(x, y, room_width, room_depth, sink_width, sink_depth, corner_threshold=50):
    """
    Check if an object is placed in a corner of the room.
    
    Args:
        x (int): X coordinate of the object
        y (int): Y coordinate of the object
        room_width (int): Width of the room
        room_depth (int): Depth of the room
        corner_threshold (int): Distance from walls to consider a corner
        
    Returns:
        bool: True if object is in a corner, False otherwise
    """
    return (x < corner_threshold) or \
           (y < corner_threshold) or \
           (x + sink_depth > room_depth - corner_threshold) or \
           (y + sink_width > room_width - corner_threshold)


def get_opposite_wall(wall):
    if wall == "top":
        return "bottom"
    elif wall == "bottom":
        return "top"
    elif wall == "left":
        return "right"
    elif wall == "right":
        return "left"
    elif wall == "top-left":
        return "bottom-right"
    elif wall == "top-right":
        return "bottom-left"
    elif wall == "bottom-left":
        return "top-right"
    elif wall == "bottom-right":
        return "top-left"


# def windows_doors_overlap(windows_doors, x, y, width, depth, height):
#     # Handle both iterable collections and single WindowsDoors objects
#     if windows_doors is None:
#         return False
    
#     # Create a list to iterate over
#     wd_list = []
    
#     # Check if windows_doors is iterable (list, tuple, etc.)
#     if hasattr(windows_doors, '__iter__') and not isinstance(windows_doors, str):
#         wd_list = windows_doors
#     else:
#         # Single WindowsDoors object
#         wd_list = [windows_doors]
    
#     for window_door in wd_list:
#         # Extract window/door properties using helper function
#         wd_x, wd_y, wd_width, wd_depth, wd_height, wd_wall = extract_door_window_based_on_type(window_door)
        
#         # Check for 2D overlap (x-y plane)
#         x_overlap = x < wd_x + wd_depth and x + depth > wd_x
#         y_overlap = y < wd_y + wd_width and y + width > wd_y
        
#         # Check for height overlap (z-axis)
#         # For windows, check if the object's height range overlaps with the window's height range
#         # For doors, we typically want to avoid any object placement in front of doors
        
#         # Default height for windows/doors if not specified
#         if wd_height is None:
#             wd_height = 200  # Default height
            
#         # # Windows are typically placed higher on walls
#         # if hasattr(window_door, 'type') and window_door.type == 'window':
#         #     # Assume windows start at z=150 from floor
#         #     window_z_start = 150
#         #     z_overlap = (z < window_z_start + wd_height) and (z + height > window_z_start)
#         # else:  # Door or unknown type
#         #     # Doors typically start from the floor (z=0)
#         #     z_overlap = (z < wd_height) and (z + height > 0)
        
#         # Return True if there's overlap in all dimensions
#         if x_overlap and y_overlap :
#             return True
    
#     return False


def calculate_overlap_area(rect1, rect2):
    x1, y1, width1, depth1 = rect1
    x2, y2, width2, depth2 = rect2
    
    # Calculate the overlap dimensions
    overlap_width = min(x1 + depth1, x2 + depth2) - max(x1, x2)
    overlap_height = min(y1 + width1, y2 + width2) - max(y1, y2)
    
    # If either dimension is negative, there is no overlap
    if overlap_width <= 0 or overlap_height <= 0:
        return 0
    
    return overlap_width * overlap_height


def calculate_space_before_object(obj, placed_objects, room_size):
    """
    Calculate the space in front of an object toward the opposite wall.
    For objects against a wall, it calculates the free space in the direction away from the wall.
    
    Args:
        obj (tuple): Object to check space for (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)
        placed_objects (list): List of all placed objects in the room
        room_size (tuple): Room dimensions (width, depth)
        
    Returns:
        float: Amount of free space in front of the object (in cm)
    """
    obj = obj['object']
    x = obj.position[0]
    y = obj.position[1]
    width = obj.width
    depth = obj.depth
    height = obj.height
    name = obj.name
    shadow = obj.shadow
    room_width, room_depth, room_height = room_size
    total_space_coordinates = (x, y, width, depth)
    
    # Determine which wall the object is against
    against_wall = "middle"  # Default if not against any wall
    
    if x == 0:
        against_wall = "top"
    elif y == 0:
        against_wall = "left"
    elif x + depth >= room_width:
        against_wall = "bottom"
    elif y + width >= room_depth:
        against_wall = "right"
    
    # Handle corners
    if x == 0 and y == 0:
        against_wall = "top-left"
    elif x == 0 and y + width >= room_depth:
        against_wall = "top-right"
    elif x + depth >= room_width and y == 0:
        against_wall = "bottom-left"
    elif x + depth >= room_width and y + width >= room_depth:
        against_wall = "bottom-right"
    
    # Calculate free space based on which wall the object is against
    free_space = 0
    
    if against_wall == "middle":
        # Object is not against any wall, calculate space in all directions
        free_space = room_width * room_depth - (width * depth)
    elif against_wall == "top":
        # Object is against top wall, calculate space toward bottom wall
        total_space_coordinates = (x, y + width, depth, room_depth - width)  # Distance from object to bottom wall
        free_space = total_space_coordinates[2] * total_space_coordinates[3]
    elif against_wall == "left":
        # Object is against left wall, calculate space toward right wall
        total_space_coordinates = (x + depth, y, room_width - depth, width)  # Distance from object to right wall
        free_space = total_space_coordinates[2] * total_space_coordinates[3]
    elif against_wall == "bottom":
        # Object is against bottom wall, calculate space toward top wall
        total_space_coordinates = (x, 0, depth, y)  # Distance from object to top wall
        free_space = total_space_coordinates[2] * total_space_coordinates[3]
    elif against_wall == "right":
        # Object is against right wall, calculate space toward left wall
        total_space_coordinates = (0, y, x, width)  # Distance from object to left wall
        free_space = total_space_coordinates[2] * total_space_coordinates[3]
    
    # Check for objects in between that reduce free space
    for other_obj in placed_objects:
        if other_obj != obj:
            other_obj = other_obj['object']
            other_x = other_obj.position[0]
            other_y = other_obj.position[1]
            other_width = other_obj.width
            other_depth = other_obj.depth
            other_height = other_obj.height
            other_name = other_obj.name
            other_shadow = other_obj.shadow
            # Check if other object is in the path between this object and opposite wall
            if check_overlap(total_space_coordinates, (other_x, other_y, other_width, other_depth)):
                overlap = calculate_overlap_area(total_space_coordinates, (other_x, other_y, other_width, other_depth))
                free_space -= overlap
    
    return free_space

# Check if the new object can be placed without overlapping with existing objects or shadows
def is_valid_placement(new_rect, placed_rects, shadow_space, room_width, room_depth, door_walls):
    """Ensures the new object does not overlap with existing objects or shadows."""

    
    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow_space  # Extract shadow values
    x, y, width, depth, height, wall = new_rect
    # check that the object actually fits in the room
    if x < 0 or y < 0 or x + depth > room_width or y + width > room_depth:
        return False  # Object extends outside the room → INVALID
    # create squares for shadow space
    if shadow_top == 0 and shadow_left == 0 and shadow_right == 0 and shadow_bottom == 0:
        shadow_space = [(x, y, width, depth)]
    else:
        shadow_space = [(x - shadow_top, y - shadow_left, width + shadow_left + shadow_right, depth + shadow_top + shadow_bottom)]
    object_space = [(x, y, width, depth)]
     
    for rect in placed_rects:
        rx = rect["object"].position[0]
        ry = rect["object"].position[1]
        r_width = rect["object"].width
        r_depth = rect["object"].depth
        r_height = rect["object"].height
        r_shadow = rect["object"].shadow
        r_wall = rect["object"].wall

        rect_sizes = (rx, ry, r_width, r_depth,r_height)
        
        r_top_shadow, r_left_shadow, r_right_shadow, r_bottom_shadow= r_shadow
        # convert values
        rx, ry, r_width, r_depth, r_height = rect_sizes
        if r_top_shadow == 0 and r_left_shadow == 0 and r_right_shadow == 0 and r_bottom_shadow == 0:
            r_shadow_space = [(rx, ry, r_width, r_depth)]
        else:
            r_shadow_space = [(rx - r_top_shadow, ry - r_left_shadow, r_width + r_left_shadow + r_right_shadow, r_depth + r_top_shadow + r_bottom_shadow)]
        r_object_space = [(rx, ry, r_width, r_depth)]

        
        # check if the actual objects overlap (STRICT)
        if check_overlap(object_space[0], r_object_space[0]):
            return False  # Objects themselves overlap → INVALID
        # check if the new object's shadow overlaps an existing OBJECT (STRICT) 
        if check_overlap(shadow_space[0], r_object_space[0]):
            return False
        # check if the existing object's shadow overlaps the new object
        if check_overlap(r_shadow_space[0], object_space[0]):
            return False
        # # check if not enough space for object
        # r_vectors = []
        # vectors = []
        # min_distance = 60
        # if (r_wall == "top-left" and wall == "top-right") or (r_wall == "bottom-right" and wall == "bottom-left") or (r_wall == "top-right" and wall == "top-left") or (r_wall == "bottom-left" and wall == "bottom-right"):
        #     return True
        # # if not in corner and not against same wall
        # elif (r_wall not in wall or wall not in r_wall):
        #     r_vectors.extend([
        #         (x, y),                # Top-left
        #         (x + depth, y),        # Top-right
        #         (x, y + width),        # Bottom-left
        #         (x + depth, y + width) # Bottom-right
        #     ])
        #     vectors.extend([
        #         (rx, ry),                # Top-left
        #         (rx + r_depth, ry),        # Top-right
        #         (rx, ry + r_width),        # Bottom-left
        #         (rx + r_depth, ry + r_width) # Bottom-right
        #     ])
        #     for i in range(len(vectors)):
        #         for j in range(len(r_vectors)):
        #             distance = np.sqrt((vectors[i][0] - r_vectors[j][0])**2 + (vectors[i][1] - r_vectors[j][1])**2)
        #             if distance < min_distance:
        #                 return False
    



    
    return True  # Placement is valid
def check_opposite_walls_distance(placed_objects, room_sizes, min_distance=60):
    """
    Check that objects placed on opposite walls have at least min_distance space between them.
    This ensures sufficient clearance for movement between opposite fixtures.
    
    Args:
        placed_objects: List of objects with positions and dimensions (x, y, width, depth, height, name, ...)
        room_sizes: Tuple of (room_width, room_depth)
        min_distance: Minimum distance required between opposite objects in cm (default: 60cm)
        
    Returns:
        tuple: (bool, list) - Boolean indicating if all objects meet the distance requirement,
               and a list of tuples containing the indices, names and actual distances of problematic object pairs
    """
    room_width, room_depth, room_height = room_sizes
    violations = []
    
    # Define the walls
    WALL_LEFT = 0    # x = 0
    WALL_RIGHT = 1   # x = room_depth
    WALL_TOP = 2     # y = 0
    WALL_BOTTOM = 3  # y = room_width
    
    # Group objects by the walls they're adjacent to
    wall_objects = {WALL_LEFT: [], WALL_RIGHT: [], WALL_TOP: [], WALL_BOTTOM: []}
    
    # Threshold for considering an object to be against a wall (in cm)
    wall_threshold = 5  # objects within 5cm of wall are considered adjacent to the wall
    # Assign objects to walls
    for i, obj in enumerate(placed_objects):
        obj = obj['object']
        x, y = obj.position[:2]
        width, depth = obj.width, obj.depth
        height = obj.height
        name = obj.name
        wall = obj.wall.lower()
        if wall == "left":
            wall_objects[WALL_LEFT].append((i, obj))
        elif wall == "right":
            wall_objects[WALL_RIGHT].append((i, obj))
        elif wall == "top":
            wall_objects[WALL_TOP].append((i, obj))
        elif wall == "bottom":
            wall_objects[WALL_BOTTOM].append((i, obj))
        elif wall == "bottom-left":
            if width > depth:
                wall_objects[WALL_BOTTOM].append((i, obj))
            elif width == depth:
                wall_objects[WALL_BOTTOM].append((i, obj))
                wall_objects[WALL_LEFT].append((i, obj))
            else:
                wall_objects[WALL_LEFT].append((i, obj))
        elif wall == "bottom-right":

            if width > depth:
                wall_objects[WALL_BOTTOM].append((i, obj))
            elif width == depth:
                wall_objects[WALL_BOTTOM].append((i, obj))
                wall_objects[WALL_RIGHT].append((i, obj))
            else:
                wall_objects[WALL_RIGHT].append((i, obj))
        elif wall == "top-left":
            if width > depth:
                wall_objects[WALL_TOP].append((i, obj))
            elif width == depth:
                wall_objects[WALL_TOP].append((i, obj))
                wall_objects[WALL_LEFT].append((i, obj))
            else:
                wall_objects[WALL_LEFT].append((i, obj))
        elif wall == "top-right":
            if width > depth:
                wall_objects[WALL_TOP].append((i, obj))
            elif width == depth:

                wall_objects[WALL_TOP].append((i, obj))
                wall_objects[WALL_RIGHT].append((i, obj))
            else:
                wall_objects[WALL_RIGHT].append((i, obj))
    
    # Check distance between objects on opposite walls
    # Left vs Right wall
    for left_idx, left_obj in wall_objects[WALL_LEFT]:
        
        left_x = left_obj.position[0]
        left_y = left_obj.position[1]
        left_width = left_obj.width
        left_depth = left_obj.depth
        left_height = left_obj.height
        left_name = left_obj.name
        left_wall = left_obj.wall.lower()
        left_shadow = left_obj.shadow
        
        for right_idx, right_obj in wall_objects[WALL_RIGHT]:
           
            right_x = right_obj.position[0]
            right_y = right_obj.position[1]
            right_width = right_obj.width
            right_depth = right_obj.depth
            right_height = right_obj.height
            right_name = right_obj.name
            right_wall = right_obj.wall.lower()
            right_shadow = right_obj.shadow
            
            if (left_x <= right_x + right_depth and left_x + left_depth >= right_x):
                # Calculate the distance between the objects in the x-direction
                distance = right_y - (left_y + left_width)
                if distance < min_distance:
                    violations.append((left_idx, right_idx, left_name, right_name, distance))
                    # print(f"Opposite walls distance violations:                   ")
                    # for left_idx, right_idx, left_name, right_name, distance in violations:
                    #     print(f"  - {left_name}(#{left_idx}) <-> {right_name}(#{right_idx}): {distance:.1f}cm (below 60cm minimum)")
    
    # Top vs Bottom wall
    for top_idx, top_obj in wall_objects[WALL_TOP]:
        
        top_x, top_y = top_obj.position[:2]
        top_width, top_depth = top_obj.width, top_obj.depth
        top_name = top_obj.name
        top_wall = top_obj.wall.lower()
        
        for bottom_idx, bottom_obj in wall_objects[WALL_BOTTOM]:
            bottom_x, bottom_y = bottom_obj.position[:2]
            bottom_width, bottom_depth = bottom_obj.width, bottom_obj.depth
            bottom_name = bottom_obj.name
            bottom_wall = bottom_obj.wall.lower()
            if (top_y <= bottom_y + bottom_width and top_y + top_width >= bottom_y):
                # Calculate the distance between the objects in the x-direction
                distance = bottom_x - (top_x + top_depth)
                if distance < min_distance:
                    violations.append((top_idx, bottom_idx, top_name, bottom_name, distance))
                    # print(f"Opposite walls distance violations:                   ")
                    # for top_idx, bottom_idx, top_name, bottom_name, distance in violations:
                    #     print(f"  - {top_name}(#{top_idx}) <-> {bottom_name}(#{bottom_idx}): {distance:.1f}cm (below 60cm minimum)")
    
    return len(violations) == 0, violations

# def identify_available_space(layouts, room_sizes, grid_size=1, windows_doors=[]):
#     """
#     Identifies available space in a room after objects have been placed.
#     Returns both with and without shadow.
#     Args:
#         layouts (list): List of layouts.
#         room_sizes (tuple): Room dimensions as (width, depth).
#         grid_size (int): Size of the grid cell in cm.
#         windows_doors (list): List of windows and doors.
#     Returns:
#         dict: {'with_shadow': [...], 'without_shadow': [...]} available spaces as (x, y, width, depth) tuples.
#     """
#     windows_doors = windows_doors
#     def _find_spaces(include_shadows):
#         room_width, room_depth = room_sizes
#         grid_width = room_width // grid_size 
#         grid_depth = room_depth // grid_size 
#         grid = [[1 for _ in range(grid_depth)] for _ in range(grid_width)]
#         # Mark occupied spaces
#         # extract layouts to layout list
#         for obj in layouts:

#             i = 0
#             while i < len(obj):

#                 name = obj[i]['object'].name
#                 width = obj[i]['object'].width
#                 depth = obj[i]['object'].depth
#                 height = obj[i]['object'].height
#                 shadow = obj[i]['object'].shadow
#                 position = obj[i]['object'].position
#                 wall = obj[i]['object'].wall
#                 x,y = position
#                 shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
                
#                 if include_shadows:
#                     start_x = max(0, (x - shadow_top) // grid_size)
#                     start_y = max(0, (y - shadow_left) // grid_size)
#                     end_x = min(grid_width, (x + depth + shadow_bottom) // grid_size )
#                     end_y = min(grid_depth, (y + width + shadow_right) // grid_size )
#                 else:
#                     start_x = max(0, x // grid_size)
#                     start_y = max(0, y // grid_size)
#                     end_x = min(grid_width, (x + depth) // grid_size )
#                     end_y = min(grid_depth, (y + width) // grid_size )
#                 for i in range(start_x, end_x):
#                     for j in range(start_y, end_y):
#                         grid[i][j] = 0
#                 i += 1
#         if include_shadows:
#             wall = windows_doors.wall
#             x = windows_doors.position[0]
#             y = windows_doors.position[1]
#             width = windows_doors.width
#             start_x = max(0, (x ) // grid_size)
#             start_y = max(0, (y) // grid_size)
#             end_x = min(grid_width, (x + width) // grid_size )
#             end_y = min(grid_depth, (y + width) // grid_size )
#             if wall == "right":
#                 end_y = start_y
#                 start_y = start_y - width
#             if wall == "bottom":
#                 end_x = start_x
#                 start_x = start_x - width
#             for i in range(start_x, end_x):
#                 for j in range(start_y, end_y):
#                     grid[i][j] = 0
#         available_spaces = []
#         visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
#         for i in range(grid_width):
#             for j in range(grid_depth):
#                 if grid[i][j] == 1 and not visited[i][j]:
#                     space = find_contiguous_space(grid, visited, i, j, grid_width, grid_depth)
#                     x = space["start_x"] * grid_size
#                     y = space["start_y"] * grid_size
#                     width = (space["end_y"] - space["start_y"]) * grid_size
#                     depth = (space["end_x"] - space["start_x"]) * grid_size
#                     if width >= 30 and depth >= 30:
#                         available_spaces.append((x, y, width, depth))
#         # closed = check_enclosed_spaces(grid, grid_size, room_width, room_depth)
#         # if closed:
#         #     st.warning("Warning: The available space in the room is not convex. This may affect optimal object placement.")
#         return available_spaces
#     return {
#         'with_shadow': _find_spaces(True),
#         'without_shadow': _find_spaces(False)
#     }


# without sink the room is invalid
def check_valid_room(placed_obj):
    """Check if the room is valid."""
    for obj in placed_obj:
        name = obj[5]
        if name == "sink" or name == "Sink" or name == "double sink" or name =="Double Sink":
            return True
    print("No sink in the room")
    return False

def extract_object_based_on_type(obj):

    # Initialize default values
    x, y = 0, 0
    width, depth = 0, 0
    height = 0
    obj_name = ''
    shadow = [0, 0, 0, 0]  # Default shadow
    
    # Extract object properties based on type
    if hasattr(obj, 'position') and hasattr(obj, 'object'):
        # It's an object with attributes
        x, y = obj.position if obj.position else (0, 0)
        width, depth = obj.object.width, obj.object.depth
        height = getattr(obj.object, 'height', 0)  # Use getattr with default
        obj_name = getattr(obj.object, 'name', '')  # Use getattr with default
        shadow = getattr(obj, 'shadow', [0, 0, 0, 0])  # Use getattr with default

    elif isinstance(obj, dict):
        # It's a dictionary
        if 'position' in obj and isinstance(obj['position'], (list, tuple)):
            # Position contains all properties
            position = obj['position']
            object = obj['object']
            if len(position) >= 6:
                x, y = position[:2]
                width, depth = position[2:4]
                height = position[4]
                obj_name = object.name
                shadow = position[5]
            elif len(position) >= 2:
                # Handle case with just position
                x, y = position[:2]

            
        else:
            # Direct properties in dictionary
            x = obj.get('x', 0)
            y = obj.get('y', 0)
            width = obj.get('width', 0)
            depth = obj.get('depth', 0)
            height = obj.get('height', 0)
            obj_name = obj.get('name', '')
            shadow = obj.get('shadow', [0, 0, 0, 0])
    elif isinstance(obj, (list, tuple)):
        # It's a tuple with properties
        if len(obj) >= 9:
            x, y = obj[0], obj[1]
            width, depth = obj[2], obj[3]
            height = obj[4]
            obj_name = obj[5]
            shadow = obj[8]
        elif len(obj) >= 6:
            x, y = obj[0], obj[1]
            width, depth = obj[2], obj[3]
            height = obj[4]
            obj_name = obj[5]
        elif len(obj) >= 5:
            x, y = obj[0], obj[1]
            width, depth = obj[2], obj[3]
            height = obj[4]
        elif len(obj) >= 4:
            x, y = obj[0], obj[1]
            width, depth = obj[2], obj[3]
    
    # Ensure shadow is a list or tuple with at least 4 elements
    if not isinstance(shadow, (list, tuple)) or len(shadow) < 4:
        shadow = [0, 0, 0, 0]
        
    return x, y, width, depth, height, obj_name, shadow

def extract_door_window_based_on_type(obj):

    # Initialize default values
    x, y = 0, 0
    width, depth, height = 0, 0, 0
    wall = ''
    
    # Extract object properties based on type
    if hasattr(obj, 'position') and hasattr(obj, 'width'):
        # It's a WindowsDoors object with attributes
        if isinstance(obj.position, (list, tuple)) and len(obj.position) >= 2:
            x, y = obj.position[0], obj.position[1]
        else:
            # Handle case where position might be a single value or not a tuple/list
            x = obj.position if not isinstance(obj.position, (list, tuple)) else 0
            y = 0
        
        width = getattr(obj, 'width', 0)
        depth = getattr(obj, 'depth', 0)
        height = getattr(obj, 'height', 0)
        wall = getattr(obj, 'wall', '')
    elif isinstance(obj, (list, tuple)):
        # It's a tuple with elements
        if len(obj) >= 7:
            # Format: [type, wall, x, y, width, depth, height]
            _, wall, x, y, width, depth, height = obj[:7]
        elif len(obj) >= 6:
            # Format might be [x, y, width, depth, height, wall]
            x, y, width, depth, height, wall = obj[:6]
        elif len(obj) >= 5:
            # Format might be [x, y, width, depth, height]
            x, y, width, depth, height = obj[:5]
            wall = ''
    elif isinstance(obj, dict):
        # It's a dictionary
        if 'position' in obj and isinstance(obj['position'], (list, tuple)) and len(obj['position']) >= 2:
            x, y = obj['position'][0], obj['position'][1]
        else:
            x = obj.get('x', 0)
            y = obj.get('y', 0)
        
        width = obj.get('width', 0)
        depth = obj.get('depth', 0)
        height = obj.get('height', 0) 
        wall = obj.get('wall', '')
    
    # Ensure all values are valid
    x = float(x) if x is not None else 0
    y = float(y) if y is not None else 0
    width = float(width) if width is not None else 0
    depth = float(depth) if depth is not None else 0
    height = float(height) if height is not None else 0
    wall = str(wall) if wall is not None else ''
    
    return x, y, width, depth, height, wall

def get_object_def(obj_type):
    return OBJECT_TYPES[obj_type]

# calculate the space behind the door "hidden space"
def calculate_behind_door_space(door_x, door_y, door_width, door_depth, door_wall,hinge,room_width, room_depth):
    hinge = hinge.lower()
    if door_wall == "top" and hinge == "left" or door_wall == "bottom" and hinge == "right":
        behind_door_space = (0, door_y+door_width, room_depth, room_width)
        return behind_door_space
    elif door_wall == "bottom" and hinge == "left" or door_wall == "top" and hinge == "right":
        behind_door_space = (0,0,  door_y, room_width)
        return behind_door_space
    elif door_wall == "left" and hinge == "left" or door_wall == "right" and hinge == "right":
        behind_door_space = (0,0, room_depth, door_x)
        return behind_door_space
    elif door_wall == "right" and hinge == "left" or door_wall == "left" and hinge == "right":
        behind_door_space = (door_x + door_width,0, room_depth, room_width)
        return behind_door_space
def calculate_before_door_space(door_x, door_y, door_width, door_depth, door_wall,hinge,room_width, room_depth):
    hinge = hinge.lower()
    if door_wall == "top":
        before_door_space = (door_x+door_width, door_y, door_width, door_width)
        return before_door_space
    elif door_wall == "bottom":
        before_door_space = (door_x-door_width,door_y,  door_width, door_width)
        return before_door_space
    elif door_wall == "left" :
        before_door_space = (door_x,door_y+door_width, door_width, door_width)
        return before_door_space
    elif door_wall == "right" :
        before_door_space = (door_x,door_y-door_width, room_width, room_width)
        return before_door_space 
def generate_random_position(wall,room_width,room_depth,obj_width,obj_depth):
    positions = []
    if wall == "top":
        positions.append((0,0,"top"))
        i = 1
        while room_depth-obj_width >= i*5:
            positions.append((0,i*5,"top"))
            i += 1
    elif wall == "bottom":
        positions.append((room_width-obj_depth,0,"bottom"))
        i = 1
        while room_depth-obj_width >= i*5:
            positions.append((room_width-obj_depth,i*5,"bottom"))
            i += 1
    elif wall == "left":
        positions.append((0,0,"left"))
        i = 1
        while room_width-obj_width >= i*5:
            positions.append((i*5,0,"left"))
            i += 1
    elif wall == "right":
        positions.append((0,room_depth-obj_depth,"right"))
        i = 1
        while room_width-obj_width >= i*5:
            positions.append((i*5,room_depth-obj_depth,"right"))
            i += 1
    
    return positions
    
def windows_doors_overlap(windows_doors, x, y, z, width, depth, height, room_width, room_depth, shadow_space,obj_type):
    new_rect = (x, y, width, depth)
    object_space = [(x, y, width, depth)]

    door_shadow=75
    isValid = False
    name = ""
    if isinstance(windows_doors, list):
        for wd in windows_doors:
            name = wd.name
            wx = wd.position[0]
            wy = wd.position[1]
            wwidth = wd.width
            wheight = wd.height
            way = wd.way
            hinge = wd.hinge
            wall = wd.wall
    else:
        name = windows_doors.name
        wx = windows_doors.position[0]
        wy = windows_doors.position[1]
        wwidth = windows_doors.width
        wheight = windows_doors.height
        way = windows_doors.way
        hinge = windows_doors.hinge
        wall = windows_doors.wall
    # Only check shadow for doors
    if "door" in name.lower():
        # Calculate shadow area based on door position
        if wall == "top":
            shadow_rect = (wx,wy, wwidth, door_shadow)
        elif wall == "bottom":
            shadow_rect = (wx-door_shadow,wy, wwidth, door_shadow)
        elif wall == "left":
            shadow_rect = (wx , wy, door_shadow, wwidth)
        elif wall == "right":
            shadow_rect = (wx,room_depth-door_shadow,door_shadow, wwidth)
        if check_overlap(shadow_rect, object_space[0]):
            return True
        if "toilet" in obj_type.lower():
            behind_door_space = calculate_behind_door_space(wx, wy, wwidth, wheight, wall,hinge,room_width, room_depth)

            if check_overlap(behind_door_space, object_space[0]):
                overlap = calculate_overlap_area(behind_door_space, object_space[0])
                if overlap < room_width * room_depth - 3600:
                    return False
                else:
                    return True
     
    if "window" in name.lower():
        # Check if one rectangle is to the left of the other
        if not(wx + wwidth <= x or x + width <= wx):
            return True
        # Check if one rectangle is above the other
        if not(wy + wheight <= y or y + depth <= wy):
            return True

    return False


# def check_enclosed_spaces(grid, grid_size, room_width, room_depth, min_path_width=50):
#     """
#     Check if there are any enclosed spaces in the room that can't be reached by a minimum width path.
    
#     Args:
#         grid (list): 2D grid representation of the room
#         grid_size (int): Size of grid cells in cm
#         room_width (int): Room width in cm
#         room_depth (int): Room depth in cm
#         min_path_width (int): Minimum required path width in cm (default: 50cm)
        
#     Returns:
#         bool: True if there are enclosed spaces, False otherwise
#     """
#     # Convert room dimensions to grid coordinates
#     grid_width = room_width // grid_size 
#     grid_depth = room_depth // grid_size 
#     # Create a copy of the grid to mark visited cells
#     visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
#     # Define minimum path width in grid cells
#     min_path_cells = min_path_width // grid_size
    
#     def is_accessible(x, y):
#         """Check if a cell is accessible and within bounds."""
#         return (0 <= x < grid_width and 0 <= y < grid_depth and 
#                 grid[x][y] == 0 and not visited[x][y])
    
#     def check_path_width(x, y):
#         """Check if there's enough width for the path."""
#         # Check horizontal width
#         for dx in range(-min_path_cells//2, min_path_cells//2 + 1):
#             nx = x + dx
#             if 0 <= nx < grid_width and grid[nx][y] == 1:
#                 return False
#         # Check vertical width
#         for dy in range(-min_path_cells//2, min_path_cells//2 + 1):
#             ny = y + dy
#             if 0 <= ny < grid_depth and grid[x][ny] == 1:
#                 return False
#         return True
    
#     def dfs(x, y):
#         """Depth-first search to mark accessible areas."""
#         stack = [(x, y)]
#         while stack:
#             x, y = stack.pop()
#             if not is_accessible(x, y) or not check_path_width(x, y):
#                 continue
            
#             visited[x][y] = True
            
#             # Add neighbors to stack
#             for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
#                 nx, ny = x + dx, y + dy
#                 if is_accessible(nx, ny):
#                     stack.append((nx, ny))
    
#     # Start DFS from the room entrances (typically along walls)
#     for x in range(grid_width):
#         if grid[x][0] == 0:
#             dfs(x, 0)
#         if grid[x][grid_depth-1] == 0:
#             dfs(x, grid_depth-1)
    
#     for y in range(grid_depth):
#         if grid[0][y] == 0:
#             dfs(0, y)
#         if grid[grid_width-1][y] == 0:
#             dfs(grid_width-1, y)
    
#     # Check if there are any unvisited empty spaces
#     for x in range(grid_width):
#         for y in range(grid_depth):
#             if grid[x][y] == 0 and not visited[x][y]:
#                 return True  # Found an enclosed space

def has_free_side(rect, objects, min_clearance=60):
    """
    shower: (x, y, w, h)
    objects: list of (x, y, w, h, name)
    min_clearance: opcionális, alapból w/2 vagy h/2
    """
    x, y, w, d = rect
    clearance = min_clearance

    # Függvény az ütközés ellenőrzésére
    def intersects(a, b):
        ax, ay, aw, ad = a
        bx, by, bw, bd = b
        return not (ax+ad <= bx or bx+bd <= ax or ay+aw <= by or by+bw <= ay)

    # Ellenőrizni kell minden oldalra
    directions = {
        "left":   (x, y-clearance, clearance, d),
        "right":  (x, y+w, clearance, d),
        "top":    (x-clearance, y, w, clearance),
        "bottom": (x+d, y, w, clearance),
    }
    i = 0
    for side, area in directions.items():
        blocked = False

        for ox, oy, ow, od in objects:
            if intersects(area, (ox, oy, ow, od)):
                # ha a blokk mélysége >= shower mélysége → blokkolt
                if od >= d/2 and ow >= w/2:
                    blocked = True
                    break
                elif od >= d/2 and (i ==0 or i ==1):
                    blocked = True
                    break
                elif ow >= w/2 and (i ==2 or i ==3):
                    blocked = True
                    break
                
            i += 1      
        if not blocked:
            return True  # legalább egy oldal szabad

    return False
