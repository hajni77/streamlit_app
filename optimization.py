from utils import check_which_wall,check_distance,adjust_object_placement, check_distance_from_wall, convert_values, adjust_object_placement_pos, is_valid_placement, convert_shadows
import streamlit as st
from utils import is_corner_placement_sink, get_object_type, is_valid_placement_without_converting

def evaluate_room_layout(placed_objects, room_sizes, object_types_dict, windows_doors=None):
    """
    Evaluate the quality of a room layout based on various criteria.
    
    Args:
        placed_objects (list): List of placed objects [(x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)]
        room_sizes (tuple): Room dimensions (width, depth)
        object_types_dict (dict): Dictionary of object types with their specifications
        windows_doors (list): List of windows and doors in the room
        
    Returns:
        float: Overall score for the layout (0-100)
        dict: Detailed scores for each criterion
    """
    room_width, room_depth = room_sizes
    total_score = 0
    scores = {}
    
    # 1. Wall and Corner Constraints (30 points)
    wall_corner_score = 0
    for obj in placed_objects:
        x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        
        # Check wall placement
        if must_be_against_wall and wall not in ["top", "bottom", "left", "right"]:
            wall_corner_score = 0  # Zero points if wall constraint violated
            break
        elif not must_be_against_wall and wall in ["top", "bottom", "left", "right"]:
            wall_corner_score = 0  # Zero points if wall constraint violated
            break
            
        # Check corner placement
        if must_be_corner and not is_corner_placement_sink(x, y, room_width, room_depth, width, depth):
            wall_corner_score = 0  # Zero points if corner constraint violated
            break
            
    scores["wall_corner_constraints"] = wall_corner_score
    total_score += scores["wall_corner_constraints"]
    
    # 2. Sink Placement (10 points)
    sink_score = 0
    for obj in placed_objects:
        x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        if name == "Sink":
                wall = check_which_wall((x,y,width,depth), room_width, room_depth)
                if wall in ["top", "bottom", "left", "right"]:
                    sink_score += 5
                else:
                    sink_score -= 5
                
    scores["sink_placement"] = max(sink_score, 0)
    total_score += scores["sink_placement"]
    
    # 3. Wall Coverage (20 points)
    wall_coverage_score = 0
    wall_coverage = {
        "top": 0,
        "bottom": 0,
        "left": 0,
        "right": 0
    }
    
    for obj in placed_objects:
        x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        if wall in wall_coverage:
            wall_coverage[wall] += width if wall in ["top", "bottom"] else depth
            
    # Calculate wall coverage percentage
    for wall in wall_coverage:
        if wall in ["top", "bottom"]:
            coverage_percent = (wall_coverage[wall] / room_width) * 100
        else:
            coverage_percent = (wall_coverage[wall] / room_depth) * 100
            
        if coverage_percent >= 70:  # Reward for good wall coverage
            wall_coverage_score += 5
            
    scores["wall_coverage"] = min(wall_coverage_score, 20)
    total_score += scores["wall_coverage"]
    
    # 4. Corner Coverage (10 points)
    corner_coverage_score = 0
    corners = ["top-left", "top-right", "bottom-left", "bottom-right"]
    corner_objects = {corner: [] for corner in corners}
    
    for obj in placed_objects:
        x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        for corner in corners:
            if is_corner_placement_sink(x, y, room_width, room_depth, width, depth):
                corner_objects[corner].append(obj)
                
    # Reward for having objects in corners
    for corner, objects in corner_objects.items():
        if objects:
            corner_coverage_score += 2.5
            
    scores["corner_coverage"] = corner_coverage_score
    total_score += scores["corner_coverage"]
    
    # 5. Door Position Constraints (10 points)
    door_constraint_score = 0
    if windows_doors:
        for obj in placed_objects:
            x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
            for door in windows_doors:
                door_x, door_y, door_width, door_depth = door
                door_wall = check_which_wall(door, room_width, room_depth)
                obj_wall = check_which_wall((x,y,width,depth), room_width, room_depth)
                
                if name == "Sink" and door_wall != obj_wall:
                    door_constraint_score += 5  # Reward sink opposite door
                elif name == "Toilet" and door_wall == obj_wall:
                    door_constraint_score -= 5  # Penalize toilet opposite door
                    
    scores["door_constraints"] = max(door_constraint_score, 0)
    total_score += scores["door_constraints"]
    
    # 6. Object Spacing (10 points)
    spacing_score = 10
    for i, obj1 in enumerate(placed_objects):
        x1, y1, width1, depth1, height1, name1, _, _, shadow1 = obj1
        for j, obj2 in enumerate(placed_objects[i+1:], i+1):
            x2, y2, width2, depth2, height2, name2, _, _, shadow2 = obj2
            
            # Calculate minimum distance between objects
            min_dist = min(abs(x1 + width1 - x2), abs(y1 + depth1 - y2))
            if min_dist < 40 and min_dist > 10:  # Too much free space
                spacing_score -= 1
                
    scores["spacing"] = max(spacing_score, 0)
    total_score += scores["spacing"]
    
    # # 1. Wall constraints (20 points)
    # wall_constraint_score = 0
    # for obj in placed_objects:
    #     x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
    #     wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        
    #     if must_be_against_wall and wall not in ["top", "bottom", "left", "right"]:
    #         wall_constraint_score += 1
    #     elif not must_be_against_wall and wall in ["top", "bottom", "left", "right"]:
    #         wall_constraint_score += 1
            
    # scores["wall_constraints"] = min(wall_constraint_score / len(placed_objects) * 20, 20)
    # total_score += scores["wall_constraints"]
    
    # # 2. Corner constraints (20 points)
    # corner_constraint_score = 0
    # for obj in placed_objects:
    #     x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        
    #     if name == "Sink" and is_corner_placement_sink(x, y, room_width, room_depth, width, depth):
    #         corner_constraint_score -= 1
    #     elif must_be_corner and is_corner_placement_sink(x, y, room_width, room_depth, width, depth):
    #         corner_constraint_score += 1
            
    # scores["corner_constraints"] = min(max(corner_constraint_score / len(placed_objects) * 20, 0), 20)
    # total_score += scores["corner_constraints"]
    
    # # 3. Object spacing (20 points)
    # spacing_score = 0
    # for i, obj1 in enumerate(placed_objects):
    #     x1, y1, width1, depth1, height1, name1, _, _, shadow1 = obj1
    #     for j, obj2 in enumerate(placed_objects[i+1:], i+1):
    #         x2, y2, width2, depth2, height2, name2, _, _, shadow2 = obj2
            
    #         # Calculate minimum distance between objects
    #         min_dist = min(abs(x1 + width1 - x2), abs(y1 + depth1 - y2))
    #         if min_dist < 30:  # Minimum spacing requirement
    #             spacing_score -= 1
                
    # scores["spacing"] = max(20 + spacing_score / len(placed_objects) * 20, 0)
    # total_score += scores["spacing"]

    # 4. Object size optimization (20 points)
    size_optimization_score = 0
    for obj in placed_objects:
        x, y, width, depth, height, name, _, _, _ = obj
        obj_def= get_object_type(name)
        if obj_def is None:
            continue
        optimal_width, optimal_depth, optimal_height = obj_def["optimal_size"]
        
        # Calculate size deviation from optimal
        width_dev = abs(width - optimal_width) / optimal_width
        depth_dev = abs(depth - optimal_depth) / optimal_depth
        height_dev = abs(height - optimal_height) / optimal_height
        
        size_score = 1 - (width_dev + depth_dev + height_dev) / 3
        size_optimization_score += size_score
        
    scores["size_optimization"] = min(size_optimization_score / len(placed_objects) * 20, 20)
    total_score += scores["size_optimization"]
    
    # 5. Shadow constraints (20 points)
    shadow_score = 0
    for obj in placed_objects:
        x, y, width, depth, height, name, _, _, shadow = obj
        shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
        
        # Check if shadow overlaps with room boundaries
        if x - shadow_left >= 0 and y - shadow_bottom >= 0 and \
           x + width + shadow_right <= room_width and y + depth + shadow_top <= room_depth:
            shadow_score += 1
            
    scores["shadow_constraints"] = min(shadow_score / len(placed_objects) * 20, 20)
    total_score += scores["shadow_constraints"]
    
    return total_score, scores

