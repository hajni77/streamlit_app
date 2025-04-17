
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
}
def visualize_door_windows(windows_doors, room_width, room_depth, ax, door_shadow=75):
    # Draw windows and doors
    for item in windows_doors:
        id_, wall, x, y,  width,height, parapet = item
        
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
    # Create 3D figure
    fig = plt.figure(figsize=(10, 10))
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

    # figsize based on room size
    fig, ax = plt.subplots(figsize=((room_depth/100)*10, (room_width/100)*10))
    
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
        name, selected_door_type, x, y, door_width, door_height, shadow = door
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





def visualize_room_with_available_spaces(placed_objects, room_sizes, available_spaces):
    room_width, room_depth = room_sizes
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=((room_depth/100)*10, (room_width/100)*10))
    
    # Draw room boundaries
    ax.add_patch(patches.Rectangle((0, 0), room_depth, room_width, 
                                   fill=False, edgecolor='black', linewidth=2))
    
    # Draw placed objects
    for obj in placed_objects:
        x, y, width, depth, height, _, _, _, _ = obj
        ax.add_patch(patches.Rectangle((y, x), width, depth, 
                                       fill=True, color='blue', alpha=0.7))
    
    # Draw available spaces
    for space in available_spaces:
        x, y, width, depth = space
        ax.add_patch(patches.Rectangle((y, x), width, depth, 
                                       fill=True, color='green', alpha=0.3))
    
    # Set limits and labels
    ax.set_xlim(0, room_depth)
    ax.set_ylim(0, room_width)
    ax.set_xlabel('Width (cm)')
    ax.set_ylabel('Depth (cm)')
    ax.set_title('Room Layout with Available Spaces')
    
    # Add legend
    blue_patch = patches.Patch(color='blue', alpha=0.7, label='Placed Objects')
    green_patch = patches.Patch(color='green', alpha=0.3, label='Available Spaces')
    ax.legend(handles=[blue_patch, green_patch])
    # rotate the fig
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ## rotate 90 degree


    plt.show()
    return fig