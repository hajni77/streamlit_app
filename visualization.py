import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import Button
import numpy as np
from mpl_toolkits.mplot3d import axes3d 
import matplotlib.patches as patches
from utils import check_which_wall,check_distance,adjust_object_placement, check_distance_from_wall, convert_values, adjust_object_placement_pos, is_valid_placement
# Initialize global variables for view angle adjustment
current_elev = 30
current_azim = 30

object_colors = {
    "Toilet": "blue",
    "Sink": "green",
    "Shower": "red",
    "Bathtub": "purple",
    "Washing Machine": "orange",
    "Double Sink": "brown",
    "Cabinet": "pink",
    "Washing Dryer": "orange",
    "Washing Machine and Dryer": "orange",
    "Asymmetrical Bathtub": "purple",
    "Toilet Bidet": "blue",

}
def visualize_door_windows(windows_doors, room_width, room_depth, ax, door_shadow=75):
    # Draw windows and doors
    for item in windows_doors:
        id_, wall, x, y,  width,height, parapet, way, hinge = item
        
        # Calculate vertices based on wall placement
        if wall == "top":
            vertices = [
                [0, y, parapet],
                [0, y + width, parapet],
                [0, y + width, parapet + height],
                [0, y, parapet + height]
            ]
            
            # 3D Shadow as a box on the floor
            if 'door' in id_.lower():
                shadow_vertices = [
                    # Bottom rectangle
                [0, y, parapet],
                [0, y + width, parapet],
                [0, y + width, parapet + height],
                [0, y, parapet + height],
                    # Top rectangle (slightly raised)
                [door_shadow, y, parapet],
                [door_shadow, y + width, parapet],
                [door_shadow, y + width, parapet + height],
                [door_shadow, y, parapet + height],
                ]
        
        elif wall == "bottom":
            vertices = [
                [room_width, y, parapet],
                [room_width, y + width, parapet],
                [room_width, y + width, parapet + height],
                [room_width, y, parapet + height]
            ]
            
            # 3D Shadow as a box on the floor
            if 'door' in id_.lower():
                # Calculate shadow vertices, 75 cm into the room
                shadow_vertices = [
                [room_width, y, parapet],
                [room_width, y + width, parapet],
                [room_width, y + width, parapet + height],
                [room_width, y, parapet + height],
                    [room_width - door_shadow, y, parapet],                 # Bottom-left
                    [room_width - door_shadow, y + width, parapet],         # Top-left
                    [room_width - door_shadow, y + width, parapet + height], # Top-right
                    [room_width - door_shadow, y, parapet + height]           # Bottom-right
                ]
        
        elif wall == "right":
            vertices = [
                    [x, room_depth,parapet],  # Top-left corner
                    [x + width, room_depth, parapet],  # Top-right corner
                    [x + width, room_depth , parapet+height],  # Bottom-right corner
                    [x, room_depth,parapet+height]  # Bottom-left corner
                ]
                
                # 3D Shadow as a box on the floor
            if 'door' in id_.lower():
                    shadow_vertices = [
                        [x, room_depth,parapet],  # Top-left corner
                        [x + width, room_depth, parapet],  # Top-right corner
                        [x + width, room_depth , parapet+height],  # Bottom-right corner
                        [x, room_depth,parapet+height] , # Bottom-left corner
                        [x, room_depth-door_shadow,parapet],  # Top-left corner
                        [x + width, room_depth-door_shadow, parapet],  # Top-right corner
                        [x + width, room_depth-door_shadow , parapet+height],  # Bottom-right corner
                        [x, room_depth-door_shadow,parapet+height]  # Bottom-left corner
                    ]

        elif wall == "left":
            vertices =  [
                    [x, 0,parapet],  # Top-left corner
                    [x + width, 0, parapet],  # Top-right corner
                    [x + width, 0 , parapet+height],  # Bottom-right corner
                    [x,0,parapet+height]  # Bottom-left corner
                ]
            
            # 3D Shadow as a box on the floor
            if 'door' in id_.lower():
                shadow_vertices = [
                    [x, 0,parapet],  # Top-left corner
                    [x + width, 0, parapet],  # Top-right corner
                    [x + width, 0 , parapet+height],  # Bottom-right corner
                        [x, 0,parapet+height] , # Bottom-left corner
                        
                        [x, door_shadow,parapet],  # Top-left corner
                        [x + width,door_shadow, parapet],  # Top-right corner
                        [x + width, door_shadow , parapet+height],  # Bottom-right corner
                        [x, door_shadow,parapet+height]  # Bottom-left corner
                    ]
                
        # Draw the window or door
        color = 'skyblue' if 'window' in id_.lower() else 'brown'
        alpha = 0.5 if 'window' in id_.lower() else 1.0
        wall_feature = Poly3DCollection([vertices], color=color, alpha=alpha, edgecolor='black')
        ax.add_collection3d(wall_feature)
        # Draw the 3D shadow for doors
        if 'door' in id_.lower():
            faces = [
                shadow_vertices[0:4],  # Bottom face
                shadow_vertices[4:8],  # Top face
                [shadow_vertices[i] for i in [0, 1, 5, 4]],  # top face
                [shadow_vertices[i] for i in [1, 2, 6, 5]],  # Right face
                [shadow_vertices[i] for i in [2, 3, 7, 6]],  # bottom face
                [shadow_vertices[i] for i in [3, 0, 4, 7]],  # Left face
            ]
            shadow = Poly3DCollection(faces, color='grey', alpha=0.3, edgecolor='none')
            ax.add_collection3d(shadow)
        # Label the window/door
        cx = sum([v[0] for v in vertices]) / 4
        cy = sum([v[1] for v in vertices]) / 4
        cz = sum([v[2] for v in vertices]) / 4
        ax.text(cx, cy, cz + 10, id_, color='black', ha='center', va='center')