def optimize_sink_corner(placed_obj, room_sizes):
    """
    Optimize sink placement by moving it from corners or switching with other objects.
    
    Args:
        placed_obj (list): List of placed objects [(x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)]
        room_sizes (tuple): Room dimensions (width, depth)
        
    Returns:
        list: Updated list of placed objects
    """
    room_width, room_depth = room_sizes
    
    for i, obj in enumerate(placed_obj):
        x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        
        # Check if this is a sink
        if name == "Sink":
            # Check if sink is in a corner
            if is_corner_placement_sink(x, y, room_width, room_depth, width, depth):
                # Try to find another object to switch with
                for j, other_obj in enumerate(placed_obj):
                    if i != j and not is_corner_placement_sink(other_obj[0], other_obj[1], room_width, room_depth, other_obj[2], other_obj[3]):
                        # Try to switch objects
                        new_positions, success, message = switch_objects(placed_obj, object_types_dict, room_sizes, i, other_obj[5])
                        if success:
                            print("Switched sink ")
                            return new_positions
                
                # If no suitable object to switch with, try to move the sink
                # Find available spaces
                available_spaces = identify_available_space(placed_obj, room_sizes)["without_shadow"]
                
                # Try to find a non-corner position
                for space in available_spaces:
                    space_x, space_y, space_width, space_depth = space
                    if not is_corner_placement_sink(space_x, space_y, room_width, room_depth, width, depth):
                        # Try to place the sink in this space
                        if space_width >= width and space_depth >= depth:
                            # Create new sink position
                            new_sink = (space_x, space_y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)
                            
                            # Check if placement is valid
                            other_positions = [(item[0], item[1], item[2], item[3], item[-1]) for item in placed_obj]
                            if is_valid_placement((space_x, space_y, width, depth), other_positions, shadow, room_width, room_depth):
                                # Update the sink position
                                del placed_obj[i]
                                placed_obj.insert(i, new_sink)
                                return placed_obj
    
    return placed_obj

