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




def identify_available_space(placed_obj, room_sizes, include_shadows=False, grid_size=10):
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
        
        if include_shadows:
            # Include shadow areas as occupied space
            shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
            
            # Calculate the extended area including shadow
            start_x = max(0, (x - shadow_left) // grid_size)
            start_y = max(0, (y - shadow_top) // grid_size)
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
    if not available_spaces or object_type not in object_types_dict:
        return None
    
    # Get object size range
    obj_def = object_types_dict[object_type]
    min_width, max_width = obj_def["size_range"][0], obj_def["size_range"][1]
    min_depth, max_depth = obj_def["size_range"][2], obj_def["size_range"][3]
    
    best_space = None
    best_fit_score = float('inf')  # Lower is better (less wasted space)
    
    for space in available_spaces:
        space_x, space_y, space_width, space_depth = space
        
        # Check if the space is large enough for the minimum size
        if space_width >= min_width and space_depth >= min_depth:
            # Calculate optimal size for this space (not exceeding max dimensions)
            width = min(max_width, space_width)
            depth = min(max_depth, space_depth)
            
            # Calculate fit score (lower is better)
            # This prioritizes spaces that are closer to the object's size
            wasted_width = space_width - width
            wasted_depth = space_depth - depth
            fit_score = wasted_width + wasted_depth
            
            if fit_score < best_fit_score:
                best_fit_score = fit_score
                best_space = (space_x, space_y, width, depth)
    
    return best_space