# visuaize placed objects
def visualize_placed_objects(placed_objects, room_width, room_depth, ax):
    for x, y,  w, d, h, name, must_be_corner, must_be_wall, shadow in placed_objects:
        z = 0 # currently all objects are on the floor

        top, left,right,bottom = shadow

        
        conv_x , conv_y, conv_w, conv_d,  conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values((x, y, w, d), shadow, check_which_wall((x, y, w, d), room_width, room_depth))
        
        shadow_x = conv_x - conv_shadow_top
        shadow_y = conv_y - conv_shadow_left
        shadow_w = conv_w + conv_shadow_left + conv_shadow_right
        shadow_d = conv_d + conv_shadow_bottom + conv_shadow_top

        
        # crop shadow if bigger than room
        if shadow_x < 0:
            shadow_x = 0
        if shadow_y < 0:
            shadow_y = 0
        if shadow_x + shadow_d > room_width:
            shadow_d = room_width - shadow_x
        if shadow_y + shadow_w > room_depth:
            shadow_w = room_depth - shadow_y
        
        shadow_floor = [
            [shadow_x, shadow_y, 0],
            [shadow_x + shadow_d, shadow_y, 0],
            [shadow_x + shadow_d, shadow_y + shadow_w, 0],
            [shadow_x, shadow_y + shadow_w, 0]
        ]
        ax.add_collection3d(Poly3DCollection([shadow_floor], color='gray', alpha=0.3))
        
        # Draw actual object (3D box)
        vertices = [
            [x, y, z], [x + d, y, z], [x + d, y + w, z], [x, y + w, z],  # Bottom face
            [x, y, z + h], [x + d, y, z + h], [x + d, y + w, z + h], [x, y + w, z + h]  # Top face
        ]
        
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # top
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # bottom
            [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # Left
        ]
        color = object_colors[name]

        obj_3d = Poly3DCollection(faces, color=color, alpha=0.8, edgecolor='black')
        ax.add_collection3d(obj_3d)
        text_offset = 5  # Adjust this value to control the height of the text above the object
        ax.text(x + w / 2, y + d / 2, z + h + text_offset, name, 
            color='black', ha='center', va='bottom', fontsize=10, weight='bold')
        # Label the object on the top face
        # ax.text(x + w / 2, y + d / 2, z + h, name, color='white', ha='center', va='center', fontsize=10)
    