def optimization(placed_obj, room_sizes):
    room_width, room_depth = room_sizes

    # First optimize sink placement
    #placed_obj = optimize_sink_corner(placed_obj, room_sizes)
    
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
            print(_1)
            if min_dist < 30 and _1 != "Sink":

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
def optimize_object(rect, shadow, room_width, room_depth, placed_obj):
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

    # grid_width = width // grid_size
    # grid_depth = depth // grid_size
    
    # # Check all internal angles
    # for i in range(1, grid_width - 1):
    #     for j in range(1, grid_depth - 1):
    #         # Check if this is a boundary cell
    #         if grid[i][j] == 1:
    #             # Check neighbors
    #             neighbors = [
    #                 grid[i-1][j],   # top
    #                 grid[i][j+1],   # right
    #                 grid[i+1][j],   # bottom
    #                 grid[i][j-1]    # left
    #             ]
                
    #             # Count occupied neighbors
    #             occupied_neighbors = sum(neighbors)
                
    #             # If we have 3 or more occupied neighbors, check for concavity
    #             if occupied_neighbors >= 3:
    #                 # Check if this forms a concave angle
    #                 if (grid[i-1][j] == 1 and grid[i][j+1] == 1 and grid[i+1][j] == 1) or \
    #                    (grid[i][j+1] == 1 and grid[i+1][j] == 1 and grid[i][j-1] == 1) or \
    #                    (grid[i+1][j] == 1 and grid[i][j-1] == 1 and grid[i-1][j] == 1) or \
    #                    (grid[i][j-1] == 1 and grid[i-1][j] == 1 and grid[i][j+1] == 1):
    #                     return False
    # return True
