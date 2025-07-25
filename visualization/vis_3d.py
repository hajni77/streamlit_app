import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from utils.helpers import check_which_wall, convert_values

class Visualizer3D:
    def __init__(self, room, room_width, room_depth, room_height=250):
        """
        Initialize the 3D visualizer with room dimensions.
        
        Args:
            room_width: Width of the room in cm
            room_depth: Depth of the room in cm
            room_height: Height of the room in cm (default 250cm)
        """
        self.room_width = room_width
        self.room_depth = room_depth
        self.room_height = room_height
        self.bathroom = room
        
        # Color mapping for different object types
        self.color_map = {
            'toilet': 'lightblue',
            'sink': 'lightgreen',
            'shower': 'lightyellow',
            'bathtub': 'lightpink',
            'bidet': 'lightgray',
            'cabinet': 'tan',
            'door': 'brown',
            'window': 'skyblue'
        }
    
    def draw_3d_room(self, objects, doors=None):
        """
        Draw a 3D visualization of the bathroom layout.
        
        Args:
            objects: List of objects with their positions and dimensions
            doors: List of doors and windows (optional)
            
        Returns:
            matplotlib.figure.Figure: A 3D figure that can be displayed and saved
        """
        room_width, room_depth, room_height = self.room_width, self.room_depth, self.room_height
        
        # Create figure and 3D axis
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Draw room boundaries (floor and walls)
        # Floor
        floor_vertices = [
            [0, 0, 0],
            [0, room_width, 0],
            [room_depth, room_width, 0],
            [room_depth, 0, 0]
        ]
        floor = Poly3DCollection([floor_vertices], alpha=0.3, facecolor='lightgray')
        ax.add_collection3d(floor)
        
        # Walls
        wall_back = Poly3DCollection([[  # Back wall (y=0)
            [0, 0, 0],
            [room_depth, 0, 0],
            [room_depth, 0, room_height],
            [0, 0, room_height]
        ]], alpha=0.2, facecolor='white')
        
        wall_right = Poly3DCollection([[  # Right wall (x=room_depth)
            [room_depth, 0, 0],
            [room_depth, room_width, 0],
            [room_depth, room_width, room_height],
            [room_depth, 0, room_height]
        ]], alpha=0.2, facecolor='white')
        
        wall_front = Poly3DCollection([[  # Front wall (y=room_width)
            [0, room_width, 0],
            [room_depth, room_width, 0],
            [room_depth, room_width, room_height],
            [0, room_width, room_height]
        ]], alpha=0.2, facecolor='white')
        
        wall_left = Poly3DCollection([[  # Left wall (x=0)
            [0, 0, 0],
            [0, room_width, 0],
            [0, room_width, room_height],
            [0, 0, room_height]
        ]], alpha=0.2, facecolor='white')
        
        ax.add_collection3d(wall_back)
        ax.add_collection3d(wall_right)
        ax.add_collection3d(wall_front)
        ax.add_collection3d(wall_left)
        
        # Draw doors and windows if provided
        if doors:
            # Handle both iterable collections and single WindowsDoors objects
            door_list = []
            if hasattr(doors, '__iter__') and not isinstance(doors, str):
                # It's an iterable (list, tuple, etc.)
                door_list = doors
            else:
                # It's a single WindowsDoors object
                door_list = [doors]
                
            for door in door_list:
                # Extract door properties based on the object type
                if hasattr(door, 'name') and hasattr(door, 'wall'):
                    # It's a WindowsDoors object
                    name = door.name
                    door_type = door.wall
                    x = door.position[0] if hasattr(door, 'position') and door.position else 0
                    y = door.position[1] if hasattr(door, 'position') and door.position else 0
                    width = door.width if hasattr(door, 'width') else 80
                    height = door.height if hasattr(door, 'height') else 200
                    shadow = None
                    way = door.way if hasattr(door, 'way') else 'inwards'
                    hinge = door.hinge if hasattr(door, 'hinge') else 'left'
                else:
                    # It's a tuple or list with door properties
                    try:
                        name, door_type, x, y, width, height, shadow, way, hinge = door
                    except (ValueError, TypeError):
                        # If unpacking fails, try to handle it gracefully
                        try:
                            if isinstance(door, dict):
                                name = door.get('name', 'Door')
                                door_type = door.get('wall', 'top')
                                x = door.get('x', 0)
                                y = door.get('y', 0)
                                width = door.get('width', 80)
                                height = door.get('height', 200)
                                shadow = door.get('shadow', None)
                                way = door.get('way', 'inwards')
                                hinge = door.get('hinge', 'left')
                            else:
                                # If we can't extract the needed properties, skip this door
                                continue
                        except:
                            # If all else fails, skip this door
                            continue
                
                # Default door height if not specified
                if height is None or height == 0:
                    height = 200  # 2m standard door height
                
                # Draw door based on wall type
                if door_type == "top":
                    # Door on top wall (y=room_width)
                    door_vertices = [
                        [y, room_width, 0],
                        [y + width, room_width, 0],
                        [y + width, room_width, height],
                        [y, room_width, height]
                    ]
                    door_poly = Poly3DCollection([door_vertices], alpha=0.7, facecolor='brown')
                    ax.add_collection3d(door_poly)
                    
                elif door_type == "bottom":
                    # Door on bottom wall (y=0)
                    door_vertices = [
                        [y, 0, 0],
                        [y + width, 0, 0],
                        [y + width, 0, height],
                        [y, 0, height]
                    ]
                    door_poly = Poly3DCollection([door_vertices], alpha=0.7, facecolor='brown')
                    ax.add_collection3d(door_poly)
                    
                elif door_type == "left":
                    # Door on left wall (x=0)
                    door_vertices = [
                        [0, x, 0],
                        [0, x + width, 0],
                        [0, x + width, height],
                        [0, x, height]
                    ]
                    door_poly = Poly3DCollection([door_vertices], alpha=0.7, facecolor='brown')
                    ax.add_collection3d(door_poly)
                    
                elif door_type == "right":
                    # Door on right wall (x=room_depth)
                    door_vertices = [
                        [room_depth, x, 0],
                        [room_depth, x + width, 0],
                        [room_depth, x + width, height],
                        [room_depth, x, height]
                    ]
                    door_poly = Poly3DCollection([door_vertices], alpha=0.7, facecolor='brown')
                    ax.add_collection3d(door_poly)
                    
                # Add text label for the door
                if door_type == "top":
                    ax.text(y + width/2, room_width, height/2, name, fontsize=8)
                elif door_type == "bottom":
                    ax.text(y + width/2, 0, height/2, name, fontsize=8)
                elif door_type == "left":
                    ax.text(0, x + width/2, height/2, name, fontsize=8)
                elif door_type == "right":
                    ax.text(room_depth, x + width/2, height/2, name, fontsize=8)
            # Draw bathroom objects
            for obj in objects:

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

            
                # Get object type for coloring
                obj_type = name.lower()
                if 'toilet' in obj_type:
                    color = self.color_map['toilet']
                elif 'sink' in obj_type:
                    color = self.color_map['sink']
                elif 'shower' in obj_type:
                    color = self.color_map['shower']
                elif 'bathtub' in obj_type or 'bath' in obj_type:
                    color = self.color_map['bathtub']
                elif 'bidet' in obj_type:
                    color = self.color_map['bidet']
                elif 'cabinet' in obj_type:
                    color = self.color_map['cabinet']
                else:
                    color = 'gray'  # Default color
                
                # Draw the object as a box
                # Bottom face
                bottom_vertices = [
                    [y, x, 0],
                    [y + width, x, 0],
                    [y + width, x + depth, 0],
                    [y, x + depth, 0]
                ]
                bottom = Poly3DCollection([bottom_vertices], alpha=0.7, facecolor=color)
                ax.add_collection3d(bottom)
                
                # Top face
                top_vertices = [
                    [y, x, height],
                    [y + width, x, height],
                    [y + width, x + depth, height],
                    [y, x + depth, height]
                ]
                top = Poly3DCollection([top_vertices], alpha=0.7, facecolor=color)
                ax.add_collection3d(top)
                
                # Side faces
                side1_vertices = [
                    [y, x, 0],
                    [y + width, x, 0],
                    [y + width, x, height],
                    [y, x, height]
                ]
                side1 = Poly3DCollection([side1_vertices], alpha=0.7, facecolor=color)
                ax.add_collection3d(side1)
                
                side2_vertices = [
                    [y + width, x, 0],
                    [y + width, x + depth, 0],
                    [y + width, x + depth, height],
                    [y + width, x, height]
                ]
                side2 = Poly3DCollection([side2_vertices], alpha=0.7, facecolor=color)
                ax.add_collection3d(side2)
                
                side3_vertices = [
                    [y + width, x + depth, 0],
                    [y, x + depth, 0],
                    [y, x + depth, height],
                    [y + width, x + depth, height]
                ]
                side3 = Poly3DCollection([side3_vertices], alpha=0.7, facecolor=color)
                ax.add_collection3d(side3)
                
                side4_vertices = [
                    [y, x + depth, 0],
                    [y, x, 0],
                    [y, x, height],
                    [y, x + depth, height]
                ]
                side4 = Poly3DCollection([side4_vertices], alpha=0.7, facecolor=color)
                ax.add_collection3d(side4)
                
                # Add text label for the object
                ax.text(y + width/2, x + depth/2, height + 10, name, fontsize=8)
        
        # Set axis labels and limits
        ax.set_xlabel('Width (cm)')
        ax.set_ylabel('Depth (cm)')
        ax.set_zlabel('Height (cm)')
        
        ax.set_xlim(0, room_width)
        ax.set_ylim(0, room_depth)
        ax.set_zlim(0, room_height)
        
        # Set title
        ax.set_title('3D Bathroom Layout')
        
        # Set equal aspect ratio
        # This is a bit tricky in 3D, but we can try to make it look proportional
        max_range = max(room_width, room_depth, room_height)
        mid_x = room_width / 2
        mid_y = room_depth / 2
        mid_z = room_height / 2
        ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        ax.set_zlim(0, max_range)
        
        # Set a good viewing angle
        ax.view_init(elev=30, azim=-60)
        
        plt.tight_layout()
        return fig