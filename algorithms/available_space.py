import numpy as np
import time
def check_enclosed_spaces(spaces_dict, room_width, room_depth, min_distance=60, door_position=None):
    """
    Check if there are any enclosed/inaccessible spaces in the room using flood-fill.
    
    This function creates a grid representation and uses flood-fill from the door location
    (or room edges if no door specified) to check if all free spaces are reachable.
    Any unreachable free space is considered enclosed.
    
    Args:
        spaces_dict (list): List of tuples (x, y, width, depth) representing available spaces.
        room_width (int): Width of the room in cm.
        room_depth (int): Depth of the room in cm.
        min_distance (int, optional): Minimum distance threshold (legacy parameter). Defaults to 60.
        door_position (tuple, optional): Door position as (wall, x, y, width) where wall is 'top'/'bottom'/'left'/'right'.
                                         If None, starts from all room edges.
    
    Returns:
        bool: True if enclosed/inaccessible spaces detected, False otherwise.
    
    Example:
        >>> spaces = [(0, 0, 100, 50), (150, 0, 50, 50)]
        >>> door_pos = ('bottom', 100, 0, 80)  # Door on bottom wall
        >>> check_enclosed_spaces(spaces, 300, 200, door_position=door_pos)
        False  # All spaces are accessible from door
    """
    # Early return if no spaces
    if len(spaces_dict) < 1:
        return False
    
    # Create a grid (1 = free space, 0 = occupied/object)
    # Use 5cm grid cells for better accuracy
    grid_size = 5
    grid_width = int(room_width // grid_size)
    grid_depth = int(room_depth // grid_size)
    
    # Initialize grid as all occupied
    grid = [[0 for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Mark available spaces as free (1)
    for space in spaces_dict:
        x, y, width, depth = space
        start_x = max(0, int(x // grid_size))
        start_y = max(0, int(y // grid_size))
        end_x = min(grid_width, int((x + depth) // grid_size))
        end_y = min(grid_depth, int((y + width) // grid_size))
        
        for i in range(start_x, end_x):
            for j in range(start_y, end_y):
                grid[i][j] = 1
    
    # Count total free cells
    total_free = sum(sum(row) for row in grid)
    
    if total_free == 0:
        return False  # No free space at all
    
    # Flood-fill from door or edges to mark reachable spaces
    visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
    def flood_fill(x, y):
        """Flood-fill to mark all reachable free spaces."""
        if x < 0 or x >= grid_width or y < 0 or y >= grid_depth:
            return
        if visited[x][y] or grid[x][y] == 0:
            return
        
        # Use iterative approach to avoid stack overflow
        stack = [(x, y)]
        
        while stack:
            cx, cy = stack.pop()
            
            if cx < 0 or cx >= grid_width or cy < 0 or cy >= grid_depth:
                continue
            if visited[cx][cy] or grid[cx][cy] == 0:
                continue
            
            visited[cx][cy] = True
            
            # Add neighbors to stack (4-directional connectivity)
            stack.append((cx + 1, cy))
            stack.append((cx - 1, cy))
            stack.append((cx, cy + 1))
            stack.append((cx, cy - 1))
    
    # Determine starting points for flood-fill
    if door_position:
        # Start from door location (more accurate)
        wall, door_x, door_y, door_width = door_position
        
        # Convert door position to grid coordinates and find starting cells
        if wall == 'top':
            # Door on top wall (x=0)
            start_y = int(door_y // grid_size)
            end_y = int((door_y + door_width) // grid_size)
            for y in range(max(0, start_y), min(grid_depth, end_y + 1)):
                if grid[0][y] == 1:
                    flood_fill(0, y)
        elif wall == 'bottom':
            # Door on bottom wall (x=room_width)
            start_y = int(door_y // grid_size)
            end_y = int((door_y + door_width) // grid_size)
            for y in range(max(0, start_y), min(grid_depth, end_y + 1)):
                if grid[grid_width - 1][y] == 1:
                    flood_fill(grid_width - 1, y)
        elif wall == 'left':
            # Door on left wall (y=0)
            start_x = int(door_x // grid_size)
            end_x = int((door_x + door_width) // grid_size)
            for x in range(max(0, start_x), min(grid_width, end_x + 1)):
                if grid[x][0] == 1:
                    flood_fill(x, 0)
        elif wall == 'right':
            # Door on right wall (y=room_depth)
            start_x = int(door_x // grid_size)
            end_x = int((door_x + door_width) // grid_size)
            for x in range(max(0, start_x), min(grid_width, end_x + 1)):
                if grid[x][grid_depth - 1] == 1:
                    flood_fill(x, grid_depth - 1)
    else:
        # Fallback: Start flood-fill from all edges
        # Top edge (x=0)
        for y in range(grid_depth):
            if grid[0][y] == 1 and not visited[0][y]:
                flood_fill(0, y)
        
        # Bottom edge (x=grid_width-1)
        for y in range(grid_depth):
            if grid[grid_width - 1][y] == 1 and not visited[grid_width - 1][y]:
                flood_fill(grid_width - 1, y)
        
        # Left edge (y=0)
        for x in range(grid_width):
            if grid[x][0] == 1 and not visited[x][0]:
                flood_fill(x, 0)
        
        # Right edge (y=grid_depth-1)
        for x in range(grid_width):
            if grid[x][grid_depth - 1] == 1 and not visited[x][grid_depth - 1]:
                flood_fill(x, grid_depth - 1)
    
    # Check if there are any unvisited free spaces (enclosed areas)
    for x in range(grid_width):
        for y in range(grid_depth):
            if grid[x][y] == 1 and not visited[x][y]:
                # Found an enclosed space that's not reachable from door/edges
                return True
    
    return False


def check_corner_accessibility(placed_objects, room_width, room_depth, min_path_width=60):
    """
    Check if all room corners are either occupied by objects or accessible via adequate pathways.
    
    A corner is considered valid if:
    1. It has an object placed in it, OR
    2. It's reachable via a pathway of at least min_path_width (default 60cm)
    
    Args:
        placed_objects (list): List of placed object entries with 'object' key
        room_width (int): Room width in cm
        room_depth (int): Room depth in cm
        min_path_width (int): Minimum pathway width in cm (default: 60)
    
    Returns:
        tuple: (all_corners_valid: bool, corner_status: dict)
               corner_status = {
                   'top_left': {'valid': bool, 'reason': str},
                   'top_right': {'valid': bool, 'reason': str},
                   'bottom_left': {'valid': bool, 'reason': str},
                   'bottom_right': {'valid': bool, 'reason': str}
               }
    
    Example:
        >>> valid, status = check_corner_accessibility(objects, 300, 200, 60)
        >>> if not valid:
        ...     print(f"Invalid corners: {[k for k, v in status.items() if not v['valid']]}")
    """
    # Define corner positions (with small tolerance for corner detection)
    corner_size = 30  # Consider 30cm x 30cm area as "corner"
    corners = {
        'top_left': (0, 0, corner_size, corner_size),
        'top_right': (0, room_depth - corner_size, corner_size, corner_size),
        'bottom_left': (room_width - corner_size, 0, corner_size, corner_size),
        'bottom_right': (room_width - corner_size, room_depth - corner_size, corner_size, corner_size)
    }
    
    corner_status = {}
    
    for corner_name, corner_rect in corners.items():
        cx, cy, cw, cd = corner_rect
        
        # Check if corner has an object
        has_object = False
        for obj_entry in placed_objects:
            obj = obj_entry['object']
            ox, oy = obj.position
            ow, od = obj.width, obj.depth
            
            # Check if object overlaps with corner area
            if not (ox + od <= cx or ox >= cx + cd or 
                    oy + ow <= cy or oy >= cy + cw):
                has_object = True
                corner_status[corner_name] = {
                    'valid': True,
                    'reason': f'Occupied by {obj.name}'
                }
                break
        
        if has_object:
            continue
        
        # Corner is empty, check if it's reachable with adequate pathway
        # Use flood-fill with minimum width constraint
        is_reachable = _check_corner_reachable_with_width(
            corner_rect, placed_objects, room_width, room_depth, min_path_width
        )
        
        if is_reachable:
            corner_status[corner_name] = {
                'valid': True,
                'reason': f'Accessible via {min_path_width}cm pathway'
            }
        else:
            corner_status[corner_name] = {
                'valid': False,
                'reason': f'Inaccessible - no {min_path_width}cm pathway'
            }
    
    # Check if all corners are valid
    all_valid = all(status['valid'] for status in corner_status.values())
    
    return all_valid, corner_status


def _check_corner_reachable_with_width(corner_rect, placed_objects, room_width, room_depth, min_width):
    """
    Helper function to check if a corner is reachable via a pathway of minimum width.
    
    Uses a grid-based approach where we mark cells as accessible only if they have
    enough clearance (min_width) in at least one direction.
    """
    grid_size = 10  # 10cm grid cells
    grid_width = int(room_width // grid_size)
    grid_depth = int(room_depth // grid_size)
    
    # Create occupancy grid
    grid = [[0 for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Mark occupied cells
    for obj_entry in placed_objects:
        obj = obj_entry['object']
        ox, oy = obj.position
        ow, od = obj.width, obj.depth
        shadow = obj.shadow if hasattr(obj, 'shadow') else (0, 0, 0, 0)
        s_top, s_left, s_right, s_bottom = shadow
        
        # Include shadow space
        start_x = max(0, int((ox - s_top) // grid_size))
        start_y = max(0, int((oy - s_left) // grid_size))
        end_x = min(grid_width, int((ox + od + s_bottom) // grid_size))
        end_y = min(grid_depth, int((oy + ow + s_right) // grid_size))
        
        for i in range(start_x, end_x):
            for j in range(start_y, end_y):
                grid[i][j] = 1  # Occupied
    
    # Create accessibility grid considering minimum width
    # A cell is accessible if it has min_width clearance in at least one direction
    accessible = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    min_cells = int(min_width // grid_size)
    
    for x in range(grid_width):
        for y in range(grid_depth):
            if grid[x][y] == 1:  # Occupied cell
                continue
            
            # Check if there's enough clearance in any direction
            # Check horizontal clearance (left-right)
            h_clear = 0
            for dy in range(-min_cells, min_cells + 1):
                ny = y + dy
                if 0 <= ny < grid_depth and grid[x][ny] == 0:
                    h_clear += 1
                else:
                    break
            
            # Check vertical clearance (top-bottom)
            v_clear = 0
            for dx in range(-min_cells, min_cells + 1):
                nx = x + dx
                if 0 <= nx < grid_width and grid[nx][y] == 0:
                    v_clear += 1
                else:
                    break
            
            # Cell is accessible if either direction has enough clearance
            if h_clear >= min_cells or v_clear >= min_cells:
                accessible[x][y] = True
    
    # Get corner grid position
    cx, cy, cw, cd = corner_rect
    corner_grid_x = int((cx + cd / 2) // grid_size)
    corner_grid_y = int((cy + cw / 2) // grid_size)
    
    # Flood-fill from room edges through accessible cells
    visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
    def flood_fill(x, y):
        if x < 0 or x >= grid_width or y < 0 or y >= grid_depth:
            return
        if visited[x][y] or not accessible[x][y]:
            return
        
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= grid_width or cy < 0 or cy >= grid_depth:
                continue
            if visited[cx][cy] or not accessible[cx][cy]:
                continue
            
            visited[cx][cy] = True
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
    
    # Start flood-fill from all edges
    for y in range(grid_depth):
        if accessible[0][y]:
            flood_fill(0, y)
        if accessible[grid_width - 1][y]:
            flood_fill(grid_width - 1, y)
    
    for x in range(grid_width):
        if accessible[x][0]:
            flood_fill(x, 0)
        if accessible[x][grid_depth - 1]:
            flood_fill(x, grid_depth - 1)
    
    # Check if corner is reachable
    if 0 <= corner_grid_x < grid_width and 0 <= corner_grid_y < grid_depth:
        return visited[corner_grid_x][corner_grid_y]
    
    return False


def get_enclosed_spaces_debug_info(spaces_dict, room_width, room_depth):
    """
    Get detailed information about enclosed spaces for debugging/visualization.
    
    Args:
        spaces_dict (list): List of tuples (x, y, width, depth) representing available spaces.
        room_width (int): Width of the room in cm.
        room_depth (int): Depth of the room in cm.
    
    Returns:
        dict: {
            'has_enclosed': bool,
            'grid': 2D list (1=free, 0=occupied),
            'reachable': 2D list (True=reachable from edges, False=enclosed),
            'enclosed_cells': list of (x, y) coordinates of enclosed cells,
            'grid_size': int (cell size in cm)
        }
    """
    if len(spaces_dict) < 1:
        return {'has_enclosed': False, 'grid': [], 'reachable': [], 'enclosed_cells': [], 'grid_size': 10}
    
    grid_size = 10
    grid_width = int(room_width // grid_size)
    grid_depth = int(room_depth // grid_size)
    
    # Initialize grid
    grid = [[0 for _ in range(grid_depth)] for _ in range(grid_width)]
    
    # Mark available spaces
    for space in spaces_dict:
        x, y, width, depth = space
        start_x = max(0, int(x // grid_size))
        start_y = max(0, int(y // grid_size))
        end_x = min(grid_width, int((x + depth) // grid_size))
        end_y = min(grid_depth, int((y + width) // grid_size))
        
        for i in range(start_x, end_x):
            for j in range(start_y, end_y):
                grid[i][j] = 1
    
    # Flood-fill from edges
    visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
    
    def flood_fill(x, y):
        if x < 0 or x >= grid_width or y < 0 or y >= grid_depth:
            return
        if visited[x][y] or grid[x][y] == 0:
            return
        
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= grid_width or cy < 0 or cy >= grid_depth:
                continue
            if visited[cx][cy] or grid[cx][cy] == 0:
                continue
            
            visited[cx][cy] = True
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
    
    # Flood-fill from all edges
    for y in range(grid_depth):
        if grid[0][y] == 1:
            flood_fill(0, y)
        if grid[grid_width - 1][y] == 1:
            flood_fill(grid_width - 1, y)
    
    for x in range(grid_width):
        if grid[x][0] == 1:
            flood_fill(x, 0)
        if grid[x][grid_depth - 1] == 1:
            flood_fill(x, grid_depth - 1)
    
    # Find enclosed cells
    enclosed_cells = []
    has_enclosed = False
    
    for x in range(grid_width):
        for y in range(grid_depth):
            if grid[x][y] == 1 and not visited[x][y]:
                enclosed_cells.append((x * grid_size, y * grid_size))
                has_enclosed = True
    
    return {
        'has_enclosed': has_enclosed,
        'grid': grid,
        'reachable': visited,
        'enclosed_cells': enclosed_cells,
        'grid_size': grid_size
    }


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
        #check time 

        room_width, room_depth = room_sizes
        # Convert to int for grid calculations
        grid_width = int(room_width // grid_size)
        grid_depth = int(room_depth // grid_size)
        grid = [[1 for _ in range(grid_depth)] for _ in range(grid_width)]
        
        # Mark occupied spaces
        for obj in placed_obj:
            name = obj['object'].name
            width = float(obj['object'].width)
            depth = float(obj['object'].depth)
            height = float(obj['object'].height)
            shadow = obj['object'].shadow
            position = obj['object'].position
            wall = obj['object'].wall
            x, y = float(position[0]), float(position[1])
            shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
            
            if include_shadows:
                start_x = max(0, int((x - shadow_top) // grid_size))
                start_y = max(0, int((y - shadow_left) // grid_size))
                end_x = min(grid_width, int((x + depth + shadow_bottom) // grid_size))
                end_y = min(grid_depth, int((y + width + shadow_right) // grid_size))
            else:
                start_x = max(0, int(x // grid_size))
                start_y = max(0, int(y // grid_size))
                end_x = min(grid_width, int((x + depth) // grid_size))
                end_y = min(grid_depth, int((y + width) // grid_size))
                
            for i in range(start_x, end_x):
                for j in range(start_y, end_y):
                    grid[i][j] = 0
        # if include_shadows:
        #     for i in windows_doors:
        #         id_, wall, x, y,  width, height, parapet, way, hinge = i
        #         start_x = max(0, int(float(x) // grid_size))
        #         start_y = max(0, int(float(y) // grid_size))
        #         end_x = min(grid_width, int((float(x) + float(width)) // grid_size))
        #         end_y = min(grid_depth, int((float(y) + float(width)) // grid_size))
        #         if wall == "right":
        #             end_y = start_y
        #             start_y = max(0, int(start_y - float(width) // grid_size))
        #         if wall == "bottom":
        #             end_x = start_x
        #             start_x = max(0, int(start_x - float(width) // grid_size))
        #         for i in range(start_x, end_x):
        #             for j in range(start_y, end_y):
        #                 grid[i][j] = 0
        available_spaces = []
        visited = [[False for _ in range(grid_depth)] for _ in range(grid_width)]
        for i in range(grid_width):
            for j in range(grid_depth):
                if grid[i][j] == 1 and not visited[i][j]:
                    space = find_contiguous_space(grid, visited, i, j, grid_width, grid_depth)
                    x = float(space["start_x"] * grid_size)
                    y = float(space["start_y"] * grid_size)
                    width = float((space["end_y"] - space["start_y"]) * grid_size)
                    depth = float((space["end_x"] - space["start_x"]) * grid_size)
                    if width >= 30 and depth >= 30:
                        available_spaces.append((x, y, width, depth))
        # closed = check_enclosed_spaces(grid, grid_size, room_width, room_depth)
        # if closed:
        #     st.warning("Warning: The available space in the room is not convex. This may affect optimal object placement.")
        return available_spaces

    return {
        #'with_shadow': _find_spaces(True),
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
    # Ensure all indices are integers
    start_x = int(start_x)
    start_y = int(start_y)
    grid_width = int(grid_width)
    grid_depth = int(grid_depth)
    
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
        "start_x": int(start_x),
        "start_y": int(start_y),
        "end_x": int(end_x) + 1,  # Add 1 to get the exclusive end
        "end_y": int(end_y) + 1   # Add 1 to get the exclusive end
    }