def check_enclosed_spaces(grid, grid_size, room_width, room_depth, min_path_width=50):
    """
    Check if there are any enclosed spaces in the room that can't be reached by a minimum width path.
    
    Args:
        grid (list): 2D grid representation of the room
        grid_size (int): Size of grid cells in cm
        room_width (int): Room width in cm
        room_depth (int): Room depth in cm
        min_path_width (int): Minimum required path width in cm (default: 50cm)
        
    Returns:
        bool: True if there are enclosed spaces, False otherwise
    """
    # Convert room dimensions to grid coordinates
    grid_width = room_width // grid_size 
    grid_depth = room_depth // grid_size 
    # Create a copy of the grid to mark visited cells
    visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Define minimum path width in grid cells
    min_path_cells = min_path_width // grid_size
    
    def is_accessible(x, y):
        """Check if a cell is accessible and within bounds."""
        return (0 <= x < grid_width and 0 <= y < grid_depth and 
                grid[x][y] == 0 and not visited[x][y])
    
    def check_path_width(x, y):
        """Check if there's enough width for the path."""
        # Check horizontal width
        for dx in range(-min_path_cells//2, min_path_cells//2 + 1):
            nx = x + dx
            if 0 <= nx < grid_width and grid[nx][y] == 1:
                return False
        # Check vertical width
        for dy in range(-min_path_cells//2, min_path_cells//2 + 1):
            ny = y + dy
            if 0 <= ny < grid_depth and grid[x][ny] == 1:
                return False
        return True
    
    def dfs(x, y):
        """Depth-first search to mark accessible areas."""
        stack = [(x, y)]
        while stack:
            x, y = stack.pop()
            if not is_accessible(x, y) or not check_path_width(x, y):
                continue
            
            visited[x][y] = True
            
            # Add neighbors to stack
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if is_accessible(nx, ny):
                    stack.append((nx, ny))
    
    # Start DFS from the room entrances (typically along walls)
    for x in range(grid_width):
        if grid[x][0] == 0:
            dfs(x, 0)
        if grid[x][grid_depth-1] == 0:
            dfs(x, grid_depth-1)
    
    for y in range(grid_depth):
        if grid[0][y] == 0:
            dfs(0, y)
        if grid[grid_width-1][y] == 0:
            dfs(grid_width-1, y)
    
    # Check if there are any unvisited empty spaces
    for x in range(grid_width):
        for y in range(grid_depth):
            if grid[x][y] == 0 and not visited[x][y]:
                return True  # Found an enclosed space
    
    return False  # No enclosed spaces found
def is_convex_space(grid, width, depth, grid_size, start_x=0, start_y=0):
    """
    Check if a space is convex by verifying that all internal angles are less than 180 degrees.
    A space can only be convex if objects are present near the corners.
    
    Args:
        grid (list): 2D grid representation of the space
        width (int): Width of the space
        depth (int): Depth of the space
        grid_size (int): Size of grid cells
        start_x (int): Starting x coordinate (for sub-spaces)
        start_y (int): Starting y coordinate (for sub-spaces)
        
    Returns:
        bool: True if the space is convex and has objects near corners, False otherwise
    """


    # First check if corners are properly occupied
    for x in [0, width-1]:
        for y in [0, depth-1]:
            # If corner is empty
            if grid[x][y] == 0:
                # Check if there are objects near this corner
                near_objects = False
                for dx in range(-1, 2):  # Check 3x3 area around corner
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < depth and grid[nx][ny] == 0:
                            # Check if this empty cell is part of an object
                            # by looking at its neighbors
                            object_near = False
                            for ndx in [-1, 1]:  # Check horizontal and vertical neighbors
                                nndx, nny = nx + ndx, ny
                                if 0 <= nndx < width and 0 <= nny < depth and grid[nndx][nny] == 1:
                                    object_near = True
                                    break
                            if object_near:
                                near_objects = True
                                break
                    if near_objects:
                        break
                if not near_objects:
                    return False
    
    # Check convexity by verifying all internal angles are less than 180 degrees
    for x in range(1, width-1):
        for y in range(1, depth-1):
            if grid[x][y] == 0:  # Only check empty cells
                # Check angles formed with adjacent cells
                angles = []
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < depth and grid[nx][ny] == 0:
                            # Calculate angle between vectors
                            angle = math.atan2(dy, dx)
                            angles.append(angle)
                
                # Sort angles and check differences
                angles.sort()
                for i in range(len(angles)):
                    diff = angles[(i+1) % len(angles)] - angles[i]
                    if diff < 0:
                        diff += 2 * math.pi
                    if diff >= math.pi:
                        return False
    
    return True

def identify_available_space(placed_obj, room_sizes, grid_size=1, windows_doors=[]):
    """
    Identifies available space in a room after objects have been placed.
    Returns both with and without shadow.
    Args:
        placed_obj (list): List of placed objects with their positions, dimensions, and shadows.
            Each object is a tuple (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow).
        room_sizes (tuple): Room dimensions as (width, depth).
        grid_size (int): Size of the grid cell in cm.
        windows_doors (list): List of windows and doors.
    Returns:
        dict: {'with_shadow': [...], 'without_shadow': [...]} available spaces as (x, y, width, depth) tuples.
    """
    def _find_spaces(include_shadows):
        room_width, room_depth = room_sizes
        grid_width = room_width // grid_size 
        grid_depth = room_depth // grid_size 
        grid = [[1 for _ in range(grid_depth)] for _ in range(grid_width)]
        # Mark occupied spaces
        for obj in placed_obj:
            x, y, width, depth, height, _1, _2, _3, shadow = obj
            x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom = convert_values((x,y,width,depth), shadow, check_which_wall((x,y,width,depth), room_width, room_depth))
            if include_shadows:
                start_x = max(0, (x - shadow_top) // grid_size)
                start_y = max(0, (y - shadow_left) // grid_size)
                end_x = min(grid_width, (x + depth + shadow_bottom) // grid_size )
                end_y = min(grid_depth, (y + width + shadow_right) // grid_size )
            else:
                start_x = max(0, x // grid_size)
                start_y = max(0, y // grid_size)
                end_x = min(grid_width, (x + depth) // grid_size )
                end_y = min(grid_depth, (y + width) // grid_size )
            for i in range(start_x, end_x):
                for j in range(start_y, end_y):
                    grid[i][j] = 0
        for i in windows_doors:
            id_, wall, x, y,  width,height, parapet, way = i
            start_x = max(0, (x ) // grid_size)
            start_y = max(0, (y) // grid_size)
            end_x = min(grid_width, (x + width) // grid_size )
            end_y = min(grid_depth, (y + width) // grid_size )
            if wall == "right":
                end_y = start_y
                start_y = start_y - width
            if wall == "bottom":
                end_x = start_x
                start_x = start_x - width
            for i in range(start_x, end_x):
                for j in range(start_y, end_y):
                    grid[i][j] = 0
        available_spaces = []
        visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
        for i in range(grid_width):
            for j in range(grid_depth):
                if grid[i][j] == 1 and not visited[i][j]:
                    space = find_contiguous_space(grid, visited, i, j, grid_width, grid_depth)
                    x = space["start_x"] * grid_size
                    y = space["start_y"] * grid_size
                    width = (space["end_y"] - space["start_y"]) * grid_size
                    depth = (space["end_x"] - space["start_x"]) * grid_size
                    if width >= 30 and depth >= 30:
                        available_spaces.append((x, y, width, depth))
        # closed = check_enclosed_spaces(grid, grid_size, room_width, room_depth)
        # if closed:
        #     st.warning("Warning: The available space in the room is not convex. This may affect optimal object placement.")
        return available_spaces
    return {
        'with_shadow': _find_spaces(True),
        'without_shadow': _find_spaces(False)
    }

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
    room_width, room_depth = room_sizes
    
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
    
    # Sort objects by size (biggest first to maximize space utilization)
    objects_to_try.sort(key=lambda x: object_sizes.get(x, float('inf')), reverse=True)
    
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
                    # convert values
                    wall = check_which_wall((x,y,width,depth), room_width, room_depth)
                    conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values((x,y,width,depth), shadow, wall)
                    # Determine which corner and adjust accordingly
                    if conv_x == 0 and conv_y == 0:  # Top-left corner
                        pass  # Already in corner
                    elif conv_x == 0 and conv_y + conv_width >= room_sizes[1] :  # Top-right corner
                        conv_y = room_sizes[1] - conv_width
                    elif conv_x + conv_depth >= room_sizes[0]  and conv_y == 0:  # Bottom-left corner
                        conv_x = room_sizes[0] - conv_depth
                    elif conv_x + conv_depth >= room_sizes[0]  and conv_y + conv_width >= room_sizes[1] :  # Bottom-right corner
                        conv_x = room_sizes[0] - conv_depth
                        conv_y = room_sizes[1] - conv_width
                    
                    placement = (x, y, width, depth)
        
        elif obj_def["must_be_against_wall"]:
            # For wall objects, filter spaces that include walls
            wall_spaces = []
            for space in remaining_spaces:
                space_x, space_y, space_width, space_depth = space
                # Check if space includes any wall
                if space_x == 0 or space_y == 0 or \
                   space_x + space_depth == room_sizes[0]  or \
                   space_y + space_width == room_sizes[1] :
                    wall_spaces.append(space)
            
            if wall_spaces:
                # Find best placement against walls
                placement = suggest_placement_in_available_space(
                    wall_spaces, obj_type, object_types_dict
                )
                
                # Adjust placement to be exactly against a wall
                if placement:
                    x, y, width, depth = placement
                    # convert values
                    wall = check_which_wall((x,y,width,depth), room_width, room_depth)
                    conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values((x,y,width,depth), shadow, wall)
                    # Determine which wall is closest and adjust accordingly
                    dist_to_top = conv_x
                    dist_to_left = conv_y
                    dist_to_bottom = room_sizes[0] - (conv_x + conv_depth)
                    dist_to_right = room_sizes[1] - (conv_y + conv_width)
                    
                    min_dist = min(dist_to_top, dist_to_left, dist_to_bottom, dist_to_right)
                    
                    if min_dist == dist_to_top:
                        conv_x = 0  # Place against top wall
                    elif min_dist == dist_to_left:
                        conv_y = 0  # Place against left wall
                    elif min_dist == dist_to_bottom:
                        conv_x = room_sizes[0] - conv_depth  # Place against bottom wall
                    elif min_dist == dist_to_right:
                        conv_y = room_sizes[1] - conv_width  # Place against right wall
                    
                    placement = (conv_x, conv_y, conv_width, conv_depth)
        
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

def suggest_additional_fixtures(placed_objects, room_sizes, object_types_dict, available_spaces_with_shadow, available_spaces_without_shadow):
    """
    Analyzes the current bathroom layout and suggests additional fixtures that could be added.
    Allows objects to be placed on available spaces with shadow (orange), and their shadow to extend into available spaces without shadow (green).
    Args:
        placed_objects (list): List of placed objects with their positions, dimensions, and shadows.
        room_sizes (tuple): Room dimensions as (width, depth).
        object_types_dict (dict): Dictionary of object types with their specifications.
        available_spaces_with_shadow (list): List of available spaces as (x, y, width, depth) tuples (orange).
        available_spaces_without_shadow (list): List of available spaces as (x, y, width, depth) tuples (green).
    Returns:
        dict: Dictionary with suggestions for additional fixtures and their potential placements.
    """
    placed_object_types = [obj[5] for obj in placed_objects]
    common_fixtures = [
        "Toilet", "Sink", "Shower", "Bathtub", "Cabinet", 
        "Double Sink", "Washing Machine", "Washing Dryer"
    ]
    room_width, room_depth = room_sizes
    object_names = [value["name"] for value in object_types_dict.values()]
    available_fixtures = [f for f in common_fixtures if f in object_names and f not in placed_object_types]
    suggestions = {}
    for fixture in available_fixtures:
        found = False
        # Try to place the object in orange (with shadow) spaces, but allow its SHADOW to extend into green (without shadow) spaces
        obj_def = next((value for value in object_types_dict.values() if value["name"] == fixture), None)
        if obj_def is None:
            continue
        # Try each available space in orange (with shadow)
        for space in available_spaces_with_shadow:
            x, y, width, depth = space
            # Use optimal size if available, else min size
            obj_width, obj_depth = obj_def.get("optimal_size", (obj_def["size_range"][0], obj_def["size_range"][2]))[:2]
            # Check if object fits in this space
            if width >= obj_width and depth >= obj_depth:
                # Calculate the shadow rectangle
                shadow_top, shadow_left, shadow_right, shadow_bottom = obj_def.get("shadow_space", (0,0,0,0))
                shadow_top, shadow_left, shadow_right, shadow_bottom = convert_shadows((shadow_top, shadow_left, shadow_right, shadow_bottom), check_which_wall((x,y,width,depth), room_width, room_depth))
                shadow_x = x - shadow_top
                shadow_y = y - shadow_left
                shadow_w = obj_width + shadow_left + shadow_right
                shadow_d = obj_depth + shadow_top + shadow_bottom
                shadow_rect = (shadow_x, shadow_y, shadow_w, shadow_d)
                # Check if the shadow area is fully inside ANY green (without shadow) space
                shadow_fits = False
                for green_space in available_spaces_without_shadow:
                    gx, gy, gw, gd = green_space
                    if (shadow_x >= gx and shadow_y >= gy and
                        shadow_x + shadow_w <= gx + gw and
                        shadow_y + shadow_d <= gy + gd):
                        shadow_fits = True
                        break
                if shadow_fits:
                    suggestions[fixture] = {
                        "position": (x, y),
                        "dimensions": (obj_width, obj_depth),
                        "shadow_rect": shadow_rect,
                        "space_efficiency": calculate_space_efficiency((x, y, obj_width, obj_depth), available_spaces_with_shadow)
                    }
                    found = True
                    break  # Only suggest one placement per fixture
        if found:
            continue
        # If optimal size does not fit, try the smallest dimension (min size)
        for space in available_spaces_with_shadow:
            x, y, width, depth = space
            min_width, max_width = obj_def["size_range"][0], obj_def["size_range"][1]
            min_depth, max_depth = obj_def["size_range"][2], obj_def["size_range"][3]
            obj_width, obj_depth = min_width, min_depth
            if width >= obj_width and depth >= obj_depth:
                shadow_top, shadow_left, shadow_right, shadow_bottom = obj_def.get("shadow_space", (0,0,0,0))
                shadow_top, shadow_left, shadow_right, shadow_bottom = convert_shadows((shadow_top, shadow_left, shadow_right, shadow_bottom), check_which_wall((x,y,width,depth), room_width, room_depth))
                shadow_x = x - shadow_top
                shadow_y = y - shadow_left
                shadow_w = obj_width + shadow_left + shadow_right
                shadow_d = obj_depth + shadow_top + shadow_bottom
                shadow_rect = (shadow_x, shadow_y, shadow_w, shadow_d)
                shadow_fits = False
                for green_space in available_spaces_without_shadow:
                    gx, gy, gw, gd = green_space
                    if (shadow_x >= gx and shadow_y >= gy and
                        shadow_x + shadow_w <= gx + gw and
                        shadow_y + shadow_d <= gy + gd):
                        shadow_fits = True
                        break
                if shadow_fits:
                    suggestions[fixture] = {
                        "position": (x, y),
                        "dimensions": (obj_width, obj_depth),
                        "shadow_rect": shadow_rect,
                        "space_efficiency": calculate_space_efficiency((x, y, obj_width, obj_depth), available_spaces_with_shadow)
                    }
                    break
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

def maximize_object_sizes(positions, room_sizes, object_types_dict, increment=5):
    """
    Attempts to maximize the size of objects while maintaining constraints.
    
    Args:
        positions (list): List of positions [(x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)]
        room_sizes (tuple): Room dimensions (width, depth)
        object_types_dict (dict): Dictionary of object types with their specifications
        increment (int): Amount to increase size by each iteration (default: 5cm)
        
    Returns:
        list: Updated list of placed objects with maximized sizes
    """
    room_width, room_depth = room_sizes
    
    # Keep trying to expand until no more objects can be expanded
    while True:
        any_expanded = False
        updated_objects = positions.copy()
        # only keep the x, y, width, depth, shadow
        objects_in_calculate = [(x, y, width, depth, shadow) for x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow in positions]
        
        for i, obj in enumerate(positions):
            x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
            obj_def= get_object_type(name)
            if obj_def is None:
                continue
                
            # Get the object's size range
            min_width, max_width, min_depth, max_depth, min_height, max_height = obj_def["size_range"]
            
            # Check if we can expand in width direction
            if not must_be_against_wall or check_which_wall((x,y,width,depth), room_width, room_depth) in ["top", "bottom"]:
                # Try to expand to the right
                new_width = min(max_width, width + increment)
                if new_width > width:
                    # Check if expanded size is valid
                    if is_valid_placement_without_converting((x, y, new_width, depth), objects_in_calculate, shadow, room_width, room_depth):
                        updated_objects[i] = (x, y, new_width, depth, height, name, must_be_corner, must_be_against_wall, shadow)
                        any_expanded = True
                        st.warning(f"Expanded width of {name} to {new_width}cm")
                        
            # Check if we can expand in depth direction
            if not must_be_against_wall or check_which_wall((x,y,width,depth), room_width, room_depth) in ["left", "right"]:
                # Try to expand downwards
                new_depth = min(max_depth, depth + increment)
                if new_depth > depth:
                    # Check if expanded size is valid
                    if is_valid_placement_without_converting((x, y, width, new_depth), objects_in_calculate, shadow, room_width, room_depth):
                        updated_objects[i] = (x, y, width, new_depth, height, name, must_be_corner, must_be_against_wall, shadow)
                        any_expanded = True
                        st.warning(f"Expanded depth of {name} to {new_depth}cm")
        
        # If no objects were expanded in this iteration, we're done
        if not any_expanded:
            break
            
        # Update positions for next iteration
        positions = updated_objects.copy()
        
    return updated_objects

def switch_objects(positions, object_types_dict, room_sizes, selected_obj_idx, new_object_name):
    if selected_obj_idx < 0 or selected_obj_idx >= len(positions):
        return positions, False, "Invalid selected object index."
    old_obj = positions[selected_obj_idx]
    # Remove the old object
    new_positions = positions[:selected_obj_idx] + positions[selected_obj_idx+1:]
    # Get new object definition
    new_obj_def = next((v for v in object_types_dict.values() if v["name"] == new_object_name), None)
    if new_obj_def is None:
        return positions, False, f"Object type '{new_object_name}' not found."
    # Try to fit new object in the removed object's space
    x, y = old_obj[0], old_obj[1]
    width, depth = new_obj_def.get("optimal_size", (new_obj_def["size_range"][0], new_obj_def["size_range"][2]))[:2]
    height = new_obj_def.get("optimal_size", (None, None, new_obj_def["size_range"][4]))[2]
    must_be_corner = new_obj_def.get("must_be_corner", False)
    must_be_against_wall = new_obj_def.get("must_be_against_wall", False)
    shadow = new_obj_def.get("shadow_space", (0,0,0,0))
    # Check if it fits in the same spot
    from utils import is_valid_placement
    room_width, room_depth = room_sizes
    # Exclude the old object from placements
    placed_rects = [(p[0], p[1], p[2], p[3], p[8]) for i, p in enumerate(positions) if i != selected_obj_idx]
    if is_valid_placement((x, y, width, depth), placed_rects, shadow, room_width, room_depth):
        # Place new object at the same spot
        new_obj = (x, y, width, depth, height, new_object_name, must_be_corner, must_be_against_wall, shadow)
        new_positions = positions[:selected_obj_idx] + [new_obj] + positions[selected_obj_idx+1:]
        return new_positions, True, f"Switched to {new_object_name} successfully."
    # If not, try to place it anywhere else in the room
    for i in range(0, int(room_width-width)+1, 5):
        for j in range(0, int(room_depth-depth)+1, 5):
            if is_valid_placement((i, j, width, depth), placed_rects, shadow, room_width, room_depth):
                new_obj = (i, j, width, depth, height, new_object_name, must_be_corner, must_be_against_wall, shadow)
                new_positions = positions[:selected_obj_idx] + [new_obj] + positions[selected_obj_idx+1:]
                return new_positions, True, f"Switched to {new_object_name} at new position ({i},{j})."
    return positions, False, f"Not enough space to switch to {new_object_name}."

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
        x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
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
    for item in windows_doors:
        id_, wall, x, y, width, height, parapet,way = item
        if id_.startswith("door"):
            # Mark the door area and add entry points
            start_x = max(0, int(x) // grid_size)
            start_y = max(0, int(y) // grid_size)
            end_x = min(grid_width, int(x + width) // grid_size)
            end_y = min(grid_depth, int(y + width) // grid_size)
            # Determine door entry points based on which wall it's on
            if wall == "left" or wall == "right":
                # Door on top or bottom wall, entry points along x-axis
                for i in range(start_x, end_x):
                    entry_y = start_y if wall == "left" else end_y - 1
                    door_positions.append((i, entry_y))
            else:
                # Door on left or right wall, entry points along y-axis
                for j in range(start_y, end_y):
                    entry_x = start_x if wall == "top" else end_x - 1
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