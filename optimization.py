from utils import check_which_wall,check_distance,adjust_object_placement, check_distance_from_wall, convert_values, adjust_object_placement_pos, is_valid_placement


def optimization(placed_obj, room_sizes):
    room_width, room_depth = room_sizes
    # loop through objects to check if they can be replaced
    extracted_positions = [(item[0], item[1], item[2], item[3], item[-1]) for item in placed_obj]

    for i,obj in enumerate(placed_obj):
        x,y,width,depth,height, _1,_2,_3,shadow = obj
        shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
        # check which wall the object is on
        wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        
        # if wall string contains - then it is a corner
        if wall not in ["top-left", "top-right", "bottom-left", "bottom-right"]:
        # check the distance from the walls perendicular to the wall the object is on
            dist_top,dist_left,dist_right,dist_bottom = check_distance_from_wall((x,y,width,depth), room_width, room_depth, wall,shadow)
            # create dictionary
            dist = {"top":dist_top, "left":dist_left, "right":dist_right, "bottom":dist_bottom}
            # select the wall key with the smallest value
            wall_side,min_dist = min(dist.items(), key=lambda x: x[1])
            
            if min_dist < 30:

                # convert values
                conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values((x,y,width,depth), shadow, wall)
                # adjust object placement
                new_x,new_y = adjust_object_placement_pos((conv_x,conv_y,conv_width,conv_depth), (conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom), room_width, room_depth, wall_side)
                # Create a new list excluding the current object
                other_positions = extracted_positions[:i] + extracted_positions[i+1:]
                
                if is_valid_placement((new_x,new_y,width,depth), other_positions, shadow, room_width, room_depth):
                    # update placed objects
                    del placed_obj[i]

                    placed_obj.insert(i, (new_x, new_y, width, depth, height, _1, _2, _3, shadow))
            ## TODO kiterjesztés méretnövelés

    return placed_obj
        
# optimize only one object  
def optimize_object (rect, shadow, room_width, room_depth, placed_obj):
    rect_wall = check_which_wall(rect, room_width, room_depth)
    x_rect, y_rect, width_rect, depth_rect = rect
    rect_top, rect_left, rect_right, rect_bottom = shadow
    
    conv_rect = convert_values(rect, shadow, rect_wall)
    for i,obj in enumerate(placed_obj):
        x,y,width,depth,height, _1,_2,_3,shadow = obj
        shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
        wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        conv_placed_obj = convert_values((x,y,width,depth), shadow, wall)
        # if rect wall and wall contains the same wall  name
        if rect_wall in wall or wall in rect_wall:
            # check the distance of the objects from each other
            dist,rect_smaller = check_distance(conv_rect, conv_placed_obj)
            if dist < 50 and dist > 0:

                if (rect_smaller):
                    new_x,new_y = adjust_object_placement(conv_rect,  room_width, room_depth, rect_wall, dist)
                elif not(rect_smaller):
                    new_x,new_y = adjust_object_placement(conv_rect,  room_width, room_depth, wall, -dist)
                # Create a new list 
                extracted_positions = [(item[0], item[1], item[2], item[3], item[-1]) for item in placed_obj]
                
                if is_valid_placement((new_x,new_y,width_rect,depth_rect),extracted_positions, (rect_top, rect_left, rect_right, rect_bottom), room_width, room_depth):
                    # update placed objects
                    x_rect = new_x
                    y_rect = new_y
                    break
    return (x_rect,y_rect, width_rect, depth_rect)