def visualize_room_with_shadows_3d(bathroom_size, placed_objects, windows_doors):
    room_width, room_depth = bathroom_size
    room_height = 280  # Fixed height for 3D visualization
    
    # Interactive mode for adjustable viewing angles
    plt.ion()
    # Create 3D figure - smaller size
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_box_aspect([room_width, room_depth, room_height])  # Aspect ratio
    
    # Room boundaries
    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_zlim(0, room_height)
    ax.set_xlabel('Width (X)')
    ax.set_ylabel('Depth (Y)')
    ax.set_zlabel('Height (Z)')
    ax.set_title('3D Room Layout')
    # show color-name mapping for objects from top to bottom
    for i, (name, color) in enumerate(object_colors.items()):
        ax.text(room_width + 1, room_depth - i*30, room_height, f"{name}: {color}", color=color, fontsize
                =10)
    visualize_door_windows(windows_doors, room_width, room_depth, ax)
    visualize_placed_objects(placed_objects, room_width, room_depth, ax) 
     
 # Initial view angle
    ax.view_init(elev=current_elev, azim=current_azim)

    
    # plt.show()
    return fig




def draw_2d_floorplan(bathroom_size,  objects, doors, indoor):
    
    room_width , room_depth = bathroom_size

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
    ax.plot([0, room_depth], [0, 0], "k-", linewidth=3)  # Bottom wall
    ax.plot([0, room_depth], [room_width, room_width], "k-", linewidth=3)  # Top wall
    ax.plot([0, 0], [0, room_width], "k-", linewidth=3)  # Left wall
    ax.plot([room_depth, room_depth], [0, room_width], "k-", linewidth=3)  # Right wall
    for door in doors:
        name, selected_door_type, x, y, door_width, door_height, shadow, way, hinge = door
        shadow = door_width
        alpha = 0.3
        name = "Outward Door"
        if indoor == "Inward":
            alpha = 0.9
            name = "Inward Door"
        # draw line in place of door
        if selected_door_type == "top" :

            obj_shadow = patches.Rectangle((y, x), door_width, shadow, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(y + door_width / 2, x + shadow / 2, name, ha="center", va="center", fontsize=10, fontweight="bold")
        elif selected_door_type == "bottom":

            obj_shadow = patches.Rectangle((y,room_width-shadow), door_width, shadow, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(y + door_width / 2, room_width - shadow + door_width / 2, name, ha="center", va="center", fontsize=10, fontweight="bold")
        elif selected_door_type == "left":

            obj_shadow = patches.Rectangle((0, x), shadow, door_width, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(0 + shadow / 2, x + door_width / 2, name, ha="center", va="center", fontsize=10, fontweight="bold")
        elif selected_door_type == "right":

            obj_shadow = patches.Rectangle((room_depth-shadow,x ), shadow, door_width, edgecolor="gray", facecolor="gray", alpha=alpha)
            ax.add_patch(obj_shadow)
            ax.text(room_depth - shadow + door_width / 2, x + door_width / 2, name, ha="center", va="center", fontsize=10, fontweight="bold")
        
        
    # Draw windows
        
    # Draw objects
    for obj in objects:
        x,y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
        conv_x , conv_y, conv_w, conv_d,  conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values((x, y, width, depth), shadow, check_which_wall((x, y, width, depth), room_width, room_depth))
        shadow_x = conv_x - conv_shadow_top
        shadow_y = conv_y - conv_shadow_left
        shadow_w = conv_w + conv_shadow_left + conv_shadow_right
        shadow_d = conv_d + conv_shadow_bottom + conv_shadow_top
        obj_rect = patches.Rectangle((conv_y, conv_x), conv_w, conv_d, edgecolor="blue", facecolor="lightblue", alpha=0.7)
        obj_shadow = patches.Rectangle((shadow_y, shadow_x), shadow_w, shadow_d, edgecolor="gray", facecolor="lightgray", alpha=0.5)
        ax.add_patch(obj_rect)
        ax.add_patch(obj_shadow)
        ax.text(conv_y + conv_w/2, conv_x + conv_d/2, name, ha="center", va="center", fontsize=10, fontweight="bold")
    return fig





def visualize_room_with_available_spaces(placed_objects, room_sizes, available_spaces_dict, shadow):
    """
    Visualizes the room with placed objects and two sets of available spaces:
    - with shadow (orange)
    - without shadow (green)
    Args:
        placed_objects (list): List of placed objects.
        room_sizes (tuple): (width, depth)
        available_spaces_dict (dict): {'with_shadow': [...], 'without_shadow': [...]} as returned by identify_available_space
    Returns:
        matplotlib.figure.Figure: The visualization figure
    """
    room_width, room_depth = room_sizes
    fig, ax = plt.subplots(figsize=((room_depth/100)*6, (room_width/100)*6))
    # Draw room boundaries
    ax.add_patch(patches.Rectangle((0, 0), room_depth, room_width, fill=False, edgecolor='black', linewidth=2))
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
    ax.set_xlim(0, room_depth)
    ax.set_ylim(0, room_width)
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


def visualize_pathway_accessibility(placed_objects, room_sizes, windows_doors, path_width=60):
    """
    Visualizes the bathroom layout with pathway accessibility from doors to objects.
    
    Args:
        placed_objects (list): List of placed objects [(x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)]
        room_sizes (tuple): Room dimensions (width, depth)
        windows_doors (list): List of windows and doors in the room
        path_width (int): Minimum width of pathways in cm (default: 60)
        
    Returns:
        matplotlib.figure.Figure: The visualization figure showing accessible pathways
    """
    room_width, room_depth = room_sizes
    
    fig, ax = plt.subplots(figsize=((room_depth/100)*6, (room_width/100)*6))
    
    # Draw room boundaries
    ax.add_patch(patches.Rectangle((0, 0), room_depth, room_width, fill=False, edgecolor='black', linewidth=2))
    
    # Create a grid for the room to check pathways
    grid_resolution = 1  # cm per grid cell
    grid_width = int(room_width / grid_resolution) + 1
    grid_depth = int(room_depth / grid_resolution) + 1
    
    # Create a grid where 1 = occupied, 0 = free space
    grid = np.zeros((grid_width, grid_depth))
    
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
    for door in windows_doors:
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
                ax.add_patch(patches.Rectangle((door_y, room_width-10), door_width, 10, fill=True, color='green', alpha=0.7))
                door_grid_x = grid_width-1
                door_grid_y = int((door_y + door_width/2) / grid_resolution)
            elif door_type == "left":
                ax.add_patch(patches.Rectangle((0, door_x), 10, door_width, fill=True, color='green', alpha=0.7))
                door_grid_x = int((door_x + door_width/2) / grid_resolution)
                door_grid_y = 0
            elif door_type == "right":
                ax.add_patch(patches.Rectangle((room_depth-10, door_x), 10, door_width, fill=True, color='green', alpha=0.7))
                door_grid_x = int((door_x + door_width/2) / grid_resolution)
                door_grid_y = grid_depth-1
            
            door_positions.append((door_grid_x, door_grid_y))
            ax.text(door_y + door_width/2, door_x + 5, "Door", ha="center", va="center", fontsize=8, color='black')
    
    # Check pathway from each door to each object
    accessible_objects = set()
    accessible_paths = []
    
    for door_grid_x, door_grid_y in door_positions:
        for i, obj in enumerate(placed_objects):
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
    for i, obj in enumerate(placed_objects):
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
    ax.set_title(f'Bathroom Layout with {path_width}cm Pathway Accessibility')
    
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


def visualize_opposite_walls_distance(placed_objects, room_sizes, violations=None, min_distance=60):
    """
    Visualize the distance between objects on opposite walls, highlighting violations.
    
    Args:
        placed_objects: List of objects with their positions and dimensions
        room_sizes: Tuple of (room_width, room_depth)
        violations: List of violations as returned by check_opposite_walls_distance
                   Each violation is (idx1, idx2, name1, name2, distance)
        min_distance: Minimum required distance (default 60cm)
        
    Returns:
        matplotlib figure showing the room layout with distance annotations
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    
    room_width, room_depth = room_sizes
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Draw room boundaries
    ax.add_patch(patches.Rectangle((0, 0), room_width, room_depth, fill=False, edgecolor='black', linewidth=2))
    
    # Draw all objects
    for i, obj in enumerate(placed_objects):
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
        _, violations = check_opposite_walls_distance(placed_objects, room_sizes, min_distance)
    
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

