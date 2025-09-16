import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from utils.helpers import check_which_wall, convert_values
from models.bathroom import Bathroom

class Visualizer3D:
    def __init__(self, bathroom:Bathroom):
        """
        Initialize the 3D visualizer with room dimensions.
        
        Args:
            room_width: Width of the room in cm
            room_depth: Depth of the room in cm
            room_height: Height of the room in cm (default 250cm)
        """
        self.room_width = bathroom.width
        self.room_depth = bathroom.depth
        self.room_height = bathroom.height
        self.objects = bathroom.objects
        self.windows_doors = bathroom.windows_doors
        self.current_elev = 30
        self.current_azim = 30
        
        # Color mapping for different object types
        self.color_map = {
            "toilet": "blue",
            "sink": "green",
            "shower": "red",
            "bathtub": "purple",
            "washing machine": "orange",
            "double sink": "brown",
            "cabinet": "pink",
            "washing dryer": "orange",
            "washing machine dryer": "orange",
            "asymmetrical bathtub": "purple",
            "toilet bidet": "blue",
            "bathtub": "purple",
        }



    def visualize_door_windows(self, ax):
        # Ensure all parameters are of the correct type
        for windows_doors in self.windows_doors:
            parapet = 0
            name = windows_doors.name
            room_width = self.room_width
            room_depth = self.room_depth
            wall = windows_doors.wall
            width = windows_doors.width
            height = windows_doors.height
            x,y = windows_doors.position
            depth = windows_doors.depth
            # Draw windows and doors
                
                # Calculate vertices based on wall placement
            if wall == "top":
                vertices = [
                        [0, y, parapet],
                        [0, y + width, parapet],
                        [0, y + width, parapet + height],
                        [0, y, parapet + height]
                ]
                    
                # 3D Shadow as a box on the floor
                if 'door' in name.lower():
                    shadow_vertices = [
                            # Bottom rectangle
                        [0, y, parapet],
                        [0, y + width, parapet],
                        [0, y + width, parapet + height],
                        [0, y, parapet + height],
                            # Top rectangle (slightly raised)
                        [width, y, parapet],
                        [width, y + width, parapet],
                        [width, y + width, parapet + height],
                        [width, y, parapet + height],
                        ]
                
            elif wall == "bottom":
                vertices = [
                        [room_width, y, parapet],
                        [room_width, y + width, parapet],
                        [room_width, y + width, parapet + height],
                        [room_width, y, parapet + height]
                ]
                    
                # 3D Shadow as a box on the floor
                if 'door' in name.lower():
                    # Calculate shadow vertices, 75 cm into the room
                    shadow_vertices = [
                        [room_width, y, parapet],
                        [room_width, y + width, parapet],
                        [room_width, y + width, parapet + height],
                        [room_width, y, parapet + height],
                        [room_width - width, y, parapet],                 # Bottom-left
                        [room_width - width, y + width, parapet],         # Top-left
                        [room_width - width, y + width, parapet + height], # Top-right
                        [room_width - width, y, parapet + height]           # Bottom-right
                        ]
                
            elif wall == "right":
                vertices = [
                        [x, room_depth,parapet],  # Top-left corner
                        [x + width, room_depth, parapet],  # Top-right corner
                        [x + width, room_depth , parapet+height],  # Bottom-right corner
                        [x, room_depth,parapet+height]  # Bottom-left corner
                        ]
                        
                # 3D Shadow as a box on the floor
                if 'door' in name.lower():
                    shadow_vertices = [
                                [x, room_depth,parapet],  # Top-left corner
                                [x + width, room_depth, parapet],  # Top-right corner
                                [x + width, room_depth , parapet+height],  # Bottom-right corner
                                [x, room_depth,parapet+height] , # Bottom-left corner
                                [x, room_depth-width,parapet],  # Top-left corner
                                [x + width, room_depth-width, parapet],  # Top-right corner
                                [x + width, room_depth-width , parapet+height],  # Bottom-right corner
                                [x, room_depth-width,parapet+height]  # Bottom-left corner
                            ]

            elif wall == "left":
                vertices =  [
                            [x, 0,parapet],  # Top-left corner
                            [x + width, 0, parapet],  # Top-right corner
                            [x + width, 0 , parapet+height],  # Bottom-right corner
                            [x,0,parapet+height]  # Bottom-left corner
                        ]
                    
                # 3D Shadow as a box on the floor
                if 'door' in name.lower():
                    shadow_vertices = [
                            [x, 0,parapet],  # Top-left corner
                            [x + width, 0, parapet],  # Top-right corner
                            [x + width, 0 , parapet+height],  # Bottom-right corner
                            [x, 0,parapet+height] , # Bottom-left corner
                            
                            [x, width,parapet],  # Top-left corner
                            [x + width,width, parapet],  # Top-right corner
                            [x + width, width , parapet+height],  # Bottom-right corner
                            [x, width,parapet+height]  # Bottom-left corner
                            ]
                        
            # Draw the window or door
            color = 'skyblue' if 'window' in name.lower() else 'brown'
            alpha = 0.5 if 'window' in name.lower() else 1.0
            wall_feature = Poly3DCollection([vertices], color=color, alpha=alpha, edgecolor='black')
            ax.add_collection3d(wall_feature)
            # Draw the 3D shadow for doors
            if 'door' in name.lower():
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
            ax.text(cx, cy, cz + 10, name, color='black', ha='center', va='center')

    # visuaize placed objects
    def visualize_placed_objects(self,ax):
        for object in self.objects:
            obj = object['object']
            z = 0 # currently all objects are on the floor
            name = obj.object_type
            room_width = self.room_width
            room_depth = self.room_depth
            room_height = self.room_height
            x,y = obj.position
            top, left,right,bottom = obj.shadow
            w = obj.width
            d = obj.depth
            h = obj.height
            
            shadow_x = x - top
            shadow_y = y - left
            shadow_w = w + left + right
            shadow_d = d + bottom + top

            
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
            color = self.color_map[name]

            obj_3d = Poly3DCollection(faces, color=color, alpha=0.8, edgecolor='black')
            ax.add_collection3d(obj_3d)
            text_offset = 5  # Adjust this value to control the height of the text above the object
            ax.text(x + w / 2, y + d / 2, z + h + text_offset, name, 
                color='black', ha='center', va='bottom', fontsize=10, weight='bold')
            # Label the object on the top face
            # ax.text(x + w / 2, y + d / 2, z + h, name, color='white', ha='center', va='center', fontsize=10)
    def visualize_room_with_shadows_3d(self):
        """Create a 3D visualization of the bathroom layout.
        
        Args:
            bathroom_size: Tuple of (width, depth) of the bathroom
            placed_objects: List of objects placed in the bathroom
            windows_doors: List of windows and doors in the bathroom
            
        Returns:
            matplotlib.figure.Figure: A 3D figure that can be displayed and saved
        """
        room_width = self.room_width
        room_depth = self.room_depth
        room_height = self.room_height

                

        plt.ion()
        # Create 3D figure - smaller size
        fig = plt.figure(figsize=(6, 6), dpi=100)
        ax = fig.add_subplot(111, projection='3d')
        
        # Use numpy arrays for aspect ratio to ensure proper data types
        ax.set_box_aspect(np.array([float(room_width), float(room_depth), float(room_height)]))  # Aspect ratio
        
        # Room boundaries - use float values
        ax.set_xlim(0.0, float(room_width))
        ax.set_ylim(0.0, float(room_depth))
        ax.set_zlim(0.0, float(room_height))
        ax.set_xlabel('Width (X)')
        ax.set_ylabel('Depth (Y)')
        ax.set_zlabel('Height (Z)')
        ax.set_title('3D Room Layout')
        
        # Show color-name mapping for objects from top to bottom
        for i, (name, color) in enumerate(self.color_map.items()):
            ax.text(float(room_width) + 1.0, float(room_depth) - i*30.0, float(room_height), 
                    f"{name}: {color}", color=color, fontsize=10)
                    
        # Visualize doors, windows and objects
        self.visualize_door_windows(ax)
        self.visualize_placed_objects(ax) 
        
        # Initial view angle
        ax.view_init(elev=float(self.current_elev), azim=float(self.current_azim))
        # fig.canvas.draw()
        # fig.tight_layout()
        # plt.ioff()

        
        return fig
    def draw_3d_room(self):
        """
        Draw a 3D visualization of the bathroom layout.
        
        Args:
            objects: List of objects with their positions and dimensions
            doors: List of doors and windows (optional)
            
        Returns:
            matplotlib.figure.Figure: A 3D figure that can be displayed and saved
        """
        room_width, room_depth, room_height = self.room_width, self.room_depth, self.room_height
        objects = self.objects
        doors = self.windows_doors
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

                name = obj['object'].name
                width = obj['object'].width
                depth = obj['object'].depth
                height = obj['object'].height
                shadow = obj['object'].shadow
                position = obj['object'].position
                wall = obj['object'].wall
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