def identify_available_space(placed_obj, room_sizes, include_shadows=False, grid_size=10, windows_doors=[]):
    """
    Identifies available space in a room after objects have been placed.
    
    Args:
        placed_obj (list): List of placed objects with their positions, dimensions, and shadows.
            Each object is a tuple (x, y, width, depth, height, _1, _2, _3, shadow).
        room_sizes (tuple): Room dimensions as (width, depth).
        include_shadows (bool): Whether to consider shadow areas as occupied space.
            Default is False (shadows are not considered occupied).
    
    Returns:
        list: List of available spaces as (x, y, width, depth) tuples.
    """
    room_width, room_depth = room_sizes
    
    # Create a grid representation of the room
    # Using a grid size of 10 cm for reasonable accuracy and performance
    grid_width = room_width // grid_size 
    grid_depth = room_depth // grid_size 
    
    # Initialize grid with all cells available (1 = available, 0 = occupied)
    grid = [[1 for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Mark occupied spaces
    for obj in placed_obj:
        x, y, width, depth, height, _1, _2, _3, shadow = obj
        # convert shadow values
        x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom = convert_values((x,y,width,depth), shadow, check_which_wall((x,y,width,depth), room_width, room_depth))
        if include_shadows:
            # Include shadow areas as occupied space
            print("name", obj[5])
            print(shadow_top, shadow_left, shadow_right, shadow_bottom)

            # Calculate the extended area including shadow
            start_x = max(0, (x - shadow_top) // grid_size)
            start_y = max(0, (y - shadow_left) // grid_size)
            end_x = min(grid_width, (x + depth + shadow_bottom) // grid_size )
            end_y = min(grid_depth, (y + width + shadow_right) // grid_size )
        else:
            # Only consider the actual object area as occupied
            start_x = max(0, x // grid_size)
            start_y = max(0, y // grid_size)
            end_x = min(grid_width, (x + depth) // grid_size )
            end_y = min(grid_depth, (y + width) // grid_size )
        
        # Mark the area as occupied
        for i in range(start_x, end_x):
            for j in range(start_y, end_y):
                grid[i][j] = 0
    for i in windows_doors:
        id_, wall, x, y,  width,height, parapet = i
        
        # Calculate the extended area including shadow
        start_x = max(0, (x ) // grid_size)
        start_y = max(0, (y) // grid_size)
        end_x = min(grid_width, (x + width) // grid_size )
        end_y = min(grid_depth, (y + 75) // grid_size )
        
        # Mark the area as occupied
        for i in range(start_x, end_x):
            for j in range(start_y, end_y):
                grid[i][j] = 0
    # Find contiguous available spaces
    available_spaces = []
    visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
    for i in range(grid_width):
        for j in range(grid_depth):
            if grid[i][j] == 1 and not visited[i][j]:
                # Found an available cell, expand to find the full available space
                space = find_contiguous_space(grid, visited, i, j, grid_width, grid_depth)
                
                # Convert back to room coordinates
                x = space["start_x"] * grid_size
                y = space["start_y"] * grid_size
                width = (space["end_y"] - space["start_y"]) * grid_size
                depth = (space["end_x"] - space["start_x"]) * grid_size
                
                # Only add spaces that are large enough to be useful (at least 30x30 cm)
                if width >= 30 and depth >= 30:
                    available_spaces.append((x, y, width, depth))
    
    return available_spaces

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

def suggest_placement_in_available_space(available_spaces, object_type, object_types_dict):
    """
    Suggests optimal placement for a new object in the available spaces.
    
    Args:
        available_spaces (list): List of available spaces as (x, y, width, depth) tuples.
        object_type (str): Type of object to place.
        object_types_dict (dict): Dictionary of object types with their size ranges.
    
    Returns:
        tuple: Suggested placement as (x, y, width, depth) or None if no suitable space.
    """
    if not available_spaces:
        return None
    
    # Find the object definition by name
    obj_def = None
    for key, value in object_types_dict.items():
        if value["name"] == object_type:
            obj_def = value
            break
    
    if obj_def is None:
        return None
    
    # First try with optimal size if available
    if "optimal_size" in obj_def:
        optimal_width = obj_def["optimal_size"][0]
        optimal_depth = obj_def["optimal_size"][1]
        
        # Try to place with optimal dimensions first
        best_space = find_best_space_for_size(available_spaces, optimal_width, optimal_depth)
        
        if best_space:
            return best_space
    
    # If optimal placement failed or no optimal size, try with size range
    min_width, max_width = obj_def["size_range"][0], obj_def["size_range"][1]
    min_depth, max_depth = obj_def["size_range"][2], obj_def["size_range"][3]
    
    return find_best_space_for_size(available_spaces, min_width, max_width, min_depth, max_depth)

def find_best_space_for_size(available_spaces, width, depth, min_width=None, min_depth=None):
    """
    Finds the best space for an object with the given dimensions.
    
    Args:
        available_spaces (list): List of available spaces as (x, y, width, depth) tuples.
        width (int): Preferred width of the object.
        depth (int): Preferred depth of the object.
        min_width (int, optional): Minimum acceptable width. If None, uses width as minimum.
        min_depth (int, optional): Minimum acceptable depth. If None, uses depth as minimum.
    
    Returns:
        tuple: Suggested placement as (x, y, width, depth) or None if no suitable space.
    """
    if min_width is None:
        min_width = width
    if min_depth is None:
        min_depth = depth
    
    best_space = None
    best_fit_score = float('inf')  # Lower is better (less wasted space)
    
    for space in available_spaces:
        space_x, space_y, space_width, space_depth = space
        
        # Try both orientations of the object
        orientations = [
            (width, depth),  # Normal orientation
            (depth, width)   # Rotated 90 degrees
        ]
        
        for obj_width, obj_depth in orientations:
            # Check if the space is large enough for the object
            if space_width >= obj_width and space_depth >= obj_depth:
                # Calculate fit score (lower is better)
                # This prioritizes spaces that are closer to the object's size
                wasted_width = space_width - obj_width
                wasted_depth = space_depth - obj_depth
                fit_score = wasted_width + wasted_depth
                
                if fit_score < best_fit_score:
                    best_fit_score = fit_score
                    best_space = (space_x, space_y, obj_width, obj_depth)
            
            # If exact size doesn't fit, try with minimum dimensions
            elif space_width >= min_width and space_depth >= min_depth:
                # Use the maximum possible dimensions that fit in this space
                adjusted_width = min(space_width, obj_width)
                adjusted_depth = min(space_depth, obj_depth)
                
                # Calculate fit score with a penalty for size reduction
                wasted_width = space_width - adjusted_width
                wasted_depth = space_depth - adjusted_depth
                size_reduction_penalty = (obj_width - adjusted_width) + (obj_depth - adjusted_depth)
                fit_score = wasted_width + wasted_depth + size_reduction_penalty * 2  # Extra penalty for size reduction
                
                if fit_score < best_fit_score:
                    best_fit_score = fit_score
                    best_space = (space_x, space_y, adjusted_width, adjusted_depth)
    
    return best_space

def add_objects_to_available_spaces(placed_objects, room_sizes, object_types_dict, priority_objects=None, available_spaces=None):
    """
    Identifies available spaces and automatically adds new objects that fit in those spaces.
    
    Args:
        placed_objects (list): List of placed objects with their positions, dimensions, and shadows.
            Each object is a tuple (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow).
        room_sizes (tuple): Room dimensions as (width, depth).
        object_types_dict (dict): Dictionary of object types with their specifications.
        priority_objects (list, optional): List of object types to prioritize for placement.
            If None, will try to place any object that fits.
    
    Returns:
        tuple: (updated_objects, added_objects)
            - updated_objects: List of all objects including newly added ones
            - added_objects: List of only the newly added objects
    """
    
    if not available_spaces:
        return placed_objects, []
    
    # Get list of objects already placed
    placed_object_types = [obj[5] for obj in placed_objects]
    
    # Get all available object types by name
    object_names = [value["name"] for value in object_types_dict.values()]
    
    # Determine which objects to try placing
    if priority_objects:
        # Filter priority objects to only include those not already placed
        objects_to_try = [obj for obj in priority_objects if obj not in placed_object_types]
    else:
        # Try all objects not already placed
        objects_to_try = [obj_type for obj_type in object_names 
                         if obj_type not in placed_object_types]
    
    # Create a mapping of object names to their optimal sizes for sorting
    object_sizes = {}
    for key, value in object_types_dict.items():
        object_name = value["name"]
        if "optimal_size" in value:
            object_sizes[object_name] = value["optimal_size"][0] * value["optimal_size"][1]
        else:
            # If optimal_size is not available, use the average of size_range
            width_avg = (value["size_range"][0] + value["size_range"][1]) / 2
            depth_avg = (value["size_range"][2] + value["size_range"][3]) / 2
            object_sizes[object_name] = width_avg * depth_avg
    
    # Sort objects by size (smallest first to maximize space utilization)
    objects_to_try.sort(key=lambda x: object_sizes.get(x, float('inf')))
    
    added_objects = []
    updated_objects = placed_objects.copy()
    
    # Keep track of spaces that have been used
    used_spaces = []
    
    # Try to place each object type
    for obj_type in objects_to_try:
        # Find object definition by name
        obj_def = None
        for key, value in object_types_dict.items():
            if value["name"] == obj_type:
                obj_def = value
                break
        
        if obj_def is None:
            continue
        
        # Get object specifications
        shadow = obj_def["shadow_space"]
        
        # Filter available spaces to exclude already used ones
        remaining_spaces = [space for i, space in enumerate(available_spaces) 
                           if i not in used_spaces]
        
        # Find best placement for this object
        placement = None
        
        # Handle special placement requirements
        if obj_def["must_be_corner"]:
            # For corner objects, filter spaces that include corners
            corner_spaces = []
            for space in remaining_spaces:
                space_x, space_y, space_width, space_depth = space
                # Check if space includes any corner
                if (space_x == 0 and space_y == 0) or \
                   (space_x == 0 and space_y + space_width == room_sizes[1]) or \
                   (space_x + space_depth == room_sizes[0] and space_y == 0) or \
                   (space_x + space_depth == room_sizes[0] and space_y + space_width == room_sizes[1]):
                    corner_spaces.append(space)
            
            if corner_spaces:
                # Find best placement in corner spaces
                placement = suggest_placement_in_available_space(
                    corner_spaces, obj_type, object_types_dict
                )
                
                # Adjust placement to be exactly in the corner
                if placement:
                    x, y, width, depth = placement
                    # Determine which corner and adjust accordingly
                    if x == 0 and y == 0:  # Top-left corner
                        pass  # Already in corner
                    elif x == 0 and y + width >= room_sizes[1] - 10:  # Top-right corner
                        y = room_sizes[1] - width
                    elif x + depth >= room_sizes[0] - 10 and y == 0:  # Bottom-left corner
                        x = room_sizes[0] - depth
                    elif x + depth >= room_sizes[0] - 10 and y + width >= room_sizes[1] - 10:  # Bottom-right corner
                        x = room_sizes[0] - depth
                        y = room_sizes[1] - width
                    
                    placement = (x, y, width, depth)
        
        elif obj_def["must_be_against_wall"]:
            # For wall objects, filter spaces that include walls
            wall_spaces = []
            for space in remaining_spaces:
                space_x, space_y, space_width, space_depth = space
                # Check if space includes any wall
                if space_x == 0 or space_y == 0 or \
                   space_x + space_depth >= room_sizes[0] - 10 or \
                   space_y + space_width >= room_sizes[1] - 10:
                    wall_spaces.append(space)
            
            if wall_spaces:
                # Find best placement against walls
                placement = suggest_placement_in_available_space(
                    wall_spaces, obj_type, object_types_dict
                )
                
                # Adjust placement to be exactly against a wall
                if placement:
                    x, y, width, depth = placement
                    # Determine which wall is closest and adjust accordingly
                    dist_to_top = x
                    dist_to_left = y
                    dist_to_bottom = room_sizes[0] - (x + depth)
                    dist_to_right = room_sizes[1] - (y + width)
                    
                    min_dist = min(dist_to_top, dist_to_left, dist_to_bottom, dist_to_right)
                    
                    if min_dist == dist_to_top:
                        x = 0  # Place against top wall
                    elif min_dist == dist_to_left:
                        y = 0  # Place against left wall
                    elif min_dist == dist_to_bottom:
                        x = room_sizes[0] - depth  # Place against bottom wall
                    elif min_dist == dist_to_right:
                        y = room_sizes[1] - width  # Place against right wall
                    
                    placement = (x, y, width, depth)
        
        # For regular objects, use standard placement
        if placement is None:
            placement = suggest_placement_in_available_space(
                remaining_spaces, obj_type, object_types_dict
            )
        
        if placement:
            x, y, width, depth = placement
            height = obj_def["optimal_size"][2]
            must_be_corner = obj_def["must_be_corner"]
            must_be_against_wall = obj_def["must_be_against_wall"]
            
            # Create new object
            new_object = (x, y, width, depth, height, obj_type, must_be_corner, must_be_against_wall, shadow)
            
            # Check if placement is valid considering all objects
            if is_valid_placement((x, y, width, depth), 
                                 [(o[0], o[1], o[2], o[3], o[8]) for o in updated_objects], 
                                 shadow, room_sizes[0], room_sizes[1]):
                
                # Add to our lists
                updated_objects.append(new_object)
                added_objects.append(new_object)
                
                # Mark the space as used
                for i, space in enumerate(available_spaces):
                    if space[0] <= x <= space[0] + space[2] and space[1] <= y <= space[1] + space[3]:
                        used_spaces.append(i)
                        break
    
    # Apply optimization to improve placement
    #if added_objects:
        #updated_objects = optimization(updated_objects, room_sizes)
    
    return updated_objects, added_objects

def suggest_additional_fixtures(placed_objects, room_sizes, object_types_dict, available_spaces):
    """
    Analyzes the current bathroom layout and suggests additional fixtures that could be added.
    
    Args:
        placed_objects (list): List of placed objects with their positions, dimensions, and shadows.
        room_sizes (tuple): Room dimensions as (width, depth).
        object_types_dict (dict): Dictionary of object types with their specifications.
        available_spaces (list): List of available spaces as (x, y, width, depth) tuples.
    
    Returns:
        dict: Dictionary with suggestions for additional fixtures and their potential placements.
    """
    print(placed_objects)
    # Get list of objects already placed
    placed_object_types = [obj[5] for obj in placed_objects]
    
    # Common bathroom fixtures to suggest
    common_fixtures = [
        "Toilet", "Sink", "Shower", "Bathtub", "Cabinet", 
        "Double Sink", "Washing Machine", "Washing Dryer"
    ]
    
    # Get all available object types by name
    object_names = [value["name"] for value in object_types_dict.values()]
    print(object_names)
    print(placed_object_types)
    # Filter to fixtures not already placed
    available_fixtures = [f for f in common_fixtures 
                         if f in object_names and f not in placed_object_types]

    suggestions = {}
    print(available_fixtures)
    for fixture in available_fixtures:
        placement = suggest_placement_in_available_space(
            available_spaces, fixture, object_types_dict
        )
        
        if placement:
            x, y, width, depth = placement
            suggestions[fixture] = {
                "position": (x, y),
                "dimensions": (width, depth),
                "space_efficiency": calculate_space_efficiency(placement, available_spaces)
            }
    
    if not suggestions:
        return {"message": "No suitable fixtures can be added to the available spaces"}
    
    return {
        "message": f"Found {len(suggestions)} potential fixtures to add",
        "suggestions": suggestions
    }

def calculate_space_efficiency(placement, available_spaces):
    """
    Calculates how efficiently a placement uses an available space.
    
    Args:
        placement (tuple): (x, y, width, depth) of the proposed placement
        available_spaces (list): List of available spaces
    
    Returns:
        float: Efficiency score between 0-1 (higher is better)
    """
    x, y, width, depth = placement
    placement_area = width * depth
    
    # Find which space this placement is in
    for space in available_spaces:
        space_x, space_y, space_width, space_depth = space
        
        # Check if placement is within this space
        if (space_x <= x < space_x + space_width and 
            space_y <= y < space_y + space_depth):
            
            space_area = space_width * space_depth
            return placement_area / space_area if space_area > 0 else 0
    
    return 0  # Not found in any space