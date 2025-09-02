import numpy as np
import time
def check_enclosed_spaces(spaces_dict, room_width, room_depth, min_distance=20):
    """
    Check if there are any enclosed spaces in the room based on the proximity of space corners.
    
    Args:
        spaces_dict (list): List of tuples (x, y, width, depth) representing spaces in the room.
        room_width (int): Width of the room.
        room_depth (int): Depth of the room.
        min_distance (int, optional): Minimum distance threshold for enclosed spaces detection. Defaults to 30.
    
    Returns:
        bool: True if enclosed spaces detected, False otherwise.
    """
    # Early return if not enough spaces to form enclosed areas
    if len(spaces_dict) < 1:
        return False
        
    # Extract corner points (vectors) from spaces more efficiently
    vectors = []
    for space in spaces_dict:
        x, y, width, depth = space
        
        # Corner points for spaces not against walls
        if x != 0 and y != 0:
            vectors.extend([
                (x, y),                # Top-left
                (x + depth, y),        # Top-right
                (x, y + width),        # Bottom-left
                (x + depth, y + width) # Bottom-right
            ])
        # Space against left wall
        elif x != 0 and y == 0:
            vectors.append((x, y + width))  # Bottom-left
            # Only add bottom-right if not at room edge
            if x + depth != room_width or y + width != room_depth:
                vectors.append((x + depth, y + width))
        # Space against top wall
        elif x == 0 and y != 0:
            vectors.append((x + depth, y))  # Top-right
            # Only add bottom-right if not at room edge
            if x + depth != room_width or y + width != room_depth:
                vectors.append((x + depth, y + width))
    
    # If we have less than 2 vectors, can't form enclosed spaces
    if len(vectors) < 2:
        return False
        
    # Use numpy for faster distance calculations
    # if len(vectors) > 5:  # Only convert to numpy for larger sets to avoid overhead
    #     vectors_array = np.array(vectors)
    #     for i in range(len(vectors)):
    #         # Calculate distances from point i to all other points efficiently
    #         point = vectors_array[i]
    #         # Broadcasting to calculate all distances at once
    #         distances = np.sqrt(np.sum((vectors_array - point)**2, axis=1))
    #         # Check if any point (except itself) is closer than min_distance
    #         if np.any((distances < min_distance) & (distances > 0)):
    #             return True
    # else:
        # For smaller sets, use the original approach to avoid numpy overhead
    for i in range(len(vectors)):
        for j in range(i+1, len(vectors)):
            distance = np.sqrt((vectors[i][0] - vectors[j][0])**2 + (vectors[i][1] - vectors[j][1])**2)
            if distance < min_distance:
                return True

    return False


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